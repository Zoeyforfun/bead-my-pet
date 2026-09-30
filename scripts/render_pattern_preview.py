#!/usr/bin/env python3
"""Render an unlabeled pattern preview for visual identity review."""

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--counts", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cell-size", type=int, default=20)
    args = parser.parse_args()

    if args.cell_size < 1:
        raise ValueError("--cell-size must be at least 1")

    pattern = json.loads(Path(args.pattern).read_text(encoding="utf-8"))
    cells = pattern["cells"]
    if not cells or not cells[0]:
        raise ValueError("pattern contains no cells")
    width = len(cells[0])
    if any(len(row) != width for row in cells):
        raise ValueError("pattern rows have inconsistent widths")

    colors = {}
    with Path(args.counts).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            colors[row["MARD色号"]] = row["HEX屏幕参考"]

    height = len(cells)
    image = Image.new("RGB", (width * args.cell_size, height * args.cell_size), "white")
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(cells):
        for x, code in enumerate(row):
            if code is None:
                continue
            if code not in colors:
                raise ValueError(f"missing color mapping for {code}")
            draw.rectangle(
                (
                    x * args.cell_size,
                    y * args.cell_size,
                    (x + 1) * args.cell_size - 1,
                    (y + 1) * args.cell_size - 1,
                ),
                fill=colors[code],
            )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")
    print(json.dumps({"width": width, "height": height, "output": str(output)}))


if __name__ == "__main__":
    main()
