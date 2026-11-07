# -*- coding: utf-8 -*-
"""桌面中考倒计时挂件

· 无边框、置顶的蓝色倒计时卡片 + 下方「添加倒计时」按钮
· 按住卡片左上角的拖动手柄（卡片任意位置也可以）可拖动窗口，位置自动记住
· 左上角手柄右侧的齿轮 → 打开设置窗口（颜色、大小、名称、日期、下方文字）
· 点「添加倒计时」打开同目录的 beijing_time.pyw（时钟 / 倒计时程序）
· 右键菜单：设置 / 打开倒计时程序 / 置顶开关 / 退出
· 设置保存在 countdown_settings.json，挂件运行中会自动刷新
"""

import json
import os
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # Python 3.9+
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # 兜底：北京时间 = UTC+8
    TZ = timezone(timedelta(hours=8))

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "countdown_settings.json"
APP_PATH = BASE_DIR / "beijing_time.pyw"
SETTINGS_PATH = BASE_DIR / "countdown_settings_ui.pyw"
PID_PATH = BASE_DIR / "countdown_widget.pid"

FONT = "Microsoft YaHei UI"
TRANSPARENT = "#ff00ff"      # 透明色键
DEFAULT_COLOR = "#1a9fe8"

CREATE_NO_WINDOW = 0x08000000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

DEFAULT_CONFIG = {
    "target": "2027-06-15 09:00",
    "title": "距离中考还有",
    "subtitle": "奋勇拼搏，决战中考",
    "color": DEFAULT_COLOR,
    "scale": 1.0,
    "x": None,
    "y": None,
}

BASE_W, BASE_H = 540, 240
CARD_BASE = (10, 8, 530, 182)
BTN_BASE = (185, 196, 355, 232)


# --------------------------------------------------------------------------- 颜色
def hex_to_rgb(color: str):
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def mix(color_a: str, color_b: str, t: float) -> str:
    a, b = hex_to_rgb(color_a), hex_to_rgb(color_b)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def luminance(color: str) -> float:
    channels = [v / 255 for v in hex_to_rgb(color)]

    def linear(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(v) for v in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# --------------------------------------------------------------------------- 通用
def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config.update(json.load(handle))
    except Exception:
        pass
    return config


def save_config(config: dict) -> None:
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


def parse_target(value):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime((value or "").strip(), fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    return None


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **options):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def draw_gear(canvas: tk.Canvas, cx, cy, r, color, width=1.5, tags=()):
    import math

    canvas.create_oval(cx - r * 0.66, cy - r * 0.66, cx + r * 0.66, cy + r * 0.66,
                       outline=color, width=width, tags=tags)
    canvas.create_oval(cx - r * 0.28, cy - r * 0.28, cx + r * 0.28, cy + r * 0.28,
                       outline=color, width=width, tags=tags)
    for i in range(8):
        a = i * math.pi / 4
        canvas.create_line(cx + math.cos(a) * r * 0.64, cy + math.sin(a) * r * 0.64,
                           cx + math.cos(a) * r * 1.0, cy + math.sin(a) * r * 1.0,
                           fill=color, width=width * 1.35, tags=tags)


def pythonw_exe() -> Path:
    exe = Path(sys.executable)
    if exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.exists():
            return candidate
    return exe


def pid_alive(pid) -> bool:
    if not pid:
        return False
    try:
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- 挂件
class CountdownWidget:
    def __init__(self, autorun=True):
        self.config = load_config()
        self._read_design()

        self.root = tk.Tk()
        self.root.title("中考倒计时")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            self.root.configure(bg="#eef4f8")

        self.W, self.H = self._scaled_size()
        self.canvas = tk.Canvas(self.root, width=self.W, height=self.H,
                                bg=TRANSPARENT, highlightthickness=0, cursor="arrow")
        self.canvas.pack()

        self._build()
        self._place_window()
        self._write_pid()

        self._config_mtime = self._mtime()
        self._watch_job = self.root.after(600, self._watch_config)
        self.root.bind("<Escape>", lambda _e: self.quit_app())
        self._update()
        if autorun:
            self.root.mainloop()

    # -- 配置 --------------------------------------------------------------
    def _mtime(self):
        try:
            return CONFIG_PATH.stat().st_mtime
        except OSError:
            return None

    def _read_design(self):
        self.title_text = self.config.get("title") or DEFAULT_CONFIG["title"]
        self.subtitle_text = self.config.get("subtitle") or ""
        self.target = parse_target(self.config.get("target")) or parse_target(
            DEFAULT_CONFIG["target"])
        self.card_color = self.config.get("color") or DEFAULT_COLOR
        try:
            self.scale = float(self.config.get("scale") or 1.0)
        except (TypeError, ValueError):
            self.scale = 1.0
        self.scale = max(0.6, min(self.scale, 1.6))

        bright = luminance(self.card_color) > 0.25
        self.text_main = "#08222e" if bright else "#ffffff"
        self.text_sub = mix(self.text_main, self.card_color, 0.25)
        self.handle_color = mix(self.card_color, "#ffffff", 0.6 if bright else 0.45)
        self.edge_color = mix(self.card_color, "#000000", 0.10 if bright else 0.15)
        self.btn_color = mix(self.card_color, "#000000", 0.18) if bright else mix(
            self.card_color, "#ffffff", 0.14)
        self.btn_text = "#ffffff" if luminance(self.btn_color) < 0.55 else "#08222e"

    def _design_key(self):
        return (self.title_text, self.subtitle_text, self.target,
                self.card_color, round(self.scale, 3))

    def _scaled_size(self):
        return int(round(BASE_W * self.scale)), int(round(BASE_H * self.scale))

    # -- 界面 --------------------------------------------------------------
    def _build(self):
        canvas = self.canvas
        canvas.delete("all")
        s = self.scale
        x1, y1, x2, y2 = (v * s for v in CARD_BASE)

        self.card = round_rect(canvas, x1, y1, x2, y2, 16 * s,
                               fill=self.card_color, outline=self.edge_color,
                               width=max(1, int(round(s))), tags=("drag", "card"))

        # 拖动手柄：六个点
        hx, hy, gap, dot = 30 * s, 26 * s, 7 * s, 3.4 * s
        for row in range(3):
            for col in range(2):
                canvas.create_oval(hx + col * gap, hy + row * gap,
                                   hx + col * gap + dot, hy + row * gap + dot,
                                   fill=self.handle_color, outline=self.handle_color,
                                   tags=("drag",))

        # 手柄右侧的齿轮：打开设置
        draw_gear(canvas, 62 * s, 32 * s, 7.6 * s, self.handle_color,
                  width=max(1.0, 1.5 * s), tags=("gear",))

        self._title_font = tkfont.Font(family=FONT, size=max(8, int(round(12 * s))))
        self._big_font = tkfont.Font(family=FONT, size=max(14, int(round(30 * s))),
                                     weight="bold")
        self._sub_font = tkfont.Font(family=FONT, size=max(7, int(round(10 * s))))

        cx = (x1 + x2) / 2
        self.title_item = canvas.create_text(cx, 44 * s, text=self.title_text,
                                             font=self._title_font, fill=self.text_main,
                                             tags=("drag",))
        self.count_item = canvas.create_text(cx, 102 * s, text="--天--时--分--秒",
                                             font=self._big_font, fill=self.text_main,
                                             tags=("drag",))
        self.sub_item = canvas.create_text(cx, 150 * s, text=self.subtitle_text,
                                           font=self._sub_font, fill=self.text_sub,
                                           tags=("drag",))

        bx1, by1, bx2, by2 = (v * s for v in BTN_BASE)
        self.btn = round_rect(canvas, bx1, by1, bx2, by2, 18 * s,
                              fill=self.btn_color, outline="", tags=("button",))
        self.btn_text_item = canvas.create_text((bx1 + bx2) / 2, (by1 + by2) / 2,
                                                text="＋ 添加倒计时", fill=self.btn_text,
                                                font=(FONT, max(8, int(round(12 * s))),
                                                      "bold"),
                                                tags=("button",))

        # 绑定
        canvas.tag_bind("drag", "<Button-1>", self._on_press)
        canvas.tag_bind("drag", "<B1-Motion>", self._on_drag)
        canvas.tag_bind("drag", "<ButtonRelease-1>", self._on_release)
        canvas.tag_bind("drag", "<Enter>", lambda _e: canvas.configure(cursor="fleur"))
        canvas.tag_bind("drag", "<Leave>", lambda _e: canvas.configure(cursor="arrow"))

        canvas.tag_bind("gear", "<Button-1>", lambda _e: self.open_settings())
        canvas.tag_bind("gear", "<Enter>", lambda _e: canvas.configure(cursor="hand2"))
        canvas.tag_bind("gear", "<Leave>", lambda _e: canvas.configure(cursor="arrow"))

        canvas.tag_bind("button", "<Button-1>", lambda _e: self.open_timer_app())
        canvas.tag_bind("button", "<Enter>", self._btn_hover_in)
        canvas.tag_bind("button", "<Leave>", self._btn_hover_out)

        canvas.bind("<Button-3>", self._show_menu)
        self._build_menu()
        self._refresh_text()

    def _build_menu(self):
        self.topmost_var = tk.BooleanVar(value=bool(self.root.attributes("-topmost")))
        self.menu = tk.Menu(self.root, tearoff=0, font=(FONT, 11))
        self.menu.add_command(label="设置…", command=self.open_settings)
        self.menu.add_command(label="打开倒计时程序", command=self.open_timer_app)
        self.menu.add_separator()
        self.menu.add_checkbutton(label="窗口置顶", variable=self.topmost_var,
                                  command=self._apply_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.quit_app)

    def _rebuild(self):
        """配色 / 大小 / 文案变化后整体重绘。"""
        old_w, old_h = self.W, self.H
        x, y = self.root.winfo_x(), self.root.winfo_y()
        # 若原来贴着屏幕右/下边缘，缩放后继续贴边，避免跑到屏幕外
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if x + old_w >= screen_w - 4:
            x = screen_w - int(round(BASE_W * self.scale)) - 40
        if y + old_h >= screen_h - 4:
            y = screen_h - int(round(BASE_H * self.scale)) - 40
        self.W, self.H = self._scaled_size()
        self.canvas.configure(width=self.W, height=self.H)
        self._build()
        x, y = self._clamp_position(x, y)
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _clamp_position(self, x, y):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, min(int(x), max(0, screen_w - self.W)))
        y = max(0, min(int(y), max(0, screen_h - self.H)))
        return x, y

    def _place_window(self):
        screen_w = self.root.winfo_screenwidth()
        x = self.config.get("x")
        y = self.config.get("y")
        if x is None or y is None:
            x, y = max(0, screen_w - self.W - 40), 80
        x, y = self._clamp_position(x, y)
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    # -- 交互 --------------------------------------------------------------
    def _on_press(self, event):
        self._drag_offset = (event.x_root - self.root.winfo_x(),
                             event.y_root - self.root.winfo_y())

    def _on_drag(self, event):
        offset_x, offset_y = self._drag_offset
        x = event.x_root - offset_x
        y = event.y_root - offset_y
        self.root.geometry(f"+{x}+{y}")
        self.pos = (x, y)

    def _on_release(self, _event=None):
        pos = getattr(self, "pos", None)
        if pos:
            self.config["x"], self.config["y"] = int(pos[0]), int(pos[1])
            save_config(self.config)
            self._config_mtime = self._mtime()

    def _btn_hover_in(self, _event=None):
        self.canvas.itemconfigure(self.btn, fill=mix(self.btn_color, "#ffffff", 0.12))

    def _btn_hover_out(self, _event=None):
        self.canvas.itemconfigure(self.btn, fill=self.btn_color)

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _apply_topmost(self):
        self.root.attributes("-topmost", bool(self.topmost_var.get()))

    # -- 功能 --------------------------------------------------------------
    def open_settings(self):
        """在时钟主程序窗口里打开设置页（单窗口，不另开设置窗口）。"""
        try:
            subprocess.Popen([str(pythonw_exe()), str(APP_PATH), "settings"],
                             cwd=str(BASE_DIR), creationflags=CREATE_NO_WINDOW)
        except Exception:
            self._flash_subtitle("打开设置失败，请确认 beijing_time.pyw 在同一文件夹")

    def open_timer_app(self):
        try:
            subprocess.Popen([str(pythonw_exe()), str(APP_PATH), "timer"],
                             cwd=str(BASE_DIR), creationflags=CREATE_NO_WINDOW)
        except Exception:
            self._flash_subtitle("找不到倒计时程序，请确认 beijing_time.pyw 在同一文件夹")

    def _flash_subtitle(self, message: str):
        self.canvas.itemconfigure(self.sub_item, text=message)
        self.root.after(2600, lambda: self.canvas.itemconfigure(
            self.sub_item, text=self.subtitle_text))

    # -- 刷新 --------------------------------------------------------------
    def _refresh_text(self):
        now = datetime.now(TZ)
        left = int((self.target - now).total_seconds())
        if left <= 0:
            text = "0天0时00分00秒"
            subtitle = "中考加油！"
        else:
            days, rest = divmod(left, 86400)
            hours, rest = divmod(rest, 3600)
            minutes, seconds = divmod(rest, 60)
            text = f"{days}天{hours}时{minutes:02d}分{seconds:02d}秒"
            subtitle = self.subtitle_text
        if self.canvas.itemcget(self.count_item, "text") != text:
            self.canvas.itemconfigure(self.count_item, text=text)
            self._fit_big_text(text)
        self.canvas.itemconfigure(self.title_item, text=self.title_text)
        self.canvas.itemconfigure(self.sub_item, text=subtitle)

    def _update(self):
        self._refresh_text()
        self.root.after(200, self._update)

    def _fit_big_text(self, text: str):
        s = self.scale
        size = max(14, int(round(30 * s)))
        self._big_font.configure(size=size)
        limit = (CARD_BASE[2] - CARD_BASE[0] - 36) * s
        while size > 10 and self._big_font.measure(text) > limit:
            size -= 2
            self._big_font.configure(size=size)

    def _watch_config(self):
        mtime = self._mtime()
        if mtime and self._config_mtime and mtime != self._config_mtime:
            old_key = self._design_key()
            self.config = load_config()
            self._read_design()
            if self._design_key() != old_key:
                self._rebuild()
            self._config_mtime = mtime
        elif mtime:
            self._config_mtime = mtime
        self._watch_job = self.root.after(600, self._watch_config)

    # -- 进程 --------------------------------------------------------------
    def _write_pid(self):
        try:
            PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
        except Exception:
            pass

    def quit_app(self):
        try:
            self.config["x"] = self.root.winfo_x()
            self.config["y"] = self.root.winfo_y()
            save_config(self.config)
        finally:
            try:
                PID_PATH.unlink()
            except Exception:
                pass
            self.root.destroy()


def main():
    try:  # 高分屏下文字更清晰
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    CountdownWidget()


if __name__ == "__main__":
    main()
