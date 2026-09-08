"""Find Dota's visible desktop window without accessing its process."""

from __future__ import annotations

import sys
from dataclasses import dataclass

if sys.platform == "win32":
    import win32gui
else:  # Keeps tests and configuration tools usable off Windows.
    win32gui = None


@dataclass(frozen=True, slots=True)
class ScreenRect:
    left: int
    top: int
    width: int
    height: int

    def as_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class DotaWindow:
    handle: int
    title: str
    client: ScreenRect
    foreground: bool


def is_dota_title(title: str) -> bool:
    return title.strip().casefold() == "dota 2"


def _window_info(handle: int, foreground: bool) -> DotaWindow | None:
    title = win32gui.GetWindowText(handle)
    left, top, right, bottom = win32gui.GetClientRect(handle)
    screen_left, screen_top = win32gui.ClientToScreen(handle, (left, top))
    width, height = right - left, bottom - top
    if not is_dota_title(title) or width <= 0 or height <= 0:
        return None
    return DotaWindow(
        handle,
        title,
        ScreenRect(screen_left, screen_top, width, height),
        foreground,
    )


def foreground_dota_window() -> DotaWindow | None:
    if win32gui is None:
        return None
    handle = win32gui.GetForegroundWindow()
    return _window_info(handle, True) if handle else None


def find_dota_window() -> DotaWindow | None:
    """Return the visible Dota client, preferring the foreground window."""
    foreground = foreground_dota_window()
    if foreground:
        return foreground
    if win32gui is None:
        return None

    found: list[DotaWindow] = []

    def visit(handle: int, _extra: object) -> None:
        if not found and win32gui.IsWindowVisible(handle):
            info = _window_info(handle, False)
            if info:
                found.append(info)

    win32gui.EnumWindows(visit, None)
    return found[0] if found else None

