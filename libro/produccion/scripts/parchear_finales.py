#!/usr/bin/env python3
"""Apply explicit, manual edits to one final comic PNG through Kie.

Each payload deliberately contains only the existing final PNG and the short
edit instruction. It never attaches character sheets, guide images, or the
original narrative prompt, because any of those can contradict a local fix.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import mantener_cola_paralela_v9_referencias as v9


REPO = Path(__file__).resolve().parents[3]
PRODUCTION = REPO / "libro/produccion"
PATCH_DIR = "final-patched"
VALID_RESOLUTIONS = {"2K", "4K"}


class PatchError(ValueError):
    """The patch request is invalid or cannot safely be resumed."""


@dataclass(frozen=True)
class Patch:
    run_id: str
    page_id: str
    instruction: str
    resolution: str = "2K"
    enabled: bool = True
    replace_existing: bool = False


@dataclass(frozen=True)
class PatchPaths:
    source: Path
    output: Path
    prompt_snapshot: Path
    receipt: Path
    retries: Path


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PatchError(f"No existe el archivo: {path}") from error
    except json.JSONDecodeError as error:
        raise PatchError(f"JSON inválido en {path}: {error}") from error
    if not isinstance(value, dict):
        raise PatchError(f"El JSON debe ser un objeto: {path}")
    return value


def patch_from_value(value: object, label: str) -> Patch:
    if not isinstance(value, dict):
        raise PatchError(f"{label} debe ser un objeto.")
    run_id = value.get("run_id")
    page_id = value.get("page_id")
    instruction = value.get("instruction")
    resolution = value.get("resolution", "2K")
    enabled = value.get("enabled", True)
    replace_existing = value.get("replace_existing", False)
    if not isinstance(run_id, str) or Path(run_id).name != run_id:
        raise PatchError(f"{label}.run_id debe ser un identificador de corrida.")
    if not isinstance(page_id, str) or not page_id:
        raise PatchError(f"{label}.page_id debe ser texto no vacío.")
    if not isinstance(instruction, str) or not instruction.strip():
        raise PatchError(f"{label}.instruction debe ser texto no vacío.")
    if resolution not in VALID_RESOLUTIONS:
        raise PatchError(f"{label}.resolution debe ser 2K o 4K.")
    if not isinstance(enabled, bool) or not isinstance(replace_existing, bool):
        raise PatchError(f"{label}.enabled y replace_existing deben ser booleanos.")
    return Patch(run_id, page_id, instruction.strip(), resolution, enabled, replace_existing)


def manifest_patches(path: Path) -> list[Patch]:
    manifest = load_json(path)
    if manifest.get("schema_version") != 1:
        raise PatchError("El manifiesto requiere schema_version: 1.")
    entries = manifest.get("patches")
    if not isinstance(entries, list):
        raise PatchError("El manifiesto requiere una lista patches.")
    patches = [patch_from_value(value, f"patches[{index}]") for index, value in enumerate(entries)]
    enabled = [patch for patch in patches if patch.enabled]
    keys = [(patch.run_id, patch.page_id) for patch in enabled]
    if len(keys) != len(set(keys)):
        raise PatchError("Hay más de un parche habilitado para la misma página.")
    return enabled


def patch_from_image(image: Path, instruction: str, four_k: bool, replace_existing: bool) -> Patch:
    image = image.resolve()
    expected_dir = "finales-4k" if four_k else "finales-2k"
    if image.parent.name != expected_dir:
        raise PatchError(f"{image} debe estar dentro de {expected_dir}; usa --4k sólo para finales 4K.")
    return Patch(image.parent.parent.name, image.stem, instruction.strip(), "4K" if four_k else "2K", True, replace_existing)


def resolve(patch: Patch) -> PatchPaths:
    config_path = PRODUCTION / "corridas" / f"{patch.run_id}.json"
    config = load_json(config_path)
    generation = config.get("generation")
    if not isinstance(generation, dict) or generation.get("model") != "gpt-image-2" or generation.get("aspect_ratio") != "2:3":
        raise PatchError(f"La corrida no declara gpt-image-2 2:3: {config_path}")
    storage = {key: v9.queue.repo_path(value) for key, value in config.get("storage", {}).items()}
    source_dir = storage.get("final4k_output_dir" if patch.resolution == "4K" else "final_output_dir")
    if source_dir is None:
        raise PatchError(f"La corrida no declara salidas {patch.resolution}: {config_path}")
    source = source_dir / f"{patch.page_id}.png"
    if not v9.queue.is_png(source):
        raise PatchError(f"No existe la final {patch.resolution} para parchear: {source}")
    run_output = source_dir.parent
    output = run_output / PATCH_DIR / source.name
    snapshot_dir = PRODUCTION / "prompts-corridas" / patch.run_id / PATCH_DIR
    jobs_dir = PRODUCTION / "jobs" / patch.run_id / PATCH_DIR
    return PatchPaths(source, output, snapshot_dir / f"{patch.page_id}.txt", jobs_dir / f"{patch.page_id}.json", jobs_dir / "retries")


def materialized_prompt(patch: Patch) -> str:
    prompt = (
        "EDICIÓN SELECTIVA DE IMAGEN — AUTORIDAD SUPERIOR:\n"
        "La única imagen adjunta es la página final existente y es la autoridad visual completa.\n"
        f"Aplica exactamente esta corrección: {patch.instruction}\n"
        "Conserva todo lo demás tal como aparece en la imagen adjunta: composición, número y orden de viñetas, "
        "personajes, poses, vestuario, fondos, paleta, estilo y todo texto no afectado explícitamente. "
        "No agregues texto, logos, marcas de agua ni elementos nuevos."
    )
    if len(prompt) > 20_000:
        raise PatchError(f"El prompt de parche excede el límite de 20,000 caracteres ({len(prompt)}): {patch.page_id}")
    return prompt


def command_for(patch: Patch, paths: PatchPaths) -> list[str]:
    return [
        str(v9.queue.KIE), "image", "gpt-image-2", "--prompt-file", str(paths.prompt_snapshot),
        "--aspect-ratio", "2:3", "--resolution", patch.resolution, "--json",
        "--image", str(paths.source), "--save-job", str(paths.receipt),
    ]


def archive_receipt(paths: PatchPaths) -> None:
    if not paths.receipt.is_file():
        return
    job_id = load_json(paths.receipt).get("jobId", "unknown")
    paths.retries.mkdir(parents=True, exist_ok=True)
    paths.receipt.replace(paths.retries / f"{paths.receipt.stem}--{job_id}.json")


def receipt_matches_prompt(paths: PatchPaths, prompt: str) -> bool:
    """A downloaded PNG plus this exact receipt is the current patch, not stale work."""
    if not paths.receipt.is_file():
        return False
    try:
        receipt = load_json(paths.receipt)
    except PatchError:
        return False
    submitted = receipt.get("submittedPayload")
    if not isinstance(submitted, dict):
        return False
    submitted_input = submitted.get("input")
    return isinstance(submitted_input, dict) and submitted_input.get("prompt") == prompt


def replace_completed_patch(paths: PatchPaths) -> None:
    """Explicitly discard only a prior patched derivative, never the source PNG."""
    if paths.output.is_file():
        paths.output.unlink()
    archive_receipt(paths)


def submit(patch: Patch, paths: PatchPaths) -> tuple[bool, str]:
    paths.prompt_snapshot.parent.mkdir(parents=True, exist_ok=True)
    paths.receipt.parent.mkdir(parents=True, exist_ok=True)
    paths.prompt_snapshot.write_text(materialized_prompt(patch), encoding="utf-8")
    result = subprocess.run(command_for(patch, paths), text=True, capture_output=True)
    detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, detail


def poll(paths: PatchPaths) -> dict:
    if not paths.receipt.is_file():
        return {"action": "ready_to_submit"}
    receipt = load_json(paths.receipt)
    job_id = receipt.get("jobId")
    if not isinstance(job_id, str) or not job_id:
        raise PatchError(f"Recibo sin jobId: {paths.receipt}")
    item, error = v9.queue.status(job_id)
    if item is None:
        return {"action": "no_credits" if v9.queue.no_credits(error) else "status_error", "detail": error, "job_id": job_id}
    status = item["status"]
    if v9.queue.no_credits(json.dumps(item.get("error", {}), ensure_ascii=False)):
        return {"action": "no_credits", "job_id": job_id, "error": item.get("error")}
    if status == "succeeded" and item.get("outputUrl"):
        paths.output.parent.mkdir(parents=True, exist_ok=True)
        download = subprocess.run(["curl", "-L", "--fail", "--output", str(paths.output), item["outputUrl"]], text=True, capture_output=True)
        if download.returncode == 0 and v9.queue.is_png(paths.output):
            return {"action": "completed", "job_id": job_id, "output": str(paths.output)}
        return {"action": "download_error", "job_id": job_id, "detail": download.stderr.strip()}
    result = {"action": status, "job_id": job_id}
    if item.get("error"):
        result["error"] = item["error"]
    return result


def execute(patch: Patch, live: bool, wait: bool, interval_seconds: int, poll_only: bool) -> dict:
    paths = resolve(patch)
    prompt = materialized_prompt(patch)
    base = {
        "run_id": patch.run_id, "page_id": patch.page_id, "resolution": patch.resolution,
        "source": str(paths.source), "output": str(paths.output),
        "attachments": [f"final-{patch.resolution.lower()}-{patch.page_id}"], "prompt_characters": len(prompt),
    }
    exists = v9.queue.is_png(paths.output)
    if poll_only:
        if exists:
            return {**base, "action": "completed"}
        status = poll(paths)
        if status["action"] == "ready_to_submit":
            return {**base, "action": "no_receipt", "detail": "No hay recibo local que se pueda consultar."}
        return {**base, **status}
    if exists and not patch.replace_existing:
        return {**base, "action": "completed"}
    if exists and receipt_matches_prompt(paths, prompt):
        return {**base, "action": "completed"}
    if not live:
        return {**base, "action": "dry_run_would_replace" if exists else "dry_run", "command": command_for(patch, paths)}
    if exists:
        replace_completed_patch(paths)
    status = poll(paths)
    if status["action"] == "ready_to_submit":
        ok, detail = submit(patch, paths)
        if not ok:
            return {**base, "action": "submission_error", "detail": detail}
        status = {"action": "submitted", "receipt": str(paths.receipt)}
    if not wait or status["action"] not in {"submitted", "queued", "running", "status_error"}:
        return {**base, **status}
    while True:
        time.sleep(interval_seconds)
        status = poll(paths)
        if status["action"] not in {"queued", "running", "status_error"}:
            return {**base, **status}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="Manifiesto JSON; procesa sólo entradas enabled: true.")
    source.add_argument("--image", type=Path, help="Final dentro de finales-2k (o finales-4k con --4k).")
    parser.add_argument("--instruction", help="Corrección requerida con --image.")
    parser.add_argument("--4k", dest="four_k", action="store_true", help="Usa una final 4K con --image.")
    parser.add_argument("--replace-existing", action="store_true", help="Con --image, reemplaza explícitamente un PNG existente en final-patched.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--poll-only", action="store_true", help="Sólo consulta el recibo existente; nunca envía ni reemplaza un parche.")
    parser.add_argument("--wait", action="store_true", help="Después de enviar, consulta Kie y descarga el PNG al terminar.")
    parser.add_argument("--interval-seconds", type=int, default=30, help="Intervalo de poll para --wait (predeterminado: 30).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.interval_seconds <= 0:
        raise SystemExit("--interval-seconds debe ser positivo.")
    if args.poll_only and not args.live:
        raise SystemExit("--poll-only requiere --live y nunca envía trabajos.")
    if args.image is not None:
        if not args.instruction:
            raise SystemExit("--instruction es obligatorio con --image.")
        patches = [patch_from_image(args.image, args.instruction, args.four_k, args.replace_existing)]
    else:
        if args.instruction or args.four_k or args.replace_existing:
            raise SystemExit("--instruction, --4k y --replace-existing sólo se usan con --image; decláralos dentro del manifiesto.")
        patches = manifest_patches(args.manifest.resolve())
    if not patches:
        print(json.dumps({"action": "nothing_to_do", "detail": "No hay parches habilitados."}, ensure_ascii=False, indent=2))
        return 0
    results = []
    exit_code = 0
    for patch in patches:
        try:
            result = execute(patch, args.live, args.wait, args.interval_seconds, args.poll_only)
        except PatchError as error:
            result = {"run_id": patch.run_id, "page_id": patch.page_id, "action": "error", "detail": str(error)}
        results.append(result)
        if result["action"] in {"error", "submission_error", "no_credits", "download_error"}:
            exit_code = 2
            if result["action"] == "no_credits":
                break
    print(json.dumps({"action": "patches_processed", "results": results}, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
