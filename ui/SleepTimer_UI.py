import tkinter as tk
from tkinter import messagebox, Canvas, Frame  # ✅ thêm import đúng
import threading
import time
from functions import load_image


class SleeptimerFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E1CFE3")
        self.config(highlightbackground="#89A34E", highlightthickness=2, bd=0)
        self.controller = controller
        self.sleep_timer_running = False
        self.sleep_time = 0
        self.image_cache = {}

        # ====== Canvas nền ======
        self.canvas = Canvas(self, bg="#FBE8DD", width=300, height=200, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.image_cache["bg_sleep"] = load_image("bg_sleep.png", size=(300, 200))
        self.canvas.create_image(150, 100, image=self.image_cache["bg_sleep"])  # ✅ trung tâm đúng vị trí
        self.canvas.create_text(150, 40, text="Sleep Timer", font=("Inter", 16, "bold"), fill="#FEFFFD")

        # ====== Ô nhập số phút ======
        self.minutes_var = tk.StringVar(value="10")
        self.entry_box = tk.Entry(
            self, textvariable=self.minutes_var,
            font=("Inter", 14), justify="center",
            bg="#FFFFFF", fg="#333", relief="flat", bd=0
        )
        self.canvas.create_window(150, 75, width=180, height=30, window=self.entry_box)

        # ===== Nút Start / Cancel =====
        self.image_cache["start_img"] = load_image("startsleep.png", size=(76, 28))
        self.image_cache["cancel_img"] = load_image("cancelsleep.png", size=(76, 28))

        self.start_btn = tk.Button(
            self, image=self.image_cache["start_img"],
            borderwidth=0, highlightthickness=0, relief="flat",
            bg="#FBE8DD", activebackground="#FBE8DD",
            command=self.start_sleep_timer
        )
        self.canvas.create_window(150, 120, window=self.start_btn)

        self.cancel_btn = tk.Button(
            self, image=self.image_cache["cancel_img"],
            borderwidth=0, highlightthickness=0, relief="flat",
            bg="#FBE8DD", activebackground="#FBE8DD",
            command=self.stop_sleep_timer
        )
        self.canvas.create_window(150, 155, window=self.cancel_btn)

    # ====== Hàm bắt đầu hẹn giờ ======
    def start_sleep_timer(self):
        try:
            minutes = int(self.minutes_var.get())
            self.sleep_time = minutes * 60
            self.sleep_timer_running = True
            messagebox.showinfo("Sleep Timer", f"Nhạc sẽ tạm dừng sau {minutes} phút.")
            threading.Thread(target=self.run_sleep_timer, daemon=True).start()
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số phút hợp lệ!")

    # ====== Luồng đếm ngược ======
    def run_sleep_timer(self):
        while self.sleep_time > 0 and self.sleep_timer_running:
            time.sleep(1)
            self.sleep_time -= 1

        if self.sleep_timer_running:
            self.sleep_timer_running = False
            if hasattr(self.controller, "songs") and not self.controller.songs.is_paused:
                self.controller.after(0, self.controller.songs.pause_and_resume_song)
            messagebox.showinfo("Sleep Timer", "⏹ Hết giờ — nhạc đã tạm dừng!")

    # ====== Dừng hẹn giờ ======
    def stop_sleep_timer(self):
        if self.sleep_timer_running:
            self.sleep_timer_running = False
            messagebox.showinfo("Sleep Timer", "Đã hủy hẹn giờ.")
