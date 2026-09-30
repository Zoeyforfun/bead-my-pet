#!/usr/bin/env python3
"""Render a print-friendly MARD chart with four-side coordinates and 5x5 guides."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_font(path: str, size: int):
    return ImageFont.truetype(path, size)


def read_palette(csv_path: Path):
    palette = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            palette[row["MARD色号"]] = row["HEX屏幕参考"]
    return palette


def fit_height(cells, target_height: int):
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


def draw_centered(draw, box, text, text_font, fill):
    x0, y0, x1, y1 = box
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.text(
        ((x0 + x1 - width) / 2, (y0 + y1 - height) / 2 - bounds[1]),
        text,
        font=text_font,
        fill=fill,
    )


def text_color(hex_color: str):
    value = hex_color.lstrip("#")
    red, green, blue = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return "#111111" if luminance > 155 else "#FFFFFF"


def render(cells, palette, output_png: Path, output_pdf: Path):
    height, width = len(cells), len(cells[0])
    cell = 44 if width <= 40 else 34
    coordinate_band = cell
    side_margin = 70
    title_height = 110
    legend_gap = 70
    legend_row_height = 58
    legend_columns = 4 if width <= 40 else 5

    counts = Counter(value for row in cells for value in row if value is not None)
    codes = sorted(counts)
    legend_rows = (len(codes) + legend_columns - 1) // legend_columns
    grid_width, grid_height = width * cell, height * cell
    canvas_width = side_margin * 2 + coordinate_band * 2 + grid_width
    canvas_height = (
        title_height
        + coordinate_band * 2
        + grid_height
        + legend_gap
        + legend_rows * legend_row_height
        + 105
    )

    image = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(FONT_BOLD, 38)
    coordinate_font = load_font(FONT_BOLD, max(14, cell // 2))
    code_font = load_font(FONT_BOLD, max(12, cell // 3))
    legend_font = load_font(FONT_BOLD, 22)
    note_font = load_font(FONT_REGULAR, 20)

    draw_centered(
        draw,
        (0, 20, canvas_width, 85),
        f"MARD Fuse Bead Pattern — {width} × {height}",
        title_font,
        "#111111",
    )

    grid_x = side_margin + coordinate_band
    grid_y = title_height + coordinate_band
    coordinate_background = "#DCEEFF"

    for column in range(width):
        x0 = grid_x + column * cell
        for y0 in (grid_y - coordinate_band, grid_y + grid_height):
            draw.rectangle(
                (x0, y0, x0 + cell, y0 + coordinate_band),
                fill=coordinate_background,
                outline="#9BB8D4",
                width=1,
            )
            draw_centered(
                draw,
                (x0, y0, x0 + cell, y0 + coordinate_band),
                str(column + 1),
                coordinate_font,
                "#163A59",
            )

    for row in range(height):
        y0 = grid_y + row * cell
        for x0 in (grid_x - coordinate_band, grid_x + grid_width):
            draw.rectangle(
                (x0, y0, x0 + coordinate_band, y0 + cell),
                fill=coordinate_background,
                outline="#9BB8D4",
                width=1,
            )
            draw_centered(
                draw,
                (x0, y0, x0 + coordinate_band, y0 + cell),
                str(row + 1),
                coordinate_font,
                "#163A59",
            )

    for row_index, row in enumerate(cells):
        for column_index, code in enumerate(row):
            x0 = grid_x + column_index * cell
            y0 = grid_y + row_index * cell
            box = (x0, y0, x0 + cell, y0 + cell)
            if code is None:
                draw.rectangle(box, fill="#FFFFFF")
                continue
            color = palette.get(code, "#DDDDDD")
            draw.rectangle(box, fill=color)
            draw_centered(draw, box, code, code_font, text_color(color))

    for column in range(width + 1):
        x = grid_x + column * cell
        is_group_line = column % 5 == 0 or column == width
        draw.line(
            (x, grid_y, x, grid_y + grid_height),
            fill="#111111" if is_group_line else "#AEB7BF",
            width=4 if is_group_line else 1,
        )
    for row in range(height + 1):
        y = grid_y + row * cell
        is_group_line = row % 5 == 0 or row == height
        draw.line(
            (grid_x, y, grid_x + grid_width, y),
            fill="#111111" if is_group_line else "#AEB7BF",
            width=4 if is_group_line else 1,
        )
    draw.rectangle(
        (grid_x, grid_y, grid_x + grid_width, grid_y + grid_height),
        outline="#000000",
        width=6,
    )

    legend_y = grid_y + grid_height + coordinate_band + legend_gap
    draw.text(
        (side_margin, legend_y - 45),
        "MARD codes and bead counts",
        font=legend_font,
        fill="#111111",
    )
    legend_column_width = (canvas_width - side_margin * 2) // legend_columns
    for index, code in enumerate(codes):
        row, column = divmod(index, legend_columns)
        x = side_margin + column * legend_column_width
        y = legend_y + row * legend_row_height
        color = palette.get(code, "#DDDDDD")
        draw.rounded_rectangle(
            (x, y + 5, x + 42, y + 47),
            radius=5,
            fill=color,
            outline="#555555",
            width=1,
        )
        draw.text(
            (x + 55, y + 10),
            f"{code} × {counts[code]}",
            font=legend_font,
            fill="#111111",
        )

    footer_y = legend_y + legend_rows * legend_row_height + 20
    draw.text(
        (side_margin, footer_y),
        f"Total beads: {sum(counts.values())}    Colors: {len(codes)}",
        font=legend_font,
        fill="#111111",
    )
    draw.text(
        (side_margin, footer_y + 38),
        "Thick grid lines divide the pattern into 5 × 5 blocks. Blank cells are not beaded.",
        font=note_font,
        fill="#555555",
    )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png, format="PNG", optimize=True)
    image.save(output_pdf, format="PDF", resolution=200.0)
    return {
        "width": width,
        "height": height,
        "colors": len(codes),
        "beads": sum(counts.values()),
        "png": str(output_png),
        "pdf": str(output_pdf),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", required=True, help="pattern.json from the deterministic converter")
    parser.add_argument("--counts", required=True, help="counts.csv containing MARD code, HEX and bead count")
    parser.add_argument("--out-prefix", required=True, help="output path without extension")
    parser.add_argument("--target-height", type=int, help="optional rectangular chart height after trimming empty rows")
    args = parser.parse_args()

    data = json.loads(Path(args.pattern).read_text(encoding="utf-8"))
    cells = data["cells"]
    if args.target_height:
        cells = fit_height(cells, args.target_height)
    palette = read_palette(Path(args.counts))
    prefix = Path(args.out_prefix)
    result = render(cells, palette, prefix.with_suffix(".png"), prefix.with_suffix(".pdf"))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
