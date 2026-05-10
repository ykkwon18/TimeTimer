"""
Time Timer — local desktop clone.

Run: python timer.py
"""

import math
import sys
import time
import tkinter as tk

if sys.platform == "win32":
    import winsound
else:
    winsound = None


WINDOW_W = 460
WINDOW_H = 540
DIAL_SIZE = 320
DIAL_PAD = 30
SLIDER_W = 360
SLIDER_H = 30
SLIDER_TRACK_H = 8
HANDLE_R = 9
RED = "#d50000"
LIGHT_RED = "#ffe0e0"
TICK_MS = 100
PULSE_MS = 50
PULSE_PERIOD_S = 3.0


class TimeTimer:
    def __init__(self, root):
        self.root = root
        root.title("Time Timer")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.minsize(280, 420)
        root.resizable(True, True)

        self.default_bg = root.cget("bg")

        self.total_seconds = 45 * 60
        self.remaining_seconds = float(self.total_seconds)
        self.running = False
        self.finished = False
        self.tick_job = None
        self.last_tick_ms = None
        self.pulse_job = None
        self.pulse_phase = 0.0

        self._build_ui()
        self._sync_all_from_total()

    def _build_ui(self):
        self.dial = tk.Canvas(
            self.root,
            width=DIAL_SIZE + 2 * DIAL_PAD,
            height=DIAL_SIZE + 2 * DIAL_PAD,
            highlightthickness=0,
            bg=self.default_bg,
        )
        self.dial.pack(pady=(10, 6), expand=True, fill="both")
        self.dial.bind("<Configure>", lambda e: self._draw_dial())

        self.entry_var = tk.StringVar(value="45:00")
        self.entry_frame = tk.Frame(self.root, bg=self.default_bg)
        self.entry_frame.pack()
        self.entry = tk.Entry(
            self.entry_frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 14),
            width=8,
            justify="center",
            relief="solid",
            bd=1,
        )
        self.entry.pack(pady=4)
        self.entry.bind("<Return>", self._on_entry_commit)
        self.entry.bind("<FocusOut>", self._on_entry_commit)

        self.slider = tk.Canvas(
            self.root,
            width=SLIDER_W,
            height=SLIDER_H,
            highlightthickness=0,
            bg=self.default_bg,
        )
        self.slider.pack(pady=8, fill="x", padx=20)
        self.slider.bind("<Button-1>", self._on_slider_press)
        self.slider.bind("<B1-Motion>", self._on_slider_drag)
        self.slider.bind("<MouseWheel>", self._on_slider_wheel)
        self.slider.bind("<Configure>", lambda e: self._draw_slider())

        self.btn_frame = tk.Frame(self.root, bg=self.default_bg)
        self.btn_frame.pack(pady=10)
        self.start_btn = tk.Button(
            self.btn_frame, text="Start", font=("Segoe UI", 11),
            width=10, height=1, command=self._on_start,
        )
        self.start_btn.pack(side="left", padx=10)
        self.stop_btn = tk.Button(
            self.btn_frame, text="Stop/Clear", font=("Segoe UI", 11),
            width=10, height=1, command=self._on_stop,
        )
        self.stop_btn.pack(side="left", padx=10)

    # ---------- drawing ----------
    def _draw_dial(self):
        c = self.dial
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        size = min(w, h) - 2 * DIAL_PAD
        if size < 60:
            return
        cx = w / 2
        cy = h / 2
        r = size / 2
        hub_r = max(4, int(r / 18))
        label_font = ("Segoe UI", max(7, int(r / 14)), "bold")
        brand_font = ("Segoe UI", max(6, int(r / 24)), "bold")
        hand_w = max(2, int(r / 30))
        tick_major_w = max(1, int(r / 80) + 1)
        tick_minor_w = 1
        ring = max(4, int(r / 30))

        c.create_oval(cx - r - ring, cy - r - ring,
                      cx + r + ring, cy + r + ring,
                      fill="#ececec", outline="#bdbdbd", width=2)
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill="white", outline="#888", width=1)

        rem = max(0.0, min(3600.0, self.remaining_seconds))
        frac = rem / 3600.0
        inset = max(3, int(r / 30))
        if rem > 0:
            c.create_arc(cx - r + inset, cy - r + inset,
                         cx + r - inset, cy + r - inset,
                         start=90, extent=360.0 * frac,
                         fill=RED, outline=RED)

        outer_off = max(2, int(r / 50))
        major_len = max(6, int(r / 12))
        minor_len = max(3, int(r / 24))
        label_off = max(14, int(r / 6))
        for m in range(60):
            ang = math.radians(90 + m * 6)
            is_major = (m % 5 == 0)
            outer = r - outer_off
            inner = r - (major_len if is_major else minor_len)
            x1 = cx + outer * math.cos(ang)
            y1 = cy - outer * math.sin(ang)
            x2 = cx + inner * math.cos(ang)
            y2 = cy - inner * math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill="#222",
                          width=tick_major_w if is_major else tick_minor_w)
            if is_major:
                lr = r - label_off
                lx = cx + lr * math.cos(ang)
                ly = cy - lr * math.sin(ang)
                c.create_text(lx, ly, text=str(m),
                              font=label_font, fill="#111")

        if rem > 0:
            ang = math.radians(90 + (rem / 60.0) * 6)
            hr = r - max(8, int(r / 10))
            hx = cx + hr * math.cos(ang)
            hy = cy - hr * math.sin(ang)
            c.create_line(cx, cy, hx, hy, fill="white",
                          width=hand_w, capstyle="round")
        c.create_oval(cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r,
                      fill="white", outline="#888")
        c.create_text(cx + r * 0.55, cy + r * 0.85, text="TIME TIMER",
                      font=brand_font, fill="#888")

    def _draw_slider(self):
        c = self.slider
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 30:
            return
        track_y = h / 2
        x0 = HANDLE_R + 2
        x1 = w - HANDLE_R - 2
        c.create_rectangle(x0, track_y - SLIDER_TRACK_H / 2,
                           x1, track_y + SLIDER_TRACK_H / 2,
                           fill="white", outline="#888")
        frac = self.total_seconds / 3600.0
        fx = x0 + (x1 - x0) * frac
        if frac > 0:
            c.create_rectangle(x0, track_y - SLIDER_TRACK_H / 2,
                               fx, track_y + SLIDER_TRACK_H / 2,
                               fill=RED, outline=RED)
        c.create_oval(fx - HANDLE_R, track_y - HANDLE_R,
                      fx + HANDLE_R, track_y + HANDLE_R,
                      fill="black", outline="black")

    def _redraw(self):
        self._draw_dial()
        self._draw_slider()

    # ---------- value sync ----------
    def _sync_all_from_total(self):
        self.remaining_seconds = float(self.total_seconds)
        self._update_entry_text()
        self._redraw()

    def _update_entry_text(self):
        secs = max(0, int(math.ceil(self.remaining_seconds - 1e-6)))
        if self.remaining_seconds <= 0:
            secs = 0
        m, s = divmod(secs, 60)
        new = f"{m:02d}:{s:02d}"
        if self.entry_var.get() != new:
            self.entry_var.set(new)

    def _set_total_seconds(self, secs):
        if self.running:
            return
        secs = max(0, min(3600, int(round(secs))))
        if secs == self.total_seconds and self.remaining_seconds == secs:
            return
        self.total_seconds = secs
        self._sync_all_from_total()

    # ---------- entry ----------
    def _on_entry_commit(self, event=None):
        if self.running:
            self._update_entry_text()
            return
        text = self.entry_var.get().strip()
        secs = self._parse_time(text)
        if secs is None:
            self._update_entry_text()
            return
        self._set_total_seconds(secs)

    @staticmethod
    def _parse_time(text):
        if not text:
            return None
        if ":" in text:
            try:
                parts = [int(p) for p in text.split(":")]
            except ValueError:
                return None
            if len(parts) == 2:
                m, s = parts
                return m * 60 + s
            if len(parts) == 3:
                h, m, s = parts
                return h * 3600 + m * 60 + s
            return None
        try:
            return int(text) * 60
        except ValueError:
            return None

    # ---------- slider ----------
    def _slider_x_to_seconds(self, x):
        w = self.slider.winfo_width()
        x0 = HANDLE_R + 2
        x1 = max(x0 + 1, w - HANDLE_R - 2)
        frac = (x - x0) / (x1 - x0)
        frac = max(0.0, min(1.0, frac))
        return int(round(frac * 60)) * 60

    def _on_slider_press(self, event):
        if self.running:
            return
        self._set_total_seconds(self._slider_x_to_seconds(event.x))

    def _on_slider_drag(self, event):
        if self.running:
            return
        self._set_total_seconds(self._slider_x_to_seconds(event.x))

    def _on_slider_wheel(self, event):
        if self.running:
            return
        direction = 1 if event.delta > 0 else -1
        self._set_total_seconds(self.total_seconds + direction * 60)

    # ---------- start/stop ----------
    def _on_start(self):
        if self.running:
            return
        if self.finished:
            self._stop_pulse()
            self.finished = False
            self.remaining_seconds = float(self.total_seconds)
        if self.remaining_seconds <= 0:
            return
        self.running = True
        self.root.attributes("-topmost", True)
        self.entry.configure(state="disabled")
        self.last_tick_ms = self._now_ms()
        self._tick()

    def _on_stop(self):
        if self.running:
            self.running = False
            if self.tick_job:
                self.root.after_cancel(self.tick_job)
                self.tick_job = None
            self.root.attributes("-topmost", False)
            self.entry.configure(state="normal")
            return
        if self.finished:
            self._stop_pulse()
            self.finished = False
        self.remaining_seconds = float(self.total_seconds)
        self._update_entry_text()
        self._redraw()

    @staticmethod
    def _now_ms():
        return int(time.monotonic() * 1000)

    def _tick(self):
        if not self.running:
            return
        now = self._now_ms()
        elapsed = (now - self.last_tick_ms) / 1000.0
        self.last_tick_ms = now
        self.remaining_seconds -= elapsed
        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0
            self.running = False
            self._update_entry_text()
            self._redraw()
            self._on_finish()
            return
        self._update_entry_text()
        self._redraw()
        self.tick_job = self.root.after(TICK_MS, self._tick)

    # ---------- finish / pulse ----------
    def _on_finish(self):
        self.finished = True
        self.entry.configure(state="normal")
        if winsound is not None:
            try:
                winsound.Beep(880, 500)
            except RuntimeError:
                pass
        self.pulse_phase = 0.0
        self._pulse()

    def _pulse(self):
        self.pulse_phase += PULSE_MS / 1000.0
        t = (1 - math.cos(self.pulse_phase * (2 * math.pi / PULSE_PERIOD_S))) / 2
        color = self._blend_hex(self.default_bg, LIGHT_RED, t)
        try:
            self.root.configure(bg=color)
            self.dial.configure(bg=color)
            self.slider.configure(bg=color)
            self.entry_frame.configure(bg=color)
            self.btn_frame.configure(bg=color)
        except tk.TclError:
            return
        self.pulse_job = self.root.after(PULSE_MS, self._pulse)

    def _stop_pulse(self):
        if self.pulse_job:
            self.root.after_cancel(self.pulse_job)
            self.pulse_job = None
        try:
            for w in (self.root, self.dial, self.slider,
                      self.entry_frame, self.btn_frame):
                w.configure(bg=self.default_bg)
        except tk.TclError:
            pass
        self.root.attributes("-topmost", False)

    def _blend_hex(self, c1, c2, t):
        r1, g1, b1 = self._to_rgb(c1)
        r2, g2, b2 = self._to_rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _to_rgb(self, color):
        if color.startswith("#"):
            h = color.lstrip("#")
            if len(h) == 3:
                h = "".join(ch * 2 for ch in h)
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r, g, b = self.root.winfo_rgb(color)
        return r // 257, g // 257, b // 257


def main():
    root = tk.Tk()
    TimeTimer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
