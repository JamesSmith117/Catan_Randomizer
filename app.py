from __future__ import annotations

import random
from pathlib import Path
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

RESOURCE_POOLS = {
    "34": {"wood": 4, "brick": 3, "sheep": 4, "wheat": 4, "ore": 3, "desert": 1},
    "56": {"wood": 6, "brick": 5, "sheep": 6, "wheat": 6, "ore": 5, "desert": 2},
}

NUMBER_POOLS = {
    "34": {"2": 1, "3": 2, "4": 2, "5": 2, "6": 2, "8": 2, "9": 2, "10": 2, "11": 2, "12": 1},
    "56": {"2": 2, "3": 3, "4": 3, "5": 3, "6": 3, "8": 3, "9": 3, "10": 3, "11": 3, "12": 2},
}

ROW_SIZES_BY_MODE = {
    "34": (3, 4, 5, 4, 3),
    "56": (4, 5, 6, 6, 5, 4),
}

IMAGE_FILES = {
    "wood": "wuh.png",
    "brick": "brih.png",
    "sheep": "shih.png",
    "wheat": "whee.png",
    "ore": "ohr.png",
    "desert": "desert.png",
}


def take_from_pool(pool: dict[str, int]) -> str:
    choice = random.choices(list(pool), weights=list(pool.values()), k=1)[0]
    pool[choice] -= 1
    if pool[choice] == 0:
        del pool[choice]
    return choice


def build_adjacency(row_sizes: tuple[int, ...]) -> dict[int, set[int]]:
    adjacency = {i: set() for i in range(sum(row_sizes))}

    offset = 0
    for size in row_sizes:
        for col in range(size - 1):
            left, right = offset + col, offset + col + 1
            adjacency[left].add(right)
            adjacency[right].add(left)
        offset += size

    offset = 0
    for row in range(len(row_sizes) - 1):
        size = row_sizes[row]
        next_size = row_sizes[row + 1]
        next_offset = offset + size

        for col in range(size):
            current = offset + col
            if next_size > size:
                next_cols = (col, col + 1)
            else:
                next_cols = []
                if col > 0:
                    next_cols.append(col - 1)
                if col < next_size:
                    next_cols.append(col)

            for next_col in next_cols:
                neighbor = next_offset + next_col
                adjacency[current].add(neighbor)
                adjacency[neighbor].add(current)

        offset = next_offset

    return adjacency


def generate_board(mode: str) -> dict:
    if mode not in ROW_SIZES_BY_MODE:
        mode = "34"

    row_sizes = ROW_SIZES_BY_MODE[mode]
    adjacency = build_adjacency(row_sizes)

    for _ in range(10000):
        resources = RESOURCE_POOLS[mode].copy()
        numbers = NUMBER_POOLS[mode].copy()
        tiles = []

        for _ in range(sum(row_sizes)):
            resource = take_from_pool(resources)
            number = None if resource == "desert" else take_from_pool(numbers)
            tiles.append({
                "resource": resource,
                "number": number,
                "image": IMAGE_FILES[resource],
            })

        invalid = False
        for index, tile in enumerate(tiles):
            if tile["number"] not in {"6", "8"}:
                continue
            if any(tiles[n]["number"] in {"6", "8"} for n in adjacency[index]):
                invalid = True
                break

        if not invalid:
            return {"mode": mode, "row_sizes": row_sizes, "tiles": tiles}

    raise RuntimeError("Could not generate a balanced board")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/board")
def api_board():
    mode = request.args.get("mode", "34")
    return jsonify(generate_board(mode))


if __name__ == "__main__":
    app.run(debug=True)
