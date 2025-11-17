from tkinter import Frame, Canvas, messagebox
# from customtkinter import CTkButton
from functions import load_image
from Connection.connector import db
import session
from ui.generate_wrapup_data  import generate_user_wrapup
from datetime import datetime, timedelta
import requests, io
from PIL import Image, ImageTk


class WrapUpFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        # Canvas nền (chừa 50px cho toolbar)
        self.canvas = Canvas(self, bg="#F7F7DC", height=600, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.current_page = 0
        self.pages=[]

        # Load dữ liệu từ MongoDB
        self.user_data = self.load_data()
        if not self.user_data:
            self.canvas.create_text(
                500, 300,
                text="No wrap-up data found!",
                font=("Inter", 20, "bold"),
                fill="#F2829E"
            )
            return

        # Các trang wrap-up
        self.pages = [
            self.create_page1(),
            self.create_page2(),
            self.create_page3(),
            self.create_page4(),
            self.create_page5()
        ]
        self.show_page(0)

    # ========== PAGE 1: INTRO ==========
    def create_page1(self):
        frame = Canvas(self, bg="#FFF6E9", width=950, height=600, highlightthickness=0)
        frame.place(x=0, y=0)

        self.image_cache["bg_page1"] = load_image("bg_page1.jpg", opacity=0.4, size=(950, 600))
        frame.create_image(480, 300, image=self.image_cache["bg_page1"])

        user = session.current_user.get("name", "User")
        month = self.user_data.get("month", "Unknown")

        frame.create_text(480, 190, text=f"Welcome back, {user}!", fill="#F2829E",
                          font=("Inter Bold", 38, "bold"))
        frame.create_text(480, 260, text=f"Your Moo_d Journey for {month}",
                          fill="#89A34E", font=("Inter", 24, "bold"))
        frame.create_text(480, 320, text="Let's see what feelings shaped your month 💫",
                          fill="#AD5E52", font=("Inter", 21, "bold"))

        self.create_nav_buttons(frame)
        return frame

    # PAGE 2: MOOD MIX
    def create_page2(self):
        frame = Canvas(self, bg="#EAF4D3", width=950, height=600, highlightthickness=0)
        self.image_cache["bg_page1_1"] = load_image("bg_page1_1.jpg", opacity=0.4, size=(960, 610))
        frame.create_image(480, 300, image=self.image_cache["bg_page1_1"])

        frame.create_text(480, 100, text="Your Mood Mix", fill="#F2829E",
                          font=("Inter Bold", 34, "bold"))

        self.image_cache["rec_page2"] = load_image("rec_page2.png", round_corner=0.2, size=(525, 375))
        frame.create_image(480, 330, image=self.image_cache["rec_page2"])

        mood_icons = {
            "Neutral": "neutral.png",
            "Happy": "happy.png",
            "Intense": "intense.png",
            "Sad": "sad.png"
        }

        moods = list(self.user_data.get("mood_count", {}).items())
        y = 200
        for mood, count in moods:
            icon = mood_icons.get(mood, "cat_neutral.png")
            self.image_cache[f"icon_{mood}"] = load_image(icon, size=(65, 65))
            frame.create_image(312, y, image=self.image_cache[f"icon_{mood}"])
            frame.create_text(440, y, text=f"{mood} ({count})",
                              fill="#F2829E", font=("Inter", 30, "bold"), anchor="w")
            y += 80
        self.create_nav_buttons(frame)
        return frame

    # PAGE 3: FAVORITE ARTISTS
    def create_page3(self):
        frame = Canvas(self, bg="#FBE8DD", width=950, height=600, highlightthickness=0)
        self.image_cache["bg_page3"] = load_image("bg_page3.jpg", opacity=0.6, size=(960, 600))
        frame.create_image(480, 300, image=self.image_cache["bg_page3"])
        self.image_cache["rec_page3"] = load_image("rec_page3.png", round_corner=0.2, size=(525, 375))
        frame.create_image(480, 330, image=self.image_cache["rec_page3"])
        frame.create_text(480, 100, text="💖 Favorite Artists 💖", fill="#89A34E", font=("Inter Bold", 33, "bold"))

        # Danh sách nghệ sĩ (tối đa 5)
        artists = self.user_data.get("top_artists", [])
        if not artists:
            frame.create_text(
                480, 310,
                text="No artist data found ",
                fill="#6B705C",
                font=("Inter Italic", 18)
            )
        else:
            y = 190
            for i, artist in enumerate(artists[:5], start=1):
                name = artist.get("ArtistName", "Unknown")
                plays = artist.get("PlayCount", 0)
                frame.create_text(
                    480, y,
                    text=f"{i}. {name}",
                    fill="#89A34E",
                    font=("Inter Bold", 25, "bold")
                )
                y += 65

        self.create_nav_buttons(frame)
        return frame

    # PAGE 4: TOP SONGS
    def create_page4(self):
        frame = Canvas(self, bg="#F7F7DC", width=950, height=600,
                       highlightthickness=0)
        self.image_cache["bg_page42"] = load_image("bg_page42.png", opacity=0.6,
                                                   size=(960, 600))
        frame.create_image(480, 300, image=self.image_cache["bg_page42"])

        # Tiêu đề
        frame.create_text(480, 80, text="Top Songs", fill="#D5678E",
                          font=("Inter Bold", 36, "bold"))

        songs = self.user_data.get("favourite_songs", [])
        if not songs:
            frame.create_text(480, 320, text="No songs found 🎧",
                              font=("Inter", 20), fill="#6B705C")
            self.create_nav_buttons(frame)
            return frame

        # Tải hình khung pastel cho mỗi bài hát
        self.image_cache["song_box"] = load_image("rec_page4.png",
                                                  size=(600, 80))

        y = 160
        for song in songs[:5]:
            title = song.get("TrackName", "Unknown")
            artist = song.get("ArtistName", "")
            artwork = song.get("Artwork", "")

            # FIX: Kiểm tra và xử lý URL bị truncated
            if artwork and '…' in artwork:
                artwork = None

            # Khung nền cho mỗi bài
            frame.create_image(480, y + 20, image=self.image_cache["song_box"])

            # Ảnh artwork - XỬ LÝ URL BỊ TRUNCATED
            if artwork and artwork.startswith(
                    'http') and artwork != "https://example.com/default_art.png":
                try:
                    # Thêm headers để tránh bị chặn
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(artwork, timeout=10,
                                            headers=headers)
                    response.raise_for_status()
                    img_data = response.content
                    pil = Image.open(io.BytesIO(img_data)).resize((65, 65))
                    photo = ImageTk.PhotoImage(pil)

                    # Lưu với key duy nhất để tránh ghi đè
                    cache_key = f"artwork_{title}_{y}"
                    self.image_cache[cache_key] = photo
                    frame.create_image(235, y + 20, image=photo)
                    print(f"Loaded artwork for: {title}")

                except Exception as e:
                    print(f"Failed to load artwork for {title}: {e}")
                    # Dùng ảnh mặc định nếu có lỗi
                    self.load_default_artwork(frame, 235, y + 20, title)
            else:
                # URL rỗng, mặc định, hoặc bị truncated
                print(f"Invalid artwork for {title}, using default")
                self.load_default_artwork(frame, 235, y + 20, title)

            # Tên bài hát + nghệ sĩ
            frame.create_text(280, y + 5, text=title,
                              anchor="w", fill="#FFFFFF",
                              font=("Inter Bold", 17, "bold"))
            frame.create_text(280, y + 35, text=artist,
                              anchor="w", fill="#FFFFFF", font=("Inter", 14))
            y += 90

        self.create_nav_buttons(frame)
        return frame

    def load_default_artwork(self, frame, x, y, title):
        """Tạo ảnh mặc định đẹp với màu pastel (không dùng ImageDraw)"""
        try:
            # Màu pastel đẹp cho artwork mặc định
            pastel_colors = ['#FFB6C1', '#FFD700', '#98FB98', '#87CEEB',
                             '#DDA0DD', '#F0E68C', '#E6E6FA']
            color_index = hash(title) % len(pastel_colors)
            color = pastel_colors[color_index]

            # Tạo ảnh đơn giản không cần ImageDraw
            img = Image.new('RGB', (65, 65), color=color)
            photo = ImageTk.PhotoImage(img)

            # Lưu với key duy nhất
            cache_key = f"default_{title}_{y}"
            self.image_cache[cache_key] = photo
            frame.create_image(x, y, image=photo)

            # Thêm icon note nhạc bằng text thay vì vẽ
            frame.create_text(x, y, text="♪", font=("Arial", 24, "bold"),
                              fill="#FFFFFF")

            print(f"Created default artwork for: {title}")

        except Exception as e:
            print(f"Default artwork failed: {e}")
            try:
                img = Image.new('RGB', (65, 65), color='#E0E0E0')
                photo = ImageTk.PhotoImage(img)
                self.image_cache[f"simple_{y}"] = photo
                frame.create_image(x, y, image=photo)
                frame.create_text(x, y, text="🎵", font=("Arial", 16),
                                  fill="#888888")
            except Exception as e2:
                print(f"Even simple fallback failed: {e2}")

    # PAGE 5: REFLECTION
    def create_page5(self):
        frame = Canvas(self, bg="#FFE9E9", width=950, height=600, highlightthickness=0)
        self.user_data.get("dominant_mood", "Neutral")
        quote = self.user_data.get(
            "dominant_mood_quote",
            "Every emotion tells your story!"
        )
        self.image_cache["bg_page5"] = load_image("bg_page5.png", opacity=0.4, size=(960, 600))
        frame.create_image(480, 300, image=self.image_cache["bg_page5"])
        frame.create_text(480, 300, text=quote,
                          fill="#F2829E", font=("Inter", 35, "bold"), width=600, justify="center")
        self.create_nav_buttons(frame)
        return frame

    # PAGE CONTROL
    def create_nav_buttons(self, frame):
        """Tạo nút điều hướng trái/phải bằng ảnh, cập nhật theo trang hiện tại"""
        try:
            # Xóa icon cũ (nếu có) để tránh chồng nút
            frame.delete("btn_left")
            frame.delete("btn_right")

            # Tải icon trái/phải
            left_icon = load_image("left.png", size=(48, 48))
            right_icon = load_image("right.png", size=(48, 48))

            if not left_icon or not right_icon:
                return

            # Giữ reference trong cache để tránh bị GC
            self.image_cache[f"nav_left_{id(frame)}"] = left_icon
            self.image_cache[f"nav_right_{id(frame)}"] = right_icon

            # Nếu KHÔNG phải trang đầu tiên → hiển thị nút back
            if self.current_page > 0:
                frame.create_image(70, 300, image=left_icon, tags="btn_left")
                frame.tag_bind("btn_left", "<Button-1>", lambda e: self.prev_page())

            # Nếu KHÔNG phải trang cuối → hiển thị nút next
            if self.current_page < len(self.pages) - 1:
                frame.create_image(890, 300, image=right_icon, tags="btn_right")
                frame.tag_bind("btn_right", "<Button-1>", lambda e: self.next_page())

        except Exception as e:
            print(f"Lỗi khi tạo nút điều hướng: {e}")

    def show_page(self, index):
        """Hiển thị đúng trang và cập nhật nút điều hướng"""
        if not (0 <= index < len(self.pages)):
            return

        # Ẩn các trang khác
        for p in self.pages:
            p.place_forget()

        # Cập nhật trang hiện tại
        self.current_page = index
        frame = self.pages[index]
        frame.place(x=0, y=0)

        # Vẽ lại nút điều hướng cho trang này
        self.create_nav_buttons(frame)

    def next_page(self):
        """Chuyển tới trang kế"""
        new_index = min(self.current_page + 1, len(self.pages) - 1)
        self.show_page(new_index)

    def prev_page(self):
        """Quay lại trang trước"""
        new_index = max(self.current_page - 1, 0)
        self.show_page(new_index)

    # ========== LOAD DATA ==========
    @staticmethod
    def load_data():
        """Tải dữ liệu wrap-up tháng trước từ MongoDB, nếu chưa có thì sinh mới"""
        if session.current_user is None:
            messagebox.showerror("Error", "No user is logged in.")
            return None

        user_id = session.current_user.get("userId")
        if not user_id:
            messagebox.showerror("Error", "User ID not found in session.")
            return None

        now = datetime.now()
        last_month_date = now.replace(day=1) - timedelta(days=1)
        last_month = last_month_date.strftime("%Y-%m")

        print(f"Checking wrap-up for user={user_id}, month={last_month}...")
        wrapup = db.find_one("user_wrapup", {"user_id": user_id, "month": last_month})

        if not wrapup:
            print(f" No wrap-up found. Generating for {last_month}...")
            try:
                wrapup = generate_user_wrapup(user_id)
                if not wrapup:
                    messagebox.showinfo("Wrap-up", "No listening data available for last month ")
                    return None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate wrap-up: {e}")
                return None

        print(f" Loaded wrap-up for {user_id} ({wrapup['month']}) — mood: {wrapup.get('dominant_mood')}")
        return wrapup
