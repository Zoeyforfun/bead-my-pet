#!/usr/bin/env python3
"""Render a high-resolution transparent PNG for importing into 颂拼豆."""

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw


def read_palette(csv_path: Path) -> dict[str, str]:
    palette = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            palette[row["MARD色号"]] = row["HEX屏幕参考"]
    return palette


def fit_height(cells: list[list[str | None]], target_height: int) -> list[list[str | None]]:
    width = len(cells[0])
    occupied = [index for index, row in enumerate(cells) if any(value is not None for value in row)]
    if not occupied:
        return [[None] * width for _ in range(target_height)]
    content = cells[min(occupied): max(occupied) + 1]
    if len(content) > target_height:
        raise ValueError(
            f"occupied content height {len(content)} exceeds target height {target_height}; "
            "use a taller target or regenerate the pattern"
        )
    extra = target_height - len(content)
    top = extra // 2
    return [[None] * width for _ in range(top)] + content + [[None] * width for _ in range(extra - top)]


def hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        raise ValueError(f"invalid HEX color: {value}")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4)) + (255,)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a high-resolution RGBA PNG with transparent empty cells and no labels or grid lines."
    )
    parser.add_argument("--pattern", required=True, help="pattern.json from the deterministic converter")
    parser.add_argument("--counts", required=True, help="counts.csv containing MARD code and HEX mapping")
    parser.add_argument("--output", required=True, help="output PNG path")
    parser.add_argument("--cell-size", type=int, default=40, help="pixels per bead cell; default 40")
    parser.add_argument("--target-height", type=int, help="optional rectangular grid height matching the standard chart")
    args = parser.parse_args()

    if args.cell_size < 1:
        raise ValueError("--cell-size must be at least 1")

    data = json.loads(Path(args.pattern).read_text(encoding="utf-8"))
    cells = data["cells"]
    if not cells or not cells[0]:
        raise ValueError("pattern contains no cells")
    grid_width = len(cells[0])
    if any(len(row) != grid_width for row in cells):
        raise ValueError("pattern rows have inconsistent widths")
    if args.target_height is not None:
        if args.target_height < 1:
            raise ValueError("--target-height must be at least 1")
        cells = fit_height(cells, args.target_height)

    palette = read_palette(Path(args.counts))
    grid_height = len(cells)
    image = Image.new(
        "RGBA",
        (grid_width * args.cell_size, grid_height * args.cell_size),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(image)
    occupied_cells = 0
    for y, row in enumerate(cells):
        for x, code in enumerate(row):
            if code is None:
                continue
            if code not in palette:
                raise ValueError(f"missing color mapping for {code}")
            x0 = x * args.cell_size
            y0 = y * args.cell_size
            draw.rectangle(
                (x0, y0, x0 + args.cell_size - 1, y0 + args.cell_size - 1),
                fill=hex_to_rgba(palette[code]),
            )
            occupied_cells += 1

    output = Path(args.output)
    if output.suffix.lower() != ".png":
        raise ValueError("--output must use the .png extension")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False, compress_level=6)
    print(json.dumps({
        "grid_width": grid_width,
        "grid_height": grid_height,
        "cell_size": args.cell_size,
        "pixel_width": image.width,
        "pixel_height": image.height,
        "occupied_cells": occupied_cells,
        "transparent_cells": grid_width * grid_height - occupied_cells,
        "mode": image.mode,
        "output": str(output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
