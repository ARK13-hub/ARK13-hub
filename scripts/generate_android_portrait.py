#!/usr/bin/env python3
"""Generate self-typing ASCII portrait from uploaded image for ARK13-hub."""
import os
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import label, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RAMP = " .`:-=+*cs#%@"
COLS = 88
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

    # Crop tightly to the headdress and torso
    crop = src.crop((0, 435, w, 975))
    cw, ch = crop.size

    rgb = np.array(crop)
    gray = np.array(crop.convert("L"))

    # Background detection (dark bluish background outside silhouette)
    is_bg_seed = (rgb[:, :, 0] < 42) & (rgb[:, :, 1] < 52) & (rgb[:, :, 2] < 72)
    lbl, num = label(is_bg_seed)
    edge_labels = set()
    for x in range(cw):
        if is_bg_seed[0, x]:
            edge_labels.add(lbl[0, x])
    for y in range(int(ch * 0.75)):
        if is_bg_seed[y, 0]:
            edge_labels.add(lbl[y, 0])
        if is_bg_seed[y, cw - 1]:
            edge_labels.add(lbl[y, cw - 1])

    bg_mask = np.isin(lbl, list(edge_labels))
    bg_mask = gaussian_filter(bg_mask.astype(float), 1.2) > 0.5

    subj = gray.copy().astype(float)
    c_norm = np.clip(subj / 255.0, 0, 1)

    # Gamma & contrast curve for metallic highlights and cloth texture
    out_gray = np.where(bg_mask, 255, (255.0 * (c_norm ** 1.3))).astype(np.uint8)

    rows = int(COLS * (ch / cw) * ROW_RATIO)
    pil_res = Image.fromarray(out_gray).resize((COLS, rows), Image.LANCZOS)
    px = np.array(pil_res)
    n = len(RAMP)

    lines = []
    for r in range(rows):
        line = "".join(
            RAMP[min(n - 1, int((1 - px[r, c] / 255.0) * n))]
            for c in range(COLS)
        ).rstrip()
        lines.append(line)

    # Clean leading and trailing blank rows
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
    out_svg = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "ascii.svg")
    generate(img_in, out_svg)
