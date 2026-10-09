from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent


def ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def probe_ok(path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg(), "-v", "error", "-i", str(path), "-f", "null", "-"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def escape_drawtext(value: str) -> str:
    return value.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")


def render(row: dict[str, str], config: dict, force: bool) -> str:
    required = ("customer_id", "customer_name", "logo_file")
    missing = [key for key in required if not row.get(key)]
    if missing:
        raise ValueError(f"missing values: {', '.join(missing)}")

    master = ROOT / config["master_video"]
    logo = ROOT / row["logo_file"]
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f"{row['customer_id']}.mp4"
    if output.exists() and not force and probe_ok(output):
        return "skipped (valid output already exists)"
    for path in (master, logo):
        if not path.exists():
            raise FileNotFoundError(path)

    font = Path(config["font"])
    if not font.exists():
        raise FileNotFoundError(font)
    customer = escape_drawtext(row["customer_name"])
    font_path = str(font).replace("\\", "/").replace(":", r"\:")
    filters = (
        "[1:v]scale=220:-1[logo];"
        "[0:v][logo]overlay=W-w-40:40:enable='between(t,0.5,2.8)'[v1];"
        f"[v1]drawtext=fontfile='{font_path}':text='{customer}':"
        "fontcolor=white:fontsize=44:box=1:boxcolor=black@0.55:boxborderw=18:"
        "x=(w-text_w)/2:y=h-text_h-70:enable='between(t,1.2,3.8)'[v2];"
        f"[v2]drawtext=fontfile='{font_path}':text='Prepared for {customer}':"
        "fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:"
        "alpha='if(lt(t,4),0,min(1,(t-4)/0.5))':enable='between(t,4,5.8)'[vout]"
    )
    command = [
        ffmpeg(), "-y", "-i", str(master), "-i", str(logo),
        "-filter_complex", filters, "-map", "[vout]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
        "-c:a", "aac", "-movflags", "+faststart", str(output),
    ]
    run(command)
    if not probe_ok(output):
        raise RuntimeError("FFmpeg produced an unreadable output")
    return "rendered and validated"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render personalized videos from CSV data.")
    parser.add_argument("--config", default="template.json")
    parser.add_argument("--data", default="customers.csv")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = json.loads((ROOT / args.config).read_text(encoding="utf-8"))
    failures = 0
    with (ROOT / args.data).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = row.get("customer_id") or "unknown-row"
            try:
                logging.info("%s: %s", key, render(row, config, args.force))
            except Exception as exc:
                failures += 1
                logging.error("%s: %s", key, exc)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
