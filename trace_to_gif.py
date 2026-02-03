import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ========================
# Config
# ========================

TRACE_FILE = "trace.json"
OUT_FILE = "trace.gif"

CELL_SIZE = 40
GRID_LINE_COLOR = (0, 0, 0)
EMPTY_COLOR = (255, 255, 255)

BRUSH_OUTLINE_COLOR = (220, 30, 30)   # red
BRUSH_OUTLINE_WIDTH = 3

FRAME_DURATION_MS = 50  # animation speed


# ========================
# Brush definitions
# (copied from gridgame.py)
# ========================

SHAPES = [
    [[1]],
    [[1, 0], [0, 1]],
    [[0, 1], [1, 0]],
    [[1, 0], [0, 1], [1, 0], [0, 1]],
    [[0, 1], [1, 0], [0, 1], [1, 0]],
    [[1, 0, 1, 0], [0, 1, 0, 1]],
    [[0, 1, 0, 1], [1, 0, 1, 0]],
    [[0, 1, 0], [1, 0, 1]],
    [[1, 0, 1], [0, 1, 0]],
]


# ========================
# Helpers
# ========================

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ========================
# Load trace
# ========================

with open(TRACE_FILE, "r") as f:
    trace = json.load(f)

colors = [hex_to_rgb(c) for c in trace["meta"]["colors"]]
frames_data = trace["frames"]

frames = []

try:
    font = ImageFont.load_default()
except:
    font = None


# ========================
# Render frames
# ========================

for frame in frames_data:
    grid = np.array(frame["grid"])
    gs = grid.shape[0]

    img = Image.new(
        "RGB",
        (gs * CELL_SIZE, gs * CELL_SIZE),
        EMPTY_COLOR
    )
    draw = ImageDraw.Draw(img)

    # --- Draw grid cells ---
    for y in range(gs):
        for x in range(gs):
            cell = grid[y, x]

            x0 = x * CELL_SIZE
            y0 = y * CELL_SIZE
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE

            if cell != -1:
                draw.rectangle(
                    [x0, y0, x1, y1],
                    fill=colors[cell]
                )

            draw.rectangle(
                [x0, y0, x1, y1],
                outline=GRID_LINE_COLOR
            )

    # --- Draw brush outline ---
    shape = SHAPES[frame["current_shape"]]
    px, py = frame["shape_pos"]

    for i, row in enumerate(shape):
        for j, cell in enumerate(row):
            if cell:
                x0 = (px + j) * CELL_SIZE
                y0 = (py + i) * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE

                draw.rectangle(
                    [x0, y0, x1, y1],
                    outline=BRUSH_OUTLINE_COLOR,
                    width=BRUSH_OUTLINE_WIDTH
                )

    # --- Draw action label ---
    action_text = frame.get("action", "")
    if action_text:
        draw.text(
            (6, 6),
            action_text,
            fill=(0, 0, 0),
            font=font
        )

    frames.append(img)


# ========================
# Save GIF
# ========================

frames[0].save(
    OUT_FILE,
    save_all=True,
    append_images=frames[1:],
    duration=FRAME_DURATION_MS,
    loop=0
)

print(f"GIF saved to {OUT_FILE}")
