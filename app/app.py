import time
import tkinter as tk
from threading import Thread

import pymem
import XInput
from XInput import EventHandler, GamepadThread


from .models import Config


GEARS = {
    (-1, 1): 1,
    (-1, -1): 2,
    (0, 1): 3,
    (0, -1): 4,
    (1, 1): 5,
    (1, -1): 6,
}


class App:
    def __init__(self, config_file: str):
        with open(config_file, encoding="utf-8") as file:
            self.config = Config.from_json(file.read())

        self.gear_x = 0
        self.gear_y = 0
        self.gear = 0

        self._init_tk()
        self._init_display()
        self._init_pymem()

    def _init_tk(self):
        self.tk = tk.Tk()
        self.tk.title("Gearbox")
        self.canvas = tk.Canvas(
            self.tk, width=600, height=400, bg=self.config.theme.bg_color, offset="0,0"
        )
        self.canvas.pack()

    def _init_display(self):
        self.display = GearDisplay(app=self)

    def _init_pymem(self):
        self.pm = pymem.Pymem()
        self.pm_initialized = False

    def _update_loop(self):
        while not self.pm_initialized:
            print("Waiting for speed2.exe")
            try:
                self.pm.open_process_from_name("speed2.exe")
                self.pm_initialized = True
                print("Hooked into the process")
            except Exception:
                pass
            time.sleep(0.5)

        while True:
            try:
                addr = self.pm.read_uint(self.pm.base_address + 0x0049CE58)
                addr = self.pm.read_uint(addr + 8) + 0x1E4
                gear = self.pm.read_int(addr) - 1
            except pymem.exception.MemoryReadError:
                continue

            if self.gear != gear:
                self.gear = gear
                self.display.update_circles()

            time.sleep(0.2)

    def run(self):
        handler = StickHandler(app=self)
        game_thread = GamepadThread(handler)
        thread = Thread(target=self._update_loop, daemon=True)

        thread.start()
        self.tk.mainloop()
        game_thread.stop()


class GearDisplay:
    def __init__(self, app: App):
        self.app = app
        self.theme = self.app.config.theme

        self._draw_elements()

    def _draw_elements(self):
        # Canvas size
        width, height = (
            self.app.canvas.winfo_reqwidth(),
            self.app.canvas.winfo_reqheight(),
        )

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
        y0 = self.y_center - self.theme.line_size // 2
        y1 = y0 + self.theme.line_size

        self.app.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.theme.line_color, outline=self.theme.line_color
        )

        # Left
        x0 = self.left
        x1 = self.top
        y0 = self.left + self.theme.line_size
        y1 = self.bottom

        self.app.canvas.create_rectangle(
            x0, x1, y0, y1, fill=self.theme.line_color, outline=self.theme.line_color
        )

        # Center
        x0 = self.x_center - self.theme.line_size // 2
        x1 = x0 + self.theme.line_size
        y0 = self.top
        y1 = self.bottom

        self.app.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.theme.line_color, outline=self.theme.line_color
        )

        # Right
        x0 = self.right - self.theme.line_size
        x1 = x0 + self.theme.line_size
        y0 = self.top
        y1 = self.bottom

        self.app.canvas.create_rectangle(
            x0, y0, x1, y1, fill=self.theme.line_color, outline=self.theme.line_color
        )

    def _draw_gear(self, x: int, y: int, idx: int = None):
        oval = self.app.canvas.create_oval(
            x,
            y,
            x + self.theme.circle_size,
            y + self.theme.circle_size,
            fill=self.theme.gear_inactive_color,
            outline=self.theme.gear_inactive_color,
            tags=["gears", f"gear_{idx}"] if idx is not None else ["gears"],
        )
        if idx is not None:
            self.app.canvas.create_text(
                x + self.theme.circle_size // 2,
                y + self.theme.circle_size // 2,
                text=str(idx) if idx > 0 else "N",
                font="Arial 12 bold",
                fill="white",
            )
        return oval

    def _draw_circles(self):
        side_x_offset = (self.theme.circle_size - self.theme.line_size) // 2

        positions = [
            # N
            (
                self.x_center - self.theme.circle_size // 2,
                self.y_center - self.theme.circle_size // 2,
            ),
            # 1
            (
                self.left - side_x_offset,
                self.top - self.theme.circle_size // 2,
            ),
            # 2
            (
                self.left - side_x_offset,
                self.bottom - self.theme.circle_size // 2,
            ),
            # 3
            (
                self.x_center - self.theme.circle_size // 2,
                self.top - self.theme.circle_size // 2,
            ),
            # 4
            (
                self.x_center - self.theme.circle_size // 2,
                self.bottom - self.theme.circle_size // 2,
            ),
            # 5
            (
                self.right - self.theme.circle_size + side_x_offset,
                self.top - self.theme.circle_size // 2,
            ),
            # 6
            (
                self.right - self.theme.circle_size + side_x_offset,
                self.bottom - self.theme.circle_size // 2,
            ),
        ]

        for idx, (x, y) in enumerate(positions):
            self._draw_gear(x, y, idx)

        # Left
        self._draw_gear(
            self.left - side_x_offset,
            self.y_center - self.theme.circle_size // 2,
        )

        # Right
        self._draw_gear(
            self.right - self.theme.circle_size + side_x_offset,
            self.y_center - self.theme.circle_size // 2,
        )

    def _draw_control_circle(self):
        x0 = self.x_center - self.theme.circle_size // 2
        y0 = self.y_center - self.theme.circle_size // 2
        x1 = x0 + self.theme.circle_size
        y1 = y0 + self.theme.circle_size

        self.gear_circle = self.app.canvas.create_oval(
            x0,
            y0,
            x1,
            y1,
            fill=None,
            outline=self.theme.control_circle_color,
        )

    def update_circles(self):
        for idx in range(7):
            color = (
                self.theme.gear_active_color
                if self.app.gear == idx
                else self.theme.gear_inactive_color
            )
            self.app.canvas.itemconfig(f"gear_{idx}", fill=color, outline=color)

    def update_control_circle(self):
        side_x_offset = (self.theme.circle_size - self.theme.line_size) // 2

        x_pos = {
            -1: self.left - side_x_offset,
            0: self.x_center - self.theme.circle_size // 2,
            1: self.right - self.theme.circle_size + side_x_offset,
        }

        y_pos = {
            -1: self.bottom - self.theme.circle_size // 2,
            0: self.y_center - self.theme.circle_size // 2,
            1: self.top - self.theme.circle_size // 2,
        }

        self.app.canvas.coords(
            self.gear_circle,
            (
                x_pos[self.app.gear_x],
                y_pos[self.app.gear_y],
                x_pos[self.app.gear_x] + self.theme.circle_size,
                y_pos[self.app.gear_y] + self.theme.circle_size,
            ),
        )


class StickHandler(EventHandler):
    def __init__(self, app: App):
        super().__init__(
            0, 1, 2, 3, filter=XInput.STICK_RIGHT + XInput.BUTTON_RIGHT_THUMB
        )
        self.app = app
        self.pm = pymem.Pymem("speed2.exe")

    def _update_gear(self, gear: int):
        addr = self.pm.read_uint(self.pm.base_address + 0x0049CE58)
        addr = self.pm.read_uint(addr + 8) + 0x1E4
        self.pm.write_int(addr, gear + 1)

    def process_stick_event(self, event):
        sens_switch = 0.5
        sens_error = 0.5

        if -sens_error <= event.y <= sens_error:
            if event.x <= -sens_switch:
                self.app.gear_x = -1
            elif event.x >= sens_switch:
                self.app.gear_x = 1
            else:
                self.app.gear_x = 0

        if event.y <= -sens_switch:
            self.app.gear_y = -1
        elif event.y >= sens_switch:
            self.app.gear_y = 1
        else:
            self.app.gear_y = 0

        if gear := GEARS.get((self.app.gear_x, self.app.gear_y)):
            self._update_gear(gear)

        self.app.display.update_control_circle()
        self.app.display.update_circles()

    def process_button_event(self, event):
        if event.type == XInput.EVENT_BUTTON_PRESSED:
            if event.button == "RIGHT_THUMB":
                self.app.gear = 0
                self._update_gear(self.app.gear)
                self.app.display.update_circles()

    def process_connection_event(self, event):
        self.app.display.update_circles()
