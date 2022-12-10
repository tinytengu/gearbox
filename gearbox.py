import tkinter as tk

import pymem
import XInput
from XInput import EventHandler, GamepadThread

gear_x = 0
gear_y = 0
gear = 0

GEARS = {
    (-1, 1): 1,
    (-1, -1): 2,
    (0, 1): 3,
    (0, -1): 4,
    (1, 1): 5,
    (1, -1): 6,
}

THEME = {
    "bg": "#171717",
    "lines": "#262626",
    "gear_inactive": "#262626",
    "gear_active": "#22C55E",
    "control_circle": "#22C55E",
}


class GearDisplay:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

        # Config
        self.line_size = 10
        self.line_color = THEME["lines"]

        self.circle_size = self.line_size * 3
        self.circle_colors = (THEME["gear_inactive"], THEME["gear_active"])

        self._draw_elements()

    def _draw_elements(self):
        # Canvas size
        width, height = self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight()

        # Gearbox area
        self.area_w = round(width * 0.6)
        self.area_h = round(height * 0.6)

        self.left = (width - self.area_w) // 2
        self.right = self.left + self.area_w
        self.x_center = width // 2

        self.top = (height - self.area_h) // 2
        self.bottom = self.top + self.area_h
        self.y_center = height // 2

        self._draw_lines()
        self._draw_circles()
        self._draw_control_circle()

    def _draw_lines(self):
        # Horizontal
        x0 = self.left
        x1 = self.right
        y0 = self.y_center - self.line_size // 2
        y1 = y0 + self.line_size

        self.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.line_color, outline=self.line_color
        )

        # Left
        x0 = self.left
        x1 = self.top
        y0 = self.left + self.line_size
        y1 = self.bottom

        self.canvas.create_rectangle(
            x0, x1, y0, y1, fill=self.line_color, outline=self.line_color
        )

        # Center
        x0 = self.x_center - self.line_size // 2
        x1 = x0 + self.line_size
        y0 = self.top
        y1 = self.bottom

        self.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.line_color, outline=self.line_color
        )

        # Right
        x0 = self.right - self.line_size
        x1 = x0 + self.line_size
        y0 = self.top
        y1 = self.bottom

        self.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.line_color, outline=self.line_color
        )

    def _draw_gear(self, x: int, y: int, idx: int = None):
        color = self.circle_colors[0]
        oval = self.canvas.create_oval(
            x,
            y,
            x + self.circle_size,
            y + self.circle_size,
            fill=color,
            outline=color,
            tags=["gears", f"gear_{idx}"] if idx is not None else ["gears"],
        )
        if idx is not None:
            self.canvas.create_text(
                x + self.circle_size // 2,
                y + self.circle_size // 2,
                text=str(idx) if idx > 0 else "N",
                font="Arial 12 bold",
                fill="white",
            )
        return oval

    def _draw_circles(self):
        side_x_offset = self.circle_size // (self.circle_size // self.line_size)

        positions = [
            # N
            (
                self.x_center - self.circle_size // 2,
                self.y_center - self.circle_size // 2,
            ),
            # 1
            (
                self.left - side_x_offset,
                self.top - self.circle_size // 2,
            ),
            # 2
            (
                self.left - side_x_offset,
                self.bottom - self.circle_size // 2,
            ),
            # 3
            (
                self.x_center - self.circle_size // 2,
                self.top - self.circle_size // 2,
            ),
            # 4
            (
                self.x_center - self.circle_size // 2,
                self.bottom - self.circle_size // 2,
            ),
            # 5
            (
                self.right - self.circle_size + side_x_offset,
                self.top - self.circle_size // 2,
            ),
            # 6
            (
                self.right - self.circle_size + side_x_offset,
                self.bottom - self.circle_size // 2,
            ),
        ]

        for idx, (x, y) in enumerate(positions):
            self._draw_gear(x, y, idx)

        # Left
        self._draw_gear(
            self.left - side_x_offset,
            self.y_center - self.circle_size // 2,
        )

        # Right
        self._draw_gear(
            self.right - self.circle_size + side_x_offset,
            self.y_center - self.circle_size // 2,
        )

    def _draw_control_circle(self):
        x0 = self.x_center - self.circle_size // 2
        y0 = self.y_center - self.circle_size // 2
        x1 = x0 + self.circle_size
        y1 = y0 + self.circle_size

        self.gear_circle = self.canvas.create_oval(
            x0,
            y0,
            x1,
            y1,
            fill=None,
            outline=THEME["control_circle"],
        )

    def update_circles(self):
        global gear

        for idx in range(7):
            color = self.circle_colors[1] if gear == idx else self.circle_colors[0]
            self.canvas.itemconfig(f"gear_{idx}", fill=color, outline=color)

    def update_control_circle(self):
        global gear_x, gear_y, gear

        side_x_offset = self.circle_size // (self.circle_size // self.line_size)

        x_pos = {
            -1: self.left - side_x_offset,
            0: self.x_center - self.circle_size // 2,
            1: self.right - self.circle_size + side_x_offset,
        }

        y_pos = {
            -1: self.bottom - self.circle_size // 2,
            0: self.y_center - self.circle_size // 2,
            1: self.top - self.circle_size // 2,
        }

        self.canvas.coords(
            self.gear_circle,
            (
                x_pos[gear_x],
                y_pos[gear_y],
                x_pos[gear_x] + self.circle_size,
                y_pos[gear_y] + self.circle_size,
            ),
        )


class StickHandler(EventHandler):
    def __init__(self, *controllers, filter: int, display: GearDisplay):
        super().__init__(*controllers, filter=filter)
        self.display = display
        self.pm = pymem.Pymem("speed2.exe")

    def _update_gear(self):
        global gear

        addr = self.pm.read_uint(self.pm.base_address + 0x0049CE58)
        addr = self.pm.read_uint(addr + 8) + 0x1E4
        self.pm.write_int(addr, gear + 1)

    def process_stick_event(self, event):
        global gear_x, gear_y, gear

        sens_switch = 0.5
        sens_error = 0.5

        if -sens_error <= event.y <= sens_error:
            if event.x <= -sens_switch:
                gear_x = -1
            elif event.x >= sens_switch:
                gear_x = 1
            else:
                gear_x = 0

        if event.y <= -sens_switch:
            gear_y = -1
        elif event.y >= sens_switch:
            gear_y = 1
        else:
            gear_y = 0

        if gear_val := GEARS.get((gear_x, gear_y)):
            gear = gear_val
            self._update_gear()

        self.display.update_control_circle()
        self.display.update_circles()

    def process_button_event(self, event):
        global gear
        if event.type == XInput.EVENT_BUTTON_PRESSED:
            if event.button == "RIGHT_THUMB":
                gear = 0
                self._update_gear()
                self.display.update_circles()

    def process_connection_event(self, event):
        self.display.update_circles()


def main():
    root = tk.Tk()
    root.title("Gearbox")
    canvas = tk.Canvas(root, width=600, height=400, bg=THEME["bg"], offset="0,0")
    canvas.pack()

    handler = StickHandler(
        0,
        1,
        2,
        3,
        filter=XInput.STICK_RIGHT + XInput.BUTTON_RIGHT_THUMB,
        display=GearDisplay(canvas),
    )
    thread = GamepadThread(handler)

    root.mainloop()
    thread.stop()


if __name__ == "__main__":
    main()
