# -*- coding: utf-8 -*-
"""时钟

· 时钟页：白底、黑色超大字，居中显示当前北京时间，下方一行日期与星期
· 倒计时页：预设时长 + 自定义分秒，开始 / 暂停 / 继续 / 重置，结束时提醒
· 左上角菜单键：点击后深色侧边菜单从左侧滑出（带缓动动画），内含「时钟」「倒计时」

快捷键：Esc 关闭菜单或退出，F11 全屏 / 还原。
"""

import json
import math
import os
import subprocess
import sys
import time
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
WIDGET_PATH = BASE_DIR / "desktop_countdown.pyw"
WIDGET_CONFIG_PATH = BASE_DIR / "countdown_settings.json"
WIDGET_PID_PATH = BASE_DIR / "countdown_widget.pid"
ALARM_PATH = BASE_DIR / "alarm.wav"
CREATE_NO_WINDOW = 0x08000000

WHITE = "#ffffff"
BLACK = "#000000"
DATE_GREY = "#4a4a4a"

SIDEBAR_BG = "#23262c"
SIDEBAR_TEXT = "#c9cdd6"
SIDEBAR_ACTIVE = "#31353e"
ACCENT = "#4c9ffe"

# 设置页（深色，仿 Windows 时钟设置页）
PAGE_BG = "#1e1e1e"
CARD_BG = "#2b2b2b"
CARD_EDGE = "#3a3a3a"
TEXT_WHITE = "#f3f3f3"
TEXT_DIM = "#a0a0a0"
ACCENT_BLUE = "#4cc2ff"

FONT = "Microsoft YaHei UI"
WEEKDAYS = "一二三四五六日"

MENU_ITEMS = [
    ("clock", "时钟", "gear"),
    ("timer", "倒计时", "hourglass"),
]

# 菜单滑入/滑出的时长与帧数
SLIDE_MS = 190
SLIDE_FRAMES = 12

# 切换页面时「淡出 → 淡入」的时长
FADE_OUT_MS = 90
FADE_IN_MS = 180
FADE_STEP_MS = 14

# 桌面挂件默认设置
WIDGET_DEFAULT_CONFIG = {
    "target": "2027-06-15 09:00",
    "title": "距离中考还有",
    "subtitle": "奋勇拼搏，决战中考",
    "color": "#1a9fe8",
    "scale": 1.0,
    "x": None,
    "y": None,
}

COLOR_PRESETS = [
    ("#1a9fe8", "蓝色"),
    ("#e86a5a", "珊瑚"),
    ("#f0a63c", "橙色"),
    ("#4cb782", "绿色"),
    ("#7a6cf0", "紫色"),
    ("#2f3b4a", "深灰"),
]

DISCLAIMER_TEXT = """本程序为个人业余时间制作的学习 / 班级小工具，不是商业软件。

1. 使用范围
   仅供本人及班级同学、老师在日常学习和班级活动中免费使用。

2. 禁止商用
   不得将本程序（包括源码、界面、铃声、图标等）用于任何商业用途：
   不得出售、出租、捆绑销售，也不得用于付费产品或收费服务。

3. 免责声明
   程序按“现状”提供。作者不对使用过程中可能出现的计时误差、提醒未响、
   显示异常或数据丢失等问题承担责任；涉及考试等重要时间，请以学校通知
   和官方时钟为准。

4. 数据与隐私
   程序完全在本机运行，不联网、不上传任何数据；设置仅保存在本机文件中。

5. 第三方内容
   界面中可能出现的第三方名称、图标等归其各自所有者所有，仅作说明用途。

6. 修改与分发
   欢迎同学自行修改、学习使用，但请保留本声明，并且不得用于商业目的。

继续使用即表示您已阅读并同意以上内容。
"""

SIZE_PRESETS = [
    ("小", 0.85),
    ("标准", 1.0),
    ("大", 1.15),
    ("特大", 1.3),
]

# 深浅两套配色：菜单、时钟、倒计时、设置统一使用
THEMES = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "sub": "#4a4a4a",
        "line": "#e3e4e8",
        "menu_bg": "#f5f6f8",
        "menu_fg": "#3a4150",
        "menu_hover": "#e9ebef",
        "menu_active": "#e3e7ee",
        "menu_active_fg": "#111111",
        "menu_line": "#e3e4e8",
        "card_bg": "#ffffff",
        "card_edge": "#e2e4e9",
        "card_title": "#111111",
        "card_sub": "#6b7280",
        "entry_bg": "#ffffff",
        "entry_fg": "#111111",
        "entry_edge": "#d6d8de",
        "chip_bg": "#f4f4f6",
        "chip_fg": "#111111",
        "chip_hover": "#e7e7ea",
        "primary_bg": "#111111",
        "primary_fg": "#ffffff",
        "primary_hover": "#333333",
        "accent": "#4c9ffe",
        "hint": "#6b7280",
        "progress_bg": "#e6e7ea",
        "progress_fg": "#000000",
        "icon_fg": "#6b7280",
    },
    "dark": {
        "bg": "#232733",
        "fg": "#ffffff",
        "sub": "#b9bfcc",
        "line": "#343849",
        "menu_bg": "#1d2027",
        "menu_fg": "#c9cdd6",
        "menu_hover": "#262a35",
        "menu_active": "#2e3240",
        "menu_active_fg": "#ffffff",
        "menu_line": "#343849",
        "card_bg": "#2e3240",
        "card_edge": "#3a3f4f",
        "card_title": "#ffffff",
        "card_sub": "#a3a9b8",
        "entry_bg": "#1d2027",
        "entry_fg": "#f2f2f2",
        "entry_edge": "#3a3f4f",
        "chip_bg": "#2e3240",
        "chip_fg": "#e8e8e8",
        "chip_hover": "#3a3f4f",
        "primary_bg": "#4cc2ff",
        "primary_fg": "#00131f",
        "primary_hover": "#7ad2ff",
        "accent": "#4cc2ff",
        "hint": "#8f95a3",
        "progress_bg": "#3a3f4f",
        "progress_fg": "#ffffff",
        "icon_fg": "#c9cdd6",
    },
}


def theme_of(name: str) -> dict:
    return THEMES.get(name, THEMES["light"])


# --------------------------------------------------------------------------- 图标
def draw_icon(canvas: tk.Canvas, kind: str, cx: float, cy: float, r: float,
              color: str, width: float = 1.6) -> None:
    """纯线条画的小图标，不依赖任何图标字体。"""
    if kind == "gear":
        canvas.create_oval(cx - r * 0.68, cy - r * 0.68, cx + r * 0.68, cy + r * 0.68,
                           outline=color, width=width)
        canvas.create_oval(cx - r * 0.30, cy - r * 0.30, cx + r * 0.30, cy + r * 0.30,
                           outline=color, width=width)
        for i in range(8):
            a = i * math.pi / 4
            canvas.create_line(cx + math.cos(a) * r * 0.66, cy + math.sin(a) * r * 0.66,
                               cx + math.cos(a) * r * 1.02, cy + math.sin(a) * r * 1.02,
                               fill=color, width=width * 1.4)
    elif kind == "hourglass":
        canvas.create_polygon(cx - r * 0.62, cy - r * 0.86, cx + r * 0.62, cy - r * 0.86,
                              cx, cy, fill="", outline=color, width=width)
        canvas.create_polygon(cx - r * 0.62, cy + r * 0.86, cx + r * 0.62, cy + r * 0.86,
                              cx, cy, fill="", outline=color, width=width)
        canvas.create_line(cx - r * 0.84, cy - r * 0.86, cx + r * 0.84, cy - r * 0.86,
                           fill=color, width=width)
        canvas.create_line(cx - r * 0.84, cy + r * 0.86, cx + r * 0.84, cy + r * 0.86,
                           fill=color, width=width)


def fit_font(font: tkfont.Font, text: str, target_w: float, target_h: float,
             min_size: int = 24, max_size: int = 360) -> int:
    """用真实字体度量反推字号，保证文字尽量大又不超出可用区域。"""
    if not text:
        return int(font.cget("size"))
    font.configure(size=100)  # 先在基准字号上量一次，再按比例缩放
    width = max(font.measure(text), 1)
    height = max(font.metrics("linespace"), 1)
    size = int(min(target_w * 100 / width, target_h * 100 / height))
    size = max(min_size, min(size, max_size))
    font.configure(size=size)
    return size


# --------------------------------------------------------------------------- 淡入淡出基类
def blend_color(color_a: str, color_b: str, t: float) -> str:
    """两色按 t 线性混合，t=0 取 color_a，t=1 取 color_b。"""
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    a = [int(color_a[1:3], 16), int(color_a[3:5], 16), int(color_a[5:7], 16)]
    b = [int(color_b[1:3], 16), int(color_b[3:5], 16), int(color_b[5:7], 16)]
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def mix_color(color: str, bg: str, alpha: float) -> str:
    """把颜色按 alpha 混向背景色：alpha=0 全背景色（不可见），alpha=1 原色。"""
    alpha = 0.0 if alpha < 0 else 1.0 if alpha > 1 else alpha
    src = [int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)]
    dst = [int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)]
    mixed = [int(round(dst[i] + (src[i] - dst[i]) * alpha)) for i in range(3)]
    return "#%02x%02x%02x" % tuple(mixed)


def mix_white(color: str, alpha: float) -> str:
    return mix_color(color, "#ffffff", alpha)


class FadePage(tk.Frame):
    """页面，可对前景/背景色插值，实现「淡出 → 淡入」的换页过渡。"""

    def __init__(self, master):
        super().__init__(master, bg=WHITE)
        self._fade_widgets = []
        self._fade_items = []
        self._fade_bg = "#ffffff"
        self.alpha = 1.0

    def register_fade(self, widget, **options):
        self._fade_widgets.append((widget, options))
        widget.configure(**{opt: mix_color(color, self._fade_bg, 0.0)
                            for opt, color in options.items()})

    def register_canvas_fill(self, canvas, item, color):
        self._fade_items.append((canvas, item, color))
        canvas.itemconfigure(item, fill=mix_color(color, self._fade_bg, 0.0))

    def fade(self, alpha: float):
        self.alpha = alpha
        for widget, options in self._fade_widgets:
            widget.configure(**{opt: mix_color(color, self._fade_bg, alpha)
                                for opt, color in options.items()})
        for canvas, item, color in self._fade_items:
            canvas.itemconfigure(item, fill=mix_color(color, self._fade_bg, alpha))


# --------------------------------------------------------------------------- 时钟页
class ClockPage(FadePage):
    def __init__(self, master):
        super().__init__(master)
        self._win_w, self._win_h = 1, 1
        self._last = None
        self._time_font = tkfont.Font(family=FONT, size=120, weight="bold")
        self._date_font = tkfont.Font(family=FONT, size=20)

        self.time_var = tk.StringVar(value="--:--:--")
        self.date_var = tk.StringVar(value="")

        self.stack = tk.Frame(self, bg=WHITE)
        self.stack.place(relx=0.5, rely=0.5, anchor="center")
        self.time_label = tk.Label(self.stack, textvariable=self.time_var, bg=WHITE,
                                   fg=BLACK, font=self._time_font)
        self.time_label.pack()
        self.date_label = tk.Label(self.stack, textvariable=self.date_var, bg=WHITE,
                                   fg=DATE_GREY, font=self._date_font)
        self.date_label.pack(pady=(10, 0))

        self.register_fade(self.time_label, fg=BLACK)
        self.register_fade(self.date_label, fg=DATE_GREY)

        self.bind("<Configure>", self._on_configure)
        self._tick()

    def apply_theme(self, theme):
        self._fade_bg = theme["bg"]
        self.configure(bg=theme["bg"])
        self.stack.configure(bg=theme["bg"])
        self.time_label.configure(bg=theme["bg"])
        self.date_label.configure(bg=theme["bg"])
        self._fade_widgets = [
            (self.time_label, {"fg": theme["fg"]}),
            (self.date_label, {"fg": theme["sub"]}),
        ]
        self.fade(1.0)

    def _on_configure(self, event):
        self._win_w, self._win_h = event.width, event.height
        self._apply_size()

    def _apply_size(self):
        if self._win_w < 20:
            return
        size = fit_font(self._time_font, self.time_var.get(),
                        target_w=self._win_w * 0.86, target_h=self._win_h * 0.40)
        self._date_font.configure(size=max(13, int(size * 0.11)))

    def _tick(self):
        dt = datetime.now(TZ)
        text = dt.strftime("%H:%M:%S")
        if text != self._last:
            self._last = text
            self.time_var.set(text)
            self.date_var.set(
                f"{dt.year}年{dt.month}月{dt.day}日 星期{WEEKDAYS[dt.weekday()]}"
            )
            self._apply_size()
        self.after(50, self._tick)


# --------------------------------------------------------------------------- 倒计时页
class TimerPage(FadePage):
    """倒计时：像系统时钟那样用 时:分:秒 上下箭头选择时长。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._win_w, self._win_h = 1, 1
        self.state = "idle"          # idle / running / paused / finished
        self.values = [0, 5, 0]      # 时 / 分 / 秒
        self._base_values = [0, 5, 0]  # 重置时回到的基准值
        self.total = 300.0
        self.remaining = 300.0
        self._deadline = 0.0

        self._flash_job = None
        self._flash_on = False
        self._digit_font = tkfont.Font(family=FONT, size=56, weight="bold")
        self._colon_font = tkfont.Font(family=FONT, size=44, weight="bold")

        self.picker = tk.Frame(self, bg=WHITE)
        self.picker.place(relx=0.5, rely=0.40, anchor="center")

        self._digit_labels = []
        self._arrow_buttons = []
        self._colons = []
        self._cols = []
        for index, (upper) in enumerate((99, 59, 59)):
            col = tk.Frame(self.picker, bg=WHITE)
            col.grid(row=0, column=index * 2, padx=8)
            up = tk.Button(col, text="\u25b2", command=lambda i=index: self._step(i, 1),
                           font=(FONT, 11), relief="flat", bd=0, highlightthickness=0,
                           bg=WHITE, fg="#999999", activebackground=WHITE,
                           activeforeground="#666666", cursor="hand2",
                           padx=10, pady=0)
            up.pack()
            digits = tk.Label(col, text="00", bg=WHITE, fg=BLACK, font=self._digit_font)
            digits.pack(pady=2)
            down = tk.Button(col, text="\u25bc", command=lambda i=index: self._step(i, -1),
                             font=(FONT, 11), relief="flat", bd=0, highlightthickness=0,
                             bg=WHITE, fg="#999999", activebackground=WHITE,
                             activeforeground="#666666", cursor="hand2",
                             padx=10, pady=0)
            down.pack(pady=(18, 0))
            self._arrow_buttons.extend((up, down))
            self._digit_labels.append(digits)
            self._cols.append(col)
            if index < 2:
                colon = tk.Label(self.picker, text=":", bg=WHITE, fg=BLACK,
                                 font=self._colon_font)
                colon.grid(row=0, column=index * 2 + 1)
                self._colons.append(colon)

        self.underline = tk.Canvas(self.picker, height=3, bg=WHITE,
                                   highlightthickness=0)
        self._bar = self.underline.create_rectangle(0, 0, 1, 3, fill=ACCENT, width=0)

        self.buttons = tk.Frame(self, bg=WHITE)
        self.buttons.place(relx=0.5, rely=0.73, anchor="center")
        self.start_btn = tk.Button(self.buttons, text="开始", command=self.toggle,
                                   font=(FONT, 12, "bold"), bg=BLACK, fg=WHITE,
                                   activebackground="#333333", activeforeground=WHITE,
                                   relief="flat", bd=0, highlightthickness=0,
                                   padx=30, pady=9, cursor="hand2")
        self.start_btn.pack(side="left", padx=(0, 10))
        self.reset_btn = tk.Button(self.buttons, text="重置", command=self.reset,
                                   font=(FONT, 12), bg="#f4f4f6", fg=BLACK,
                                   activebackground="#e7e7ea", activeforeground=BLACK,
                                   relief="flat", bd=0, highlightthickness=0,
                                   padx=24, pady=9, cursor="hand2")
        self.reset_btn.pack(side="left")

        self.presets = tk.Frame(self, bg=WHITE)
        self.presets.place(relx=0.5, rely=0.85, anchor="center")
        self._preset_buttons = []
        for minutes, text in ((50, "50 分钟"), (100, "100 分钟"), (120, "120 分钟")):
            button = tk.Button(self.presets, text=text,
                               command=lambda m=minutes: self._apply_preset(m),
                               font=(FONT, 11), bg="#f4f4f6", fg=BLACK,
                               activebackground="#e7e7ea", activeforeground=BLACK,
                               relief="flat", bd=0, highlightthickness=0,
                               padx=18, pady=7, cursor="hand2")
            button.pack(side="left", padx=6)
            self._preset_buttons.append(button)

        self.bind("<Configure>", self._on_configure)
        self._sync_button()
        self._render()
        self.after_idle(self._paint_underline)
        self._tick()

    # -- 尺寸 --------------------------------------------------------------
    def _on_configure(self, event):
        self._win_w, self._win_h = event.width, event.height
        size = int(max(30, min(self._win_w * 0.105, self._win_h * 0.17)))
        if int(self._digit_font.cget("size")) != size:
            self._digit_font.configure(size=size)
            self._colon_font.configure(size=int(size * 0.78))
        self.after_idle(self._paint_underline)

    def _paint_underline(self, _event=None):
        first, last = self._digit_labels[0], self._digit_labels[-1]
        try:
            left = first.winfo_rootx() - self.picker.winfo_rootx()
            right = last.winfo_rootx() - self.picker.winfo_rootx() + last.winfo_width()
            top = first.winfo_rooty() - self.picker.winfo_rooty() + first.winfo_height() + 8
        except tk.TclError:
            return
        self.underline.place(x=left, y=top, width=max(1, right - left), height=3)
        self.underline.coords(self._bar, 0, 0, max(1, right - left), 3)

    # -- 选时 --------------------------------------------------------------
    def _step(self, index, delta):
        if self.state in ("running", "paused"):
            return
        if self.state == "finished":
            self.state = "idle"
        upper = (99, 59, 59)[index]
        self.values[index] = (self.values[index] + delta) % (upper + 1)
        self.total = float(self._read_values())
        self.remaining = self.total
        self._sync_button()
        self._render()

    def _read_values(self):
        hours, minutes, seconds = self.values
        return hours * 3600 + minutes * 60 + seconds

    def _apply_preset(self, minutes):
        self._stop_alert()
        self.set_preset(minutes)

    def set_preset(self, minutes):
        self._stop_alert()
        hours, rest = divmod(max(0, int(minutes)) * 60, 3600)
        self.values = [min(hours, 99), rest // 60, rest % 60]
        self.state = "idle"
        self.total = float(max(1, self._read_values()))
        self.remaining = self.total
        self._sync_button()
        self._render()

    # -- 逻辑 --------------------------------------------------------------
    def _sync_button(self):
        self.start_btn.configure(text={
            "idle": "开始",
            "running": "暂停",
            "paused": "继续",
            "finished": "重新开始",
        }[self.state])

    def _set_arrows_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for button in self._arrow_buttons:
            button.configure(state=state,
                             disabledforeground=self.t.get("sub", "#8a8a8a"))

    def toggle(self):
        if self.state == "running":
            self.state = "paused"
            self._sync_button()
            return

        if self.state in ("idle", "finished"):
            seconds = self._read_values()
            if seconds <= 0:
                self.app.toast("请先设置倒计时时长")
                return
            self._base_values = list(self.values)
            self.total = float(seconds)
            self.remaining = float(seconds)

        self._stop_alert()
        self._deadline = time.monotonic() + self.remaining
        self.state = "running"
        self._set_arrows_enabled(False)
        self._sync_button()
        self._render()

    def reset(self):
        self._stop_alert()
        self.state = "idle"
        self.values = list(self._base_values)
        self.total = float(self._read_values())
        self.remaining = self.total
        self._set_arrows_enabled(True)
        self._sync_button()
        self._render()

    def _finish(self):
        self.state = "finished"
        self.remaining = 0.0
        self._set_arrows_enabled(True)
        self._sync_button()
        self.app.start_alarm()
        self.app.show_timer_alert(self._stop_alert)
        self._flash_digits()

    def _flash_digits(self):
        if self.state != "finished":
            return
        self._flash_on = not getattr(self, "_flash_on", False)
        color = self.t["accent"] if self._flash_on else self.t["fg"]
        for label in self._digit_labels + self._colons:
            label.configure(fg=color)
        self._flash_job = self.after(460, self._flash_digits)

    def _stop_alert(self):
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
            self._flash_job = None
        for label in self._digit_labels + self._colons:
            label.configure(fg=self.t["fg"])
        self.app.stop_alarm()
        self.app.stop_timer_alert()

    def _tick(self):
        if self.state == "running":
            left = self._deadline - time.monotonic()
            if left <= 0:
                self._finish()
            else:
                self.remaining = left
        self._render()
        self.after(50, self._tick)

    # -- 渲染 --------------------------------------------------------------
    def _render(self):
        if self.state in ("running", "paused"):
            seconds = int(math.ceil(max(self.remaining, 0.0) - 1e-9))
        elif self.state == "finished":
            seconds = 0
        else:
            seconds = self._read_values()
        hours, rest = divmod(max(0, seconds), 3600)
        minutes, secs = divmod(rest, 60)
        for label, value in zip(self._digit_labels, (hours, minutes, secs)):
            text = f"{value:02d}"
            if label.cget("text") != text:
                label.configure(text=text)
        self._paint_underline()

    # -- 主题 --------------------------------------------------------------
    def apply_theme(self, theme):
        self.t = theme
        self._fade_bg = theme["bg"]
        self.configure(bg=theme["bg"])
        self.picker.configure(bg=theme["bg"])
        for col in self._cols:
            col.configure(bg=theme["bg"])
        self.buttons.configure(bg=theme["bg"])
        self.presets.configure(bg=theme["bg"])
        for button in self._preset_buttons:
            button.configure(bg=theme["chip_bg"], fg=theme["chip_fg"],
                             activebackground=theme["chip_hover"],
                             activeforeground=theme["chip_fg"])
        self.underline.configure(bg=theme["bg"])
        for label in self._digit_labels + self._colons:
            label.configure(bg=theme["bg"])
        for button in self._arrow_buttons:
            button.configure(bg=theme["bg"], activebackground=theme["bg"],
                             fg=theme["sub"], activeforeground=theme["fg"])

        self._fade_widgets = []
        for label in self._digit_labels + self._colons:
            self._fade_widgets.append((label, {"fg": theme["fg"]}))
        for button in self._arrow_buttons:
            self._fade_widgets.append((button, {"fg": theme["sub"],
                                                "activeforeground": theme["fg"]}))
        self._fade_widgets.append(
            (self.start_btn, {"bg": theme["primary_bg"], "fg": theme["primary_fg"],
                              "activebackground": theme["primary_hover"],
                              "activeforeground": theme["primary_fg"]}))
        self._fade_widgets.append(
            (self.reset_btn, {"bg": theme["chip_bg"], "fg": theme["chip_fg"],
                              "activebackground": theme["chip_hover"],
                              "activeforeground": theme["chip_fg"]}))
        for button in self._preset_buttons:
            self._fade_widgets.append(
                (button, {"bg": theme["chip_bg"], "fg": theme["chip_fg"],
                          "activebackground": theme["chip_hover"],
                          "activeforeground": theme["chip_fg"]}))
        self._fade_items = [(self.underline, self._bar, theme["accent"])]
        self.fade(1.0)
        self._set_arrows_enabled(self.state in ("idle", "finished"))


class MenuButton(tk.Canvas):
    SIZE = 46

    def __init__(self, master, command, theme):
        super().__init__(master, width=self.SIZE, height=self.SIZE,
                         bg=theme["bg"], highlightthickness=0, cursor="hand2")
        self._command = command
        self._rest_bg = theme["bg"]
        self._hover_bg = theme["line"]
        self._ink = theme["fg"]
        for i in range(3):
            self.create_line(14, 17 + i * 6, 32, 17 + i * 6, width=2,
                             fill=self._ink, capstyle="round", tags=("bar",))
        self.bind("<Button-1>", lambda _e: self._command())
        self.bind("<Enter>", lambda _e: self.configure(bg=self._hover_bg))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._rest_bg))

    def apply_theme(self, theme):
        self._rest_bg = theme["bg"]
        self._hover_bg = theme["line"]
        self._ink = theme["fg"]
        self.configure(bg=self._rest_bg)
        self.itemconfigure("bar", fill=self._ink)


# --------------------------------------------------------------------------- 侧边菜单
class SidebarRow(tk.Frame):
    def __init__(self, master, key, text, kind, command, theme):
        super().__init__(master, bg=theme["menu_bg"], height=46, cursor="hand2")
        self.pack_propagate(False)
        self.key = key
        self.kind = kind
        self._command = command
        self._active = False
        self.t = theme

        self.accent = tk.Frame(self, width=3, bg=theme["menu_bg"])
        self.accent.pack(side="left", fill="y")
        self.icon = tk.Canvas(self, width=26, height=26, bg=theme["menu_bg"],
                              highlightthickness=0)
        self.icon.pack(side="left", padx=(15, 12))
        self.label = tk.Label(self, text=text, bg=theme["menu_bg"], fg=theme["menu_fg"],
                              font=(FONT, 13), anchor="w")
        self.label.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self._draw_icon(theme["menu_fg"])

        for widget in (self, self.accent, self.icon, self.label):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)

    def _draw_icon(self, color):
        self.icon.delete("all")
        draw_icon(self.icon, self.kind, 13, 13, 7.8, color)

    def _set_bg(self, color):
        self.configure(bg=color)
        for widget in (self.accent, self.icon, self.label):
            widget.configure(bg=color)

    def apply_theme(self, theme):
        self.t = theme
        if self._active:
            self.set_active(True)
        else:
            self._set_bg(theme["menu_bg"])
            self._draw_icon(theme["menu_fg"])
            self.label.configure(fg=theme["menu_fg"])

    def _on_enter(self, _event=None):
        if not self._active:
            self._set_bg(self.t["menu_hover"])
            self._draw_icon(self.t["menu_active_fg"])
            self.label.configure(fg=self.t["menu_active_fg"])

    def _on_leave(self, _event=None):
        if not self._active:
            self._set_bg(self.t["menu_bg"])
            self._draw_icon(self.t["menu_fg"])
            self.label.configure(fg=self.t["menu_fg"])

    def _on_click(self, _event=None):
        self._command(self.key)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._set_bg(self.t["menu_active"])
            self.accent.configure(bg=self.t["menu_active"])
            self._draw_icon(self.t["menu_active_fg"])
            self.label.configure(fg=self.t["menu_active_fg"])
        else:
            self._set_bg(self.t["menu_bg"])
            self.accent.configure(bg=self.t["menu_bg"])
            self._draw_icon(self.t["menu_fg"])
            self.label.configure(fg=self.t["menu_fg"])


class Sidebar(tk.Frame):
    WIDTH = 262

    def __init__(self, master, on_item, on_settings=None, theme=None,
                 on_theme=None, dark=False):
        theme = theme or THEMES["light"]
        super().__init__(master, bg=theme["menu_bg"])
        self.t = theme
        self.rows = {}
        self._gear_active = False

        self._top = tk.Frame(self, bg=theme["menu_bg"], height=12)
        self._top.pack(fill="x")
        self._edge = tk.Frame(self, width=1, bg=theme["menu_line"])
        self._edge.place(relx=1.0, rely=0, anchor="ne", relheight=1)
        for key, text, kind in MENU_ITEMS:
            row = SidebarRow(self, key, text, kind, on_item, theme)
            row.pack(fill="x", padx=8, pady=1)
            self.rows[key] = row

        # 底部左下角的齿轮：打开设置
        self._filler = tk.Frame(self, bg=theme["menu_bg"])
        self._filler.pack(fill="both", expand=True)
        # 底部的「深色模式」开关
        self._theme_dark = dark
        self._on_theme = on_theme or (lambda _v: None)
        self.theme_row = tk.Frame(self, bg=theme["menu_bg"], cursor="hand2", height=44)
        self.theme_row.pack(fill="x", padx=8, pady=(0, 2))
        self.theme_accent = tk.Frame(self.theme_row, width=3, bg=theme["menu_bg"])
        self.theme_accent.pack(side="left", fill="y")
        self.theme_icon = tk.Canvas(self.theme_row, width=26, height=26,
                                    bg=theme["menu_bg"], highlightthickness=0)
        self.theme_icon.pack(side="left", padx=(15, 12))
        self.theme_label = tk.Label(self.theme_row, text="深色模式", bg=theme["menu_bg"],
                                    fg=theme["menu_fg"], font=(FONT, 13), anchor="w")
        self.theme_label.pack(side="left", expand=True, fill="x")
        for widget in (self.theme_row, self.theme_accent, self.theme_icon,
                       self.theme_label):
            widget.bind("<Button-1>", lambda _e: self._on_theme(not self._theme_dark))
            widget.bind("<Enter>", self._theme_hover_on)
            widget.bind("<Leave>", self._theme_hover_off)
        self._draw_theme_icon()


        self.gear_row = tk.Frame(self, bg=theme["menu_bg"], cursor="hand2", height=44)
        self.gear_row.pack(fill="x", padx=8, pady=(0, 14))
        self.gear_accent = tk.Frame(self.gear_row, width=3, bg=theme["menu_bg"])
        self.gear_accent.pack(side="left", fill="y")
        self.gear_icon = tk.Canvas(self.gear_row, width=26, height=26, bg=theme["menu_bg"],
                                   highlightthickness=0)
        self.gear_icon.pack(side="left", padx=(15, 12))
        self.gear_label = tk.Label(self.gear_row, text="设置", bg=theme["menu_bg"],
                                   fg=theme["menu_fg"], font=(FONT, 13), anchor="w")
        self.gear_label.pack(side="left", expand=True, fill="x")

        for widget in (self.gear_row, self.gear_accent, self.gear_icon, self.gear_label):
            widget.bind("<Enter>", self._gear_hover_on)
            widget.bind("<Leave>", self._gear_hover_off)
            if on_settings is not None:
                widget.bind("<Button-1>", lambda _e: on_settings())
        self._style_gear()

        # 会滑动的蓝色选中条（时钟 / 倒计时 / 设置 之间移动）
        self._active_key = "clock"
        self._indicator_y = 0.0
        self._indicator_h = 0.0
        self._indicator_job = None
        self.indicator = tk.Frame(self, width=3, bg=theme["accent"])
        self.indicator.place(x=8, y=0, width=3, height=1)
        self.bind("<Configure>",
                  lambda _e: self.after_idle(lambda: self._move_indicator(animate=False)))

    def set_dark_state(self, dark):
        self._theme_dark = bool(dark)
        self._draw_theme_icon()

    def _theme_hover_on(self, _event=None):
        for widget in (self.theme_row, self.theme_accent, self.theme_icon,
                       self.theme_label):
            widget.configure(bg=self.t["menu_hover"])

    def _theme_hover_off(self, _event=None):
        for widget in (self.theme_row, self.theme_accent, self.theme_icon,
                       self.theme_label):
            widget.configure(bg=self.t["menu_bg"])

    def _draw_theme_icon(self):
        canvas = self.theme_icon
        canvas.delete("all")
        color = self.t["menu_fg"]
        if self._theme_dark:
            canvas.create_oval(5, 4, 21, 20, fill=color, outline=color)
            canvas.create_oval(11, 2, 27, 18, fill=self.t["menu_bg"],
                               outline=self.t["menu_bg"])
        else:
            canvas.create_oval(8, 8, 18, 18, outline=color, width=1.6)
            for i in range(8):
                a = i * math.pi / 4
                canvas.create_line(13 + math.cos(a) * 6.4, 13 + math.sin(a) * 6.4,
                                   13 + math.cos(a) * 9.4, 13 + math.sin(a) * 9.4,
                                   fill=color, width=1.6)

    def _gear_hover_on(self, _event=None):
        if self._gear_active:
            return
        for widget in (self.gear_row, self.gear_accent, self.gear_icon, self.gear_label):
            widget.configure(bg=self.t["menu_hover"])
        self.gear_icon.delete("all")
        draw_icon(self.gear_icon, "gear", 13, 13, 7.8, self.t["menu_active_fg"])
        self.gear_label.configure(fg=self.t["menu_active_fg"])

    def _gear_hover_off(self, _event=None):
        self._style_gear()

    def _style_gear(self):
        active = self._gear_active
        bg = self.t["menu_active"] if active else self.t["menu_bg"]
        fg = self.t["menu_active_fg"] if active else self.t["menu_fg"]
        for widget in (self.gear_row, self.gear_icon, self.gear_label):
            widget.configure(bg=bg)
        self.gear_accent.configure(bg=bg)
        self.gear_icon.delete("all")
        draw_icon(self.gear_icon, "gear", 13, 13, 7.8, fg)
        self.gear_label.configure(fg=fg)

    def apply_theme(self, theme):
        self.t = theme
        self.configure(bg=theme["menu_bg"])
        self._edge.configure(bg=theme["menu_line"])
        for widget in (self._top, self._filler):
            widget.configure(bg=theme["menu_bg"])
        for row in self.rows.values():
            row.apply_theme(theme)
        for widget in (self.theme_row, self.theme_accent, self.theme_icon,
                       self.theme_label):
            widget.configure(bg=theme["menu_bg"])
        self.theme_label.configure(fg=theme["menu_fg"])
        self._draw_theme_icon()
        self._style_gear()
        if hasattr(self, "indicator"):
            self.indicator.configure(bg=theme["accent"])
            self.after_idle(lambda: self._move_indicator(animate=False))

    def set_active(self, key):
        self._active_key = key
        for row_key, row in self.rows.items():
            row.set_active(row_key == key)
        self._gear_active = key == "settings"
        self._style_gear()
        self.after_idle(self._move_indicator)

    def _target_row(self):
        if self._active_key == "settings":
            return self.gear_row
        return self.rows.get(self._active_key)

    def _move_indicator(self, animate=True):
        row = self._target_row()
        if row is None or not row.winfo_ismapped():
            return
        target_y = row.winfo_y()
        target_h = row.winfo_height()
        if target_h <= 1:
            return
        if self._indicator_h <= 1:
            animate = False
        if (abs(target_y - self._indicator_y) < 0.5
                and abs(target_h - self._indicator_h) < 0.5):
            return
        if not animate:
            self._indicator_y, self._indicator_h = float(target_y), float(target_h)
            self.indicator.place_configure(y=target_y, height=target_h)
            return
        if self._indicator_job is not None:
            self.after_cancel(self._indicator_job)
            self._indicator_job = None
        start_y, start_h = self._indicator_y, self._indicator_h
        steps = 12

        def frame(index):
            t = index / steps
            eased = 1 - (1 - t) ** 3
            y = start_y + (target_y - start_y) * eased
            h = start_h + (target_h - start_h) * eased
            self._indicator_y, self._indicator_h = y, h
            self.indicator.place_configure(y=int(round(y)),
                                           height=max(1, int(round(h))))
            if index < steps:
                self._indicator_job = self.after(14, lambda: frame(index + 1))
            else:
                self._indicator_y, self._indicator_h = float(target_y), float(target_h)
                self.indicator.place_configure(y=target_y, height=target_h)
                self._indicator_job = None

        frame(0)


# --------------------------------------------------------------------------- 挂件设置读写
def load_widget_config() -> dict:
    config = dict(WIDGET_DEFAULT_CONFIG)
    try:
        with WIDGET_CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config.update(json.load(handle))
    except Exception:
        pass
    return config


def save_widget_config(config: dict) -> None:
    try:
        with WIDGET_CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


def parse_widget_target(value):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime((value or "").strip(), fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    return None


def widget_pythonw() -> Path:
    exe = Path(sys.executable)
    if exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.exists():
            return candidate
    return exe


def read_widget_pid():
    try:
        return int(WIDGET_PID_PATH.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def pid_alive(pid) -> bool:
    if not pid:
        return False
    try:
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    except Exception:
        return False


def widget_running() -> bool:
    return pid_alive(read_widget_pid())


def start_widget() -> None:
    try:
        subprocess.Popen([str(widget_pythonw()), str(WIDGET_PATH)],
                         cwd=str(BASE_DIR), creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass


def stop_widget() -> None:
    pid = read_widget_pid()
    if pid_alive(pid):
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass
    try:
        WIDGET_PID_PATH.unlink()
    except Exception:
        pass


AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "DSHCountdownWidget"


def autostart_enabled() -> bool:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY) as key:
            winreg.QueryValueEx(key, AUTOSTART_NAME)
        return True
    except Exception:
        return False


def set_autostart(enabled: bool) -> bool:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enabled:
                command = f'"{widget_pythonw()}" "{WIDGET_PATH}"'
                winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def rounded_points(x1, y1, x2, y2, r):
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


# --------------------------------------------------------------------------- 设置页控件
class ToggleSwitch(tk.Canvas):
    WIDTH, HEIGHT = 46, 24

    def __init__(self, master, value, command, bg="#ffffff", accent="#4c9ffe"):
        super().__init__(master, width=self.WIDTH, height=self.HEIGHT, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self.accent = accent
        self._pos = 1.0 if self.value else 0.0
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _draw(self):
        self.delete("all")
        radius = self.HEIGHT / 2
        fill = self.accent if self.value else "#5c5c5c"
        self.create_polygon(rounded_points(0, 0, self.WIDTH, self.HEIGHT, radius),
                            smooth=True, fill=fill, outline="")
        x = radius + self._pos * (self.WIDTH - 2 * radius)
        self.create_oval(x - radius + 2, 2, x + radius - 2, self.HEIGHT - 2,
                         fill="#ffffff" if self.value else "#d0d0d0", outline="")

    def set_colors(self, bg, accent):
        self.configure(bg=bg)
        self.accent = accent
        self._draw()

    def _on_click(self, _event=None):
        self.set(not self.value, notify=True)

    def set(self, value, notify=False):
        value = bool(value)
        if value == self.value:
            return
        self.value = value
        self._animate()
        if notify and self.command:
            self.command(value)

    def _animate(self):
        target = 1.0 if self.value else 0.0
        start = self._pos
        steps = 14

        def frame(index):
            t = index / steps
            self._pos = start + (target - start) * (1 - (1 - t) ** 3)
            self._draw()
            if index < steps:
                self.after(14, lambda: frame(index + 1))
            else:
                self._pos = target
                self._draw()

        frame(0)


class SizeSelector(tk.Canvas):
    """四个尺寸选项 + 会滑动的蓝色选中块。"""

    ITEM_W = 62
    HEIGHT = 30
    PAD = 4

    def __init__(self, master, options, value, command, theme):
        width = self.ITEM_W * len(options) + self.PAD * 2
        super().__init__(master, width=width, height=self.HEIGHT,
                         bg=theme["card_bg"], highlightthickness=0, cursor="hand2")
        self.theme = theme
        self.options = options
        self.command = command
        self.value = value
        self._index = self._index_of(value)
        self._x = self.PAD + self._index * self.ITEM_W
        self._anim_job = None
        self._indicator = self.create_polygon(rounded_points(0, 0, 10, 10, 14),
                                              smooth=True, fill=theme["accent"],
                                              outline="")
        self._texts = []
        for i, (text, _value) in enumerate(options):
            cx = self.PAD + i * self.ITEM_W + self.ITEM_W / 2
            self._texts.append(self.create_text(cx, self.HEIGHT / 2, text=text,
                                                font=(FONT, 9), fill=theme["chip_fg"]))
        self._draw_indicator()
        self._paint_texts()
        self.bind("<Button-1>", self._on_click)

    def _index_of(self, scale):
        for i, (_text, value) in enumerate(self.options):
            if abs(value - scale) < 1e-6:
                return i
        return 1

    def _draw_indicator(self):
        self.coords(self._indicator,
                    *rounded_points(self._x + 2, 3, self._x + self.ITEM_W - 2,
                                    self.HEIGHT - 3, 13))

    def _paint_texts(self):
        for i, item in enumerate(self._texts):
            self.itemconfigure(item, fill=(self.theme["primary_fg"] if i == self._index
                                           else self.theme["chip_fg"]))

    def _on_click(self, event):
        index = int((event.x - self.PAD) // self.ITEM_W)
        index = max(0, min(index, len(self.options) - 1))
        scale = self.options[index][1]
        if abs(scale - self.value) > 1e-6:
            self.command(scale)

    def set_value(self, scale, animate=True):
        index = self._index_of(scale)
        self.value = scale
        target = self.PAD + index * self.ITEM_W
        if index == self._index and abs(self._x - target) < 0.5:
            return
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self._index = index
        if not animate:
            self._x = target
            self._draw_indicator()
            self._paint_texts()
            return
        start = self._x
        steps = 12

        def frame(i):
            t = i / steps
            eased = 1 - (1 - t) ** 3
            self._x = start + (target - start) * eased
            self._draw_indicator()
            self._paint_texts()
            if i < steps:
                self._anim_job = self.after(14, lambda: frame(i + 1))
            else:
                self._x = target
                self._draw_indicator()
                self._anim_job = None

        frame(0)


class SettingsCard(tk.Canvas):
    """一条设置项：圆角卡片 + 左侧标题说明 + 右侧控件区。"""

    HEIGHT = 60

    def __init__(self, master, title, subtitle="", control_width=260, theme=None):
        theme = theme or THEMES["light"]
        super().__init__(master, height=self.HEIGHT, bg=theme["bg"],
                         highlightthickness=0)
        self._rect = self.create_polygon(rounded_points(0, 0, 20, 20, 8),
                                         smooth=True, fill=theme["card_bg"],
                                         outline=theme["card_edge"])
        self.create_text(20, 21, text=title, anchor="w", fill=theme["card_title"],
                         font=(FONT, 11, "bold"))
        if subtitle:
            self.create_text(20, 40, text=subtitle, anchor="w", fill=theme["card_sub"],
                             font=(FONT, 9))
        self._control_width = control_width
        self.control = tk.Frame(self, bg=theme["card_bg"])
        self._win = self.create_window(0, 0, window=self.control, anchor="e")
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event=None):
        width = max(self.winfo_width(), 20)
        self.coords(self._rect, *rounded_points(1, 1, width - 1, self.HEIGHT - 1, 10))
        self.coords(self._win, width - 20, self.HEIGHT / 2)
        self.itemconfigure(self._win, width=self._control_width)


class SettingsPage(tk.Frame):
    """单窗口内的设置页，配色跟随主题。"""

    def __init__(self, master, app, theme=None):
        super().__init__(master, bg=(theme or THEMES["light"])["bg"])
        self.app = app
        self.t = theme or THEMES["light"]
        self.config = load_widget_config()
        self._hint_job = None
        self._built = False

        self.canvas = tk.Canvas(self, bg=self.t["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=self.t["bg"])
        self._window = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas)
        self.inner.bind("<Configure>",
                        lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.app.bind_all("<MouseWheel>", self._on_wheel, add="+")

        self._rebuild()
        self.after(1500, self._poll)

    # -- 主题 --------------------------------------------------------------
    def set_theme(self, theme):
        self.t = theme
        self.configure(bg=theme["bg"])
        self.canvas.configure(bg=theme["bg"])
        self.inner.configure(bg=theme["bg"])
        self._rebuild()

    def _rebuild(self):
        for child in self.inner.winfo_children():
            child.destroy()
        self._build()
        self.refresh()
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # -- 滚动 --------------------------------------------------------------
    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_wheel(self, event):
        if getattr(self.app, "current_page", None) != "settings":
            return
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    # -- 构建 --------------------------------------------------------------
    def _build(self):
        t = self.t
        inner = self.inner
        tk.Label(inner, text="设置", bg=t["bg"], fg=t["fg"], font=(FONT, 24, "bold"),
                 anchor="w").pack(fill="x", padx=(76, 48), pady=(16, 10))

        tk.Label(inner, text="窗口倒计时", bg=t["bg"], fg=t["fg"],
                 font=(FONT, 13, "bold"), anchor="w").pack(fill="x", padx=48,
                                                           pady=(0, 10))

        # 1. 桌面挂件开关
        row = SettingsCard(inner, "桌面倒计时", "在桌面显示中考倒计时挂件",
                           control_width=56, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.toggle = ToggleSwitch(row.control, value=widget_running(),
                                   command=self._toggle_widget, bg=t["card_bg"],
                                   accent=t["accent"])
        self.toggle.pack()

        row = SettingsCard(inner, "开机自启动", "登录 Windows 后自动打开桌面倒计时挂件",
                           control_width=56, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.autostart_toggle = ToggleSwitch(row.control, value=autostart_enabled(),
                                             command=self._toggle_autostart,
                                             bg=t["card_bg"], accent=t["accent"])
        self.autostart_toggle.pack()

        # 2. 卡片颜色
        row = SettingsCard(inner, "卡片颜色", "挂件卡片的主色", control_width=356, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.swatches = {}
        for color, _name in COLOR_PRESETS:
            canvas = tk.Canvas(row.control, width=36, height=24, bg=t["card_bg"],
                               highlightthickness=0, cursor="hand2")
            canvas.pack(side="left", padx=(0, 6))
            self.swatches[color] = canvas
            canvas.bind("<Button-1>", lambda _e, c=color: self._choose_color(c))
        tk.Button(row.control, text="自定义…", command=self._pick_color, font=(FONT, 9),
                  bg=t["chip_bg"], fg=t["chip_fg"], activebackground=t["chip_hover"],
                  activeforeground=t["chip_fg"], relief="flat", bd=0,
                  highlightthickness=0, padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(4, 0))

        # 3. 卡片大小
        row = SettingsCard(inner, "卡片大小", "小 / 标准 / 大 / 特大，整体等比缩放",
                           control_width=300, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.size_selector = SizeSelector(row.control, SIZE_PRESETS,
                                          getattr(self, "_current_scale", 1.0),
                                          self._choose_scale, t)
        self.size_selector.pack(side="right")

        # 4. 名称
        row = SettingsCard(inner, "倒计日名称", "显示在卡片上方的标题",
                           control_width=286, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.title_entry = self._entry(row.control, width=24)
        self.title_entry.pack(side="right")

        # 5. 日期
        row = SettingsCard(inner, "倒计时日期", "例如 2027-06-15 09:00",
                           control_width=336, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.time_entry = self._entry(row.control, width=7)
        self.time_entry.pack(side="right")
        tk.Label(row.control, text="时间", bg=t["card_bg"], fg=t["card_sub"],
                 font=(FONT, 9)).pack(side="right", padx=8)
        self.date_entry = self._entry(row.control, width=12)
        self.date_entry.pack(side="right")

        # 6. 下方文字
        row = SettingsCard(inner, "下方文字", "显示在卡片底部的小字",
                           control_width=286, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        self.subtitle_entry = self._entry(row.control, width=24)
        self.subtitle_entry.pack(side="right")

        row = SettingsCard(inner, "免责声明", "个人制作，仅供班级学习使用，请勿商用",
                           control_width=110, theme=t)
        row.pack(fill="x", padx=48, pady=4)
        tk.Button(row.control, text="查看声明", command=self.app.show_disclaimer,
                  font=(FONT, 10), bg=t["chip_bg"], fg=t["chip_fg"],
                  activebackground=t["chip_hover"], activeforeground=t["chip_fg"],
                  relief="flat", bd=0, highlightthickness=0, padx=14, pady=6,
                  cursor="hand2").pack(side="right")

        self.hint = tk.Label(inner, text="修改后自动保存，正在运行的挂件会自动刷新",
                             bg=t["bg"], fg=t["hint"], font=(FONT, 9), anchor="w")
        self.hint.pack(fill="x", padx=48, pady=(12, 20))

    def _entry(self, parent, width):
        t = self.t
        entry = tk.Entry(parent, width=width, font=(FONT, 10), bg=t["entry_bg"],
                         fg=t["entry_fg"], insertbackground=t["entry_fg"], relief="flat",
                         highlightthickness=1, highlightbackground=t["entry_edge"],
                         highlightcolor=t["accent"], disabledbackground=t["entry_bg"],
                         disabledforeground=t["sub"])
        entry.bind("<FocusOut>", lambda _e: self._commit_text())
        entry.bind("<Return>", lambda _e: self._commit_text())
        return entry

    # -- 状态 --------------------------------------------------------------
    def refresh(self):
        self.config = load_widget_config()
        target = parse_widget_target(self.config.get("target")) or parse_widget_target(
            WIDGET_DEFAULT_CONFIG["target"])
        values = (
            (self.title_entry, self.config.get("title", "")),
            (self.subtitle_entry, self.config.get("subtitle", "")),
            (self.date_entry, target.strftime("%Y-%m-%d")),
            (self.time_entry, target.strftime("%H:%M")),
        )
        for entry, value in values:
            entry.delete(0, "end")
            entry.insert(0, value)
        self._choose_color(self.config.get("color") or WIDGET_DEFAULT_CONFIG["color"],
                           save=False)
        try:
            scale = float(self.config.get("scale") or 1.0)
        except (TypeError, ValueError):
            scale = 1.0
        self._choose_scale(scale, save=False)
        self.toggle.set(widget_running())
        self.autostart_toggle.set(autostart_enabled())
        self._set_hint("修改后自动保存，正在运行的挂件会自动刷新")

    def _set_hint(self, message, error=False, sticky_ms=2200):
        self.hint.configure(text=message,
                            fg="#ff8a80" if error else self.t["hint"])
        if self._hint_job is not None:
            self.after_cancel(self._hint_job)
        if sticky_ms:
            self._hint_job = self.after(
                sticky_ms, lambda: self.hint.configure(
                    text="修改后自动保存，正在运行的挂件会自动刷新",
                    fg=self.t["hint"]))

    def _poll(self):
        self.toggle.set(widget_running())
        self.after(1500, self._poll)

    # -- 操作 --------------------------------------------------------------
    def _choose_color(self, color, save=True):
        for preset, canvas in self.swatches.items():
            canvas.delete("all")
            canvas.create_polygon(rounded_points(1, 2, 35, 22, 6), smooth=True,
                                  fill=preset, outline="")
            if preset.lower() == color.lower():
                canvas.create_polygon(rounded_points(0, 1, 36, 23, 7), smooth=True,
                                      fill="", outline=self.t["fg"], width=2)
        if not save:
            self._current_color = color
            return
        self.config["color"] = color
        save_widget_config(self.config)
        self._current_color = color
        self._set_hint("已保存颜色")

    def _pick_color(self):
        from tkinter import colorchooser

        color = colorchooser.askcolor(color=getattr(self, "_current_color", "#1a9fe8"),
                                      parent=self.app, title="选择卡片颜色")[1]
        if color:
            self._choose_color(color)

    def _choose_scale(self, scale, save=True):
        self._current_scale = scale
        if hasattr(self, "size_selector"):
            self.size_selector.set_value(scale, animate=save)
        if save:
            self.config["scale"] = scale
            save_widget_config(self.config)
            self._set_hint("已保存大小")

    def _commit_text(self):
        date_text = self.date_entry.get().strip()
        time_text = self.time_entry.get().strip()
        target = parse_widget_target(f"{date_text} {time_text}")
        if target is None:
            self._set_hint("日期或时间格式不对，例如 2027-06-15 / 09:00", error=True)
            return
        self.config = load_widget_config()
        self.config.update(
            target=target.strftime("%Y-%m-%d %H:%M"),
            title=self.title_entry.get().strip() or WIDGET_DEFAULT_CONFIG["title"],
            subtitle=self.subtitle_entry.get().strip(),
            color=getattr(self, "_current_color", self.config.get("color")),
            scale=getattr(self, "_current_scale", self.config.get("scale")),
        )
        save_widget_config(self.config)
        self._set_hint("已保存")

    def _toggle_autostart(self, value):
        if set_autostart(bool(value)):
            self._set_hint("已开启开机自启动" if value else "已关闭开机自启动")
        else:
            self.autostart_toggle.set(not value, notify=False)
            self._set_hint("写入注册表失败，无法修改开机自启动", error=True)

    def _toggle_widget(self, value):
        if value:
            start_widget()
            self._set_hint("桌面倒计时已开启")
        else:
            stop_widget()
            self._set_hint("桌面倒计时已关闭")
        self.after(600, lambda: self.toggle.set(widget_running()))


class App(tk.Tk):
    WIDTH = 1060
    HEIGHT = 680

    def __init__(self):
        super().__init__()
        self.title("时钟")
        self.minsize(720, 460)
        self._center(self.WIDTH, self.HEIGHT)
        self._fullscreen = False
        self._anim_job = None
        self._sidebar_x = 0
        self._fade_job = None
        self._theme_job = None

        config = load_widget_config()
        self.theme_name = config.get("theme") if config.get("theme") in THEMES else "light"
        self.theme = theme_of(self.theme_name)
        self.configure(bg=self.theme["bg"])

        self.clock_page = ClockPage(self)
        self.timer_page = TimerPage(self, self)
        self.settings_page = SettingsPage(self, self, self.theme)
        self.pages = {"clock": self.clock_page, "timer": self.timer_page,
                      "settings": self.settings_page}
        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)

        # 菜单键放在一个 Frame 里，方便用 lift() 保持在页面之上
        self.menu_holder = tk.Frame(self, bg=self.theme["bg"])
        self.menu_holder.place(x=14, y=14)
        self.menu_btn = MenuButton(self.menu_holder, self.toggle_menu, self.theme)
        self.menu_btn.pack()

        self.sidebar = Sidebar(self, self.on_menu_item, self.open_settings, self.theme,
                              on_theme=self.toggle_theme_menu,
                              dark=self.theme_name == "dark")
        self.menu_open = False
        self.current_page = None

        self._toast = None
        self._toast_job = None
        self._alert = None

        self.bind("<Escape>", self._on_escape)
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind_all("<Button-1>", self._global_click, add="+")

        self.apply_theme(self.theme_name, save=False)
        self.show_page("clock", animated=False)

    # -- 主题 --------------------------------------------------------------
    def set_theme(self, name):
        self.apply_theme(name, save=True)

    def toggle_theme_menu(self, value=None):
        """菜单里的深色模式开关：圆形扩散动画后切换主题。"""
        target = "dark" if value else "light"
        if target == self.theme_name:
            self.sidebar.set_dark_state(self.theme_name == "dark")
            return
        self._animate_theme_change(target)

    def _animate_theme_change(self, name):
        """从菜单图标扩散的圆形波纹 + 配色交叉渐变，文字与图标全程可见。"""
        if self._theme_job is not None:
            return
        if self.current_page == "settings":
            self.apply_theme(name, save=True)
            return
        old = theme_of(self.theme_name)
        new = theme_of(name)
        steps = 14

        def frame(index):
            t = index / steps
            eased = t * t * (3 - 2 * t)
            palette = {}
            for key, value in old.items():
                other = new.get(key, value)
                if (isinstance(value, str) and value.startswith("#")
                        and isinstance(other, str) and other.startswith("#")):
                    palette[key] = blend_color(value, other, eased)
                else:
                    palette[key] = other if eased >= 0.5 else value
            self._paint_palette(palette)
            if index < steps:
                self._theme_job = self.after(18, lambda: frame(index + 1))
            else:
                self._theme_job = None
                self.apply_theme(name, save=True)

        frame(0)

    def _paint_palette(self, palette):
        self.configure(bg=palette["bg"])
        self.menu_holder.configure(bg=palette["bg"])
        self.menu_btn.apply_theme(palette)
        self.sidebar.apply_theme(palette)
        self.clock_page.apply_theme(palette)
        self.timer_page.apply_theme(palette)

    def apply_theme(self, name, save=False):
        self.theme_name = name if name in THEMES else "light"
        self.theme = theme_of(self.theme_name)
        t = self.theme
        self.configure(bg=t["bg"])
        self.menu_holder.configure(bg=t["bg"])
        self.menu_btn.apply_theme(t)
        self.sidebar.apply_theme(t)
        self.clock_page.apply_theme(t)
        self.timer_page.apply_theme(t)
        self.settings_page.set_theme(t)
        self.sidebar.set_dark_state(self.theme_name == "dark")
        if save:
            config = load_widget_config()
            config["theme"] = self.theme_name
            save_widget_config(config)

    # -- 窗口 --------------------------------------------------------------
    def _center(self, width: int, height: int):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_fullscreen(self, _event=None):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)

    def _on_escape(self, _event=None):
        if self.menu_open:
            self.close_menu()
        elif self.current_page == "settings":
            self.show_page("clock")
        else:
            self.destroy()

    # -- 菜单动画 ----------------------------------------------------------
    def _slide_to(self, target_x: int, on_done=None):
        """从当前 x 缓动滑到 target_x（ease-out 三次方）。"""
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

        start_x = self._sidebar_x
        delta = target_x - start_x
        interval = max(1, SLIDE_MS // SLIDE_FRAMES)

        def frame(index):
            t = index / SLIDE_FRAMES
            eased = 1 - (1 - t) ** 3
            self._sidebar_x = int(round(start_x + delta * eased))
            self.sidebar.place_configure(x=self._sidebar_x)
            if index < SLIDE_FRAMES:
                self._anim_job = self.after(interval, lambda: frame(index + 1))
            else:
                self._anim_job = None
                if on_done is not None:
                    on_done()

        frame(0)

    def toggle_menu(self):
        if self.menu_open:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        if self.menu_open:
            return
        self.menu_open = True
        self._sidebar_x = -Sidebar.WIDTH
        self.sidebar.place(x=self._sidebar_x, y=0, width=Sidebar.WIDTH, relheight=1)
        self.sidebar.lift()
        self._slide_to(0)

    def close_menu(self):
        if not self.menu_open:
            return
        self.menu_open = False
        self._slide_to(-Sidebar.WIDTH, on_done=self.sidebar.place_forget)

    def on_menu_item(self, key):
        # 切换页面时菜单保持展开，点空白处才收回
        self.show_page(key)

    def _global_click(self, event):
        if not self.menu_open:
            return
        widget = event.widget
        if (widget is self.menu_btn
                or self._is_inside(widget, self.menu_holder)
                or self._is_inside(widget, self.sidebar)):
            return
        self.close_menu()

    @staticmethod
    def _is_inside(widget, ancestor) -> bool:
        while widget is not None:
            if widget is ancestor:
                return True
            widget = getattr(widget, "master", None)
        return False

    # -- 换页：淡出 → 淡入 --------------------------------------------------
    def _animate_fade(self, page, start, end, duration, on_done=None):
        steps = max(1, int(duration / FADE_STEP_MS))

        def frame(index):
            t = index / steps
            eased = t * t * (3 - 2 * t)  # smoothstep，起止更柔和
            page.fade(start + (end - start) * eased)
            if index < steps:
                self._fade_job = self.after(FADE_STEP_MS, lambda: frame(index + 1))
            else:
                self._fade_job = None
                if on_done is not None:
                    on_done()

        frame(0)

    def show_page(self, key, animated=True):
        new_page = self.pages[key]
        if key == "settings" or self.current_page == "settings":
            animated = False          # 设置页是深色的，不做白色淡入淡出

        if key == self.current_page:
            self.sidebar.set_active(key)
            if self._fade_job is not None:      # 正在切换途中又切回来：还原
                self.after_cancel(self._fade_job)
                self._fade_job = None
                self._restore_alpha(self.current_page)
            self._sync_page_theme()
            return

        if self._fade_job is not None:          # 连续点击：先收尾
            self.after_cancel(self._fade_job)
            self._fade_job = None
            if self.current_page is not None:
                self._restore_alpha(self.current_page)

        old_page = self.pages[self.current_page] if self.current_page else None
        self.sidebar.set_active(key)

        if not animated or old_page is None:
            if hasattr(new_page, "fade"):
                new_page.fade(1.0)
            new_page.lift()
            self.menu_holder.lift()
            if self.menu_open:
                self.sidebar.lift()
            self.current_page = key
            self._sync_page_theme()
            if key == "settings":
                self.settings_page.refresh()
            return

        def enter():
            new_page.fade(0.0)
            new_page.lift()
            self.menu_holder.lift()
            if self.menu_open:
                self.sidebar.lift()
            self.current_page = key
            self._sync_page_theme()
            self._animate_fade(new_page, 0.0, 1.0, FADE_IN_MS)

        self._animate_fade(old_page, 1.0, 0.0, FADE_OUT_MS, enter)

    def _restore_alpha(self, key):
        page = self.pages.get(key) if key else None
        if page is not None and hasattr(page, "fade"):
            page.fade(1.0)

    def _sync_page_theme(self):
        self.menu_btn.apply_theme(self.theme)
        self.menu_holder.configure(bg=self.theme["bg"])

    # -- 设置 --------------------------------------------------------------
    def open_settings(self):
        """在同一个窗口里切到设置页（不另开窗口），菜单保持展开。"""
        self.show_page("settings")

    # -- 倒计时提醒 --------------------------------------------------------
    def start_alarm(self):
        try:
            import winsound

            winsound.PlaySound(str(ALARM_PATH),
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            return True
        except Exception:
            try:
                self.bell()
            except Exception:
                pass
            return False

    def stop_alarm(self):
        try:
            import winsound

            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    def show_timer_alert(self, on_stop):
        self.stop_timer_alert()
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass
        frame = tk.Frame(self, bg="#1c1c1e", padx=18, pady=10)
        tk.Label(frame, text="\u23f0 时间到", bg="#1c1c1e", fg="#ffffff",
                 font=(FONT, 13, "bold")).pack(side="left")
        tk.Button(frame, text="停止", command=on_stop, font=(FONT, 11, "bold"),
                  bg="#4cc2ff", fg="#00131f", activebackground="#7ad2ff",
                  activeforeground="#00131f", relief="flat", bd=0, highlightthickness=0,
                  padx=16, pady=4, cursor="hand2").pack(side="left", padx=(16, 0))
        frame.place(relx=0.5, rely=0.9, anchor="center")
        frame.lift()
        self._alert = frame

    def stop_timer_alert(self):
        if self._alert is not None:
            self._alert.destroy()
            self._alert = None

    # -- 免责声明 ----------------------------------------------------------
    def show_disclaimer(self):
        if getattr(self, "_disclaimer", None) is not None:
            self._disclaimer.lift()
            return
        t = self.theme
        win = tk.Toplevel(self)
        win.title("免责声明")
        win.configure(bg=t["bg"])
        win.transient(self)
        win.resizable(False, False)
        width, height = 660, 470
        x = max(0, self.winfo_rootx() + (self.winfo_width() - width) // 2)
        y = max(0, self.winfo_rooty() + (self.winfo_height() - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(win, text="免责声明", bg=t["bg"], fg=t["fg"],
                 font=(FONT, 16, "bold"), anchor="w").pack(
            fill="x", padx=24, pady=(18, 10))

        body = tk.Frame(win, bg=t["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        text = tk.Text(body, wrap="word", bg=t["card_bg"], fg=t["fg"],
                       relief="flat", bd=0, padx=16, pady=14,
                       font=(FONT, 10), highlightthickness=1,
                       highlightbackground=t["card_edge"],
                       insertbackground=t["fg"], yscrollcommand=lambda *a: None)
        scrollbar = tk.Scrollbar(body, orient="vertical", command=text.yview,
                                 bg=t["bg"], troughcolor=t["bg"],
                                 activebackground=t["chip_hover"], relief="flat",
                                 bd=0, width=12)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", DISCLAIMER_TEXT)
        text.configure(state="disabled")
        text.yview_moveto(0.0)
        text.see("1.0")

        def close():
            self._disclaimer = None
            win.destroy()

        tk.Button(win, text="我知道了", command=close, font=(FONT, 11, "bold"),
                  bg=t["primary_bg"], fg=t["primary_fg"],
                  activebackground=t["primary_hover"],
                  activeforeground=t["primary_fg"], relief="flat", bd=0,
                  highlightthickness=0, padx=26, pady=8,
                  cursor="hand2").pack(side="right", padx=24, pady=(0, 18))
        self._disclaimer = win
        win.grab_set()
        win.focus_force()

    # -- 其它 --------------------------------------------------------------
    def toast(self, message: str):
        if self._toast is None:
            self._toast = tk.Label(self, bg="#1c1c1e", fg="#ffffff",
                                   font=(FONT, 12), padx=18, pady=9)
        self._toast.configure(text=message)
        self._toast.place(relx=0.5, rely=0.93, anchor="center")
        self._toast.lift()
        if self._toast_job is not None:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(1900, self._toast.place_forget)

    def beep(self):
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            try:
                self.bell()
            except Exception:
                pass


if __name__ == "__main__":
    try:  # 高 DPI 下文字更清晰
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = App()
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if arg in ("timer", "--timer", "countdown"):
        # 从桌面挂件的「添加倒计时」直接进入倒计时页
        app.show_page("timer", animated=False)
    elif arg in ("settings", "--settings", "setting"):
        # 从挂件齿轮进入设置页（同一个窗口，不另开窗口）
        app.show_page("settings", animated=False)
    app.mainloop()
