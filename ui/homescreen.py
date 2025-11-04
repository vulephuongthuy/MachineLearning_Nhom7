import datetime as dt
from datetime import datetime
import threading
import time
import tkinter
from io import BytesIO
from tkinter import Menu, PhotoImage, Entry, Scale, Canvas, Frame, \
    messagebox, Label
from tkinter.constants import HORIZONTAL
from urllib.request import urlopen
import pymongo
import sys

import requests
import vlc
from PIL.Image import Resampling

import session
from Recommendation import *
from functions import *
from ui.Login_UI import ProfileFrame
import zipfile
import tempfile
import os
import pandas as pd
import tkinter as tk

from ui.WrapUp_UI import WrapUpFrame


class MainScreen(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent

        self.canvas = tkinter.Canvas(self, bg="#F7F7DC", height=600,
                                     width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)
        self.songs = Song(self, controller)
        self.buttons = Button(self, self.canvas, self)
        self.player = vlc.MediaPlayer()

        self.songs.set_buttons(self.buttons)
        self.buttons.set_songs(self.songs)

        self.playlist_manager = SongListManager(self, controller, "playlist")
        self.songs.playlist_manager = self.playlist_manager


        self.buttons.songs = self.songs
        self.buttons.toolbar()
        self.buttons.init_progress_bar()
        self.buttons.search_music()
        self.buttons.volume()

        # Profile area
        self.profile_area = Frame(self.canvas, bg="lightgray")
        self.profile_frame = None
        self.wrapup_frame = None
        if hasattr(self.master, "protocol"):
            self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        # self.songs.load_user_songs()
        # self.purchased_tracks_cache = set()
        # self.load_purchased_cache()
        self.image_cache = {}
        self.max_image_cache = 500
        # Load all tracks for search
        self.all_tracks = []
        self.after(1000, self.load_all_tracks)  # Load sau 1 giây
        #Frame gợi ý tìm kiếm
        # Frame gợi ý tìm kiếm
        self.suggestion_color = "#FDEFF2"
        self.suggestion_border_color = "#E08DA8"
        self.suggestion_container = tk.Frame(
            self,
            bg=self.suggestion_color,
            highlightthickness=1,
            highlightbackground=self.suggestion_border_color,
            highlightcolor=self.suggestion_border_color
        )
        self.suggestion_canvas = tk.Canvas(
            self.suggestion_container, bg=self.suggestion_color,
            highlightthickness=0
        )

        self.suggestion_scrollbar = tk.Scrollbar(
            self.suggestion_container, orient="vertical",
            command=self.suggestion_canvas.yview
        )

        # SỬA: Đảm bảo tên là suggestion_frame (không có 's')
        self.suggestion_frame = tk.Frame(
            self.suggestion_canvas, bg=self.suggestion_color
        )
        self.suggestion_frame.bind(
            '<Configure>', lambda e: self.suggestion_canvas.configure(
                scrollregion=self.suggestion_canvas.bbox("all")
            )
        )
        self.suggestion_canvas.create_window((0, 0),
                                             window=self.suggestion_frame,
                                             anchor="nw")
        self.suggestion_canvas.configure(
            yscrollcommand=self.suggestion_scrollbar.set
        )

        self.suggestion_scrollbar.pack(side="right", fill="y")
        self.suggestion_canvas.pack(side="left", fill="both",
                                    expand=True)  # SỬA: pack canvas thay vì frame

        if not hasattr(self, 'image_cache'):
            self.image_cache = {}


    def on_close(self):
        """Dừng nhạc VLC và thoát ứng dụng"""
        try:
            if hasattr(self, "player") and isinstance(self.player, vlc.MediaPlayer):
                self.player.stop()
                self.player.release()
        except Exception as e:
            print(f"⚠️ Lỗi khi dừng nhạc: {e}")

        if hasattr(self, "master"):
            self.master.destroy()
        self.destroy()
        sys.exit()

    def show_default_content(self):
        """Hiển thị content mặc định"""
        if self.profile_frame:
            self.profile_frame.destroy()
            self.profile_frame = None
        if self.wrapup_frame:
            self.wrapup_frame.destroy()
            self.wrapup_frame = None
        self.profile_area.place_forget()

    def open_profile(self):
        """Mở ProfileFrame như frame con, chừa toolbar"""
        self.songs.fixed_canvas.place_forget()
        self.profile_area.place(x=50, y=0, width=950, height=600)
        if self.profile_frame is None:
            self.profile_frame = ProfileFrame(parent=self.profile_area, controller=self.controller)
            self.profile_frame.place(x=0, y=0, width=950, height=600)
        else:
            self.profile_frame.lift()

    def open_wrapup(self):
        """Mở WrapUpFrame như frame con, chừa toolbar"""
        self.songs.fixed_canvas.place_forget()
        self.profile_area.place(x=50, y=0, width=950, height=600)
        if self.wrapup_frame is None:
            self.wrapup_frame = WrapUpFrame(parent=self.profile_area, controller=self.controller)
            self.wrapup_frame.place(x=0, y=0, width=950, height=600)
        else:
            self.wrapup_frame.lift()

    def open_sleeptimer(self):
        """Hiển thị popup SleepTimer (hiển thị đè trên HomeScreen, không bị che)"""
        try:
            if not hasattr(self,
                           "sleeptimer_frame") or self.sleeptimer_frame is None:
                # 🎯 SỬA: Thêm "ui." trước import
                from ui.SleepTimer_UI import SleeptimerFrame

                # Dùng parent = self để đè lên toàn HomeScreen
                self.sleeptimer_frame = SleeptimerFrame(parent=self,
                                                        controller=self.controller)
                # đặt vị trí giữa góc phải, nổi rõ
                self.sleeptimer_frame.place(x=650, y=290, width=300, height=200)
                self.sleeptimer_frame.lift()  # 🔝 đưa lên trên cùng
                print("🩵 SleepTimerFrame created.")
            else:
                if self.sleeptimer_frame.winfo_ismapped():
                    self.sleeptimer_frame.place_forget()
                    print("🩶 SleepTimerFrame hidden.")
                else:
                    self.sleeptimer_frame.place(x=650, y=290, width=300,
                                                height=200)
                    self.sleeptimer_frame.lift()
                    print("🩵 SleepTimerFrame shown again.")
        except Exception as e:
            import traceback
            print("❌ Lỗi khi mở SleepTimer:", e)
            traceback.print_exc()

    def logout(self):
        """Xử lý logout từ HomeScreen"""
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            # Gọi logout của controller
            self.controller.logout()

    def show_search_suggestions(self):
        """Lọc và hiển thị gợi ý"""
        query = self.buttons.search_entry.get().lower().strip()

        # Xóa gợi ý cũ - SỬA: dùng suggestion_frame thay vì sugesstions_frame
        for widget in self.suggestion_frame.winfo_children():
            widget.destroy()

        # Nếu query rỗng, ẩn container và thoát
        if not query:
            self.suggestion_container.place_forget()
            return

        # Kiểm tra xem all_tracks đã được load chưa
        if not hasattr(self, 'all_tracks') or not self.all_tracks:
            print("⚠️ Chưa có dữ liệu bài hát để tìm kiếm")
            return

        query_words = query.split()
        results = []  # Sẽ lưu (score, track)

        for track in self.all_tracks:
            track_name = track.get("trackName", "").lower()
            artist_name = track.get("artistName", "").lower()

            # Chỉ kiểm tra nếu bài hát có tên
            if not track_name:
                continue

            search_string = track_name + " " + artist_name
            score = 0

            # Tính điểm dựa trên độ khớp
            if all(word in search_string for word in query_words):
                score += 10  # +10 điểm nếu khớp tất cả các từ

                # Thêm điểm cho khớp chính xác
                if track_name.startswith(query):
                    score += 50
                elif artist_name.startswith(query):
                    score += 30

                # Thêm điểm cho từng từ khớp
                for word in query_words:
                    if track_name.startswith(word):
                        score += 5
                    if artist_name.startswith(word):
                        score += 2

            if score > 0:
                results.append((score, track))

        # Sắp xếp theo điểm cao nhất
        results.sort(key=lambda item: item[0], reverse=True)
        top_results = [track for score, track in results[:20]]

        if not top_results:
            self.suggestion_container.place_forget()
            return

        # Tạo các item gợi ý
        for song in top_results:
            self.create_suggestion_item(song)

        # Cập nhật scroll region và hiển thị container
        self.suggestion_frame.update_idletasks()
        self.suggestion_canvas.configure(
            scrollregion=self.suggestion_canvas.bbox("all")
        )

        # Hiển thị container gợi ý
        self.suggestion_container.place(
            x=661,
            y=57,
            width=300,
            height=min(180, len(top_results) * 60)
            # Chiều cao tự động điều chỉnh
        )
        self.suggestion_container.lift()

    def hide_suggestions_on_focus_out(self):
        """Ẩn gợi ý khi focus ra ngoài (sau một khoảng delay nhỏ)"""

        def hide_after_delay():
            # Kiểm tra xem focus có ở trong search entry hoặc suggestion container không
            focused_widget = self.focus_get()
            if (focused_widget != self.buttons.search_entry and
                    focused_widget not in self.suggestion_container.winfo_children()):
                self.suggestion_container.place_forget()

        self.after(150,
                   hide_after_delay)  # Delay 150ms để người dùng có thể click vào gợi ý

    def create_suggestion_item(self, song):
        """Tạo 1 hàng gợi ý - Click anywhere works"""
        pink_bg = self.suggestion_color  # Màu nền ban đầu: #FDEFF2 (hồng nhạt)
        pink_hover = "#F8C8D8"  # 🎯 Màu hồng đậm hơn khi hover

        # Frame chính
        item_frame = tk.Frame(self.suggestion_frame, bg=pink_bg)
        item_frame.pack(fill="x", expand=True, padx=2, pady=1)

        # 🎯 Đặt tag để nhận diện
        item_frame.song_data = song

        # Frame ảnh
        img_frame = tk.Frame(item_frame, bg=pink_bg, width=40, height=40)
        img_frame.pack(side="left", padx=5, pady=5)
        img_frame.pack_propagate(False)

        img_label = tk.Label(img_frame, bg=pink_bg, text="🎵",
                             font=("Arial", 10))
        img_label.pack(expand=True)

        # Tải ảnh
        artwork_url = song.get("artworkUrl100", "")
        if artwork_url:
            threading.Thread(
                target=self.safe_load_image,
                args=(artwork_url, img_label, (40, 40)),
                daemon=True
            ).start()

        # Frame text
        text_frame = tk.Frame(item_frame, bg=pink_bg)
        text_frame.pack(side="left", fill="x", expand=True, anchor="w")

        track_name = self.truncate_text(song.get("trackName", "N/A"), 25)
        artist_name = self.truncate_text(song.get("artistName", "N/A"), 30)

        track_label = tk.Label(text_frame, text=track_name, bg=pink_bg,
                               fg="#D66D8B", anchor="w",
                               font=("Arial", 10, "bold"))
        track_label.pack(fill="x")

        artist_label = tk.Label(text_frame, text=artist_name, bg=pink_bg,
                                fg="#E08DA8", anchor="w", font=("Arial", 8))
        artist_label.pack(fill="x")

        # 🎯 Hàm xử lý sự kiện với màu hồng đậm
        def handle_click(event):
            # Tìm frame cha chứa song data
            widget = event.widget
            while widget and not hasattr(widget, 'song_data'):
                widget = widget.master
            if widget and hasattr(widget, 'song_data'):
                self.handle_suggestion_click(widget.song_data)

        def handle_enter(event):
            widget = event.widget
            while widget and not hasattr(widget, 'song_data'):
                widget = widget.master
            if widget:
                # 🎯 ĐỔI MÀU HỒNG ĐẬM
                widget.config(bg=pink_hover, cursor="hand2")
                # Cập nhật màu cho tất cả children
                for child in widget.winfo_children():
                    try:
                        child.config(bg=pink_hover)
                    except:
                        pass

        def handle_leave(event):
            widget = event.widget
            while widget and not hasattr(widget, 'song_data'):
                widget = widget.master
            if widget:
                # 🎯 TRỞ VỀ MÀU HỒNG NHẠT BAN ĐẦU
                widget.config(bg=pink_bg, cursor="")
                # Cập nhật màu cho tất cả children
                for child in widget.winfo_children():
                    try:
                        child.config(bg=pink_bg)
                    except:
                        pass

        # 🎯 Bind cho TẤT CẢ widgets trong item
        all_widgets = [item_frame, img_frame, img_label, text_frame,
                       track_label, artist_label]
        for widget in all_widgets:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)

        return item_frame

    def truncate_text(self, text, max_length):
        """Cắt ngắn text nếu quá dài"""
        return text[:max_length] + "..." if len(text) > max_length else text

    def safe_load_image(self, url, label, size):
        """Tải ảnh an toàn - đơn giản hóa"""
        try:
            if url in self.image_cache:
                photo = self.image_cache[url]
            else:
                response = requests.get(url, timeout=5)
                img = Image.open(BytesIO(response.content))
                img = img.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                # Giới hạn cache size
                if len(self.image_cache) >= self.max_image_cache:
                    # Remove oldest entry
                    oldest_key = next(iter(self.image_cache))
                    del self.image_cache[oldest_key]

                self.image_cache[url] = photo

            def update_ui():
                try:
                    if label.winfo_exists():
                        label.config(image=photo)
                        label.image = photo
                except tk.TclError:
                    pass

            self.after(0, update_ui)

        except Exception as e:
            # Fail silently - giữ icon mặc định
            pass

    # def handle_suggestion_click(self, song):
    #     """Xử lý click vào suggestion item - SIÊU NHANH với cache"""
    #     print(f"🎵 Click bài hát: {song.get('trackName')}")
    #
    #     track_id = song.get('trackId')
    #     track_name = song.get('trackName')
    #
    #     # 🎯 KIỂM TRA: Nếu cache chưa load, load ngay
    #     if not hasattr(self,
    #                    'purchased_tracks_cache') or self.purchased_tracks_cache is None:
    #         print("⚠️ Cache chưa load, loading now...")
    #         self.load_purchased_cache()
    #
    #     # 🎯 KIỂM TRA CACHE CỰC NHANH
    #     if track_id in self.purchased_tracks_cache:
    #         # ĐÃ MUA - PLAY NGAY
    #         print(f"✅ Đã mua, đang phát: {track_name}")
    #         self.songs.on_song_click(track_id)
    #         self.suggestion_container.place_forget()
    #         self.buttons.search_entry.delete(0, 'end')
    #     else:
    #         # CHƯA MUA - HIỆN MESSAGE BOX NGAY
    #         print(f"❌ Chưa mua, hiện message box: {track_name}")
    #         response = messagebox.askyesno(
    #             "Bài hát chưa mua",
    #             f"Bạn chưa mua bài hát '{track_name}'.\n\nBạn có muốn mua bài hát này?",
    #             icon='question'
    #         )
    #         if response:
    #             print(f"🎯 User chọn mua: {track_name}")
    #             self.open_payment_for_song(song)
    #         else:
    #             print(f"❌ User từ chối mua: {track_name}")
    def handle_suggestion_click(self, song):
        """Xử lý click vào suggestion item - ĐỌC TRỰC TIẾP TỪ DB"""
        print(f"🎵 Click bài hát: {song.get('trackName')}")

        track_id = str(song.get('trackId'))
        track_name = song.get('trackName')

        # 🎯 KIỂM TRA TRỰC TIẾP TỪ DB - LUÔN CÓ DATA MỚI NHẤT
        if self.is_track_purchased(track_id):
            # ĐÃ MUA - PLAY NGAY
            print(f"✅ Đã mua, đang phát: {track_name}")
            self.songs.on_song_click(track_id)
            self.suggestion_container.place_forget()
            self.buttons.search_entry.delete(0, 'end')
        else:
            # CHƯA MUA - HIỆN MESSAGE BOX
            print(f"❌ Chưa mua, hiện message box: {track_name}")
            response = messagebox.askyesno(
                "Bài hát chưa mua",
                f"Bạn chưa mua bài hát '{track_name}'.\n\nBạn có muốn mua bài hát này?",
                icon='question'
            )
            if response:
                print(f"🎯 User chọn mua: {track_name}")
                self.open_payment_for_song(song)
            else:
                print(f"❌ User từ chối mua: {track_name}")

    def is_track_purchased(self, track_id):
        """Kiểm tra trực tiếp từ DB xem track đã được mua chưa - XỬ LÝ CẢ STRING VÀ NUMBER"""
        try:
            user_id = session.current_user.get("userId")
            if not user_id:
                print("⚠️ Chưa có user ID")
                return False

            db = self.controller.get_db()

            # 🎯 CHUẨN HÓA ID
            user_id_str = str(user_id)
            track_id_str = str(track_id)

            # 🎯 DEBUG
            print(f"🔍 IS_TRACK_PURCHASED DEBUG:")
            print(f"   User ID: {user_id_str}")
            print(f"   Track ID: {track_id_str}")

            # 🎯 QUERY LINH HOẠT - THỬ CẢ STRING VÀ NUMBER
            queries = [
                # Thử với string trước (cách MainScreen đang dùng)
                {"userId": user_id_str, "trackId": track_id_str},
                # Thử với number (cách Payment có thể đang lưu)
                {"userId": user_id_str, "trackId": int(track_id) if track_id.isdigit() else track_id},
                # Thử với user_id number (phòng trường hợp)
                {"userId": int(user_id) if user_id.isdigit() else user_id, "trackId": track_id_str},
            ]

            for i, query in enumerate(queries):
                purchase = db.db["purchase"].find_one(query)
                if purchase:
                    print(f"✅ FOUND PURCHASE với query {i + 1}: {query}")
                    print(f"   Track: {purchase.get('trackName')}")
                    return True

            print(f"❌ PURCHASE NOT FOUND với mọi query")
            return False

        except Exception as e:
            print(f"❌ Lỗi kiểm tra purchase: {e}")
            import traceback
            traceback.print_exc()
            return False

    # def open_payment_for_song(self, song):
    #     """Mở payment frame cho bài hát"""
    #     self.suggestion_container.place_forget()
    #     self.buttons.search_entry.delete(0, 'end')
    #
    #     try:
    #         if hasattr(self.controller, 'show_frame'):
    #             self.controller.show_frame("Payment")
    #
    #             if hasattr(self.controller, 'frames') and "Payment" in self.controller.frames:
    #                 payment_frame = self.controller.frames["Payment"]
    #                 if hasattr(payment_frame, 'set_track'):
    #                     payment_frame.set_track(song)
    #                     print(f"✅ Đã chuyển bài hát đến Payment: {song.get('trackName')}")
    #
    #         elif hasattr(self, 'master') and hasattr(self.master, 'show_frame'):
    #             self.master.show_frame("Payment")
    #
    #         else:
    #             print("❌ Không thể truy cập Payment frame")
    #
    #     except Exception as e:
    #         print(f"❌ Lỗi mở Payment: {e}")
    #         messagebox.showerror("Lỗi", "Không thể mở trang thanh toán")
    def open_payment_for_song(self, song):
        """Mở payment frame cho bài hát"""
        self.suggestion_container.place_forget()
        self.buttons.search_entry.delete(0, 'end')

        try:
            # Cách 1: Dùng controller chính
            if hasattr(self.controller, 'show_frame'):
                self.controller.show_frame("Payment")

                # Truyền dữ liệu bài hát sang Payment frame
                if hasattr(self.controller, 'frames') and "Payment" in self.controller.frames:
                    payment_frame = self.controller.frames["Payment"]
                    if hasattr(payment_frame, 'set_track'):
                        payment_frame.set_track(song)
                        print(f"✅ Đã chuyển bài hát đến Payment: {song.get('trackName')}")

            # Cách 2: Dùng master nếu controller không có show_frame
            elif hasattr(self, 'master') and hasattr(self.master, 'show_frame'):
                self.master.show_frame("Payment")

            # Cách 3: Fallback - thử truy cập trực tiếp
            else:
                print("⚠️ Không tìm thấy controller, thử cách khác...")
                # Tìm Payment frame trong parent
                for widget in self.master.winfo_children():
                    if hasattr(widget, '__class__') and widget.__class__.__name__ == "PaymentFrame":
                        widget.lift()
                        if hasattr(widget, 'set_track'):
                            widget.set_track(song)
                        print(f"✅ Đã tìm thấy và chuyển đến Payment frame")
                        break
                else:
                    print("❌ Không thể truy cập Payment frame")

        except Exception as e:
            print(f"❌ Lỗi mở Payment: {e}")
            messagebox.showerror("Lỗi", "Không thể mở trang thanh toán")


    def load_image_async(self, url, label, size):
        """Tải ảnh từ URL trong Thread - Fix memory issues"""
        try:
            import requests
            from io import BytesIO

            # Sử dụng requests thay vì urlopen để kiểm soát timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            img = img.resize(size, Image.Resampling.LANCZOS)

            # 🎯 QUAN TRỌNG: Giới hạn số lượng image cache
            if len(self.image_cache) > 1000:
                # Xóa một nửa cache cũ để tránh memory leak
                keys_to_remove = list(self.image_cache.keys())[:500]
                for key in keys_to_remove:
                    del self.image_cache[key]

            photo = ImageTk.PhotoImage(img)
            self.image_cache[url] = photo

            # Cập nhật UI trong main thread - THÊM KIỂM TRA BỔ SUNG
            def update_ui():
                try:
                    if (label.winfo_exists() and
                            hasattr(self, 'suggestion_container') and
                            self.suggestion_container.winfo_exists()):
                        label.config(image=photo)
                        label.image = photo
                except (tk.TclError, AttributeError) as e:
                    print(f"⚠️ Widget không tồn tại khi update ảnh: {e}")

            self.after(0, update_ui)

        except Exception as e:
            print(f"❌ Lỗi tải ảnh {url}: {e}")

            def set_default():
                try:
                    if label.winfo_exists():
                        label.config(text="🎵", font=("Arial", 12))
                except tk.TclError:
                    pass

            self.after(0, set_default)

    def load_all_tracks(self):
        """Load tất cả bài hát từ database để tìm kiếm"""
        try:
            db = self.controller.get_db()
            # Lấy tất cả tracks từ database, giới hạn 1000 bài để tránh quá tải
            self.all_tracks = list(db.db["tracks"].find())
            print(f"✅ Đã load {len(self.all_tracks)} bài hát cho tìm kiếm")
        except Exception as e:
            print(f"❌ Lỗi khi load tracks: {e}")
            self.all_tracks = []

    # def load_purchased_cache(self):
    #     """Load tất cả purchased tracks vào cache"""
    #     try:
    #         user_id = session.current_user.get("userId")
    #         if not user_id:
    #             print("⚠️ Chưa có user ID để load cache")
    #             return
    #
    #         db = self.controller.get_db()
    #         purchases = list(db.db["purchase"].find(
    #             {"userId": str(user_id)},
    #             {"trackId": 1}
    #         ).limit(1000))  # Giới hạn 1000 bài
    #
    #         self.purchased_tracks_cache = {p["trackId"] for p in purchases}
    #         print(
    #             f"✅ Đã cache {len(self.purchased_tracks_cache)} bài hát đã mua")
    #
    #         # Debug: in 5 bài đầu để kiểm tra
    #         if self.purchased_tracks_cache:
    #             sample_tracks = list(self.purchased_tracks_cache)[:5]
    #             print(f"📝 Sample cached tracks: {sample_tracks}")
    #
    #     except Exception as e:
    #         print(f"❌ Lỗi load cache: {e}")
    #         self.purchased_tracks_cache = set()

class Button():
    def __init__(self, parent, canvas, song):
        super().__init__()
        self.parent = parent
        self.canvas = canvas
        self.main_screen = song
        self.songs = song
        self.repeat_mode = 0
        self.volume_slider = None  # Biến để kiểm soát thanh volume
        self.current_volume = 100  # Mặc định 100 khi mở app
        self.is_playing = False  # Biến kiểm tra trạng thái phát nhạc
        self.is_paused = False
        self.is_rotating = False
        self.play_button = None
        self.search_entry = None
        self.volume_icon = None
        self.profile_window = None
        self.image_ids = {}
        self.image_cache = {}
        self.buttons = {}  # Dictionary để lưu trữ các button nếu cần dùng sau này
        self.love_state = "love(1)"
        self.load_icons()
        self.parent.buttons = self
        self.progress_bg = None
        self.progress_fill = None
        self.progress_knob = None
        self.current_time_text = None  # Định nghĩa trước
        self.total_time_text = None
        self.title_text = None
        self.current_title = "Home"
        self.create_title()
        self.create_home_recommendations()
        self.menu = Menu(self.parent, tearoff=0)

    def set_songs(self, songs):
        self.songs = songs

    def toolbar(self):
        self.canvas.create_rectangle(
            0.0,
            0.0,
            50.0,
            600.0,
            fill="#C6D5A3",
            outline=""
        )
        image_files = {
            "logo 1": ("logo 1.png", 25, 20),
            "logo 2": ("logo 2.png", 25, 75),
            "home": ("home 1.png", 25, 152),
            "library": ("library 1.png", 25, 232),
            "history": ("history 1.png", 25, 300),
            "report": ("report 1.png", 25, 368),
            "logout": ("logout 1.png", 25, 549),
        }

        for key, (file_name, x, y) in image_files.items():
            if key == "logo 1":
                self.image_cache[key] = load_image(file_name, size=(90, 90))
            else:
                self.image_cache[key] = PhotoImage(
                    file=relative_to_assets(file_name))

            img_id = self.canvas.create_image(x, y, image=self.image_cache[key])
            self.image_ids[key] = img_id

        self.canvas.tag_bind(self.image_ids["logo 2"], "<Button-1>",
                             lambda e: self.toggle_view("profile"))
        self.canvas.tag_bind(self.image_ids["home"], "<Button-1>", lambda e: self.toggle_view("home"))
        self.canvas.tag_bind(self.image_ids["history"], "<Button-1>", lambda e: self.toggle_view("history"))
        self.canvas.tag_bind(self.image_ids["library"], "<Button-1>", lambda e: self.toggle_view("library"))
        self.canvas.tag_bind(self.image_ids["report"], "<Button-1>", lambda e: self.toggle_view("report"))
        self.canvas.tag_bind(self.image_ids["logout"], "<Button-1>", lambda e: self.parent.logout())
    def create_title(self):
        """Tạo hoặc cập nhật tiêu đề"""
        if self.title_text is None:
            self.title_text = self.canvas.create_text(103.0, 27.0, anchor="nw", text=self.current_title,
                                                      fill="#89A34E", font=("Jua Regular", 40 * -1))
            # Bind sự kiện click để edit
            self.canvas.tag_bind(self.title_text, "<Button-1>", self.edit_title)
        else:
            self.canvas.itemconfig(self.title_text, text=self.current_title)

    def edit_title(self, event=None):
        # Chỉ cho edit nếu đang ở playlist
        fixed_titles = ["Home", "History", "Library", "Owned Songs", "Liked Songs"]
        if self.current_title in fixed_titles:
            return

        # Tạo Entry ngay trên tiêu đề
        self.title_entry = Entry(self.canvas, font=("Jua Regular", 30), fg="#89A34E", bg="#F7F7DC", relief="flat", bd=0, highlightthickness=0)
        self.title_entry.insert(0, self.current_title)
        self.title_entry.place(x=100, y=20, width=400, height=50)
        self.title_entry.focus()
        self.title_entry.select_range(0, tkinter.END)

        # Bind sự kiện
        self.title_entry.bind("<Return>", self.save_title)
        self.title_entry.bind("<FocusOut>", self.save_title)

    def save_title(self, event):
        """Lưu tiêu đề mới"""
        new_name = self.title_entry.get().strip()

        if new_name and new_name != self.current_title:
            # Cập nhật database
            db = self.parent.controller.get_db()
            username = session.current_user.get("username")
            old_name = self.current_title

            db.db["user"].update_one(
                {"username": username, "playlists.name": old_name},
                {"$set": {"playlists.$.name": new_name}}
            )
            # Cập nhật tiêu đề
            self.current_title = new_name
            self.canvas.itemconfig(self.title_text, text=new_name)
        # Xóa entry
        self.title_entry.destroy()

    def create_home_recommendations(self):
        """Tạo 3 dòng chữ gợi ý trên canvas cuộn của màn hình Home"""
        song_canvas = self.parent.songs.canvas
        self.recommendation_texts = {
            "today": song_canvas.create_text(
                0, 0, anchor="nw",
                text="Recommended for today",
                fill="#89A34E", font=("Coiny Regular", 24)
            ),
            "top chart": song_canvas.create_text(
                0, 251, anchor="nw",
                text="Monthly chart ",
                fill="#89A34E", font=("Coiny Regular", 24)
            ),
            "artist": song_canvas.create_text(
                0, 502, anchor="nw",
                text="Recommended artist",
                fill="#89A34E", font=("Coiny Regular", 24)
            ),
            "genres": song_canvas.create_text(
                0, 753, anchor="nw",
                text="Recommended genres",
                fill="#89A34E", font=("Coiny Regular", 24)
            ),
        }

    def toggle_view(self, view_type):
        """Chuyển đổi giữa danh sách bài hát, lịch sử nghe và danh sách yêu thích"""
        # Ẩn tất cả danh sách trước khi hiển thị danh sách mới
        self.hide_songs_list()
        self.hide_history()
        self.parent.songs.hide_all_views()
        self.parent.show_default_content()

        if hasattr(self.parent, 'playlist_manager') and self.parent.playlist_manager:
            self.parent.playlist_manager.hide()
            self.parent.playlist_manager = None
        if view_type == "profile":
            self.parent.open_profile()
        elif view_type == "home":
            self.show_songs_list()
            self.current_title = "Home"
        elif view_type == "history":
            self.show_history()
            self.current_title = "History"
        elif view_type == "library":
            self.show_library()
            self.current_title = "Library"
        elif view_type == "report":
            self.parent.open_wrapup()
        self.create_title()

    def show_songs_list(self):
        """Hiển thị danh sách bài hát"""
        self.parent.songs.canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def hide_songs_list(self):
        """Ẩn danh sách bài hát"""
        self.parent.songs.canvas.place_forget()

    def show_library(self):
        """Hiển thị thư viện"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_playlists_from_db()
        self.parent.songs.update_library_display()
        self.parent.songs.library_canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def show_history(self):
        """Hiển thị danh sách lịch sử"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_history_from_db()
        self.parent.songs.update_history_display()
        self.parent.songs.history_canvas.place(x=103, y=90)
        self.parent.songs.history_canvas.config(scrollregion=self.parent.songs.history_canvas.bbox("all"))
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def hide_history(self):
        """Ẩn danh sách lịch sử"""
        self.parent.songs.history_canvas.place_forget()

    def show_favorites(self):
        """Hiển thị danh sách yêu thích"""
        self.parent.songs.favorites_canvas.place(x=103, y=90)

    def hide_favorites(self):
        """Ẩn danh sách yêu thích"""
        self.parent.songs.favorites_canvas.place_forget()

    def init_progress_bar(self):
        """Tạo thanh tiến trình"""
        c = self.parent.songs.fixed_canvas
        elements = {
            "progress_bg": ("rectangle", (308, 55, 750, 62), "#D9D9D9"),
            "progress_fill": ("rectangle", (308, 55, 318, 62), "#F2829E"),
            "progress_knob": ("oval", (308, 53, 320, 65), "#F2829E"),
            "current_time_text": ("text", (270, 48), "0:00"),
            "total_time_text": ("text", (764, 48), "0:00"),
        }
        for name, (shape, coords, *extra) in elements.items():
            text_color = "#000000"
            if shape == "rectangle":
                setattr(self, name, c.create_rectangle(*coords, fill=extra[0], outline=""))
            elif shape == "oval":
                setattr(self, name, c.create_oval(*coords, fill=extra[0], outline=""))
            elif shape == "text":
                setattr(self, name, c.create_text(*coords, anchor="nw",
                                                            text=extra[0], fill=text_color,
                                                            font=("Newsreader Regular", -14)))

        # Gán sự kiện chuột để kéo thanh tiến trình
        c.tag_bind(self.progress_knob, "<B1-Motion>", self.seek_song)
        c.tag_bind(self.progress_fill, "<Button-1>", self.seek_song)

        self.update_progress_bar()

    def update_progress_bar(self):
        """Cập nhật thanh tiến trình"""
        c = self.parent.songs.fixed_canvas
        if not self.songs.is_playing or self.songs.is_paused:
            return

        current_time = self.songs.get_current_time()
        total_time = self.songs.get_total_time()

        # Giới hạn current_time không vượt quá 30
        if current_time >= total_time:
            current_time = total_time

        # Cập nhật text
        c.itemconfig(self.current_time_text,
                     text=self.format_time(current_time))
        c.itemconfig(self.total_time_text,
                     text=self.format_time(total_time))

        # Cập nhật thanh tiến trình
        start_x, end_x = 308, 750
        progress_x = start_x + (end_x - start_x) * (current_time / total_time)
        c.coords(self.progress_fill, start_x, 55, progress_x, 62)
        c.coords(self.progress_knob, progress_x - 6, 53, progress_x + 6, 65)

        if self.songs.is_playing and not self.songs.is_paused:
            self.canvas.after(500, self.update_progress_bar)

    def format_time(self, seconds):
        """Chuyển đổi giây sang định dạng mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def seek_song(self, event):
        """Xử lý kéo thanh tiến trình để tua nhạc"""
        start_x, end_x = 308, 750
        total_time = self.songs.get_total_time()

        #Tính thời gian mới
        click_x = min(max(event.x, start_x), end_x)
        new_time = ((click_x - start_x) / (end_x - start_x)) * total_time
        #Gọi class `Song` để tua bài
        self.songs.is_seeking = True
        self.songs.seek_song(new_time)

        self.update_progress_bar()

    def load_icons(self):
        """Tải ảnh cho các icon"""
        icons = {
            "play": "play.png",
            "pause": "pause.png",
            "previous": "previous.png",
            "next": "next.png",
            "repeat": "repeat.png",
            "repeat one time": "repeat one time.png",
            "repeat always": "repeat always.png",
            "love(1)": "heart.png",
            "love(2)": "heart (1).png",
            "sleeptimer": "timer.png",
            "dots": "dots.png",
        }
        for key, file_name in icons.items():
            self.image_cache[key] = PhotoImage(
                file=relative_to_assets(file_name))
        c = self.parent.songs.fixed_canvas
        button_positions = {
            "play": (537, 20),
            "previous": (477, 20),
            "next": (602, 20),
            "repeat": (662, 20),
            "love": (417, 20),
            "sleeptimer": (352, 20),
            "dots": (722, 20)
        }
        button_callbacks = {
            "play": lambda e: self.parent.songs.play_pause(),
            "previous": lambda e: self.parent.songs.previous_song(e),
            "next": self.parent.songs.next_song,
            "repeat": self.toggle_repeat,
            "love": self.toggle_love,
            "sleeptimer": lambda e : self.parent.open_sleeptimer()
        }

        self.parent.songs.update_love_button_state()
        for key, (x, y) in button_positions.items():
            image = self.image_cache[self.love_state] if key == "love" else self.image_cache[key]
            self.buttons[key] = c.create_image(x, y, image=image)
            c.tag_bind(self.buttons[key], "<Button-1>",button_callbacks.get(key, lambda e: None))

    def toggle_love(self, event=None):
        """Chuyển đổi trạng thái của nút love"""
        c = self.parent.songs.fixed_canvas
        if self.love_state == "love(1)":
            self.love_state = "love(2)"
            self.parent.songs.add_to_favorite()
        else:
            self.love_state = "love(1)"
            self.parent.songs.remove_from_favorite()
        #Cập nhật hình ảnh của nút love
        c.itemconfig(self.buttons["love"],image=self.image_cache[self.love_state])

    def toggle_repeat(self, event=None):
        c = self.parent.songs.fixed_canvas
        self.repeat_mode = (self.repeat_mode + 1) % 3
        self.parent.songs.repeat_mode = self.repeat_mode  #Cập nhật repeat_mode trong Song

        if self.repeat_mode == 0:
            c.itemconfig(self.buttons["repeat"],image=self.image_cache["repeat"])
        elif self.repeat_mode == 1:
            c.itemconfig(self.buttons["repeat"],image=self.image_cache["repeat one time"])
        else:
            c.itemconfig(self.buttons["repeat"],image=self.image_cache["repeat always"])

    # Tạo khung tìm kiếm bo góc bằng ảnh
    @staticmethod
    def create_rounded_rectangle(width, height, radius, color):
        # Tạo ảnh hình chữ nhật bo góc
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))  # Nền trong suốt
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((0, 0, width, height), radius=radius,
                               fill=color)
        return ImageTk.PhotoImage(img)

    def search_music(self):
        self.image_cache["search_box"] = self.create_rounded_rectangle(235, 30,
                                                                       15,
                                                                       "#F586A3")
        self.canvas.create_image(851, 42, image=self.image_cache["search_box"])
        self.image_cache["search"] = PhotoImage(
            file=relative_to_assets("search.png"))
        self.canvas.create_image(755, 42, image=self.image_cache["search"])

        self.search_entry = Entry(self.canvas, font=("Newsreader Regular", 14),
                                  fg="#000000", bg="#F586A3", bd=0)
        self.search_entry.place(x=773, y=30, width=188, height=27)

        # Bind events
        self.search_entry.bind("<KeyRelease>",
                               lambda
                                   event: self.main_screen.show_search_suggestions())
        self.search_entry.bind("<FocusOut>",
                               lambda
                                   e: self.main_screen.hide_suggestions_on_focus_out())
        self.search_entry.bind("<FocusIn>",
                               lambda
                                   e: self.main_screen.show_search_suggestions())

    def volume(self):
        c = self.parent.songs.fixed_canvas
        self.image_cache["volume"] = PhotoImage(file=relative_to_assets(
            "medium-volume.png"))
        self.volume_icon = c.create_image(820, 55,
                                                    image=self.image_cache["volume"])
        # Gán sự kiện click vào icon volume
        c.tag_bind(self.volume_icon, "<Button-1>", self.toggle_volume_slider)

    def toggle_volume_slider(self, event=None):
        """Hiện hoặc ẩn thanh volume khi nhấn vào icon"""
        if self.volume_slider and self.volume_slider.winfo_ismapped():
            self.volume_slider.place_forget()  # Ẩn nếu đang hiện
        else:
            self.show_volume_slider()

    def show_volume_slider(self):
        """Hiển thị thanh điều chỉnh âm lượng với thiết kế bo tròn"""
        if not self.volume_slider:
            self.volume_slider = Scale(
                self.parent.songs.fixed_canvas.master, from_=0, to=100, orient=HORIZONTAL,
                length=100, sliderlength=20, width=10, troughcolor="#D9D9D9",
                bg="#F7F7DC", fg="#000000",
                highlightthickness=0, borderwidth=0, command=self.set_volume
            )
        self.volume_slider.set(self.current_volume)
        self.volume_slider.place(x=890, y=555)  # Đặt vị trí gần icon volume

    def set_volume(self, value):
        """Cập nhật âm lượng của trình phát nhạc"""
        self.current_volume = int(value)  # Lưu lại mức âm lượng hiện tại
        if hasattr(self.parent, "player") and self.parent.player is not None:
            self.parent.player.audio_set_volume(self.current_volume)

class Song():
    def __init__(self, parent, controller, button=None):
        super().__init__()
        self.controller = controller
        self.parent = parent
        self.button = button
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.songs_list = []  # Danh sách đường dẫn bài hát
        self.song_data = {}
        self.history_list = []
        self.playlist_count = 0
        self.playlists = []
        self.image_cache = {}

        self.current_index = -1
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.repeat_mode = 0  # 0: No Repeat, 1: Repeat One, 2: Repeat Always
        self.repeat_once_flag = False

        self.is_seeking = False
        self.last_seek_time = 0

        self.playlist_manager = None

        self.current_song_image = None
        self.clip_canvas = None
        self.buttons = None

        self.current_time = 0
        self.total_time = 0
        self.paused_time = 0
        self.start_time = 0

        # === PHẦN RECOMMENDATION FOR TODAY===
        self.ai_components = None
        self.recommendation_items = []

        self.owned_songs_manager = SongListManager(self.parent, controller, "owned_songs")
        self.liked_songs_manager = SongListManager(self.parent, controller, "liked_songs")
        self.playlist_manager = SongListManager(self.parent, controller, "playlist")

        # Canvas lịch sử
        self.history_canvas = Canvas(self.parent, width=1000, height=408,
                                     bg="#F7F7DC", bd=0, highlightthickness=0)
        self.history_canvas.place(x=103, y=90)
        self.history_canvas.place_forget()  # Ẩn ngay khi khởi tạo
        self.history_frame = Frame(self.history_canvas, bg="#F7F7DC")
        self.history_canvas_window = self.history_canvas.create_window((0, 0), window=self.history_frame,
                                                                       anchor="nw", width=844)
        self.history_canvas.bind("<Enter>",
                                 lambda e: self.history_canvas.bind_all("<MouseWheel>", self.scroll_with_mouse))
        self.history_canvas.bind("<Leave>",
                                 lambda e: self.history_canvas.unbind_all("<MouseWheel>"))

        # Tạo một canvas riêng để chứa danh sách bài hát
        self.canvas = Canvas(self.parent, width=1000, height=408, bg="#F7F7DC",
                             bd=0, highlightthickness=0)
        self.canvas.place(x=103, y=90)  # Đặt vị trí cho danh sách bài hát
        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.scroll_with_mouse)

        # Tạo canvas riêng cho recommendations ngang
        self.recommendation_canvas = Canvas(self.canvas, width=900, height=210,
                                            bg="#F7F7DC", highlightthickness=0)
        self.recommendation_canvas_id = self.canvas.create_window(0, 40, window=self.recommendation_canvas,
                                                                  anchor="nw", width=900, height=210)
        self.recommendation_canvas.configure(xscrollcommand=lambda *args: None)
        # Frame chứa các recommendation item (sắp xếp ngang)
        self.recommendation_frame = Frame(self.recommendation_canvas,bg="#F7F7DC")
        self.recommendation_canvas.create_window((0, 0),window=self.recommendation_frame,
                                                 anchor="nw")
        self.recommendation_canvas.drag_data = {"x": 0}

        # Binding events - THÊM TRÊN CẢ FRAME
        self.recommendation_canvas.bind("<ButtonPress-1>", self.start_drag)
        self.recommendation_canvas.bind("<B1-Motion>", self.do_drag)
        self.recommendation_frame.bind("<ButtonPress-1>", self.start_drag)
        self.recommendation_frame.bind("<B1-Motion>", self.do_drag)

        # Canvas thư viện
        self.library_canvas = Canvas(self.parent, width=1000, height=408,
                                     bg="#F7F7DC", bd=0, highlightthickness=0)
        self.library_canvas.place(x=103, y=90)
        self.library_canvas.place_forget()
        self.library_frame = Frame(self.library_canvas, bg="#F7F7DC")
        self.library_canvas_window = self.library_canvas.create_window((0, 0),
                                                                       window=self.library_frame,
                                                                       anchor="nw",
                                                                       width=844)

        self.library_canvas.bind("<Enter>",
                                 lambda e: self.library_canvas.bind_all("<MouseWheel>", self.scroll_with_mouse))
        self.library_canvas.bind("<Leave>",
                                 lambda e: self.library_canvas.unbind_all("<MouseWheel>"))

        self.current_index = -1  # Chỉ mục của bài hát hiện tại
        self.songs_list = []  # Danh sách bài hát
        self.fixed_canvas = Canvas(self.parent, bg="#F7F7DC", height=78,
                                   width=950, bd=0, highlightthickness=0)
        self.fixed_canvas.place(x=50, y=522)  # Đặt ở dưới cùng

        self.parent.bind("<Configure>", self.check_song_end)

        self.init_ai_recommender()
        # === END AI RECOMMENDATION ===

        # Tạo AI recommendations sau khi khởi tạo xong
        self.parent.after(2000, self.load_ai_recommendations)

    def set_buttons(self, buttons):
        self.buttons = buttons

    def hide_all_views(self):
        """Ẩn tất cả các view"""
        self.canvas.place_forget()
        self.library_canvas.place_forget()

        # Ẩn các manager
        self.owned_songs_manager.hide()
        self.liked_songs_manager.hide()
        self.playlist_manager.hide()

    def init_ai_recommender(self):
        """Khởi tạo AI Recommender"""
        try:
            if not session.current_user:
                print("❌ No user session")
                self.ai_components = None
                return

            user_id = session.current_user.get("userId")
            print(f"🎯 Loading AI for user: {user_id}")

            # 1. Lấy moodID mới nhất từ MongoDB
            try:
                db = self.controller.get_db()
                latest_mood = db.db["mood_tracking_history"].find_one(
                    {"userId": user_id}, sort=[("timestamp", -1)]
                )
                current_mood_id = latest_mood.get("moodID",
                                                  1) if latest_mood else 1
                print(f"🎭 Latest moodID for user {user_id}: {current_mood_id}")
            except Exception as e:
                print(f"❌ Error getting mood from MongoDB: {e}")
                current_mood_id = 1

            # 2. Load model từ zip file
            zip_path = "models/recommend_for_today.zip"
            print(f"🔍 Looking for model at: {zip_path}")

            if not os.path.exists(zip_path):
                print(f"❌ Model zip file not found: {zip_path}")
                self.ai_components = None
                return

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                temp_dir = tempfile.mkdtemp()
                print(f"📁 Extracting to temp directory: {temp_dir}")
                zip_ref.extractall(temp_dir)

                all_files = os.listdir(temp_dir)
                print(f"📄 Files in temp directory: {all_files}")

                # Tìm file model (.joblib)
                model_files = [f for f in all_files if f.endswith('.joblib')]
                if model_files:
                    model_path = os.path.join(temp_dir, model_files[0])
                    print(f"✅ Loading model from: {model_path}")

                    # Load components bằng joblib
                    try:
                        import joblib
                        components = joblib.load(model_path)
                        print("✅ Model loaded with joblib")
                    except Exception as e:
                        print(f"❌ Joblib load failed: {e}")
                        self.ai_components = None
                        return

                    # Lấy DB connection
                    db_connection = self.controller.get_db()

                    # Tạo recommendation functions
                    def new_is_new_user(user_id):
                        """KIỂM TRA user có phải là user mới không"""
                        user_id_str = str(user_id)
                        favorites_df = components['favorites_with_artist']

                        # Kiểm tra user có trong favorites không
                        favorites_df['userId'] = favorites_df['userId'].astype(str)
                        user_exists = user_id_str in favorites_df[
                            'userId'].astype(str).values

                        print(
                            f"🎯 FINAL RESULT: User {user_id_str} is {'EXISTING' if user_exists else 'NEW'} user")
                        return not user_exists

                    def new_recommend_for_user(user_id, top_n=10):
                        """Recommendations cho user CŨ"""
                        print(
                            f"🎯 Running recommend_for_user for EXISTING user: {user_id}")
                        try:
                            return recommend_for_user(user_id, components,
                                                      db_connection, top_n)
                        except Exception as e:
                            print(f"❌ Error in recommend_for_user: {e}")
                            import traceback
                            traceback.print_exc()
                            return pd.DataFrame()

                    def new_recommend_for_new_user(user_id, top_n=10):
                        """Recommendations cho user MỚI"""
                        print(
                            f"🎯 Running recommend_for_new_user for NEW user: {user_id}")
                        try:
                            return recommend_for_new_user(user_id, components,
                                                          db_connection, top_n)
                        except Exception as e:
                            print(f"❌ Error in recommend_for_new_user: {e}")
                            import traceback
                            traceback.print_exc()
                            return pd.DataFrame()

                    # Tạo recommendation functions mới
                    new_functions = {
                        'is_new_user': new_is_new_user,
                        'recommend_for_user': new_recommend_for_user,
                        'recommend_for_new_user': new_recommend_for_new_user
                    }

                    self.ai_components = {
                        'model': components['model'],
                        'feature_cols': components['feature_cols'],
                        'favorites_with_artist': components[
                            'favorites_with_artist'],
                        'current_mood': pd.DataFrame(
                            [{'userId': user_id, 'moodID': current_mood_id}]),
                        'tracks': components['tracks'],
                        'ratings': components['ratings'],
                        'song_mood': components['song_mood'],
                        'purchased': components['purchased'],
                        'df': components['df'],
                        'recommendation_functions': new_functions
                    }

                    # Test user type
                    print(f"\n🧪 TESTING is_new_user for {user_id}:")
                    test_result = new_is_new_user(user_id)
                    print(
                        f"🎯 TEST RESULT: User {user_id} is {'NEW' if test_result else 'EXISTING'}")

                else:
                    print("❌ No .joblib file found in zip")
                    self.ai_components = None
                    return

        except Exception as e:
            print(f"❌ Failed to init AI: {e}")
            import traceback
            traceback.print_exc()
            self.ai_components = None

    def get_ai_recommendations(self, user_id, num_recommendations=10):
        """Lấy recommendations - Phân biệt rõ user mới/cũ"""
        if not self.ai_components:
            return self.get_fallback_recommendations(num_recommendations)

        try:
            user_id_str = str(user_id)
            functions = self.ai_components['recommendation_functions']
            current_mood_id = self.ai_components['current_mood'].iloc[0][
                'moodID']

            # Kiểm tra user type
            is_new_user = functions['is_new_user'](user_id_str)
            user_type = "MỚI" if is_new_user else "CŨ"
            print(
                f"🎯 User {user_id_str} là {user_type} với mood {current_mood_id}")

            # Gọi recommendation function tương ứng
            if is_new_user:
                print("🆕 Using NEW USER algorithm: Heuristic scoring")
                recommendations_df = functions['recommend_for_new_user'](
                    user_id_str, num_recommendations)
            else:
                print(
                    "👤 Using EXISTING USER algorithm: LightGBM + Collaborative Filtering")
                recommendations_df = functions['recommend_for_user'](
                    user_id_str, num_recommendations)

            if recommendations_df is not None and not recommendations_df.empty:
                recommendations = []
                for _, row in recommendations_df.iterrows():
                    # Tính confidence dựa trên loại user
                    if is_new_user:
                        confidence = min(float(row.get('score', 0.8)) * 1.2,
                                         0.95)
                    else:
                        confidence = min(
                            float(row.get('final_score', 0.8)) * 1.2, 0.95)

                    recommendations.append({
                        'trackId': int(row['trackId']),
                        'name': f"{row['trackName']} - {row.get('artistName', 'Unknown')}",
                        'track_name': row['trackName'],
                        'artist_name': row.get('artistName', 'Unknown'),
                        'confidence': confidence,
                        'mood_used': current_mood_id,
                        'user_type': user_type
                    })

                print(
                    f"✅ Generated {len(recommendations)} recommendations for {user_type} user")
                return recommendations

        except Exception as e:
            print(f"❌ Joblib model error: {e}")
            import traceback
            traceback.print_exc()

        return self.get_fallback_recommendations(num_recommendations)

    def get_fallback_recommendations(self, num_recommendations):
        """Fallback khi model không hoạt động"""
        tracks = self.ai_components.get('tracks', pd.DataFrame())
        if tracks.empty:
            return []

        top_tracks = tracks.head(num_recommendations)
        return [{
            'trackId': int(row['trackId']),
            'name': f"{row['trackName']} - {row.get('artistName', 'Unknown')}",
            'track_name': row['trackName'],
            'artist_name': row.get('artistName', 'Unknown'),
            'confidence': 0.7,
            'user_type': 'FALLBACK'
        } for _, row in top_tracks.iterrows()]

    def load_ai_recommendations(self):
        """Tải AI recommendations cho user"""
        if not session.current_user or not self.ai_components:
            return

        user_id = session.current_user.get("userId")
        if not user_id:
            return

        def load_recommendations():
            recommendations = self.get_ai_recommendations(user_id)
            self.parent.after(0, lambda: self.display_ai_recommendations(
                recommendations))

        threading.Thread(target=load_recommendations, daemon=True).start()

    def display_ai_recommendations(self, recommendations):
        """Hiển thị AI recommendations theo hàng ngang"""
        # Xóa recommendations cũ
        self.clear_ai_recommendations()

        if not recommendations:
            print("⚠️ No AI recommendations available")
            return

        print(
            f"🎵 Displaying {len(recommendations)} AI recommendations horizontally")

        # Kích thước mỗi item
        item_width = 150
        item_height = 200
        item_margin = 20

        for i, rec in enumerate(recommendations):
            x_pos = i * (item_width + item_margin)
            self.create_recommendation_item(rec, x_pos, 0, item_width,
                                            item_height, i)

        # Cập nhật kích thước recommendation frame để có thể scroll ngang
        total_width = len(recommendations) * (item_width + item_margin)
        self.recommendation_frame.config(width=total_width, height=item_height)
        self.recommendation_canvas.config(
            scrollregion=self.recommendation_canvas.bbox("all"))
        self.recommendation_canvas.configure(xscrollcommand=lambda *args: None)

    def start_drag(self, event):
        self.recommendation_canvas.drag_start_x = event.x
        self.recommendation_canvas.config(cursor="hand2")

    def do_drag(self, event):
        if not hasattr(self.recommendation_canvas, 'drag_start_x'):
            return

        delta_x = self.recommendation_canvas.drag_start_x - event.x

        # Lấy vị trí scroll hiện tại
        current_pos = self.recommendation_canvas.canvasx(0)

        # Tính vị trí mới - di chuyển theo đúng delta_x
        new_pos = current_pos + delta_x

        # Giới hạn trong phạm vi cho phép
        bbox = self.recommendation_canvas.bbox("all")
        if bbox:
            canvas_width = self.recommendation_canvas.winfo_width()
            content_width = bbox[2]
            max_scroll = max(0, content_width - canvas_width)
            new_pos = max(0, min(new_pos, max_scroll))

            # Di chuyển đến vị trí mới
            self.recommendation_canvas.xview_moveto(new_pos / content_width)

        # Cập nhật vị trí bắt đầu cho lần kéo tiếp theo
        self.recommendation_canvas.drag_start_x = event.x

    def clear_ai_recommendations(self):
        """Xóa tất cả AI recommendations hiện tại"""
        for item in self.recommendation_items:
            if 'frame' in item and item['frame'].winfo_exists():
                item['frame'].destroy()
        self.recommendation_items.clear()

    def create_recommendation_item(self, recommendation, x, y, width, height,
                                   index):
        """Tạo một item recommendation theo dạng card ngang"""
        # Tạo frame cho mỗi recommendation (card)
        frame = Frame(self.recommendation_frame, bg="#F7F7DC", width=width,
                      height=height)
        frame.pack_propagate(False)
        frame.place(x=x, y=y)

        # Màu cho item
        bg_color = "#F7F7DC"
        text_color = "#89A34E"

        image_frame = Frame(frame, bg=bg_color, width=120, height=120)
        image_frame.pack(pady=5)
        image_frame.pack_propagate(False)

        # Tải và hiển thị ảnh bài hát
        def load_album_art(track_id, img_label):
            """Tải ảnh album - Fix lỗi numpy.int64"""
            db = self.controller.get_db()
            # 🎯 QUAN TRỌNG: Convert trackId sang int trước khi query
            track_id_int = int(track_id)
            song = db.db["tracks"].find_one({"trackId": track_id_int})

            if song and song.get("artworkUrl100"):
                image_url = song.get("artworkUrl100")
                image_bytes = urlopen(image_url).read()
                pil_image = Image.open(BytesIO(image_bytes))
                pil_image = pil_image.resize((120, 120),
                                             Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(pil_image)

                def update_image():
                    if img_label.winfo_exists():
                        img_label.config(image=img)
                        img_label.image = img

                self.parent.after(0, update_image)

        # Label cho ảnh
        img_label = Label(image_frame, bg=bg_color, width=120, height=120)
        img_label.pack()

        price_label = Label(image_frame, text="6.500",
                            font=("Inter", 8, "bold"),
                            fg="white", bg="#F586A3",
                            relief="flat", bd=0, width=6, height=1)
        price_label.place(relx=0.6, rely=0.8)
        price_label.place_forget()

        price_label.bind("<Button-1>",
                        lambda e:
                        self.controller.process_payment(song))
        price_label.bind("<Enter>",
                         lambda e: price_label.config(
                             bg="#F56A8A"))  # Hiệu ứng hover
        price_label.bind("<Leave>",
                         lambda e: price_label.config(bg="#F586A3"))

        def show_price_label(event):
            price_label.place(relx=0.6, rely=0.8)

        def hide_price_label(event):
            price_label.place_forget()

        # THÊM: Binding hover cho image_frame và img_label
        image_frame.bind("<Enter>", show_price_label)
        image_frame.bind("<Leave>", hide_price_label)
        img_label.bind("<Enter>", show_price_label)
        img_label.bind("<Leave>", hide_price_label)

        # Chạy trong thread để tải ảnh
        # Trong create_recommendation_item, sửa dòng này:
        threading.Thread(target=load_album_art,
                         args=(recommendation['trackId'], img_label),
                         daemon=True).start()

        # Tách tên bài hát và nghệ sĩ
        song_name = recommendation['name']
        if " - " in song_name:
            track_name, artist_name = song_name.split(" - ", 1)
        else:
            track_name = song_name
            artist_name = "Unknown Artist"

        # Hiển thị thông tin bài hát
        title_label = Label(frame, text=track_name,
                            font=("Coiny Regular", 10),
                            fg=text_color, bg=bg_color,
                            wraplength=width - 10, justify="center")
        title_label.pack(padx=5, pady=2)

        artist_label = Label(frame, text=artist_name,
                             font=("Newsreader Regular", 8),
                             fg=text_color, bg=bg_color,
                             wraplength=width - 10, justify="center")
        artist_label.pack(padx=5, pady=2)

        # Lưu thông tin để có thể play khi click
        song_data = {
            'name': song_name,
            'track_name': track_name,
            'artist_name': artist_name,
            'trackId': recommendation.get('trackId'),
            'frame': frame,
            'title_label': title_label,
            'artist_label': artist_label,
            'confidence': recommendation.get('confidence', 0)
        }

        self.recommendation_items.append(song_data)

        db = self.controller.get_db()
        # 🎯 QUAN TRỌNG: Convert trackId sang int trước khi query
        track_id_int = int(recommendation['trackId'])
        song = db.db["tracks"].find_one({"trackId": track_id_int})

        # Thêm sự kiện click để phát nhạc
        for widget in [frame, img_label, title_label, artist_label]:
            widget.bind("<Button-1>",
                        lambda e:
                        self.controller.process_payment(song))
            # Thêm hiệu ứng hover
            widget.bind("<Enter>",
                        lambda e, w=widget: self.on_recommendation_hover(w,
                                                                         True))
            widget.bind("<Leave>",
                        lambda e, w=widget: self.on_recommendation_hover(w,
                                                                         False))

    def on_recommendation_hover(self, widget, is_enter):
        """Hiệu ứng khi hover vào recommendation item"""
        if is_enter:
            widget.config(cursor="hand2")
            if hasattr(widget, 'config') and 'bg' in widget.keys():
                if widget not in [item.get('image_frame') for item in
                                  self.recommendation_items] + [item.get('img_label') for item in
                         self.recommendation_items]: widget.config(bg="#F0F0E0")
        else:
            if hasattr(widget, 'config') and 'bg' in widget.keys():
                if widget not in [item.get('image_frame') for item in
                                  self.recommendation_items] + [item.get('img_label') for item in
                         self.recommendation_items]: widget.config(bg="#F7F7DC")

    def current_utc_iso(self):
        """Trả về thời gian UTC dạng ISO8601 có hậu tố Z"""
        now = pd.Timestamp.utcnow()
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_month_collection_name(self):
        """Xác định tên collection lịch sử theo tháng hiện tại (vd: history_2025-10)"""
        now = dt.datetime.utcnow()
        return f"history_{now.year}-{now.month:02d}"

    def load_history_from_db(self):
        """Tải danh sách lịch sử nghe nhạc từ MongoDB dựa trên session.current_user"""
        db = self.controller.get_db()
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        user_id = session.current_user.get("userId")
        try:
            query = {"userId": str(user_id)}

            # Dùng find với sort sẵn, limit để tránh tải quá nhiều
            history_docs = db.db["user_history"].find(query) \
                .sort("LastPlayedAt", pymongo.DESCENDING) \
                .limit(50)  # Giới hạn 50 bản ghi gần nhất

            self.history_list = []
            for doc in history_docs:
                self.history_list.append({
                    "trackId": doc.get("trackId"),
                    "trackName": doc.get("trackName", "Unknown"),
                    "artistName": doc.get("artistName", "Unknown Artist"),
                    "artworkUrl100": doc.get("artworkUrl100", "assets/default.png")
                })

            self.update_history_display()
            print(
                f"✅ Đã tải {len(self.history_list)} bài hát trong lịch sử (userId={user_id}).")

        except Exception as e:
            print(f"❌ Lỗi khi tải lịch sử từ MongoDB: {e}")

    def save_to_history(self, song: dict):
        db = self.controller.get_db()
        user_id = session.current_user.get("userId")

        try:
            # ✅ Chuẩn bị dữ liệu
            track_id = song.get("trackId")
            track_name = song.get("trackName")
            artist_name = song.get("artistName")
            artwork = song.get("artworkUrl100", "assets/default.png")
            played_time = self.current_utc_iso()  # dùng hàm nội bộ

            # ---------- 1️⃣ Ghi vào user_history ----------
            existing_entry = db.db["user_history"].find_one({
                "userId": str(user_id),
                "trackId": int(track_id)
            })

            if existing_entry:
                db.db["user_history"].update_one(
                    {"_id": existing_entry["_id"]},
                    {
                        "$inc": {"PlayCount": 1},
                        "$set": {"LastPlayedAt": played_time}
                    }
                )
            else:
                db.db["user_history"].insert_one({
                    "userId": str(user_id),
                    "trackId": int(track_id),
                    "trackName": track_name,
                    "artistName": artist_name,
                    "artworkUrl100": artwork,
                    "PlayCount": 1,
                    "LastPlayedAt": played_time
                })

            # ---------- 2️⃣ Ghi vào bảng lịch sử tháng ----------
            month_collection = self.get_month_collection_name()
            purchase_doc = db.db["purchase"].find_one(
                {"trackId": int(track_id)})
            category = purchase_doc.get("category", "normal") if purchase_doc\
                else "normal"
            db.db[month_collection].insert_one({
                "userId": str(user_id),
                "trackId": int(track_id),
                "trackName": track_name,
                "artistName": artist_name,
                "artworkUrl100": artwork,
                "category": category,
                "played_at": played_time,
                "source": "future"
            })

            print(f"💾 Đã lưu lịch sử nghe: {track_name} ({month_collection})")

        except Exception as e:
            print(f"❌ Lỗi khi lưu lịch sử nghe: {e}")

    def update_history_list(self, song):
        """Đưa bài hát mới nhất lên đầu danh sách hiển thị"""
        self.history_list = [s for s in self.history_list if
                             s.get("trackId") != song.get("trackId")]
        self.history_list.insert(0, song)

    def update_history_display(self):
        """Cập nhật hiển thị lịch sử"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()  #Xóa danh sách cũ
        for song in self.history_list:
            self.create_history_item(song)

        #Cập nhật lại khung cuộn chính xác
        self.history_frame.update_idletasks()
        self.history_canvas.config(scrollregion=self.history_canvas.bbox("all"))

    def create_history_item(self, song: dict):
        """Tạo một ô bài hát trong khung lịch sử"""
        frame = Frame(self.history_frame, bg="#F7F7DC", padx=10, pady=5)
        frame.pack(fill="x", expand=True)

        img_label = Label(frame, bg="#F7F7DC")
        img_label.pack(side="left", padx=10)

        # Tải ảnh bất đồng bộ
        def load_image():
            url = song.get("artworkUrl100", "")
            if url in self.image_cache:
                img = self.image_cache[url]
            else:
                try:
                    image_bytes = urlopen(url).read()
                    pil_image = Image.open(BytesIO(image_bytes))
                    img = ImageTk.PhotoImage(pil_image)
                    self.image_cache[url] = img
                except Exception:
                    img = PhotoImage(file="assets/default.png")
                    self.image_cache[url] = img

            def update_label():
                if img_label.winfo_exists():  # ✅ Kiểm tra tồn tại
                    img_label.config(image=img)
                    img_label.image = img  # giữ reference

            img_label.after(0, update_label)

        threading.Thread(target=load_image, daemon=True).start()

        text_frame = Frame(frame, bg="#F7F7DC")
        text_frame.pack(side="left", fill="x", expand=True)

        text_color = "#89A34E"
        title_label = Label(text_frame, text=song.get("trackName", "Unknown"), font=("Coiny Regular",
                                                          18),fg=text_color,bg="#F7F7DC")
        title_label.pack(anchor="w")
        artist_label = Label(text_frame, text=song.get("artistName", "Unknown Artist"),font=("Newsreader Regular", 14), fg=text_color,bg="#F7F7DC")
        artist_label.pack(anchor="w")

        #Khi click vào bài hát → gọi on_song_click(trackId)
        track_id = song.get("trackId")

        for widget in (frame, img_label, title_label, artist_label):
            widget.bind("<Button-1>",
                        lambda e, tid=track_id: self.on_song_click(tid))

    def load_owned_songs_from_db(self):
        """Tải bài hát sở hữu từ database"""
        self.owned_songs_manager.load_from_db("purchase", sort_field="purchased_at")

    def load_liked_songs_from_db(self):
        """Tải bài hát yêu thích từ database"""
        self.liked_songs_manager.load_from_db("user_favorite", sort_field="added_at")

    def load_playlist_from_db(self, playlist_name):
        self.playlist_manager.load_from_db("playlist", playlist_name=playlist_name)

    def show_owned_songs(self):
        """Hiển thị bài hát sở hữu"""
        self.owned_songs_manager.show()
        self.load_owned_songs_from_db()

        # XÓA HEADER KHI Ở CHẾ ĐỘ ADD SONG
        if self.parent.buttons.current_title == "Add song":
            self.parent.after(100, lambda: [
                widget.destroy() for widget in self.owned_songs_manager.frame.winfo_children()
                if isinstance(widget, Frame) and hasattr(widget, '_is_header_frame')
            ])

    def hide_owned_songs(self):
        """Ẩn bài hát sở hữu"""
        self.owned_songs_manager.hide()

    def show_liked_songs(self):
        """Hiển thị bài hát yêu thích"""
        self.liked_songs_manager.show()
        self.load_liked_songs_from_db()
    def hide_liked_songs(self):
        """Ẩn bài hát yêu thích"""
        self.liked_songs_manager.hide()

    def add_to_favorite(self, song=None):
        """Thêm bài hát vào danh sách yêu thích"""
        song = song or self.current_song
        if not song:
            return False

        try:
            db = self.controller.get_db()
            user_id, track_id = int(
                session.current_user.get("userId")), song.get("trackId")

            # Kiểm tra đã tồn tại
            if db.db["user_favorite"].find_one(
                    {"userId": user_id, "trackId": track_id}):
                return True

            # Thêm vào favorites
            db.db["user_favorite"].insert_one({
                "userId": user_id,
                "trackId": track_id,
                "trackName": song.get("trackName"),
                "artistName": song.get("artistName"),
                "primaryGenreName": song.get("primaryGenreName", ""),
                "artworkUrl100": song.get("artworkUrl100",
                                          "assets/default.png"),
                "added_at": self.current_utc_iso()
            })

            self.update_love_button_state(True)  # Cập nhật UI
            return True

        except Exception as e:
            print(f"❌ Lỗi thêm favorites: {e}")
            return False

    def remove_from_favorite(self, song=None):
        """Xóa bài hát khỏi danh sách yêu thích"""
        song = song or self.current_song
        if not song:
            return False

        try:
            result = self.controller.get_db().db["user_favorite"].delete_one({
                "userId": int(session.current_user.get("userId")),
                "trackId": song.get("trackId")
            })

            if result.deleted_count > 0:
                self.update_love_button_state(False)  # Cập nhật UI
                return True
            return False

        except Exception as e:
            print(f"❌ Lỗi xóa favorites: {e}")
            return False

    def update_love_button_state(self, is_favorite=None):
        """Cập nhật trạng thái nút love (có thể tự detect hoặc truyền trạng thái)"""
        if not self.current_song or not hasattr(self.parent,
                                                'buttons') or not self.parent.buttons:
            return

        if is_favorite is None:
            try:
                existing = self.controller.get_db().db[
                    "user_favorite"].find_one({
                    "userId": int(session.current_user.get("userId")),
                    "trackId": self.current_song.get("trackId")
                })
                is_favorite = existing is not None
            except Exception:
                is_favorite = False

        state = "love(2)" if is_favorite else "love(1)"
        self.parent.buttons.love_state = state
        self.fixed_canvas.itemconfig(
            self.parent.buttons.buttons["love"],
            image=self.parent.buttons.image_cache[state]
        )

    def show_playlist(self, playlist_name):
        """Hiển thị playlist"""
        # Ẩn tất cả các view khác
        self.hide_all_views()

        # LƯU TÊN PLAYLIST GỐC TRƯỚC KHI CHUYỂN SANG CHẾ ĐỘ ADD
        if hasattr(self.parent, 'buttons'):
            self.parent.buttons._last_playlist_name = playlist_name

        # Sử dụng playlist_manager
        if self.playlist_manager:
            self.playlist_manager.load_from_db("playlist",
                                               playlist_name=playlist_name)
            self.playlist_manager.show()
            self.parent.buttons.current_title = playlist_name
            self.parent.buttons.create_title()
        else:
            print("❌ playlist_manager not found in Song class")

    def update_library_display(self):
        """Cập nhật hiển thị thư viện"""
        self.load_playlists_from_db()
        self.library_canvas.delete("all")

        self.create_library_display(5, 7, "Owned Songs", "owned song.png", self.handle_card_click, "owned_songs")
        self.create_library_display(235, 7, "Liked Songs", "liked song.png", self.handle_card_click, "liked_songs")
        self.library_canvas.create_text(4, 210, text="My playlists", fill="#89A34E", font=("Inter", 24), anchor="nw")
        self.create_library_display(5, 270, "", "create.png", self.handle_create_playlist)

        self.display_playlists()

        self.library_frame.update_idletasks()
        self.library_canvas.config(scrollregion=self.library_canvas.bbox("all"))

    def create_library_display(self, x, y, label, image_file, callback, callback_arg=None):
        img = load_image(image_file, size=(175, 150))
        if img:
            img_id = self.library_canvas.create_image(x, y, image=img, anchor="nw")
            self.image_cache[image_file] = img
        else:
            img_id = self.library_canvas.create_rectangle(x, y, x + 175, y + 150,
                                                          fill="#F2829E", outline="#89A34E", width=2)
        text_id = self.library_canvas.create_text(x + 85, y + 170, text=label,
                                                  fill="#89A34E", font=("Inter", 18), anchor="center")
        if callback_arg is not None:
            self.library_canvas.tag_bind(img_id, "<Button-1>", lambda e, arg=callback_arg: callback(arg))
            self.library_canvas.tag_bind(text_id, "<Button-1>", lambda e, arg=callback_arg: callback(arg))
        else:
            self.library_canvas.tag_bind(img_id, "<Button-1>", lambda e: callback())
            self.library_canvas.tag_bind(text_id, "<Button-1>", lambda e: callback())

    def handle_card_click(self, card_type):
        """Xử lý click card"""
        self.hide_all_views()
        if card_type == "owned_songs":
            self.show_owned_songs()
            self.parent.buttons.current_title = "Owned Songs"
        elif card_type == "liked_songs":
            self.show_liked_songs()
            self.parent.buttons.current_title = "Liked Songs"
        self.parent.buttons.create_title()

    def create_playlist_card(self, x, y, label, image_file="chăm hoa 1.png"):
        img = load_image(image_file, size=(175, 150), round_corner=10)
        img_id = None
        if img:
            img_id = self.library_canvas.create_image(x, y, image=img, anchor="nw")
            self.image_cache[label] = img

        text_id = self.library_canvas.create_text(x + 15, y + 160, text=label, fill="#89A34E", font=("Inter", 18),
                                                  anchor="nw")

        self.library_canvas.tag_bind(img_id, "<Button-1>", lambda e, name=label: self.show_playlist(name))
        self.library_canvas.tag_bind(text_id, "<Button-1>", lambda e, name=label: self.show_playlist(name))

    def display_playlists(self):
        for i, playlist in enumerate(self.playlists):
            if i < 3:
                row = 0
                col = i + 1
            else:
                row = (i - 3) // 4 + 1
                col = (i - 3) % 4

            x = 5 + col * 230
            y = 270 + row * 220
            self.create_playlist_card(x, y, playlist['name'])

    def handle_create_playlist(self):
        try:
            current_count = len(self.playlists)
            if current_count < 3:
                row = 0
                col = current_count + 1
            else:
                row = (current_count - 3) // 4 + 1
                col = (current_count - 3) % 4

            x = 5 + col * 230
            y = 270 + row * 220

            label = f"My Playlist #{current_count + 1}"
            self.create_playlist_card(x, y, label)
            self.save_playlist_to_db(label)
            self.update_library_display()

        except Exception as e:
            print(f"❌ Lỗi khi tạo playlist: {e}")

    def load_playlists_from_db(self):
        db = self.controller.get_db()
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return

        username = session.current_user.get("username")
        try:
            user_doc = db.db["user"].find_one({"username": username})
            if user_doc and "playlists" in user_doc:
                self.playlists = user_doc["playlists"]
                print(f"✅ Đã tải {len(self.playlists)} playlists từ database: {[p['name'] for p in self.playlists]}")
            else:
                self.playlists = []
                print("ℹ️ User không có playlists nào")

        except Exception as e:
            print(f"❌ Lỗi khi tải playlists từ MongoDB: {e}")
            self.playlists = []

    def save_playlist_to_db(self, playlist_name: str) -> bool:
        try:
            if not session.current_user:
                print("❌ Lỗi: Chưa có user đăng nhập")
                return False

            username = session.current_user.get("username")
            db = self.controller.get_db()

            playlist_data = {
                "name": playlist_name,
                "created_at": datetime.now(),
                "songs": []
            }
            db.db["user"].update_one(
                {"username": username},
                {"$push": {"playlists": playlist_data}}
            )

            print(f"✅ Đã lưu playlist '{playlist_name}' cho user '{username}'")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi lưu playlist: {e}")
            return False

    def on_song_click(self, track_id):
        user_id = session.current_user.get("userId")
        db = self.controller.get_db()
        try:
            print(f"🔍 Kiểm tra purchase: userId={user_id}, trackId={track_id}")

            # KIỂM TRA USER ĐÃ MUA BÀI HÁT NÀY CHƯA
            purchase_exists = db.db["purchase"].find_one({
                "userId": str(user_id),
                "trackId": int(track_id)
            })

            if not purchase_exists:
                print(f"❌ User {user_id} chưa mua bài hát trackId={track_id}")
                return

            print(f"✅ User {user_id} đã mua bài hát trackId={track_id}")
            # Tìm bài hát theo trackId trong collection 'tracks'
            song = db.db["tracks"].find_one({"trackId": int(track_id)})

            if not song:
                print(f"⚠️ Không tìm thấy trackId={track_id} trong MongoDB.tracks")
                return

            # ---------------- Hiển thị lên fixed_canvas ----------------
            self.fixed_canvas.delete("song_info")

            # Tải ảnh artwork từ URL
            image_url = song.get("artworkUrl100", "")
            try:
                image_bytes = urlopen(image_url).read()
                pil_image = Image.open(BytesIO(image_bytes)).convert(
                    "RGBA")  # ✅ ép về RGBA để resize chắc chắn
                resized_image = pil_image.resize((68, 68), Resampling.LANCZOS)

                img = ImageTk.PhotoImage(resized_image)
                self.current_song_image = img
            except Exception as e:
                print(f"⚠️ Lỗi tải ảnh cho trackId={track_id}: {e}")
                self.current_song_image = PhotoImage(file="../images/White_bg.png")

            # Hiển thị ảnh + tên bài hát + nghệ sĩ
            text_color = "#F586A3"
            x_min, x_max = 104, 255
            y_track, y_artist = 27, 50

            self.fixed_canvas.create_image(20, 5, anchor="nw",
                                           image=self.current_song_image, tags="song_info")
            # ----- Tạo vùng “clip” để ẩn phần chữ vượt ra -----
            clip_width = x_max - x_min
            clip_height = 50

            self.clip_canvas = tkinter.Canvas(
                self.fixed_canvas,
                width=clip_width,
                height=clip_height,
                bg="#F7F7DC",  # cùng màu nền để hòa vào
                highlightthickness=0
            )
            self.clip_canvas.place(x=x_min, y=y_track - 15)

            track_name = song.get("trackName", "Unknown Song")
            artist_name = song.get("artistName", "Unknown Artist")

            track_text = self.clip_canvas.create_text(
                0, 12, text=track_name, fill=text_color,
                font=("Coiny Regular", -18), anchor="w"
            )
            artist_text = self.clip_canvas.create_text(
                0, 42, text=artist_name, fill=text_color,
                font=("Newsreader Regular", -14), anchor="w"
            )

            self.scroll_text(self.clip_canvas, track_text, clip_width)
            self.scroll_text(self.clip_canvas, artist_text, clip_width)
            print(
                f"🎵 Đã hiển thị bài hát: {song.get('trackName')} - {song.get('artistName')}")
            self.play_song(song)

        except Exception as e:
            print(f"❌ Lỗi khi truy vấn bài hát từ MongoDB: {e}")

    def scroll_text(self, canvas, text_id, visible_width, speed=2, delay=50):
        """Hiệu ứng trôi chữ liên tục trong vùng [x_min, x_max]."""
        bbox = canvas.bbox(text_id)
        if not bbox:
            return

        text_width = bbox[2] - bbox[0]

        # Nếu chữ ngắn hơn vùng hiển thị thì không cần trôi
        if text_width <= visible_width:
            return

        def animate(direction=-1):
            # Di chuyển chữ
            canvas.move(text_id, speed * direction, 0)
            x1, y1, x2, y2 = canvas.bbox(text_id)

            # Đảo hướng khi chạm biên
            if x2 <= visible_width or x1 >= 0:
                direction *= -1

            canvas.after(delay, animate, direction)

        animate()

    def update_scroll_region(self, event=None):
        """Cập nhật kích thước vùng cuộn dựa trên nội dung"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        self.owned_songs_manager.canvas.configure(scrollregion=self.owned_songs_manager.canvas.bbox("all"))
        self.liked_songs_manager.canvas.configure(scrollregion=self.liked_songs_manager.canvas.bbox("all"))
        self.playlist_manager.canvas.configure(scrollregion=self.playlist_manager.canvas.bbox("all"))
        self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all"))

    def scroll_with_mouse(self, event):
        """Cuộn danh sách bằng chuột giữa"""
        active_managers = [
            self.owned_songs_manager,
            self.liked_songs_manager,
            self.playlist_manager
        ]
        for manager in active_managers:
            if manager.canvas.winfo_ismapped():
                manager.scroll_with_mouse(event)
                return
        if self.history_canvas.winfo_ismapped():
            self.history_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        elif self.library_canvas.winfo_ismapped():
            self.library_canvas.yview_scroll(-1 * (event.delta // 120),"units")
        else:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def seek_song(self, new_time):
        """Tua bài hát đến thời gian mới"""
        if not self.current_song:
            return

        new_time = max(0, min(new_time, 30))

        # Chống spam tua liên tục
        now = time.time()
        if self.is_seeking and now - self.last_seek_time < 0.2:
            return
        self.last_seek_time = now
        self.is_seeking = True

        # --- Giữ trạng thái đang phát ---
        self.is_playing = True
        self.is_paused = False

        try:
            # VLC đôi khi không cập nhật ngay, nên delay nhẹ
            self.player.set_time(int(new_time * 1000))
            self.current_time = new_time
            self.start_time = time.time() - new_time
        except Exception as e:
            print("⚠️ Seek error:", e)
            return

        # --- Cập nhật UI ngay lập tức ---
        self.parent.buttons.update_progress_bar()

        # --- Khoá update thanh tiến trình tạm thời ---
        def release_seek_flag():
            # Chỉ bỏ khoá nếu đã ổn định >0.5s từ lần tua cuối
            if time.time() - self.last_seek_time >= 0.5:
                self.is_seeking = False

        self.parent.after(500, release_seek_flag)

    def get_paused_time(self):
        """Trả về thời gian tại điểm pause"""
        return self.paused_time

    def get_start_time(self):
        """Trả về thời gian bắt đầu của bài hát"""
        return self.start_time

    def get_current_time(self):
        """Lấy thời gian hiện tại của bài hát đang phát"""
        if self.is_playing:
            self.current_time = time.time() - self.start_time
        elif self.is_paused:
            self.current_time = self.paused_time
        else:
            self.current_time = 0

            # Giới hạn không vượt quá 30 giây
        self.current_time = min(self.current_time, 30)
        return self.current_time

    def get_total_time(self):
        """Lấy tổng thời gian bài hát hiện tại"""
        return 30

    def play_song(self, song):
        """Phát nhạc dựa trên document MongoDB (track object)"""
        try:
            song_url = song.get("previewUrl") or song.get("filePath")
            if not song_url:
                print("⚠️ Không có URL hoặc filePath hợp lệ để phát.")
                return

            media = self.instance.media_new(song_url)
            self.player.set_media(media)
            self.player.play()

            self.current_song = song
            self.is_playing = True
            self.is_paused = False
            self.start_time = time.time()
            self.total_time = 30
            self.paused_time = 0

            # Đổi icon Play → Pause
            self.fixed_canvas.itemconfig(
                self.parent.buttons.buttons["play"],
                image=self.parent.buttons.image_cache["pause"]
            )
            self.parent.buttons.update_progress_bar()

            print(
                f"🎶 Playing now: {song.get('trackName')} - {song.get('artistName')}")
            self.check_song_end()
            self.fixed_canvas.after(500, lambda: self.save_to_history(song))
            self.update_love_button_state()

        except Exception as e:
            print(f"❌ Lỗi khi phát nhạc: {e}")

    def play_pause(self):
        """Toggle giữa Play ↔ Pause: đổi nút và điều khiển nhạc"""
        if not self.current_song:
            return

        c = self.fixed_canvas
        play_button = self.parent.buttons.buttons["play"]

        player_state = self.player.get_state()
        if player_state == vlc.State.Playing:
            # Nhạc đang phát → tạm dừng
            self.player.pause()
            self.is_paused = True
            self.is_playing = False
            self.paused_time = time.time() - self.start_time
            c.itemconfig(play_button,
                         image=self.parent.buttons.image_cache["play"])
        else:
            # Nhạc đang pause → tiếp tục phát
            self.player.play()
            self.is_paused = False
            self.is_playing = True
            self.start_time = time.time() - self.paused_time
            # self.paused_time = 0
            c.itemconfig(play_button,
                         image=self.parent.buttons.image_cache["pause"])
            self.parent.buttons.update_progress_bar()

    def _update_current_playlist_button(self):
        """Cập nhật nút play của playlist đang hiển thị"""
        managers = [self.owned_songs_manager,
                    self.liked_songs_manager, self.playlist_manager]

        for manager in managers:
            if manager.canvas.winfo_ismapped() and hasattr(manager, '_update_play_button'):
                manager._update_play_button()
                break

    def stop_music(self):
        """Dừng phát nhạc hoàn toàn"""
        self.player.stop()
        self.is_playing = False
        self.is_paused = False
        self.is_seeking = False
        # self.start_time = 0
        # self.paused_time = 0

    def next_song(self, event=None):
        """Chuyển sang bài tiếp theo"""
        db = self.controller.get_db()
        user_id = session.current_user.get("userId")

        current_track_id = int(self.current_song["trackId"])
        # Lấy danh sách purchase của user, sắp theo thời gian mua
        purchases = list(
            db.db["purchase"].find({"userId": user_id}).sort("purchased_at",
                                                              1))

        # Tìm vị trí bài hiện tại trong danh sách
        for i, purchase in enumerate(purchases):
            if int(purchase["trackId"]) == current_track_id:
                next_index = (i + 1) % len(purchases)
                next_track_id = int(purchases[next_index]["trackId"])

                next_song = db.db["tracks"].find_one(
                    {"trackId": next_track_id})

                if next_song:
                    print(f"🎵 Phát bài tiếp theo: {next_song['trackName']}")
                    self.repeat_once_flag = False
                    self.on_song_click(next_song["trackId"])
                return

        print("⚠️ Bài hiện tại không có trong danh sách purchase.")

    def previous_song(self, event=None):
        """Quay lại bài trước"""
        db = self.controller.get_db()
        user_id = session.current_user.get("userId")

        current_track_id = int(self.current_song["trackId"])
        # Lấy danh sách purchase của user, sắp theo thời gian mua
        purchases = list(
            db.db["purchase"].find({"userId": user_id}).sort("purchased_at",
                                                             1))
        if not purchases:
            print("⚠️ Người dùng chưa mua bài hát nào.")
            return
        # Tìm vị trí bài hiện tại trong danh sách
        for i, purchase in enumerate(purchases):
            if int(purchase["trackId"]) == current_track_id:
                prev_index = (i - 1) % len(purchases)
                prev_track_id = int(purchases[prev_index]["trackId"])

                prev_song = db.db["tracks"].find_one({"trackId": prev_track_id})
                if prev_song:
                    print(f"🎵 Phát bài trước: {prev_song['trackName']}")
                    self.repeat_once_flag = False
                    self.on_song_click(prev_song["trackId"])
                return

        print("⚠️ Bài hiện tại không có trong danh sách purchase.")

    def check_song_end(self, event=None):
        """Kiểm tra khi bài hát kết thúc và xử lý chế độ lặp"""
        try:
            if self.is_paused or not self.is_playing:
                # Nếu đang pause hoặc không phát → kiểm tra lại sau 0.5s
                self.parent.after(500, self.check_song_end)
                return

            current_time = self.get_current_time()
            song_length = self.get_total_time()

            # Nếu bài hát kết thúc (cách 0.5s)
            if self.player.get_state() == vlc.State.Ended:
                # self.start_time = 0
                # self.paused_time = 0
                # self.is_playing = False
                # self.is_paused = False

                if self.repeat_mode == 1:  # Repeat One
                    if not getattr(self, "repeat_once_flag", False):
                        # Lặp bài hiện tại 1 lần
                        self.repeat_once_flag = True
                        self.play_song(self.current_song)
                    else:
                        # Sau lần lặp → chuyển bài tiếp theo
                        self.repeat_once_flag = False
                        self.next_song()

                elif self.repeat_mode == 2:  # Repeat Always
                    # Lặp bài hiện tại vô hạn
                    self.play_song(self.current_song)

                else:  # Normal
                    # Chế độ bình thường → chuyển bài tiếp theo
                    self.next_song()
            else:
                self.parent.after(500, self.check_song_end)

        except Exception as e:
            print("Lỗi khi kiểm tra kết thúc bài hát:", e)

class SongListManager:
    """Quản lý và hiển thị danh sách bài hát cho history, owned_songs, liked_songs"""

    def __init__(self, parent, controller, list_type):
        self.parent = parent  # MainScreen instance
        self.controller = controller
        self.list_type = list_type  # "history", "owned_songs", "liked_songs"

        self.song_list = []
        self.image_cache = {}
        # self.is_playing_playlist = False
        self.play_button_label = None

        self.add_song_canvas = None
        self.song_selection_canvas = None
        self.song_selection_frame = None
        self.search_add_entry = None

        # Tạo canvas cho song
        self.canvas = Canvas(self.parent, width=1000, height=408, bg="#F7F7DC",
                             bd=0, highlightthickness=0)
        self.canvas.place(x=103, y=90)
        self.canvas.place_forget()

        self.frame = Frame(self.canvas, bg="#F7F7DC")
        self.canvas_window = self.canvas.create_window((0, 0),
                                                       window=self.frame,
                                                       anchor="nw", width=844)

        # Bind sự kiện cuộn
        self.canvas.bind("<Enter>",
                         lambda e: self.canvas.bind_all("<MouseWheel>",
                                                        self.scroll_with_mouse))
        self.canvas.bind("<Leave>",
                         lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

    def scroll_with_mouse(self, event):
        """Cuộn bằng chuột"""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def load_from_db(self, collection_name, user_field="userId",
                     sort_field=None, playlist_name=None):
        db = self.controller.get_db()
        if not session.current_user:
            return
        try:
            # XỬ LÝ PLAYLIST
            if collection_name == "playlist":
                self._load_playlist(db, playlist_name)
            # XỬ LÝ CÁC COLLECTION THÔNG THƯỜNG
            else:
                user_id = session.current_user.get("userId")
                if collection_name == "user_favorite":
                    query = {user_field: int(user_id)}
                else:
                    query = {user_field: str(user_id)}
                cursor = db.db[collection_name].find(query)

                if sort_field:
                    cursor = cursor.sort(sort_field, pymongo.DESCENDING)
                cursor = cursor.limit(50)

                self.song_list = []
                for doc in cursor:
                    self.song_list.append({
                        "trackId": doc.get("trackId"),
                        "trackName": doc.get("trackName", "Unknown"),
                        "artistName": doc.get("artistName", "Unknown Artist"),
                        "artworkUrl100": doc.get("artworkUrl100",
                                                 "assets/default.png")
                    })
                print(
                    f"✅ Đã tải {len(self.song_list)} bài hát từ {collection_name}")
            self.update_display(is_playlist=(collection_name == "playlist"))
            self.show()
        except Exception as e:
            print(f"❌ Lỗi khi tải từ {collection_name}: {e}")

    def _load_playlist(self, db, playlist_name):
        username = session.current_user.get("username")
        user_doc = db.db["user"].find_one({"username": username})
        playlist = next((p for p in user_doc.get("playlists", []) if
                         p["name"] == playlist_name), None)

        self.song_list = []
        for song_data in playlist.get("songs", []):
            track = db.db["tracks"].find_one(
                {"trackId": song_data.get("trackId")})
            if track:
                self.song_list.append({
                    "trackId": track.get("trackId"),
                    "trackName": track.get("trackName", "Unknown"),
                    "artistName": track.get("artistName", "Unknown Artist"),
                    "artworkUrl100": track.get("artworkUrl100",
                                               "assets/default.png")
                })
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def update_display(self, is_playlist=False, playlist_name=None):
        for widget in self.frame.winfo_children():
            widget.destroy()

        is_add_mode = hasattr(self.parent,
                              'buttons') and self.parent.buttons.current_title == "Add song"
        if not is_add_mode and ((
                                        self.song_list and self.list_type != "history") or self.list_type == "playlist"):
            self._create_header_buttons()

        # Hiển thị thông báo nếu không có bài hát
        if not self.song_list:
            Label(self.frame, text="No song in here",
                  font=("Newsreader Regular", 18), fg="#89A34E",
                  bg="#F7F7DC").pack(pady=50)
        else:
            # Danh sách bài hát
            for song in self.song_list:
                self.create_song_item(song)

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _create_header_buttons(self):
        header_frame = Frame(self.frame, bg="#F7F7DC", pady=5)
        header_frame.pack(fill="x")
        header_frame._is_header_frame = True
        icons = []

        # Nếu là playlist và có bài hát: hiện play, shuffle, add
        if self.list_type == "playlist" and self.song_list:
            icons.extend([
                ("play", "play.png", lambda e: self.toggle_play_playlist()),
                ("shuffle", "shuffle.png", lambda e: self.shuffle_playlist()),
                ("add", "add.png", lambda e: self.add_to_playlist())
            ])
        # Nếu là playlist và rỗng: chỉ hiện add
        elif self.list_type == "playlist" and not self.song_list:
            icons.append(("add", "add.png", lambda e: self.add_to_playlist()))
        # Nếu không phải playlist và có bài hát: hiện play, shuffle
        elif self.list_type != "playlist" and self.song_list and self.list_type != "history":
            icons.extend([
                ("play", "play.png", lambda e: self.toggle_play_playlist()),
                ("shuffle", "shuffle.png", lambda e: self.shuffle_playlist()),
            ])

        for key, icon_file, callback in icons:
            icon_img = PhotoImage(file=relative_to_assets(icon_file))
            icon_label = Label(header_frame, image=icon_img, bg="#F7F7DC",
                               cursor="hand2")
            icon_label.image = icon_img
            icon_label.pack(side="left", padx=15)
            icon_label.bind("<Button-1>", callback)

            if key == "play":
                self.play_button_label = icon_label
                self.play_icon, self.pause_icon = icon_img, PhotoImage(
                    file=relative_to_assets("pause.png"))

    def add_to_playlist(self):
        """Mở giao diện owned_songs để thêm vào playlist"""
        self.hide()
        self.original_playlist_name = self.parent.buttons.current_title

        self.parent.buttons.current_title = "Add song"
        self.parent.buttons.create_title()

        canvas = self.parent.buttons.canvas
        down_icon_img = PhotoImage(file=relative_to_assets("down.png"))
        self.down_icon_label = Label(canvas, image=down_icon_img, bg="#F7F7DC",
                                     cursor="hand2")
        self.down_icon_label.image = down_icon_img
        self.down_icon_label.place(x=300, y=33)

        # Bind sự kiện click để quay lại
        self.down_icon_label.bind("<Button-1>",
                                  lambda e: self._return_from_add_mode())

        self.parent.songs.show_owned_songs()

    def _return_from_add_mode(self):
        """Quay lại từ chế độ Add to"""
        # Xóa icon down
        if hasattr(self, 'down_icon_label') and self.down_icon_label:
            self.down_icon_label.destroy()

        # Quay lại playlist gốc
        if hasattr(self, 'original_playlist_name'):
            self._return_to_playlist(self.original_playlist_name)

    def _add_song_to_playlist_by_id(self, track_id):
        """Thêm bài hát vào playlist bằng trackId"""
        try:
            # SỬA: Kiểm tra và lấy tên playlist từ nhiều nguồn
            playlist_name = None

            # Ưu tiên 1: từ original_playlist_name
            if hasattr(self,
                       'original_playlist_name') and self.original_playlist_name:
                playlist_name = self.original_playlist_name
            # Ưu tiên 2: từ parent.buttons.current_title (trước khi chuyển sang "Add song")
            elif hasattr(self.parent, 'buttons') and hasattr(
                    self.parent.buttons, 'current_title'):
                # Tìm trong lịch sử hoặc lưu trữ tên playlist gốc
                playlist_name = getattr(self.parent.buttons,
                                        '_last_playlist_name', None)

            if not playlist_name:
                print("❌ Không tìm thấy tên playlist đích")
                messagebox.showerror("Error",
                                     "Cannot determine target playlist!")
                return

            db = self.controller.get_db()
            username = session.current_user.get("username")

            # Lấy thông tin bài hát từ trackId
            track = db.db["tracks"].find_one({"trackId": track_id})
            if not track:
                messagebox.showerror("Error", "Song not found!")
                return

            # Kiểm tra xem bài hát đã có trong playlist chưa
            user_doc = db.db["user"].find_one({"username": username})
            playlist = next((p for p in user_doc.get("playlists", []) if
                             p["name"] == playlist_name), None)

            if playlist:
                # Kiểm tra trùng lặp
                existing_song = next((s for s in playlist.get("songs", []) if
                                      s.get("trackId") == track_id), None)
                if existing_song:
                    messagebox.showwarning("Warning",
                                           "This song is already in the playlist!")
                    return
            # Thêm bài hát vào playlist
            song_data = {
                "trackId": track_id,
                "added_at": datetime.now()
            }
            result = db.db["user"].update_one(
                {"username": username, "playlists.name": playlist_name},
                {"$push": {"playlists.$.songs": song_data}}
            )

            if result.modified_count > 0:
                messagebox.showinfo("Success",
                                    f"Added '{track['trackName']}' to {playlist_name}!")
                # Quay lại playlist
                self._return_to_playlist(playlist_name)
            else:
                messagebox.showerror("Error", "Failed to add song to playlist!")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding song: {str(e)}")
            print(f"❌ Lỗi chi tiết: {e}")

    def _return_to_playlist(self, playlist_name):
        """Quay lại hiển thị playlist sau khi thêm bài hát"""
        # Xóa icon down nếu có
        if hasattr(self, 'down_icon_label') and self.down_icon_label:
            self.down_icon_label.destroy()

        # Ẩn owned_songs
        self.parent.songs.owned_songs_manager.hide()

        # Khôi phục tiêu đề - SỬA: dùng playlist_name được truyền vào
        self.parent.buttons.current_title = playlist_name
        self.parent.buttons.create_title()

        # Hiển thị lại playlist
        self.parent.songs.show_playlist(playlist_name)

    def create_song_item(self, song: dict):
        """Tạo một ô bài hát"""
        frame = Frame(self.frame, bg="#F7F7DC", padx=10, pady=5)
        frame.pack(fill="x", expand=True)

        img_label = Label(frame, bg="#F7F7DC")
        img_label.pack(side="left", padx=10)

        # Tải ảnh bất đồng bộ
        def load_image_song():
            url = song.get("artworkUrl100", "")
            if url in self.image_cache:
                img = self.image_cache[url]
            else:
                try:
                    image_bytes = urlopen(url).read()
                    pil_image = Image.open(BytesIO(image_bytes))
                    img = ImageTk.PhotoImage(pil_image)
                    self.image_cache[url] = img
                except Exception:
                    img = PhotoImage(file="assets/default.png")
                    self.image_cache[url] = img

            def update_label():
                if img_label.winfo_exists():
                    img_label.config(image=img)
                    img_label.image = img

            img_label.after(0, update_label)  # type: ignore

        threading.Thread(target=load_image_song, daemon=True).start()

        text_frame = Frame(frame, bg="#F7F7DC")
        text_frame.pack(side="left", fill="x", expand=True)

        text_color = "#89A34E"
        title_label = Label(text_frame, text=song.get("trackName", "Unknown"),
                            font=("Coiny Regular", 18), fg=text_color,
                            bg="#F7F7DC")
        title_label.pack(anchor="w")
        artist_label = Label(text_frame,
                             text=song.get("artistName", "Unknown Artist"),
                             font=("Newsreader Regular", 14), fg=text_color,
                             bg="#F7F7DC")
        artist_label.pack(anchor="w")

        track_id = song.get("trackId")
        if (hasattr(self.parent, 'buttons') and
                self.parent.buttons.current_title == "Add song"):

            add_icon_img = PhotoImage(file=relative_to_assets("add 1.png"))
            add_btn = Label(frame, image=add_icon_img, bg="#F7F7DC",
                            cursor="hand2")
            add_btn.image = add_icon_img
            add_btn.pack(side="right", padx=10)

            # SỬA LẠI CÁCH BIND - DÙNG HÀM RIÊNG ĐỂ TRÁNH LỖI SCOPE
            def add_handler(event, tid=track_id):
                current_playlist = getattr(self, 'original_playlist_name',
                                           'Unknown')
                print(
                    f"🎯 Adding song with track_id: {tid} to playlist: {current_playlist}")
                print(
                    f"🎯 Debug - self.original_playlist_name: {getattr(self, 'original_playlist_name', 'NOT SET')}")
                self._add_song_to_playlist_by_id(tid)

            add_btn.bind("<Button-1>", add_handler)

            # Gán track_id và bind sự kiện click bài hát (giữ nguyên)
        title_label._track_id = track_id
        artist_label._track_id = track_id
        for widget in (frame, img_label, title_label, artist_label):
            widget.bind("<Button-1>",
                        lambda e, tid=track_id: self.parent.songs.on_song_click(
                            tid))

    def toggle_play_playlist(self):
        """Toggle play/pause cho playlist và đồng bộ 2 nút"""
        if not self.parent.songs.current_song or not self.parent.songs.is_playing:
            # Chưa có bài nào đang phát → phát bài đầu
            if self.song_list:
                first_song = self.song_list[0]
                self.parent.songs.on_song_click(first_song["trackId"])
        else:
            self.parent.songs.play_pause()
        self._update_play_button()

    def _update_play_button(self):
        """Cập nhật nút play của playlist hiện tại"""
        if hasattr(self, 'play_button_label'):
            if self.parent.songs.is_playing:
                self.play_button_label.config(image=self.pause_icon)
                self.play_button_label.image = self.pause_icon
            else:
                self.play_button_label.config(image=self.play_icon)
                self.play_button_label.image = self.play_icon

    def shuffle_playlist(self):
        """Xáo trộn playlist"""
        import random
        if self.song_list:
            random.shuffle(self.song_list)
            self.parent.songs.on_song_click(self.song_list[0]["trackId"])
            self._update_play_button()

    def show(self):
        """Hiển thị canvas"""
        self.canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)
        self.frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0.0)

    def hide(self):
        """Ẩn canvas"""
        self.canvas.place_forget()

