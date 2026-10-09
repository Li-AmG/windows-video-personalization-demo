from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def logo(path: Path, color: str, text: str) -> None:
    image = Image.new("RGBA", (520, 180), color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 62)
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((520 - (box[2] - box[0])) / 2, 50), text, fill="white", font=font)
    image.save(path)


logo(ASSETS / "acme.png", "#136F63", "ACME")
logo(ASSETS / "north.png", "#375A7F", "NORTH")

subprocess.run(
    [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y",
        "-f", "lavfi", "-i", "color=c=#20262e:s=1280x720:d=6:r=30",
        "-f", "lavfi", "-i", "sine=frequency=330:duration=6",
        "-vf", "drawgrid=width=80:height=80:color=white@0.06:t=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(ROOT / "master.mp4"),
    ],
    check=True,
)
