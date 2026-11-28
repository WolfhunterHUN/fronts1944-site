"""Makes the landing page's silent video loops (hero, feature cards, the HQ dossier) from the game's own footage.

Sources (all in-game captures, no HUD unless noted):
  C:\\Playground\\UP\\RTS-merge\\Builds\\Steam\\keyart\\capture   key-art takes, 2560 x 1440
  C:\\Playground\\UP\\RTS-merge\\Builds\\Steam\\media\\capture    Steam media takes, 1920 x 1080

Each loop is cut from one take and closed with a short crossfade from its tail into its head, so it repeats without a
visible jump. The poster is the loop's first frame, so the switch from picture to video does not jump either.

Usage: python -I tools/make_loops.py [name ...]      (ffmpeg on PATH; no names = all)
Writes assets/video/loop_<name>.mp4 and assets/img/loop_<name>-md.jpg (800 px) / -lg.jpg (1600 px).
"""
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
STEAM = Path(r"C:\Playground\UP\RTS-merge\Builds\Steam")
KEY = STEAM / "keyart" / "capture"
CAP = STEAM / "media" / "capture"
VID = SITE / "assets" / "video"
IMG = SITE / "assets" / "img"

# name: (source, start s, length s, crossfade s, output width, crf, crop or None)
# crop is ffmpeg crop=w:h:x:y on the source, before scaling.
LOOPS = {
    "hero":     (KEY / "KA1_para_wide.mp4",                  2.0,  8.0, 1.0, 1600, 27, None),
    "hero_sm":  (KEY / "KA1_para_wide.mp4",                  2.0,  8.0, 1.0, 960, 29, None),   # phones
    "bombers":  (CAP / "M_F27_carpet_street_16x9.mp4",       6.0, 10.0, 0.8, 768, 29, None),
    "house":    (CAP / "M_F24_house_to_bunker_16x9.mp4",     3.0,  7.0, 0.8, 768, 29, None),
    "train":    (CAP / "M_F20_troop_train_16x9.mp4",         5.5,  6.5, 0.8, 768, 29, None),
    "weather":  (CAP / "M_F25_lightning_16x9.mp4",           0.0,  8.0, 0.5, 768, 29, None),
    "zrinyi":   (KEY / "KA3_zrinyi_wide.mp4",                0.0,  7.0, 0.6, 768, 29, None),
    "pacific":  (CAP / "M_F13_rts_pacific_beach_16x9.mp4",   0.0, 10.0, 0.8, 768, 29, "1152:648:40:250"),
    # the HQ dossier: the real HUD, a bombing run drawn and the stamps on the map
    "stamp":    (CAP / "M_F02_hud_carpet_stamp_16x9.mp4",    0.5, 13.0, 0.8, 1280, 27, None),
}


def run(cmd):
    subprocess.run(cmd, check=True)


def make(name, ffmpeg):
    src, start, length, fade, width, crf, crop = LOOPS[name]
    pre = (f"crop={crop}," if crop else "") + f"scale={width}:-2:flags=lanczos,fps=30,format=yuv420p"
    # main = clip[fade..length]; its last `fade` seconds dissolve into head = clip[0..fade],
    # so the loop ends on clip[fade], exactly where it restarts.
    graph = (
        f"[0:v]{pre},split[a][b];"
        f"[a]trim=start={fade},setpts=PTS-STARTPTS,fps=30[main];"
        f"[b]trim=end={fade},setpts=PTS-STARTPTS,fps=30[head];"
        f"[main][head]xfade=transition=fade:duration={fade}:offset={length - 2 * fade:.3f},format=yuv420p[v]"
    )
    out = VID / f"loop_{name}.mp4"
    run([ffmpeg, "-v", "error", "-y", "-ss", str(start), "-t", str(length), "-i", str(src),
         "-filter_complex", graph, "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high",
         "-movflags", "+faststart", str(out)])
    # the hero keeps its own close-up still (paratroopers-lg.jpg) under the loop, so it needs no poster
    sizes = {} if name.startswith("hero") else {"md": 800} if width <= 800 else {"md": 800, "lg": 1600}
    for tag, w in sizes.items():
        run([ffmpeg, "-v", "error", "-y", "-i", str(out), "-frames:v", "1",
             "-vf", f"scale={min(w, width)}:-2:flags=lanczos", "-q:v", "4", str(IMG / f"loop_{name}-{tag}.jpg")])
    print(f"{name:8s} {out.stat().st_size // 1024:5d} KB  ({length - fade:.1f} s)")


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ffmpeg is not on PATH")
    VID.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(LOOPS)
    for n in names:
        make(n, ffmpeg)


if __name__ == "__main__":
    main()
