#!/usr/bin/env python3
"""
8x8 Game Boy tile pixel editor (Tkinter)
- Main canvas: 8x8 pixels (cell size = 1)
- Palette: white, light gray, dark gray, black
- Mapping (low_bit, high_bit):
    0 white -> (1,1)
    1 light -> (1,0)
    2 dark  -> (0,0)
    3 black -> (0,1)
- Produces 16 bytes (low/high per row), then swaps pairs for little endian output.
- Hex field is editable: pressing Enter updates the tile graphics.
"""

import tkinter as tk
from tkinter import messagebox

GRID = 8

PALETTE = [
    "#FFFFFF",  # 0 white
    "#C0C0C0",  # 1 light gray
    "#606060",  # 2 dark gray
    "#000000",  # 3 black
]

# confirmed GB bit mapping
GB_MAPPING = {
    0: (1, 1),  # white
    1: (1, 0),  # light
    2: (0, 0),  # dark
    3: (0, 1),  # black
}

# reverse mapping: (low,high) -> index
GB_REVERSE = {v: k for k, v in GB_MAPPING.items()}


class GBPixelEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("8x8 Game Boy Tile Editor")
        self.resizable(False, False)

        self.grid_data = [[0 for _ in range(GRID)] for _ in range(GRID)]
        self.current = 3  # default black

        # tiny 8x8 canvas
        self.canvas = tk.Canvas(self, width=GRID, height=GRID, bd=1, relief="solid")
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        self._draw_canvas()

        # large preview
        self.preview_scale = 24
        self.preview = tk.Canvas(
            self,
            width=GRID * self.preview_scale,
            height=GRID * self.preview_scale,
            bd=1,
            relief="solid",
        )
        self.preview.grid(row=0, column=1, padx=10, pady=10)

        # palette
        controls = tk.Frame(self)
        controls.grid(row=0, column=2, sticky="n", padx=10, pady=10)

        tk.Label(controls, text="Palette").pack(pady=(0, 6))
        for i, col in enumerate(PALETTE):
            tk.Button(
                controls, bg=col, width=6, height=1, command=lambda idx=i: self.set_color(idx)
            ).pack(pady=2)

        tk.Label(controls, text="Current").pack(pady=(8, 4))
        self.current_display = tk.Label(
            controls, bg=PALETTE[self.current], width=12, height=1, relief="sunken"
        )
        self.current_display.pack(pady=2)

        tk.Button(controls, text="Clear", width=12, command=self.clear).pack(pady=(8, 4))

        # canvas painting
        self.canvas.bind("<Button-1>", self.paint_left)
        self.canvas.bind("<B1-Motion>", self.paint_left)
        self.canvas.bind("<Button-3>", self.paint_right)
        self.canvas.bind("<B3-Motion>", self.paint_right)

        # preview painting
        self.preview.bind("<Button-1>", self.paint_preview_left)
        self.preview.bind("<B1-Motion>", self.paint_preview_left)
        self.preview.bind("<Button-3>", self.paint_preview_right)
        self.preview.bind("<B3-Motion>", self.paint_preview_right)

        # editable hex field
        tk.Label(self, text="GB little-endian hex (edit & press Enter):").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=10
        )
        self.hex_entry = tk.Entry(self, width=60)
        self.hex_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10))
        self.hex_entry.bind("<Return>", self.hex_changed)

        # initial preview & hex
        self._update_preview()
        self._update_hex_display()

    # ------------------ model & UI ------------------

    def set_color(self, idx):
        self.current = idx
        self.current_display.config(bg=PALETTE[idx])

    def clear(self):
        for y in range(GRID):
            for x in range(GRID):
                self.grid_data[y][x] = 0
        self._draw_canvas()
        self._update_preview()
        self._update_hex_display()

    # ------------------ painting ------------------

    def paint_left(self, event):
        x = int(event.x)
        y = int(event.y)
        if 0 <= x < GRID and 0 <= y < GRID:
            self.grid_data[y][x] = self.current
            self._draw_pixel(x, y)
            self._update_preview()
            self._update_hex_display()

    def paint_right(self, event):
        x = int(event.x)
        y = int(event.y)
        if 0 <= x < GRID and 0 <= y < GRID:
            self.grid_data[y][x] = 0
            self._draw_pixel(x, y)
            self._update_preview()
            self._update_hex_display()

    def paint_preview_left(self, event):
        x = int(event.x // self.preview_scale)
        y = int(event.y // self.preview_scale)
        if 0 <= x < GRID and 0 <= y < GRID:
            self.grid_data[y][x] = self.current
            self._draw_canvas()
            self._update_preview()
            self._update_hex_display()

    def paint_preview_right(self, event):
        x = int(event.x // self.preview_scale)
        y = int(event.y // self.preview_scale)
        if 0 <= x < GRID and 0 <= y < GRID:
            self.grid_data[y][x] = 0
            self._draw_canvas()
            self._update_preview()
            self._update_hex_display()

    # ------------------ drawing ------------------

    def _draw_canvas(self):
        self.canvas.delete("all")
        for y in range(GRID):
            for x in range(GRID):
                self._draw_pixel(x, y)

    def _draw_pixel(self, x, y):
        tag = f"p_{x}_{y}"
        self.canvas.delete(tag)
        col = PALETTE[self.grid_data[y][x]]
        self.canvas.create_rectangle(x, y, x + 1, y + 1, fill=col, outline="", tags=tag)

    def _update_preview(self):
        self.preview.delete("all")
        s = self.preview_scale
        for y in range(GRID):
            for x in range(GRID):
                col = PALETTE[self.grid_data[y][x]]
                self.preview.create_rectangle(
                    x * s, y * s, x * s + s, y * s + s, fill=col, outline=""
                )

    # ------------------ GB encoding ------------------

    def grid_to_tile_bytes(self):
        tile = []
        for y in range(GRID):
            low = 0
            high = 0
            for x in range(GRID):
                lo, hi = GB_MAPPING[self.grid_data[y][x]]
                low |= lo << (7 - x)
                high |= hi << (7 - x)
            tile.append(low)
            tile.append(high)
        return tile

    @staticmethod
    def to_little_endian_pairs(tile_bytes):
        out = []
        for i in range(0, 16, 2):
            a = tile_bytes[i]
            b = tile_bytes[i + 1]
            out.append(b)
            out.append(a)
        return out

    def _update_hex_display(self):
        tile = self.grid_to_tile_bytes()
        swapped = self.to_little_endian_pairs(tile)
        hex_str = " ".join(f"{b:02X}" for b in swapped)
        self.hex_entry.delete(0, tk.END)
        self.hex_entry.insert(0, hex_str)

    # ------------------ Hex → Grid decoding ------------------

    def hex_changed(self, event=None):
        text = self.hex_entry.get().strip()
        parts = text.split()

        if len(parts) != 16:
            messagebox.showerror("Error", "Hex must contain exactly 16 bytes.")
            return

        try:
            bytes_le = [int(p, 16) for p in parts]
        except ValueError:
            messagebox.showerror("Error", "Invalid hex byte detected.")
            return

        # undo little endian swap
        tile = []
        for i in range(0, 16, 2):
            b = bytes_le[i]
            a = bytes_le[i + 1]
            tile.append(a)
            tile.append(b)

        # decode:
        # tile = [low,row0, high,row0, low,row1, high,row1 ...]
        try:
            for row in range(8):
                low = tile[2 * row]
                high = tile[2 * row + 1]
                for x in range(8):
                    bit = 7 - x
                    lo = (low >> bit) & 1
                    hi = (high >> bit) & 1
                    idx = GB_REVERSE[(lo, hi)]
                    self.grid_data[row][x] = idx
        except Exception:
            messagebox.showerror("Error", "Hex does not map to valid GB color codes.")
            return

        self._draw_canvas()
        self._update_preview()


if __name__ == "__main__":
    app = GBPixelEditor()
    app.mainloop()
