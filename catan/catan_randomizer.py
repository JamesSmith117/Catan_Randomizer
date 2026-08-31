import argparse
import random
import os
import sys
import subprocess

from PIL import Image, ImageDraw, ImageFont
import numpy as np

# this is a script that will randomize the catan board
# it will randomize the tiles
# it will randomize the numbers on the tiles

RESOURCE_POOLS = {
    "34": {"wood": 4, "brick": 3, "sheep": 4, "wheat": 4, "ore": 3, "desert": 1},
    "56": {"wood": 6, "brick": 5, "sheep": 6, "wheat": 6, "ore": 5, "desert": 2},
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_IMAGES = {
    "wood": os.path.join(SCRIPT_DIR, "wuh.png"),
    "brick": os.path.join(SCRIPT_DIR, "brih.png"),
    "sheep": os.path.join(SCRIPT_DIR, "shih.png"),
    "wheat": os.path.join(SCRIPT_DIR, "whee.png"),
    "ore": os.path.join(SCRIPT_DIR, "ohr.png"),
    "desert": os.path.join(SCRIPT_DIR, "desert.png"),
}

NUMBER_POOLS = {
    "34": {"2": 1, "3": 2, "4": 2, "5": 2, "6": 2, "8": 2, "9": 2, "10": 2, "11": 2, "12": 1},
    "56": {"2": 2, "3": 3, "4": 3, "5": 3, "6": 3, "8": 3, "9": 3, "10": 3, "11": 3, "12": 2},
}

ROW_SIZES_BY_MODE = {
    "34": (3, 4, 5, 4, 3),
    "56": (4, 5, 6, 6, 5, 4),
}

TILE_IMAGE_WIDTH = 200
_hex_cache = {}


def _load_hex_image(path, target_width=TILE_IMAGE_WIDTH):
    if path in _hex_cache:
        return _hex_cache[path]

    im = Image.open(path).convert("RGBA")
    pixels = np.array(im)
    rgb = pixels[:, :, :3].astype(np.int16)
    corner_avg = rgb[0, 0].mean()
    dark_bg = corner_avg < 128

    if dark_bg:
        content = rgb.max(axis=2) > 25
        pixels[~content, 3] = 0
    else:
        content = rgb.min(axis=2) < 245
        pixels[~content, 3] = 0

    ys, xs = np.where(content)
    cropped = Image.fromarray(pixels).crop(
        (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    )
    width, height = cropped.size
    resized = cropped.resize(
        (target_width, max(1, int(height * target_width / width))),
        Image.Resampling.LANCZOS,
    )
    _hex_cache[path] = resized
    return resized


class Tile:
    def __init__(self, number, resource):
        self.number = number
        self.resource = resource
        self.image = RESOURCE_IMAGES[resource]

    def __repr__(self):
        if self.resource == "desert":
            return "Tile(desert)"
        return f"Tile({self.resource}, {self.number})"

    def __str__(self):
        if self.resource == "desert":
            return f"{'desert':<8}"
        return f"{self.resource:<5} {self.number:>2}"


def _take(pool):
    choice = random.choices(list(pool.keys()), weights=list(pool.values()), k=1)[0]
    pool[choice] -= 1
    if pool[choice] == 0:
        del pool[choice]
    return choice


def random_tile(resource_pool, number_pool):
    resource = _take(resource_pool)
    if resource == "desert":
        return Tile(None, resource)
    number = _take(number_pool)
    return Tile(number, resource)


def _build_adjacency(row_sizes):
    """Hex neighbors for a centered Catan layout with the given row sizes."""
    adj = {i: set() for i in range(sum(row_sizes))}

    offset = 0
    for size in row_sizes:
        for col in range(size - 1):
            left, right = offset + col, offset + col + 1
            adj[left].add(right)
            adj[right].add(left)
        offset += size

    offset = 0
    for row in range(len(row_sizes) - 1):
        size = row_sizes[row]
        next_size = row_sizes[row + 1]
        next_offset = offset + size

        for col in range(size):
            i = offset + col
            if next_size > size:
                neighbors = (col, col + 1)
            else:
                neighbors = []
                if col > 0:
                    neighbors.append(col - 1)
                if col < next_size:
                    neighbors.append(col)
            for next_col in neighbors:
                j = next_offset + next_col
                adj[i].add(j)
                adj[j].add(i)

        offset = next_offset

    return {i: frozenset(neighbors) for i, neighbors in adj.items()}


_ADJACENCY_CACHE = {}


def _adjacency_for(row_sizes):
    if row_sizes not in _ADJACENCY_CACHE:
        _ADJACENCY_CACHE[row_sizes] = _build_adjacency(row_sizes)
    return _ADJACENCY_CACHE[row_sizes]


class Board:
    def __init__(self, mode="34"):
        self.mode = mode
        self.row_sizes = ROW_SIZES_BY_MODE[mode]
        self.adjacency = _adjacency_for(self.row_sizes)
        tile_count = sum(self.row_sizes)

        while True:
            remaining_resources = RESOURCE_POOLS[mode].copy()
            remaining_numbers = NUMBER_POOLS[mode].copy()
            self.tiles = [
                random_tile(remaining_resources, remaining_numbers)
                for _ in range(tile_count)
            ]
            if not self._has_adjacent_high_numbers():
                break

    def _has_adjacent_high_numbers(self):
        high = {"6", "8"}
        for i, tile in enumerate(self.tiles):
            if tile.number not in high:
                continue
            for j in self.adjacency[i]:
                if j > i and self.tiles[j].number in high:
                    return True
        return False

    def __str__(self):
        return self.print_board()

    def __repr__(self):
        return self.print_board()

    def print_board(self):
        rows = []
        index = 0
        max_width = max(self.row_sizes)
        tile_width = 8  # matches Tile.__str__
        gap = 2

        for size in self.row_sizes:
            row_tiles = self.tiles[index : index + size]
            index += size
            row = (" " * gap).join(str(tile) for tile in row_tiles)
            indent = ((max_width - size) * (tile_width + gap)) // 2
            rows.append(" " * indent + row)

        return "\n".join(rows)

    def render(self):
        hexes = [_load_hex_image(tile.image) for tile in self.tiles]
        cell_w = max(h.size[0] for h in hexes)
        cell_h = max(h.size[1] for h in hexes)

        # Pad every tile to the same cell size so spacing is consistent.
        padded = []
        for hex_im in hexes:
            cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
            cell.alpha_composite(
                hex_im,
                ((cell_w - hex_im.size[0]) // 2, (cell_h - hex_im.size[1]) // 2),
            )
            padded.append(cell)

        # Hand-drawn hexes fill their bounding boxes at the sides, so row
        # neighbors need full-width spacing to touch without overlapping.
        # Rows nest at ~3/4 height with a half-tile horizontal offset.
        horiz = cell_w
        vert = int(round(cell_h * 0.75))
        pad = 30

        # Centering each row independently only offsets it correctly from its
        # neighbor when the row size changes by one (the normal 3-4-5-4-3
        # board). Two consecutive rows of the same size -- e.g. the two
        # size-6 rows in the 5-6 player layout -- would then land at the
        # same x and stack instead of interlocking, so track each row's
        # left edge cumulatively: growing shifts left by a half tile,
        # staying the same size or shrinking shifts right by a half tile.
        row_lefts = [0.0]
        for i in range(1, len(self.row_sizes)):
            shift = -horiz / 2 if self.row_sizes[i] > self.row_sizes[i - 1] else horiz / 2
            row_lefts.append(row_lefts[-1] + shift)

        row_widths = [(size - 1) * horiz + cell_w for size in self.row_sizes]
        min_left = min(row_lefts)
        max_right = max(left + width for left, width in zip(row_lefts, row_widths))

        board_w = pad * 2 + int(round(max_right - min_left))
        board_h = pad * 2 + (len(self.row_sizes) - 1) * vert + cell_h
        board = Image.new("RGBA", (board_w, board_h), (28, 28, 36, 255))

        centers = []
        index = 0
        for row, size in enumerate(self.row_sizes):
            x0 = int(round(row_lefts[row] - min_left)) + pad
            y = pad + row * vert
            for col in range(size):
                hex_im = padded[index]
                x = x0 + col * horiz
                yy = y
                board.alpha_composite(hex_im, (x, yy))
                centers.append(
                    (
                        x + cell_w // 2 + 28,
                        yy + cell_h // 2 - 10,
                    )
                )
                index += 1

        draw = ImageDraw.Draw(board)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()

        token_r = 22
        for tile, (cx, cy) in zip(self.tiles, centers):
            if tile.number is None:
                continue
            draw.ellipse(
                (cx - token_r, cy - token_r, cx + token_r, cy + token_r),
                fill=(245, 236, 210, 255),
                outline=(40, 40, 40, 255),
                width=2,
            )
            color = (180, 30, 30, 255) if tile.number in ("6", "8") else (20, 20, 20, 255)
            draw.text((cx, cy), tile.number, font=font, fill=color, anchor="mm")

        return board.convert("RGB")


    def save_image(self, path=None):
        if path is None:
            path = os.path.join(SCRIPT_DIR, "catan_board.png")
        image = self.render()
        image.save(path)
        return path


def prompt_player_count():
    while True:
        answer = input("How many players? (3-4 or 5-6): ").strip().lower()
        answer = answer.replace(" ", "")
        if answer in ("3-4", "3,4", "34", "3", "4"):
            return "34"
        if answer in ("5-6", "5,6", "56", "5", "6"):
            return "56"
        print("Please enter '3-4' or '5-6'.")


def parse_args():
    parser = argparse.ArgumentParser(description="Randomize a Catan board layout.")
    parser.add_argument(
        "--mode",
        choices=("34", "56"),
        help="Board size for 3-4 or 5-6 players.",
    )
    parser.add_argument(
        "--output",
        help="Path for the generated board image.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the generated image after saving.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for player count even when stdin is not a TTY.",
    )
    return parser.parse_args()


def resolve_mode(args):
    if args.mode:
        return args.mode
    if args.interactive or sys.stdin.isatty():
        return prompt_player_count()
    print("No TTY detected; defaulting to 3-4 player mode. Use --mode 56 to override.")
    return "34"


def main():
    args = parse_args()
    mode = resolve_mode(args)
    board = Board(mode)
    print(board)
    path = board.save_image(args.output)
    print(f"\nSaved board image to {path}")
    if args.no_open:
        return
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        elif sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except OSError:
        pass


if __name__ == "__main__":
    main()
