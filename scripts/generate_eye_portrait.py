#!/usr/bin/env python3
"""Generate Pennywise eye self-typing ASCII SVG portrait for ARK13-hub."""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RAMP = " .`:-=+*cs#%@"
COLS = 86
ROW_RATIO = 0.48
CHAR_W = 7.74
FONT_SIZE = 12.9
LINE_H = 15
ROW_DELAY = 0.08
FAMILY = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FG_LIGHT = "#6e7681"
FG_DARK = "#c9d1d9"


def generate(image_path, out_svg_path):
    src = Image.open(image_path)
    w, h = src.size

    # Crop focusing on the eye and the vertical blood streaks above and below
    crop = src.crop((0, 80, w, 920))
    cw, ch = crop.size

    rgb = np.array(crop).astype(float)
    gray = np.array(crop.convert("L")).astype(float)

    # Red makeup streak extraction: high R, low G/B
    red_paint = np.clip(rgb[:, :, 0] - (rgb[:, :, 1] + rgb[:, :, 2]) * 0.5, 0, 255)

    # Invert grayscale for features (pupil, eyelashes, creases)
    darkness = 255.0 - gray

    # Feature darkness combines structural darkness and red paint texture
    feat_darkness = darkness.copy()
    feat_darkness += red_paint * 0.7
    feat_darkness = np.clip(feat_darkness, 0, 255)

    # Suppress flat pale skin background to clean space
    is_pale_skin = (gray > 190) & (red_paint < 25)
    feat_darkness[is_pale_skin] *= 0.15

    # Map to 0..255 (255 = blank space, 0 = darkest dense char)
    processed_gray = np.clip(255.0 - feat_darkness, 0, 255).astype(np.uint8)

    rows = int(COLS * (ch / cw) * ROW_RATIO)
    res = Image.fromarray(processed_gray).resize((COLS, rows), Image.LANCZOS)
    px = np.array(res)
    n = len(RAMP)

    lines = []
    for r in range(rows):
        line = "".join(
            RAMP[min(n - 1, int((1 - px[r, c] / 255.0) * n))]
            for c in range(COLS)
        ).rstrip()
        lines.append(line)

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    pad = 14
    width = int(COLS * CHAR_W + pad * 2)
    height = len(lines) * LINE_H + pad * 2

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{FAMILY}">',
        f'<style>.a{{fill:{FG_LIGHT}}}'
        f'@media(prefers-color-scheme:dark){{.a{{fill:{FG_DARK}}}}}</style>',
    ]

    for i, line in enumerate(lines):
        y = pad + i * LINE_H
        begin = f"{i * ROW_DELAY:.2f}s"
        end = f"{(i + 1) * ROW_DELAY:.2f}s"
        w_px = max(len(line), 1) * CHAR_W
        safe = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        p.append(
            f'<clipPath id="c{i}"><rect x="{pad}" y="{y}" '
            f'height="{LINE_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{w_px:.1f}" '
            f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        p.append(
            f'<g clip-path="url(#c{i})"><text xml:space="preserve" '
            f'x="{pad}" y="{y + 11.2:.1f}" class="a" '
            f'font-size="{FONT_SIZE}">{safe}</text></g>'
        )
        p.append(
            f'<rect y="{y + 1}" width="6" height="12" class="a" '
            f'opacity="0">'
            f'<animate attributeName="x" from="{pad}" to="{pad + w_px:.1f}" '
            f'begin="{begin}" dur="{ROW_DELAY}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.8" begin="{begin}"/>'
            f'<set attributeName="opacity" to="0" begin="{end}"/></rect>'
        )

    p.append("</svg>")
    svg_content = "".join(p)

    with open(out_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved {out_svg_path} with {len(lines)} lines")


if __name__ == "__main__":
    img_in = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "photo.jpg")
    out_svg = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "pennywise-eye.svg")
    generate(img_in, out_svg)
