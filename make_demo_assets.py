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

background = Image.new("RGB", (1280, 720))
pixels = background.load()
for y in range(720):
    for x in range(1280):
        pixels[x, y] = (18 + x // 32, 32 + y // 18, 58 + x // 40)
draw = ImageDraw.Draw(background)
title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 76)
subtitle = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 34)
small = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 25)
draw.rounded_rectangle((85, 85, 1195, 635), radius=32, fill=(8, 15, 30, 190), outline="#5DD9C1", width=4)
draw.text((130, 130), "PRODUCT LAUNCH", font=title, fill="white")
draw.text((134, 238), "Reusable master video", font=subtitle, fill="#5DD9C1")
draw.line((135, 305, 720, 305), fill="#5DD9C1", width=4)
draw.text((135, 350), "One video. Many customers.", font=subtitle, fill="white")
draw.text((135, 410), "Logo, name and outro are supplied from CSV.", font=small, fill="#D5E5F2")
draw.rounded_rectangle((830, 340, 1100, 510), radius=24, fill="#16283D", outline="#6D88A4", width=3)
draw.text((890, 400), "MASTER", font=subtitle, fill="#AFC4D8")
background.save(ROOT / "master-background.png")

subprocess.run(
    [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y",
        "-loop", "1", "-i", str(ROOT / "master-background.png"),
        "-f", "lavfi", "-i", "sine=frequency=330:duration=10",
        "-t", "10", "-r", "30",
        "-vf", "zoompan=z='min(zoom+0.0005,1.06)':d=300:s=1280x720:fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(ROOT / "master.mp4"),
    ],
    check=True,
)
