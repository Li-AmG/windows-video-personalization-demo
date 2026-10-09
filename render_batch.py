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
        "[1:v]scale=250:-1,split=2[logo_main][logo_outro];"
        "[0:v][logo_main]overlay=W-w-75:75:enable='between(t,1,6.8)'[v1];"
        f"[v1]drawtext=fontfile='{font_path}':text='PERSONALIZED FOR':"
        "fontcolor=#5DD9C1:fontsize=28:x=135:y=505:enable='between(t,1.5,6.8)'[v2];"
        f"[v2]drawtext=fontfile='{font_path}':text='{customer}':"
        "fontcolor=white:fontsize=58:box=1:boxcolor=#0A1424@0.85:boxborderw=20:"
        "x=125:y=545:enable='between(t,1.5,6.8)'[v3];"
        "[v3]drawbox=x=0:y=0:w=iw:h=ih:color=#07111F@0.96:t=fill:enable='between(t,7,10)'[v4];"
        "[v4][logo_outro]overlay=(W-w)/2:(H-h)/2-90:enable='between(t,7,10)'[v5];"
        f"[v5]drawtext=fontfile='{font_path}':text='Prepared exclusively for {customer}':"
        "fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2+95:"
        "alpha='if(lt(t,7),0,min(1,(t-7)/0.45))':enable='between(t,7,10)'[vout]"
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
