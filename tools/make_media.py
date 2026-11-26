"""Makes the site's pictures and the trailer from the game's own kits.

Sources:
  screenshots  C:\\Playground\\UP\\RTS\\Builds\\ItchPage\\screenshots_0.5   (in-game, 1920 x 1080)
  icon         C:\\Playground\\UP\\RTS-merge\\Tools\\Discord\\icon.png
  trailer      C:\\Playground\\UP\\RTS\\Builds\\Trailer\\final               (needs ffmpeg on PATH)

Usage: python -I tools/make_media.py [--no-video]
Writes assets/img/*.jpg (large 1600 px for the hero and the gallery, card 800 px), favicons and assets/video/teaser.mp4.
"""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parents[1]
S5 = Path(r"C:\Playground\UP\RTS\Builds\ItchPage\screenshots_0.5")
ICON = Path(r"C:\Playground\UP\RTS-merge\Tools\Discord\icon.png")
TRAILER = Path(r"C:\Playground\UP\RTS\Builds\Trailer\final")
IMG = SITE / "assets" / "img"
VID = SITE / "assets" / "video"

# name on the site -> screenshot file. Every picture is the game's own frame.
SHOTS = {
    "paratroopers": "08_paratroopers_drop.png",
    "carpet_street": "02_carpet_down_the_street.png",
    "carpet_order": "01_bomber_carpet_order.png",
    "house_bunker": "10_house_to_bunker.png",
    "house_open": "11_held_house_open_roof.png",
    "train": "04_town_fight_supply_train.png",
    "lightning": "15_lightning_over_the_line.png",
    "winter": "12_winter_front_bomb.png",
    "zrinyi": "17_hungarian_zrinyi_fires.png",
    "chiha": "18_japanese_chiha_fires.png",
    "sherman_river": "19_sherman_river_crossing.png",
    "lagoon": "05_pacific_lagoon_causeway.png",
    "cave": "16_pacific_cave_strongpoint.png",
    "attack_stamp": "06_attack_order_stamp.png",
    "front_3v3": "13_3v3_front_from_above.png",
    "report": "24_after_action_report.png",
    "codex": "21_arsenal_codex.png",
    "setup": "20_battle_setup_seven_nations.png",
}
SIZES = {"lg": 1600, "md": 800}


def fit16x9(im, w):
    h = w * 9 // 16
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def pictures():
    IMG.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, fn in SHOTS.items():
        im = Image.open(S5 / fn).convert("RGB")
        for tag, w in SIZES.items():
            out = IMG / f"{name}-{tag}.jpg"
            fit16x9(im, w).save(out, quality=80 if tag == "lg" else 78, optimize=True, progressive=True)
            total += out.stat().st_size
    icon = Image.open(ICON).convert("RGBA")
    for s in (32, 180, 512):
        icon.resize((s, s), Image.LANCZOS).save(SITE / "assets" / f"icon-{s}.png", optimize=True)
    # the social-card picture (1200 x 630): the paratroopers frame
    og = Image.open(S5 / SHOTS["paratroopers"]).convert("RGB")
    k = max(1200 / og.width, 630 / og.height)
    og = og.resize((round(og.width * k), round(og.height * k)), Image.LANCZOS)
    x, y = (og.width - 1200) // 2, (og.height - 630) // 2
    og.crop((x, y, x + 1200, y + 630)).save(IMG / "social-card.jpg", quality=82, optimize=True)
    print("pictures: %d files, %d KB" % (len(SHOTS) * len(SIZES), total // 1024))


def video():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found: trailer skipped")
        return
    VID.mkdir(parents=True, exist_ok=True)
    src = TRAILER / "FRONTS1944_Teaser_NewNations_v2_YouTube_1920x1080.mp4"
    out = VID / "teaser.mp4"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "27",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)], check=True)
    # the poster is the teaser's own frame: the Zrinyi II fires its 105 mm (27.3 s)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", "27.3", "-i", str(out), "-frames:v", "1", "-q:v", "4",
                    str(IMG / "teaser-poster.jpg")], check=True)
    print("trailer: %s, %.1f MB" % (out.name, out.stat().st_size / 1e6))


if __name__ == "__main__":
    pictures()
    if "--no-video" not in sys.argv:
        video()
