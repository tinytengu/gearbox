from dataclasses import dataclass
from dataclass_wizard import JSONWizard


@dataclass(repr=True)
class Theme:
    bg_color: str
    line_color: str
    gear_inactive_color: str
    gear_active_color: str
    control_circle_color: str
    line_size: int
    circle_size: int


@dataclass(repr=True)
class Config(JSONWizard):
    gears: int
    autodetect_gears: bool
    show_reverse: bool
    theme: Theme
