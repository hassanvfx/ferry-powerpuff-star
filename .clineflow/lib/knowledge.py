#!/usr/bin/env python3
"""Tenant-scoped, additive ClineFlow knowledge records.

Records use JSON syntax in .yml files. JSON is valid YAML, keeps the core
dependency-free in normal use, and makes immutable records unambiguous.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

LEDGERS = ("specification", "verification", "goals", "last_session", "timeline")
SCHEMA = 3
TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TENANT_RE = re.compile(r"^t-[0-9a-f]{32}$")
STREAM_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def root_from(value: str) -> Path:
    root = Path(value).resolve()
    if not (root / "knowledge").is_dir():
        fail(f"knowledge/ does not exist under {root}")
    return root


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def private_identity_path(root: Path) -> Path:
    common = git(root, "rev-parse", "--git-common-dir")
    if not common:
        fail("tenant identity requires a Git repository")
    path = Path(common)
    if not path.is_absolute():
        path = (root / path).resolve()
    return path / "clineflow" / "tenant-identity.json"


def normalize_email(value: str) -> str:
    value = value.strip()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        fail("an explicit Git author email must contain a local part and domain")
    local, domain = value.rsplit("@", 1)
    return f"{local}@{domain.lower()}"


def normalize_machine(value: str) -> str:
    value = value.strip().lower()
    if not value:
        fail("machine name is empty")
    return value


def normalize_mac(value: str) -> str:
    compact = re.sub(r"[^0-9A-Fa-f]", "", value)
    if not re.fullmatch(r"[0-9a-fA-F]{12}", compact):
        fail("MAC address must contain exactly 12 hexadecimal characters")
    return compact.lower()


def configured_identity(root: Path) -> tuple[str, str, str | None] | None:
    email = os.environ.get("GIT_AUTHOR_EMAIL", "").strip()
    if not email:
        email = git(root, "config", "--get", "author.email")
    if not email:
        email = git(root, "config", "--get", "user.email")
    name = os.environ.get("GIT_AUTHOR_NAME", "").strip() or git(root, "config", "--get", "author.name") or git(root, "config", "--get", "user.name") or None
    if email:
        return "email", normalize_email(email), name.strip() if name else None
    hostname = socket.gethostname().strip()
    if hostname:
        return "machine", normalize_machine(hostname), name.strip() if name else None
    node = uuid.getnode()
    if node:
        return "mac", normalize_mac(f"{node:012x}"), name.strip() if name else None
    return None


def tenant_id(source: str, value: str) -> str:
    return "t-" + digest_bytes(f"clineflow-tenant-v1:{source}:{value}".encode())[:32]


def load_pinned(root: Path) -> dict[str, Any] | None:
    path = private_identity_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read pinned tenant identity: {error}")
    if not isinstance(data, dict) or not TENANT_RE.fullmatch(str(data.get("id", ""))):
        fail("pinned tenant identity is malformed")
    return data


def write_pinned(root: Path, source: str, value: str, name: str | None) -> dict[str, Any]:
    path = private_identity_path(root)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = {"schema": 1, "source": source, "value": value, "id": tenant_id(source, value), "name": name}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    return data


def identity(root: Path, pin: bool = True) -> tuple[dict[str, Any], dict[str, Any] | None]:
    detected = configured_identity(root)
    if detected is None:
        fail("no Git author email, machine name, or MAC address is available; run identity set")
    source, value, name = detected
    detected_data = {"source": source, "value": value, "id": tenant_id(source, value), "name": name}
    pinned = load_pinned(root)
    if pinned is None and pin:
        pinned = write_pinned(root, source, value, name)
    if pinned is not None and (pinned["source"] != source or pinned["value"] != value):
        return pinned, detected_data
    return pinned or detected_data, None


def yaml_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except OSError as error:
        fail(f"{path}: cannot read record: {error}")
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError:
            fail(f"{path}: non-JSON YAML needs PyYAML from .clineflow/core-requirements.lock: {json_error}")
        try:
            value = yaml.safe_load(path.read_text())
        except yaml.YAMLError as error:
            fail(f"{path}: invalid YAML: {error}")
    if not isinstance(value, dict):
        fail(f"{path}: record must be a mapping")
    return value


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        Path(temporary).replace(path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            Path(temporary).unlink()


@contextlib.contextmanager
def lock(root: Path) -> Iterator[None]:
    directory = root / "knowledge" / ".clineflow-sync.lock"
    try:
        directory.mkdir()
    except FileExistsError:
        fail("knowledge synchronization is already running in this worktree")
    try:
        yield
    finally:
        directory.rmdir()


def journals(root: Path) -> list[Path]:
    return sorted(path for path in (root / "knowledge" / "journals").glob("*/*.md") if path.name != "index.md")


def topic_path(root: Path, topic: str) -> Path:
    if not TOPIC_RE.fullmatch(topic):
        fail("topic must be a lowercase hyphenated slug")
    return root / "knowledge" / "journals" / topic


def frontmatter(title: str, description: str, author: dict[str, Any], topic: str, stream: str) -> str:
    author_lines = ["author:", f"  id: {author['id']}"]
    if author.get("name"):
        author_lines.append(f"  name: {json.dumps(author['name'])}")
    return "\n".join([
        "---", "type: Engineering Journal", f"title: {json.dumps(title)}", f"description: {json.dumps(description)}",
        "tags: [engineering]", "status: draft", *author_lines, "clineflow:", f"  schema: {SCHEMA}", f"  topic: {topic}", f"  stream: {stream}",
        "generated:", "  by: clineflow/3", f"  at: {now()}", "---", "", "# Goal", "", "Describe the outcome and success criteria.", "",
        "# Task Contract", "", "- Intended outcome:", "- Observable success criteria:", "- Constraints and non-goals:", "- Open questions and assumptions:", "",
        "# Execution Boundaries", "", "- Authorized scope and exclusions:", "- Affected interfaces, owners, and relevant side effects:", "- Escalate before changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria:", "- Delegation integrator and remaining integration checks, when applicable:", "", "# Handoff Topology", "", "- Selection: single handoff or milestone chain, and why:", "- Parent integrator and final end-to-end acceptance, when applicable:", "- Milestones: for each independently testable boundary, record its owner and exclusions, entry condition, inputs and outputs, local acceptance proof, downstream consumer, dependencies, contributor, integrator, and escalation or rollback condition:", "",
        "# Existing Approaches", "", "- Relevant project patterns or established approaches considered:", "- Why the selected approach fits, or why a novel approach is necessary:", "",
        "# Planned Proof", "", "- Deterministic checks to run and the rules they enforce:", "- Integration checks to run:", "- Remaining judgment or coverage limits:", "",
        "# Status", "", "- [ ] Planned", "- [ ] In progress", "- [ ] Complete", "", "# Work Log", "", "# Decisions", "", "# Verification Results", "", "Record commands run and their factual outcomes separately from planned proof, including failures and gaps.", "", "# Open Issues", "", "# References", "",
    ])


def cmd_identity(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    if args.identity_command == "set":
        normalizers = {"email": normalize_email, "machine": normalize_machine, "mac": normalize_mac}
        name = args.name.strip() if args.name else None
        pinned = write_pinned(root, args.source, normalizers[args.source](args.value), name)
        print(json.dumps({"id": pinned["id"], "source": pinned["source"], "name": pinned.get("name")}, indent=2))
        return
    pinned, drift = identity(root, pin=True)
    response = {"id": pinned["id"], "source": pinned["source"], "name": pinned.get("name"), "pinned": True}
    if drift:
        response["detected_change"] = {"source": drift["source"], "id": drift["id"]}
        response["action"] = "Run `knowledge identity set` to change the pinned tenant."
    print(json.dumps(response, indent=2))


def cmd_topics(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    for directory in sorted((root / "knowledge" / "journals").iterdir()):
        if directory.is_dir() and TOPIC_RE.fullmatch(directory.name):
            print(directory.name)


def cmd_journal(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    pinned, drift = identity(root)
    if drift:
        fail("detected identity differs from the pinned tenant; inspect it with `knowledge identity` or change it explicitly")
    folder = topic_path(root, args.topic)
    if args.journal_command == "resume":
        if not STREAM_RE.fullmatch(args.stream):
            fail("stream must be a UUID")
        matches = list(folder.glob(f"{args.stream}--{pinned['id']}.md"))
        if len(matches) != 1:
            fail("no matching stream belongs to the pinned tenant")
        print(matches[0].relative_to(root).as_posix())
        return
    stream = str(uuid.uuid4())
    path = folder / f"{stream}--{pinned['id']}.md"
    if path.exists():
        fail("generated journal path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter(args.title, args.description or f"Tenant journal for {args.topic}.", pinned, args.topic, stream))
    print(path.relative_to(root).as_posix())


def journal_metadata(path: Path) -> dict[str, str]:
    text = path.read_text()
    topic = re.search(r"^  topic: ([a-z0-9-]+)$", text, re.MULTILINE)
    stream = re.search(r"^  stream: ([0-9a-f-]{36})$", text, re.MULTILINE)
    author = re.search(r"^  id: (t-[0-9a-f]{32})$", text, re.MULTILINE)
    if not (topic and stream and author):
        fail(f"{path}: tenant journal metadata is missing or malformed")
    return {"topic": topic.group(1), "stream": stream.group(1), "author": author.group(1)}


def parse_assignment(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        fail(f"{label} must use key=value")
    key, item = value.split("=", 1)
    if not key or not item:
        fail(f"{label} must use non-empty key=value")
    return key, item


def cmd_record(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    pinned, drift = identity(root)
    if drift:
        fail("detected identity differs from the pinned tenant; change it explicitly before recording work")
    journal = (root / args.journal).resolve()
    try:
        relative_journal = journal.relative_to(root).as_posix()
    except ValueError:
        fail("journal must be inside the repository")
    metadata = journal_metadata(journal)
    if metadata["topic"] != args.topic or metadata["stream"] != args.stream or metadata["author"] != pinned["id"]:
        fail("record topic, stream, author, and journal metadata must agree")
    reviews = {name: "unchanged" for name in LEDGERS}
    for assignment in args.review:
        ledger, state = parse_assignment(assignment, "--review")
        if ledger not in LEDGERS or state not in {"unchanged", "changed"}:
            fail("review must be one of specification, verification, goals, last_session, timeline = unchanged|changed")
        reviews[ledger] = state
    changes: list[dict[str, str]] = []
    for assignment in args.item:
        key, statement = parse_assignment(assignment, "--item")
        parts = key.split(":", 1)
        if len(parts) != 2 or parts[0] not in LEDGERS or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", parts[1]):
            fail("item key must use ledger:item-id")
        changes.append({"ledger": parts[0], "id": parts[1], "statement": statement})
        reviews[parts[0]] = "changed"
    record_id = str(uuid.uuid4())
    snapshot_relative = f"knowledge/updates/{args.topic}/snapshots/{record_id}.md"
    snapshot = root / snapshot_relative
    journal_bytes = journal.read_bytes()
    record = {
        "schema": SCHEMA, "id": record_id, "at": now(), "author": {"id": pinned["id"], **({"name": pinned["name"]} if pinned.get("name") else {})},
        "topic": args.topic, "stream": args.stream, "journal": {"path": relative_journal, "sha256": digest_bytes(journal_bytes), "snapshot": snapshot_relative},
        "reviews": reviews, "ledger_changes": changes, "timeline": {"summary": args.timeline or args.summary}, "log": {"summary": args.summary},
        "revises": args.revises, "retracts": args.retracts, "resolves": args.resolves,
    }
    destination = root / "knowledge" / "updates" / args.topic / f"{record_id}--{pinned['id']}.yml"
    if destination.exists():
        fail("generated record path already exists")
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(journal_bytes)
    write_json_atomic(destination, record)
    print(destination.relative_to(root).as_posix())


def records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    update_root = root / "knowledge" / "updates"
    result: list[tuple[Path, dict[str, Any]]] = []
    if not update_root.exists():
        return result
    for path in sorted(update_root.glob("*/*.yml")):
        record = yaml_json(path)
        result.append((path, record))
    return result


def validate_record(root: Path, path: Path, record: dict[str, Any], read_bytes: Any = None) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != SCHEMA: errors.append("schema must be 3")
    identifier = str(record.get("id", ""))
    if not STREAM_RE.fullmatch(identifier): errors.append("id must be a UUID")
    topic = str(record.get("topic", ""))
    if not TOPIC_RE.fullmatch(topic): errors.append("topic must be a slug")
    author = record.get("author")
    if not isinstance(author, dict) or not TENANT_RE.fullmatch(str(author.get("id", ""))): errors.append("author.id must be an opaque tenant ID")
    if any(key in record for key in ("email", "hostname", "mac", "identity")): errors.append("raw identity data is forbidden")
    expected_name = f"{identifier}--{author.get('id')}.yml" if isinstance(author, dict) else ""
    if path.name != expected_name: errors.append("filename must be UUID--tenant.yml")
    if topic == "migration" and record.get("legacy") is True:
        return errors
    journal = record.get("journal")
    if not isinstance(journal, dict): errors.append("journal is required")
    else:
        path_value = journal.get("path")
        if not isinstance(path_value, str) or path_value.startswith("/") or ".." in Path(path_value).parts:
            errors.append("journal.path must be a repository-relative path")
        else:
            target = root / path_value
            if read_bytes is None and not target.is_file(): errors.append("journal.path does not exist")
            else:
                try:
                    snapshot = journal.get("snapshot")
                    if snapshot:
                        if not isinstance(snapshot, str) or not snapshot.startswith("knowledge/updates/") or ".." in Path(snapshot).parts:
                            raise ValueError(snapshot)
                        content = read_bytes(snapshot) if read_bytes else (root / snapshot).read_bytes()
                    else:
                        content = None
                except (OSError, ValueError):
                    errors.append("journal snapshot does not exist")
                else:
                    if content is not None and journal.get("sha256") != digest_bytes(content): errors.append("journal digest does not match its immutable snapshot")
                    if not isinstance(journal.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", str(journal.get("sha256"))): errors.append("journal.sha256 must be a SHA-256 digest")
    reviews = record.get("reviews")
    if not isinstance(reviews, dict) or set(reviews) != set(LEDGERS) or not all(value in {"unchanged", "changed"} for value in reviews.values()):
        errors.append("reviews must explicitly cover every ledger")
    return errors


def projection(root: Path, all_records: list[tuple[Path, dict[str, Any]]]) -> dict[str, str]:
    ordered = sorted((record for _, record in all_records), key=lambda item: (str(item.get("at", "")), str(item.get("id", ""))))
    items: dict[str, dict[str, list[dict[str, Any]]]] = {ledger: {} for ledger in LEDGERS}
    for record in ordered:
        for change in record.get("ledger_changes", []):
            if isinstance(change, dict) and change.get("ledger") in items:
                items[change["ledger"]].setdefault(str(change.get("id")), []).append({"record": record["id"], "statement": change.get("statement", "")})
    files: dict[str, str] = {}
    timestamp = ordered[-1]["at"] if ordered else None
    for ledger in LEDGERS:
        entries = [{"id": item_id, "alternatives": values, "unresolved": len(values) > 1} for item_id, values in sorted(items[ledger].items())]
        data: dict[str, Any] = {"version": SCHEMA, "updated_at": timestamp, "generated_at": timestamp, "ledger": ledger, "records": [record["id"] for record in ordered], "items": entries}
        if ledger == "specification": data.update({"confirmed": [], "assumptions": [], "constraints": [], "non_goals": [], "open_questions": [], "journal_refs": []})
        elif ledger == "verification": data.update({"acceptance_criteria": [], "regression_checks": [], "evidence_refs": [], "open_verification": [], "journal_refs": []})
        elif ledger == "goals": data.update({"active_goals": [], "priorities": [], "success_measures": [], "blocked_goals": [], "completed_goals": [], "journal_refs": []})
        elif ledger == "last_session": data.update({"latest_change": ordered[-1]["log"]["summary"] if ordered else None, "specification_summary": [], "verification_summary": [], "goals_summary": [], "next_recommended_step": None, "next_step_refs": [], "journal_refs": []})
        else: data["events"] = [{"at": r["at"], "actor": r["author"]["id"], "summary": r["timeline"]["summary"], "refs": [r["journal"]["path"]]} for r in ordered]
        files[f"clineflow_{ledger}.yml"] = json.dumps(data, indent=2) + "\n"
    log = ["# Knowledge Update Log", ""]
    for record in reversed(ordered): log.extend([f"## {record['at'][:10]}", "", f"* **{record['author']['id']}**: {record['log']['summary']}", ""])
    files["log.md"] = "\n".join(log)
    journal_lines = ["# Task Journals", ""]
    for path in journals(root):
        metadata = journal_metadata(path)
        journal_lines.append(f"* [{path.stem}]({path.relative_to(root / 'knowledge' / 'journals').as_posix()}) — topic `{metadata['topic']}`, tenant `{metadata['author']}`.")
    files["journals/index.md"] = "\n".join(journal_lines) + "\n"
    topics: dict[str, list[Path]] = {}
    for path in journals(root): topics.setdefault(journal_metadata(path)["topic"], []).append(path)
    for topic, members in topics.items():
        lines = [f"# Topic: {topic}", "", "Tenant work streams:", ""]
        for path in members:
            metadata = journal_metadata(path)
            lines.append(f"* [{path.stem}]({path.name}) — `{metadata['author']}` / `{metadata['stream']}`")
        files[f"topics/{topic}/index.md"] = "\n".join(lines) + "\n"
    return files


def cmd_sync(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    all_records = records(root)
    errors = [(path, error) for path, record in all_records for error in validate_record(root, path, record)]
    if errors:
        for path, error in errors: print(f"ERROR: {path.relative_to(root)}: {error}", file=sys.stderr)
        raise SystemExit(1)
    files = projection(root, all_records)
    fingerprint = digest_bytes("".join(digest_bytes(path.read_bytes()) for path, _ in all_records).encode())
    if args.check:
        for relative, expected in files.items():
            target = root / "knowledge" / relative
            if not target.is_file() or target.read_text() != expected:
                fail(f"generated projection is stale: knowledge/{relative}")
        print(f"Knowledge projections are current ({fingerprint}).")
        return
    with lock(root):
        for relative, content in files.items():
            write_json_atomic(root / "knowledge" / relative, json.loads(content) if relative.endswith(".yml") else content) if relative.endswith(".yml") else (root / "knowledge" / relative).parent.mkdir(parents=True, exist_ok=True) or (root / "knowledge" / relative).write_text(content)
        write_json_atomic(root / "knowledge" / ".clineflow-projection.json", {"schema": SCHEMA, "fingerprint": fingerprint, "generated_at": now()})
    print(f"Rebuilt {len(files)} local knowledge projections ({fingerprint}).")


def cmd_validate(args: argparse.Namespace) -> None:
    root = root_from(args.root)
    reader = None
    if args.mode == "staged":
        indexed = git(root, "ls-files", "--stage", "knowledge/updates").splitlines()
        all_records = []
        for line in indexed:
            parts = line.split(None, 3)
            if len(parts) != 4:
                continue
            path = Path(parts[3])
            if path.suffix != ".yml":
                continue
            try:
                record = json.loads(git(root, "show", f":{path.as_posix()}"))
            except json.JSONDecodeError as error:
                fail(f"{path}: staged record is not valid JSON-compatible YAML: {error}")
            all_records.append((root / path, record))
        def reader(relative: str) -> bytes:
            value = subprocess.run(["git", "-C", str(root), "show", f":{relative}"], capture_output=True, check=False)
            if value.returncode:
                raise OSError(relative)
            return value.stdout
    else:
        all_records = records(root)
    seen: set[str] = set(); failures = 0
    for path, record in all_records:
        identifier = str(record.get("id", ""))
        if identifier in seen:
            print(f"ERROR: duplicate record id: {identifier}", file=sys.stderr); failures += 1
        seen.add(identifier)
        for error in validate_record(root, path, record, reader):
            print(f"ERROR: {path.relative_to(root)}: {error}", file=sys.stderr); failures += 1
    changes = git(root, "diff", "--name-status", "HEAD" if args.mode == "working" else "--cached").splitlines()
    for change in changes:
        parts = change.split("\t")
        if len(parts) >= 2 and parts[-1].startswith("knowledge/updates/") and parts[0][0] in "MDR":
            print(f"ERROR: published update records are immutable: {parts[-1]}", file=sys.stderr); failures += 1
    if failures: raise SystemExit(1)
    print(f"Tenant knowledge validation passed: {len(all_records)} immutable record(s).")


def cmd_migrate(args: argparse.Namespace) -> None:
    root = root_from(args.root); knowledge = root / "knowledge"; baseline = knowledge / "baseline" / "schema-1"
    if (knowledge / "updates").exists():
        print("Knowledge is already in additive-record layout."); return
    with lock(root):
        baseline.mkdir(parents=True, exist_ok=True)
        old_files = [knowledge / f"clineflow_{ledger}.yml" for ledger in LEDGERS] + [knowledge / "log.md", knowledge / "journals" / "index.md"]
        for source in old_files:
            if source.exists():
                target = baseline / source.relative_to(knowledge)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                source.unlink()
        (knowledge / "updates" / "migration").mkdir(parents=True, exist_ok=True)
        identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, f"clineflow-schema-2:{root}"))
        record = {"schema": SCHEMA, "id": identifier, "at": now(), "author": {"id": "t-" + "0" * 32}, "topic": "migration", "stream": identifier, "legacy": True,
                  "journal": {"path": "knowledge/baseline/schema-1/log.md", "sha256": digest_bytes((baseline / "log.md").read_bytes()) if (baseline / "log.md").exists() else digest_bytes(b"")},
                  "reviews": {ledger: "changed" for ledger in LEDGERS}, "ledger_changes": [], "timeline": {"summary": "Migrated schema-1 ledger views to additive records."}, "log": {"summary": "Preserved schema-1 knowledge as a baseline archive."}, "revises": [], "retracts": [], "resolves": []}
        write_json_atomic(knowledge / "updates" / "migration" / f"{identifier}--{record['author']['id']}.yml", record)
    cmd_sync(argparse.Namespace(root=str(root), check=False))
    print("Migration preserved schema-1 views in knowledge/baseline/schema-1/. Stage only the reported migration files when ready.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="knowledge")
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    identity_parser = sub.add_parser("identity"); identity_sub = identity_parser.add_subparsers(dest="identity_command", required=True)
    identity_sub.add_parser("show")
    set_parser = identity_sub.add_parser("set"); set_parser.add_argument("source", choices=("email", "machine", "mac")); set_parser.add_argument("value"); set_parser.add_argument("--name")
    sub.add_parser("topics")
    journal_parser = sub.add_parser("journal"); journal_sub = journal_parser.add_subparsers(dest="journal_command", required=True)
    new = journal_sub.add_parser("new"); new.add_argument("--topic", required=True); new.add_argument("--title", required=True); new.add_argument("--description")
    resume = journal_sub.add_parser("resume"); resume.add_argument("--topic", required=True); resume.add_argument("--stream", required=True)
    record = sub.add_parser("record"); record.add_argument("--topic", required=True); record.add_argument("--stream", required=True); record.add_argument("--journal", required=True); record.add_argument("--summary", required=True); record.add_argument("--timeline"); record.add_argument("--review", action="append", default=[]); record.add_argument("--item", action="append", default=[]); record.add_argument("--revises", action="append", default=[]); record.add_argument("--retracts", action="append", default=[]); record.add_argument("--resolves", action="append", default=[])
    sync = sub.add_parser("sync"); sync.add_argument("--check", action="store_true")
    validate = sub.add_parser("validate"); validate.add_argument("--mode", choices=("working", "staged"), default="working")
    sub.add_parser("migrate")
    args = parser.parse_args()
    {"identity": cmd_identity, "topics": cmd_topics, "journal": cmd_journal, "record": cmd_record, "sync": cmd_sync, "validate": cmd_validate, "migrate": cmd_migrate}[args.command](args)


if __name__ == "__main__":
    main()
