import os
import shutil
import smtplib
from bson import ObjectId
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from customtkinter import CTkEntry
from FinalProject.moo_d.functions import *
from tkinter import Tk, Canvas, messagebox, Frame, filedialog
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
from tkinter import Scrollbar
class LoginFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        self.username_entry = None
        self.password_entry = None
        self.signin_button = None

        self.canvas = Canvas(self, bg="#FFFFFF", height=600, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.load_background()
        self.create_widgets()

    def load_background(self):
        """Tải ảnh nền cho giao diện"""
        self.image_cache["ml_bg"] = load_image("ml_bg.png", opacity=1, size=(1020, 623))
        self.image_cache["ml2"] = load_image("ml2.png", size=(1095, 650))
        self.image_cache["ml3"] = load_image("ml3.png", rotate=24)
        self.image_cache["ml4"] = load_image("ml4.png", size=(80, 80))
        self.image_cache["ml5"] = load_image("ml5.png", size=(93, 88))
        self.image_cache["box"] = load_image("ml1.png", opacity=0.9, size=(650, 600), round_corner=20)
        self.image_cache["ml6"] = load_image("ml6.png", size=(232, 232), rotate=18)

        self.canvas.create_image(500, 300, image=self.image_cache["ml_bg"])
        self.canvas.create_image(500, 420, image=self.image_cache["ml2"])
        self.canvas.create_image(190, 180, image=self.image_cache["ml3"])
        self.canvas.create_image(70, 540, image=self.image_cache["ml4"])
        self.canvas.create_image(300, 480, image=self.image_cache["ml5"])
        self.canvas.create_image(690, 300, image=self.image_cache["box"])
        self.canvas.create_image(900, 130, image=self.image_cache["ml6"])

    def create_widgets(self):
        # Text
        self.canvas.create_text(460, 70, anchor="nw", text="Welcome!", fill="#F2829E",
                         font=("Inter Bold", 50, "bold"))
        self.canvas.create_text(525, 170, text="Username:", font=("Inter", 16, "bold"),
                         fill="#F2829E", anchor="w")
        self.canvas.create_text(525, 270, text="Password:", font=("Inter", 16, "bold"),
                         fill="#F2829E", anchor="w")

        # Entries
        self.username_entry = CTkEntry(
            master=self,
            width=340,
            height=45,
            font=("Inter", 16),
            fg_color="transparent",
            text_color="#1E1E1E",
            border_width=1,
            border_color="#F2829E",
            placeholder_text="Username",
            placeholder_text_color="#F2829E",
            corner_radius=0
        )
        self.username_entry.place(x=530, y=200)

        self.password_entry = CTkEntry(
            master=self,
            width=340,
            height=45,
            font=("Inter", 16),
            fg_color="transparent",
            text_color="#1E1E1E",
            border_width=1,
            border_color="#F2829E",
            placeholder_text="Password",
            placeholder_text_color="#F2829E",
            show="*",
            corner_radius=0
        )
        self.password_entry.place(x=530, y=300)

        # Buttons
        self.signin_button = CTkButton(self, cursor="hand2", width=340, height=40,
                                       text="Sign In", font=("Inter", 18, "bold"),
                                       text_color="#FFFFFF", fg_color="#F2829E",
                                       hover_color="#6465B2", corner_radius=0,
                                       command=self.attempt_login)
        self.signin_button.place(x=530, y=370)

        # Sign up link
        self.canvas.create_text(580, 440, text="Don't have an account?",
                         font=("Inter", 12), fill="#1E1E1E", anchor="w")
        self.canvas.create_text(750, 430, text="Sign up", font=("Inter", 12),
                         fill="#F2829E", anchor="nw", tags="signup")
        self.canvas.tag_bind("signup", "<Button-1>", lambda e: self.controller.show_frame("SignUpFrame"))

        # Bind Enter key để login
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())
        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        try:
            user = db.find_one("user", {
                "username": username,
                "password": password
            })
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
            return

        if user:
            import FinalProject.moo_d.session as session
            session.current_user = user
            print("✅ Logged in user:", session.current_user)

            # Chuyển sang MoodTracker
            self.controller.show_frame("MoodTracker")
            self.controller.destroy_frame("LoginFrame")
            return

        messagebox.showerror("Error", "Incorrect username or password!")

    # def attempt_login(self):
    #     username = self.username_entry.get().strip()
    #     password = self.password_entry.get().strip()
    #     if user:
    #         session.current_user = user
    #         print("✅ Logged in user:", session.current_user)
    #         self.controller.show_frame("MoodTracker")
    #     # try:
    #     #     with open("data/user.json", "r", encoding="utf-8") as file:
    #     #         users = json.load(file)
    #     # except FileNotFoundError:
    #     #     messagebox.showerror("Error", "User data not found.")
    #     #     return
    #     #
    #     # for user in users:
    #     #     if user["username"] == username and user["password"] == password:
    #     #         session.current_user = user
    #     #         self.controller.show_frame("MoodTracker")
    #     #         self.controller.destroy_frame("LoginFrame")
    #     #         return
    #
    #     try:
    #         user = db.find_one("user", {
    #             "username": username,
    #             "password": password
    #         })
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Database error: {e}")
    #         return
    #
    #     if user:
    #         session.current_user = user
    #         self.controller.show_frame("MoodTracker")
    #         self.controller.destroy_frame("LoginFrame")
    #         return
    #
    #     messagebox.showerror("Error", "Incorrect username or password!")

    # def on_show(self):
    #     """Được gọi khi frame được hiển thị"""
    #     self.clear_entries()

    # def clear_entries(self):
    #     """Xóa nội dung trong các ô nhập liệu"""
    #     self.username_entry.delete(0, 'end')
    #     self.password_entry.delete(0, 'end')


class SignUpFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        self.name_entry = None
        self.email_entry = None
        self.username_entry = None
        self.password_entry = None
        self.signup_button = None
        self.back_button = None

        self.canvas = Canvas(self, bg="#FFFFFF", height=600, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.load_background()
        self.create_widgets()

    def load_background(self):
        """Tải ảnh nền cho giao diện (giống LoginFrame)"""
        self.image_cache["ml_bg"] = load_image("ml_bg.png", opacity=1, size=(1020, 623))
        self.image_cache["ml2"] = load_image("ml2.png", size=(1095, 650))
        self.image_cache["ml3"] = load_image("ml3.png", rotate=24)
        self.image_cache["ml4"] = load_image("ml4.png", size=(80, 80))
        self.image_cache["ml5"] = load_image("ml5.png", size=(93, 88))
        self.image_cache["box"] = load_image("ml1.png", opacity=1, size=(650, 600), round_corner=20)

        self.canvas.create_image(500, 300, image=self.image_cache["ml_bg"])
        self.canvas.create_image(500, 420, image=self.image_cache["ml2"])
        self.canvas.create_image(190, 180, image=self.image_cache["ml3"])
        self.canvas.create_image(70, 540, image=self.image_cache["ml4"])
        self.canvas.create_image(300, 480, image=self.image_cache["ml5"])
        self.canvas.create_image(690, 300, image=self.image_cache["box"])

    def create_widgets(self):
        # Text
        self.canvas.create_text(500, 37.0, anchor="nw", text="Create Account",
                         font=("Inter Bold", 40, "bold"), fill="#F2829E")
        self.canvas.create_text(520, 100, anchor="nw", text="Name:",
                         font=("Inter", 16, "bold"), fill="#F2829E")
        self.canvas.create_text(520, 195, anchor="nw", text="Email:",
                         font=("Inter", 16, "bold"), fill="#F2829E")
        self.canvas.create_text(520, 288, anchor="nw", text="Username:",
                         font=("Inter", 16, "bold"), fill="#F2829E")
        self.canvas.create_text(520, 383, anchor="nw", text="Password:",
                         font=("Inter", 16, "bold"), fill="#F2829E")

        # Entries
        self.name_entry = CTkEntry(master=self, width=360, height=45,
                                   font=("Inter", 16), fg_color="transparent",
                                   text_color="#1E1E1E", border_width=1,
                                   border_color="#F2829E", placeholder_text="Enter Your Name",
                                   placeholder_text_color="#F2829E", corner_radius=0)
        self.name_entry.place(x=520, y=139)

        self.email_entry = CTkEntry(master=self, width=360, height=45,
                                    font=("Inter", 16), fg_color="transparent",
                                    text_color="#1E1E1E", border_width=1,
                                    border_color="#F2829E", placeholder_text="Enter Your Email",
                                    placeholder_text_color="#F2829E", corner_radius=0)
        self.email_entry.place(x=520, y=232)

        self.username_entry = CTkEntry(master=self, width=360, height=45,
                                       font=("Inter", 16), fg_color="transparent",
                                       text_color="#1E1E1E", border_width=1,
                                       border_color="#F2829E", placeholder_text="Choose A Username",
                                       placeholder_text_color="#F2829E", corner_radius=0)
        self.username_entry.place(x=520, y=325)

        self.password_entry = CTkEntry(master=self, width=360, height=45,
                                       font=("Inter", 16), fg_color="transparent",
                                       text_color="#1E1E1E", border_width=1,
                                       border_color="#F2829E", placeholder_text="Enter Your Password",
                                       placeholder_text_color="#F2829E", show="*", corner_radius=0)
        self.password_entry.place(x=520, y=419)

        # Buttons
        self.signup_button = CTkButton(self, cursor="hand2", width=360, height=45,
                                       text="Sign Up", font=("Inter", 18, "bold"),
                                       text_color="#FFFFFF", fg_color="#F2829E",
                                       hover_color="#F2829E", corner_radius=0,
                                       command=self.sign_up)
        self.signup_button.place(x=515, y=490)


        self.back_button = CTkButton(self, cursor="hand2", width=35, height=35,
                                     text="←", font=("Inter", 40, "bold"),
                                     text_color="#F2829A", fg_color="#FEFBE5",hover_color="#FEFBE5", corner_radius=0,
                                     command=self.go_back)
        self.back_button.place(x=420, y=40)

        # Bind Enter key để sign up
        for entry in [self.name_entry, self.email_entry, self.username_entry, self.password_entry]:
            entry.bind("<Return>", lambda event: self.sign_up())

    def sign_up(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not all([name, email, username, password]):
            messagebox.showerror("Error", "Please enter all fields")
            return

        if not is_valid_username(username):
            messagebox.showerror("Error",
                                 "Invalid username! It must contain only letters, numbers, or underscores (_), with at least 3 characters.")
            return

        if not is_valid_email(email):
            messagebox.showerror("Error", "Invalid email format! Please enter a valid email.")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long!")
            return

        self.save_user(username, password, name, email)

    def save_user(self, username, password, name, email):
        # Kiểm tra username đã tồn tại chưa
        existing_user = db.find_one("user", {"username": username})
        if existing_user:
            messagebox.showerror("Error", "Username already exists!")
            return

        # Kiểm tra email đã tồn tại chưa
        existing_email = db.find_one("user", {"email": email})
        if existing_email:
            messagebox.showerror("Error", "Email is already registered!")
            return

        user_object_id = ObjectId()

        # Tạo user mới
        new_user = {
            "_id": user_object_id,
            "userId": str(user_object_id)[-6:],
            "name": name,
            "email": email,
            "username": username,
            "password": password,
            "profile_picture": str(relative_to_assets("profile_default.jpg")),
        }

        try:
            # Lưu vào MongoDB
            db.insert_one("user", new_user)

            # Gửi email chào mừng
            self.send_welcome_email(email)
            self.go_back()

        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

    def send_welcome_email(self, user_email):
        # Giữ nguyên hàm send_welcome_email
        email_address = "thutna23416@st.uel.edu.vn"
        app_password = "wyas ubap nhqv wwap"

        msg = MIMEMultipart()
        msg["From"] = email_address
        msg["To"] = user_email
        msg["Subject"] = "Welcome to Moo_d!"

        body = """
        Hi there,

        Thank you for signing up for Moo_d Music – your new favorite place to vibe, discover, and enjoy music that matches your mood.

        We're thrilled to have you on board!
        Stay tuned for curated playlists, personalized mood tracks, and fresh beats tailored just for you.

        Let's set the Moo_d together.

        Cheers,  
        The Moo_d Team
        """
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(email_address, app_password)
                server.sendmail(email_address, user_email, msg.as_string())
        except Exception as e:
            print(f"Lỗi khi gửi email đến {user_email}: {e}")

    def go_back(self):
        """Quay lại màn hình đăng nhập"""
        self.controller.show_frame("LoginFrame")
        self.controller.destroy_frame("SignUpFrame")

    # def on_show(self):
    #     """Được gọi khi frame được hiển thị"""
    #     self.name_entry.focus_set()
    #     self.clear_entries()

    # def clear_entries(self):
    #     """Xóa nội dung trong các ô nhập liệu"""
    #     self.name_entry.delete(0, 'end')
    #     self.email_entry.delete(0, 'end')
    #     self.username_entry.delete(0, 'end')
    #     self.password_entry.delete(0, 'end')

class MoodTracker(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        self.canvas = Canvas(self, bg="#FFFFFF", height=600, width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.load_background()
        self.create_widgets()

    def load_background(self):
        """Load nền và overlay pastel."""
        # Load ảnh gốc
        bg_img = load_image("bg_mood.png", size=(1000, 600))

        # Tạo gradient overlay pastel
        from PIL import Image, ImageDraw

        # Chuyển bg_img sang PIL Image nếu chưa phải
        if hasattr(bg_img, '_PhotoImage__photo'):
            # Nếu là PhotoImage, lấy dữ liệu từ tkinter
            bg_pil = Image.open(relative_to_assets("bg_mood.png")).resize((1000, 600)).convert("RGBA")
        else:
            # Giả sử load_image trả về PIL Image
            bg_pil = bg_img.convert("RGBA")

        # Tạo gradient pastel
        gradient = Image.new("RGBA", bg_pil.size)
        draw = ImageDraw.Draw(gradient)

        for y in range(bg_pil.height):
            ratio = y / bg_pil.height
            # Màu pastel: từ #FFD4D4 (hồng nhạt) đến #E8EDC8 (xanh lá nhạt)
            r = int(0xFF * (1 - ratio) + 0xE8 * ratio)
            g = int(0xD4 * (1 - ratio) + 0xED * ratio)
            b = int(0xD4 * (1 - ratio) + 0xC8 * ratio)
            draw.line([(0, y), (bg_pil.width, y)], fill=(r, g, b, int(255 * 0.25)))

        # Kết hợp ảnh gốc với gradient
        bg_final = Image.alpha_composite(bg_pil, gradient)

        self.image_cache["mood_bg"] = ImageTk.PhotoImage(bg_final)
        self.canvas.create_image(500, 300, image=self.image_cache["mood_bg"])


    def create_widgets(self):
        """Tạo text và ảnh-nút."""
        self.canvas.create_text(
            49, 66,
            anchor="nw",
            text="Hello <username>,",
            fill="#F2829E",
            font=("Inter", 45, "bold")
        )
        self.canvas.create_text(
            49, 138,
            anchor="nw",
            text="Choose your mood and let’s get started!",
            fill="#F2829E",
            font=("Inter", 32, "bold")
        )

        moods = {
            "Happy": (61, 232, "happymood.png"),
            "Sad": (500, 232, "sadmood.png"),
            "Neutral": (61, 395, "neutralmood.png"),
            "Intense": (500, 395, "intensemood.png")
        }

        for name, (x, y, file) in moods.items():
            img = load_image(file, size=(391, 141), opacity=0.9)
            hover_img = load_image(file, size=(391, 141), opacity=1.0)
            click_img = load_image(file, size=(370, 133), opacity=1)

            self.image_cache[f"{name}_normal"] = img
            self.image_cache[f"{name}_hover"] = hover_img
            self.image_cache[f"{name}_click"] = click_img

            item = self.canvas.create_image(x + 195, y + 70, image=img, tag=name)

            # Bind các trạng thái
            self.canvas.tag_bind(name, "<Enter>", lambda e, mood=name: self.on_hover(mood))
            self.canvas.tag_bind(name, "<Leave>", lambda e, mood=name: self.on_leave(mood))
            self.canvas.tag_bind(name, "<ButtonPress-1>", lambda e, mood=name: self.on_press(mood))
            self.canvas.tag_bind(name, "<ButtonRelease-1>", lambda e, mood=name: self.on_release(mood))

    def on_hover(self, mood):
        self.canvas.itemconfig(mood, image=self.image_cache[f"{mood}_hover"])

    def on_leave(self, mood):
        self.canvas.itemconfig(mood, image=self.image_cache[f"{mood}_normal"])

    def on_press(self, mood):
        self.canvas.itemconfig(mood, image=self.image_cache[f"{mood}_click"])

    def on_release(self, mood):
        self.canvas.itemconfig(mood, image=self.image_cache[f"{mood}_hover"])
        print(f"✨ {mood} pressed!")
        self.controller.show_frame("HomeScreen")
        self.controller.destroy_frame("MoodTracker")
from FinalProject.moo_d.Recommendation_artist import recommend_for_user
import threading
import time
import tkinter
from datetime import datetime
from io import BytesIO
from tkinter import Menu, PhotoImage, Entry, Scale, Canvas, Frame, \
    messagebox, Label
from tkinter.constants import HORIZONTAL
from urllib.request import urlopen
import pymongo
import vlc
#from PIL import Image, ImageTk, ImageDraw
from PIL.Image import Resampling
import customtkinter as ctk
from FinalProject.moo_d.session import  *
from FinalProject.moo_d.functions  import *

class MainScreen(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent

        try:
            self.all_tracks = self.controller.all_tracks_data
        except AttributeError:
            print("Lỗi: HomeScreen không tìm thấy self.controller.all_tracks_data")
            self.all_tracks = []  # Gán list rỗng để tránh lỗi

        self.canvas = tkinter.Canvas(self, bg="#F7F7DC", height=600,
                                     width=1000, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # Khởi tạo songs trước rồi mới tạo buttons
        self.songs = Song(self, controller)
        self.buttons = Button(self, self.canvas, self)
        self.player = vlc.MediaPlayer()

        self.songs.set_buttons(self.buttons)
        self.buttons.set_songs(self.songs)

        self.buttons.songs = self.songs
        self.buttons.toolbar()
        self.buttons.init_progress_bar()
        self.buttons.search_music()
        self.buttons.volume()
        # self.create_home_recommendations()
        # self.load_recommended_artists()

        # MainScreen area
        self.main_area = Frame(self.canvas, bg="lightgray")
        self.profile_frame = None
        self.wrapup_frame= None
        self.current_content_frame = None  # Frame đang hiển thị


        # === KHUNG GỢI Ý TÌM KIẾM (Scrollable) ===
        self.suggestion_color = "#FDEFF2"  # Màu hồng nhạt
        self.suggestion_border_color = "#E08DA8"  # Màu viền hồng (lấy từ màu chữ)

        # 1. Container chính, cái này sẽ được .place()
        self.suggestion_container = tk.Frame(
            self,
            bg=self.suggestion_color,
            highlightthickness=1,  # <--- SỬA DÒNG NÀY
            highlightbackground=self.suggestion_border_color,  # <--- THÊM DÒNG NÀY
            highlightcolor=self.suggestion_border_color  # <--- THÊM DÒNG NÀY
        )

        # 2. Canvas để cuộn
        self.suggestion_canvas = tk.Canvas(self.suggestion_container, bg=self.suggestion_color, highlightthickness=0)

        # 3. Scrollbar
        self.suggestion_scrollbar = tk.Scrollbar(self.suggestion_container, orient="vertical",
                                                 command=self.suggestion_canvas.yview)

        # 4. Frame nội dung (nơi chứa các item)
        self.suggestions_frame = tk.Frame(self.suggestion_canvas, bg=self.suggestion_color)

        # 5. Liên kết Frame nội dung với Canvas
        self.suggestions_frame.bind(
            "<Configure>",
            lambda e: self.suggestion_canvas.configure(
                scrollregion=self.suggestion_canvas.bbox("all")
            )
        )
        self.suggestion_canvas.create_window((0, 0), window=self.suggestions_frame, anchor="nw")
        self.suggestion_canvas.configure(yscrollcommand=self.suggestion_scrollbar.set)

        # 6. Đóng gói (pack) canvas và scrollbar vào container
        self.suggestion_scrollbar.pack(side="right", fill="y")
        self.suggestion_canvas.pack(side="left", fill="both", expand=True)

        # 2. TẠO CACHE ẢNH (nếu chưa có)
        if not hasattr(self, 'image_cache'):
            self.image_cache = {}

    def show_artist_detail(self, artist_name):
        """Hiển thị artist detail - CẬP NHẬT TITLE THÀNH 'DETAIL'"""
        # Ẩn frame hiện tại
        self.hide_current_content()

        # Cập nhật title thành "Detail"
        if hasattr(self, 'buttons'):
            self.buttons.current_title = "Detail"
            self.buttons.create_title()

        # Tạo artist frame mới
        from FinalProject.moo_d.ui.ArtistDetail_UI import ArtistDetailFrame
        self.artist_frame = ArtistDetailFrame(self, self.controller, artist_name)
        self.current_content_frame = self.artist_frame
        print(f"✅ Đã mở ArtistDetail cho: {artist_name}")

    def hide_current_content(self):
        """Ẩn frame content hiện tại - CHỈ ẨN, KHÔNG DESTROY SONG FRAME"""
        if self.current_content_frame and self.current_content_frame.winfo_exists():
            try:
                # CHỈ destroy các frame custom như ArtistDetail
                if hasattr(self.current_content_frame, '_is_destroyed'):
                    self.current_content_frame.destroy()
                else:
                    self.current_content_frame.place_forget()
            except:
                pass
            self.current_content_frame = None

        # CHỈ ẨN songs canvas, KHÔNG DESTROY
        if hasattr(self, 'songs'):
            self.songs.canvas.place_forget()

    def show_default_content(self):
        """Hiển thị content mặc định - OVERRIDE để ẩn custom frames"""
        # Ẩn tất cả custom frames trước
        self.hide_all_custom_frames()

        # Hiển thị content mặc định
        if self.profile_frame:
            self.profile_frame.destroy()
            self.profile_frame = None
        if self.wrapup_frame:
            self.wrapup_frame.destroy()
            self.wrapup_frame = None
        self.main_area.place_forget()

        # Hiển thị songs content
        if hasattr(self, 'songs'):
            self.songs.canvas.place(x=105, y=90)
            self.songs.fixed_canvas.place(x=50, y=525)

    # def show_default_content(self):
    #     """Hiển thị content mặc định"""
    #     if self.profile_frame:
    #         self.profile_frame.destroy()
    #         self.profile_frame = None
    #     if self.wrapup_frame:
    #         self.wrapup_frame.destroy()
    #         self.wrapup_frame = None
    #     self.main_area.place_forget()

    def open_profile(self):
        """Mở ProfileFrame như frame con, chừa toolbar"""
        self.songs.fixed_canvas.place_forget()
        self.main_area.place(x=50, y=0, width=950, height=600)
        if self.profile_frame is None:
            self.profile_frame = ProfileFrame(parent=self.main_area, controller=self.controller)
            self.profile_frame.place(x=0, y=0, width=950, height=600)
        else:
            self.profile_frame.lift()

    def open_wrapup(self):
        """Hiển thị frame WrapUp (full màn hình, đè lên
        HomeScreen)"""
        if hasattr(self, "sleeptimer_frame") and self.sleeptimer_frame.winfo_ismapped():
            self.sleeptimer_frame.place_forget()
        try:
            if not hasattr(self, "wrapup_frame") or self.wrapup_frame is None:
                from FinalProject.moo_d.ui.WrapUp_UI import WrapUpFrame
                self.wrapup_frame = WrapUpFrame(parent=self, controller=self.controller)
                self.wrapup_frame.place(x=0, y=0, relwidth=1, relheight=1)
                self.wrapup_frame.lift()
                print("📊 WrapUpFrame created.")
            else:
                if self.wrapup_frame.winfo_ismapped():
                    self.wrapup_frame.place_forget()
                    print("📉 WrapUpFrame hidden.")
                else:
                    self.wrapup_frame.place(x=0, y=0, relwidth=1, relheight=1)
                    self.wrapup_frame.lift()
                    print("📈 WrapUpFrame shown again.")
        except Exception as e:
            import traceback
            print("❌ Lỗi khi mở WrapUpFrame:", e)
            traceback.print_exc()

    def open_sleeptimer(self):
        """Hiển thị popup SleepTimer (hiển thị đè trên HomeScreen, không bị che)"""
        try:
            if not hasattr(self, "sleeptimer_frame") or self.sleeptimer_frame is None:
                from FinalProject.moo_d.ui.SleepTimer_UI import SleeptimerFrame
                # Dùng parent = self để đè lên toàn HomeScreen
                self.sleeptimer_frame = SleeptimerFrame(parent=self, controller=self.controller)
                # đặt vị trí giữa góc phải, nổi rõ
                self.sleeptimer_frame.place(x=650, y=290, width=300, height=200)
                self.sleeptimer_frame.lift()  # 🔝 đưa lên trên cùng
                print("🩵 SleepTimerFrame created.")
            else:
                if self.sleeptimer_frame.winfo_ismapped():
                    self.sleeptimer_frame.place_forget()
                    print("🩶 SleepTimerFrame hidden.")
                else:
                    self.sleeptimer_frame.place(x=650, y=290, width=300, height=200)
                    self.sleeptimer_frame.lift()
                    print("🩵 SleepTimerFrame shown again.")
        except Exception as e:
            import traceback
            print("❌ Lỗi khi mở SleepTimer:", e)
            traceback.print_exc()

    def hide_all_custom_frames(self):
        """Ẩn tất cả custom frames (ArtistDetail, etc.)"""
        if hasattr(self, '_active_frames'):
            for frame in self._active_frames[:]:  # Copy list để tránh modification during iteration
                try:
                    if hasattr(frame, 'hide'):
                        frame.hide()
                    else:
                        frame.place_forget()
                except:
                    continue
    # def create_home_recommendations(self):
    #     song_canvas = self.parent.songs.canvas
    #     self.recommendation_texts = {
    #         "today": song_canvas.create_text(
    #             0, 0, anchor="nw",
    #             text="Recommended for today",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #         "top chart": song_canvas.create_text(
    #             0, 251, anchor="nw",
    #             text="Monthly chart ",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #         "artist": song_canvas.create_text(
    #             0, 502, anchor="nw",
    #             text="Recommended artist",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #         "genres": song_canvas.create_text(
    #             0, 753, anchor="nw",
    #             text="Recommended genres",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #     }
    #
    #     # ✅ Gọi hiển thị danh sách nghệ sĩ sau khi vẽ label
    #     self.load_recommended_artists(song_canvas)
    #
    # def create_home_recommendations(self):
    #     # Lỗi cũ: self.parent.songs.canvas có thể sai
    #     # nên dùng self.songs.canvas
    #     try:
    #         song_canvas = self.songs.canvas
    #     except AttributeError:
    #         print("Lỗi: không tìm thấy self.songs.canvas")
    #         return
    #
    #     self.recommendation_texts = {
    #         "today": song_canvas.create_text(
    #             0, 0, anchor="nw",
    #             text="Recommended for today",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #         "top chart": song_canvas.create_text(
    #             0, 251, anchor="nw",
    #             text="Monthly chart ",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #         # === ĐÃ XÓA PHẦN ARTIST Ở ĐÂY ===
    #
    #         "genres": song_canvas.create_text(
    #             0, 753, anchor="nw",  # <-- CHÚ Ý: y=753 có thể cần đổi
    #             text="Recommended genres",
    #             fill="#89A34E", font=("Coiny Regular", 24)
    #         ),
    #     }

        # === ĐÃ XÓA LỆNH GỌI self.load_recommended_artists Ở ĐÂY ===
    # # 🧩 Thêm hàm này ngay DƯỚI class, trong cùng file
    # def load_recommended_artists(self):
    #     """Hiển thị danh sách Recommended Artists lên canvas."""
    #     from FinalProject.moo_d.Recommendation_artist import recommend_for_user
    #     from FinalProject.moo_d.Connection.connector import db  # Import db từ connector
    #     import FinalProject.moo_d.session as session
    #     import requests
    #     from io import BytesIO
    #     from PIL import Image, ImageTk, ImageDraw
    #
    #     song_canvas = self.songs.canvas
    #
    #     def make_circle(img, size=(50, 50)):
    #         img = img.resize(size).convert("RGBA")
    #         mask = Image.new("L", size, 0)
    #         draw = ImageDraw.Draw(mask)
    #         draw.ellipse((0, 0, size[0], size[1]), fill=255)
    #         img.putalpha(mask)
    #         return img
    #
    #     user_id = session.current_user.get("userId")
    #     recs = recommend_for_user(user_id)
    #
    #     if not hasattr(self, "artist_images_cache"):
    #         self.artist_images_cache = []
    #
    #     start_x = 40
    #     start_y = 540
    #
    #     if not recs:
    #         song_canvas.create_text(
    #             start_x, start_y, text="(No recommendations found 🥲)",
    #             fill="#A98467", font=("Inter", 14), anchor="w"
    #         )
    #         return
    #
    #     for i, r in enumerate(recs):
    #         artist = r["artist"]
    #         tag = r["type"]
    #
    #         # ✅ SỬA: Dùng db.find_one() thay vì db.tracks.find_one()
    #         track = db.find_one("tracks", {"artistName": artist})
    #         img_url = track.get("artworkUrl100") if track else None
    #
    #         photo = None
    #         if img_url:
    #             try:
    #                 resp = requests.get(img_url, timeout=3)
    #                 img = Image.open(BytesIO(resp.content))
    #                 img = make_circle(img)
    #                 photo = ImageTk.PhotoImage(img)
    #             except Exception as e:
    #                 print(f"⚠️ Lỗi tải ảnh {artist}: {e}")
    #
    #         if photo is None:
    #             try:
    #                 placeholder = Image.open("assets/artist_default.png")
    #                 placeholder = make_circle(placeholder)
    #                 photo = ImageTk.PhotoImage(placeholder)
    #             except:
    #                 # Nếu không có file placeholder, tạo ảnh trống
    #                 placeholder = Image.new("RGBA", (50, 50), (200, 200, 200, 255))
    #                 placeholder = make_circle(placeholder)
    #                 photo = ImageTk.PhotoImage(placeholder)
    #
    #         self.artist_images_cache.append(photo)
    #
    #         song_canvas.create_image(start_x, start_y + i * 70, image=photo, anchor="w")
    #         song_canvas.create_text(
    #             start_x + 60, start_y + i * 70 + 5,
    #             text=f"{tag} — {artist}",
    #             fill="#89A34E", font=("Inter", 15), anchor="w"
    #         )
        # === DÁN ĐOẠN CODE NÀY VÀO LỚP MainScreen ===
        # (Nó sẽ THAY THẾ hàm load_recommended_artists cũ của bạn)

    # def load_recommended_artists(self):
    #     """
    #     Tạo khu vực "Recommended Artist" có thể cuộn ngang
    #     sử dụng customtkinter.
    #     """
    #
    #     # 1. Sửa lỗi ModuleNotFoundError
    #     # Đảm bảo file recommendation_artist.py nằm cùng cấp với app.py/main.py
    #     try:
    #         from FinalProject.moo_d.Recommendation_artist  import recommend_for_user, db
    #         import FinalProject.moo_d.session as session
    #     except ModuleNotFoundError:
    #         print("❌ LỖI: Không tìm thấy file 'recommendation_artist.py'.")
    #         return
    #     except ImportError as e:
    #         print(f"❌ LỖI IMPORT: {e}")
    #         return
    #
    #     import requests
    #     from io import BytesIO
    #     from PIL import Image, ImageDraw, ImageTk
    #
    #     # 2. Tạo tiêu đề "Recommended Artist"
    #     # Chúng ta đặt nó lên `self` (là MainScreen),
    #     # dùng tọa độ y=502 từ hàm create_home_recommendations cũ của bạn
    #     title_label = ctk.CTkLabel(
    #         self,  # Đặt lên MainScreen
    #         text="Recommended Artist",
    #         font=ctk.CTkFont(family="Inter Bold", size=24),
    #         text_color="#89A34E"  # Giữ màu của bạn
    #     )
    #     # Đặt tiêu đề.
    #     # (Bạn cần điều chỉnh `x`, `y` cho khớp với layout của bạn)
    #     title_label.place(x=60, y=502)  # Giả sử x=60
    #
    #     # 3. Tạo một Khung có thể cuộn ngang
    #     self.artist_scroll_frame = ctk.CTkScrollableFrame(
    #         self,  # Đặt lên MainScreen
    #         orientation="horizontal",  # <-- CUỘN NGANG
    #         fg_color="transparent",  # Nền trong suốt
    #         height=160,
    #         width=900# Chiều cao khoảng 150-170
    #     )
    #
    #     # Đặt khung cuộn này ngay dưới tiêu đề
    #     # (Điều chỉnh x, y, width cho khớp)
    #     self.artist_scroll_frame.place(x=50, y=540)
    #
    #     # 4. Lấy dữ liệu
    #     user_id = session.current_user.get("userId")
    #     recs = recommend_for_user(user_id)  # Hàm này từ file .py của bạn
    #
    #     if not hasattr(self, "artist_images_cache"):
    #         self.artist_images_cache = {}  # Dùng dict để lưu ảnh
    #
    #     if not recs:
    #         no_recs_label = ctk.CTkLabel(self.artist_scroll_frame,
    #                                      text="(No recommendations found 🥲)",
    #                                      font=ctk.CTkFont(size=14),
    #                                      text_color="#A98467")
    #         no_recs_label.pack(side="left", padx=10)
    #         return
    #
    #     # 5. Lặp qua các nghệ sĩ và tạo item
    #     for i, r in enumerate(recs):
    #         artist_name = r["artist"]
    #
    #         # Lấy URL ảnh (giống code cũ của bạn)
    #         track = db["tracks"].find_one({"artistName": artist_name}, {"artworkUrl100": 1})
    #         img_url = track.get("artworkUrl100") if track else None
    #
    #         # Tạo một item nghệ sĩ và pack vào khung cuộn
    #         artist_item_frame = self.create_artist_item(
    #             parent=self.artist_scroll_frame,
    #             artist_name=artist_name,
    #             image_url=img_url,
    #             item_id=f"artist_{i}"
    #         )
    #         artist_item_frame.grid(row=0, column=i, padx=15, pady=10)
    #
    # def create_artist_item(self, parent, artist_name, image_url, item_id):
    #     """
    #     Tạo một widget cho 1 nghệ sĩ (ảnh tròn + tên)
    #     """
    #     from PIL import Image, ImageDraw, ImageTk
    #     import requests
    #     from io import BytesIO
    #
    #     # Hàm helper tạo ảnh tròn (lấy từ code cũ của bạn)
    #     def make_circle(img, size=(100, 100)):
    #         img = img.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    #         mask = Image.new("L", size, 0)
    #         draw = ImageDraw.Draw(mask)
    #         draw.ellipse((0, 0, size[0], size[1]), fill=255)
    #         img.putalpha(mask)
    #         return img
    #
    #     # Khung chứa cho 1 nghệ sĩ
    #     item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    #
    #     # --- Tải Ảnh ---
    #     photo = None
    #     if image_url in self.artist_images_cache:
    #         photo = self.artist_images_cache[image_url]
    #     else:
    #         try:
    #             resp = requests.get(image_url, timeout=3)
    #             pil_image = Image.open(BytesIO(resp.content))
    #             pil_image_circle = make_circle(pil_image)
    #         except Exception as e:
    #             print(f"⚠️ Lỗi tải ảnh {artist_name}: {e}")
    #             # Dùng ảnh default
    #             pil_image = Image.open(relative_to_assets("artist_default.png"))
    #             pil_image_circle = make_circle(pil_image)
    #
    #         photo = ctk.CTkImage(light_image=pil_image_circle, size=(100, 100))
    #         self.artist_images_cache[image_url] = photo  # Lưu vào cache
    #
    #     # 1. Widget Ảnh (dùng CTkLabel)
    #     image_label = ctk.CTkLabel(
    #         item_frame,
    #         image=photo,
    #         text=""
    #     )
    #     image_label.pack(pady=(0, 5))
    #
    #     # 2. Widget Tên
    #     name_label = ctk.CTkLabel(
    #         item_frame,
    #         text=artist_name,
    #         font=ctk.CTkFont(size=13),
    #         text_color="#FFFFFF"  # <-- Đổi màu chữ cho phù hợp (trong ảnh là màu trắng)
    #     )
    #     name_label.pack()
    #
    #     return item_frame

    def logout(self):
        """Xử lý logout từ HomeScreen"""
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            self.controller.logout()

        # (Bên trong class MainScreen, dán 5 hàm này vào dưới cùng)

    # (Bên trong class MainScreen, file Login_UI.py)

    # (Bên trong class MainScreen, file Login_UI.py)

    def show_search_suggestions(self):
        """Hàm chính: Lọc và hiển thị gợi ý (Cải tiến với tính điểm)"""
        query = self.buttons.search_entry.get().lower()

        # 1. Xóa gợi ý cũ
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        # 2. Nếu query rỗng, ẩn Container và thoát
        if not query:
            self.suggestion_container.place_forget()
            return

        # =================================================
        # === LOGIC TÌM KIẾM MỚI (VỚI TÍNH ĐIỂM) ===
        # =================================================
        query_words = query.split()
        results = []  # Sẽ lưu (score, track)

        # 3. Lặp qua TẤT CẢ các bài hát để chấm điểm (có thể hơi chậm)
        for t in self.all_tracks:
            track_name = t.get("trackName", "").lower()
            artist_name = t.get("artistName", "").lower()

            # Chỉ kiểm tra nếu bài hát có tên
            if not track_name:
                continue

            search_string = track_name + " " + artist_name
            score = 0

            # 3.1. Kiểm tra điều kiện "AND" (phải chứa tất cả các từ)
            if all(word in search_string for word in query_words):

                # ĐIỂM CƠ BẢN
                score += 10  # +10 điểm nếu khớp tất cả các từ

                # 3.2. ĐIỂM THƯỞNG (Rất quan trọng)

                # Thưởng nặng nếu TÊN BÀI HÁT bắt đầu bằng query
                if track_name.startswith(query):
                    score += 50

                # Thưởng vừa nếu TÊN NGHỆ SĨ bắt đầu bằng query
                elif artist_name.startswith(query):
                    score += 30

                # Thưởng nhẹ cho mỗi từ riêng lẻ
                for word in query_words:
                    if track_name.startswith(word):
                        score += 5
                    if artist_name.startswith(word):
                        score += 2

            # 3.3. Nếu có điểm, thêm vào danh sách
            if score > 0:
                results.append((score, t))

        # 4. Sắp xếp tất cả kết quả theo điểm (cao nhất trước)
        results.sort(key=lambda item: item[0], reverse=True)

        # 5. Lấy 20 bài hát có điểm cao nhất
        top_results = [track for score, track in results[:20]]
        # ===============================================
        # === KẾT THÚC LOGIC MỚI ===
        # ===============================================

        # 6. Nếu không có kết quả, ẩn Container
        if not top_results:
            self.suggestion_container.place_forget()
            return

        # 7. Tạo các hàng gợi ý mới
        for song in top_results:
            self.create_suggestion_item(song)

        # 8. Cập nhật scrollregion (cho khung cuộn)
        self.suggestions_frame.update_idletasks()
        self.suggestion_canvas.configure(scrollregion=self.suggestion_canvas.bbox("all"))

        # 9. Hiển thị Container (UI màu hồng)
        self.suggestion_container.place(
            x=661,  # Vị trí x cho khung rộng 300
            y=57,  # Vị trí y
            width=300,  # Chiều rộng mới
            height=180  # Chiều cao cố định
        )
        self.suggestion_container.lift()
    def create_suggestion_item(self, song):
        """Tạo 1 hàng gợi ý (ảnh + text) giống Spotify"""

        # Màu hồng nhạt (lấy từ self)
        pink_bg = self.suggestion_color

        item_frame = tk.Frame(self.suggestions_frame, bg=pink_bg)
        item_frame.pack(fill="x", expand=True, padx=2, pady=2)

        img_label = tk.Label(item_frame, bg=pink_bg, width=40, height=40)
        img_label.pack(side="left", padx=5)

        artwork_url = song.get("artworkUrl100", "").replace("100x100", "40x40")
        if artwork_url in self.image_cache:
            img_label.config(image=self.image_cache[artwork_url])
        elif artwork_url:
            threading.Thread(
                target=self.load_image_async,
                args=(artwork_url, img_label, (40, 40)),
                daemon=True
            ).start()
        else:
            img_label.config(text="?")

        text_frame = tk.Frame(item_frame, bg=pink_bg)
        text_frame.pack(side="left", fill="x", expand=True, anchor="w")

        # Màu hồng đậm cho chữ
        pink_text_dark = "#D66D8B"
        pink_text_light = "#E08DA8"

        track_label = tk.Label(text_frame, text=song.get("trackName", "N/A"),
                               bg=pink_bg, fg=pink_text_dark,  # Đổi màu chữ
                               anchor="w", font=("Arial", 10, "bold"))
        track_label.pack(fill="x")

        artist_label = tk.Label(text_frame, text=song.get("artistName", "N/A"),
                                bg=pink_bg, fg=pink_text_light,  # Đổi màu chữ
                                anchor="w", font=("Arial", 8))
        artist_label.pack(fill="x")

        widgets = [item_frame, img_label, text_frame, track_label, artist_label]
        for widget in widgets:
            widget.bind("<Button-1>", lambda e, s=song: self.play_suggestion(s))
        # (Hàm này cũng nằm bên trong class MainScreen)

    def load_image_async(self, url, label, size):
        """Tải ảnh từ URL trong Thread, sau đó cập nhật UI"""
        try:
            raw_data = urlopen(url).read()
            img = Image.open(BytesIO(raw_data))
            img = img.resize(size, Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.image_cache[url] = photo

            # SỬA LỖI: BỌC LẠI KHỐI TRY
            # Để tránh lỗi khi label đã bị hủy
            try:
                label.config(image=photo)
                label.image = photo  # Giữ tham chiếu
            except tk.TclError:
                pass  # Bỏ qua nếu label đã bị hủy

        except Exception as e:
            print(f"Lỗi tải ảnh: {e}")

            # SỬA LỖI: BỌC LẠI KHỐI EXCEPT
            # Để tránh lỗi khi label đã bị hủy
            try:
                label.config(text="?")
            except tk.TclError:
                pass  # Bỏ qua nếu label đã bị hủy

    # (Bên trong class MainScreen, file Login_UI.py)

    def play_suggestion(self, song):
        """Hàm được gọi khi click vào 1 gợi ý"""
        print(f"Chơi bài hát từ gợi ý: {song.get('trackName')}")

        # 1. Gọi on_song_click để VẼ thanh nhạc VÀ phát nhạc
        # (Đây là hàm nằm trong self.songs)
        self.songs.on_song_click(song.get('trackId'))

        # 2. Ẩn khung gợi ý (container màu hồng)
        self.suggestion_container.place_forget()

        # 3. Xóa chữ trong thanh search
        self.buttons.search_entry.delete(0, 'end')

    # (Bên trong file Login_UI.py)

        # (Hàm này phải nằm bên trong class MainScreen)

    def play_song(self, song):
        try:
            song_url = song.get("previewUrl") or song.get("filePath")
            if not song_url:
                print("⚠️ Không có URL hoặc filePath hợp lệ để phát.")
                return

            # SỬA LỖI: Thêm 'self.controller.'
            # Giờ đây self.controller (là App) đã có 'instance' và 'player'
            media = self.controller.instance.media_new(song_url)
            self.controller.player.set_media(media)
            self.controller.player.play()

            # (Các thuộc tính này của MainScreen)
            self.current_song = song
            self.is_playing = True
            self.is_paused = False
            self.start_time = time.time()
            self.total_time = song.get("trackTimeMillis", 0) / 1000

            # SỬA LỖI: Dùng 'self.buttons' (không phải 'self.parent.buttons')
            # Vì 'buttons' là thuộc tính của MainScreen (self)
            self.songs.fixed_canvas.itemconfig(
                self.buttons.buttons["play"],  # Lấy nút 'play' từ self.buttons
                image=self.buttons.image_cache["pause"]  # Lấy ảnh 'pause' từ self.buttons
            )
            tk.Misc.tkraise(self.songs.fixed_canvas)

            print(f"🎶 Playing now: {song.get('trackName')} - {song.get('artistName')}")

        except Exception as e:
                print(f"❌ Lỗi khi phát nhạc: {e}")

    # ... (các hàm khác của MainScreen như on_song_click, show_search_suggestions...)

    def hide_all_custom_frames(self):
        """Ẩn tất cả custom frames (ArtistDetail, etc.)"""
        if hasattr(self, '_active_frames'):
            for frame in self._active_frames[:]:  # Copy list để tránh modification during iteration
                try:
                    if hasattr(frame, 'hide') and frame.winfo_exists():
                        frame.hide()
                    elif frame.winfo_exists():
                        frame.place_forget()
                except:
                    continue

class SongListManager:
    """Quản lý và hiển thị danh sách bài hát cho history, owned_songs, liked_songs"""

    def __init__(self, parent, controller, list_type):
        self.parent = parent  # MainScreen instance
        self.controller = controller
        self.list_type = list_type  # "history", "owned_songs", "liked_songs"

        self.song_list = []
        self.image_cache = {}

        # Tạo canvas cho song
        self.canvas = Canvas(self.parent, width=1000, height=408,
                             bg="#F7F7DC", bd=0, highlightthickness=0)
        self.canvas.place(x=103, y=90)
        self.canvas.place_forget()

        self.frame = Frame(self.canvas, bg="#F7F7DC")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.frame,
                                                       anchor="nw", width=844)

        # Bind sự kiện cuộn
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self.scroll_with_mouse))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def load_from_db(self, collection_name, user_field="userId", sort_field=None):
        """Tải dữ liệu từ MongoDB collection và tự động hiển thị"""
        db = self.controller.get_db()
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return

        user_id = session.current_user.get("userId")
        try:
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
                    "artworkUrl100": doc.get("artworkUrl100", "assets/default.png")
                })

            self.update_display()
            self.show()
            print(f"✅ Đã tải {len(self.song_list)} bài hát từ {collection_name}")

        except Exception as e:
            print(f"❌ Lỗi khi tải từ {collection_name}: {e}")

    def update_display(self):
        """Cập nhật hiển thị"""
        for widget in self.frame.winfo_children():
            widget.destroy()

        for song in self.song_list:
            self.create_song_item(song)

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

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

            img_label.after(0, update_label) # type: ignore

        threading.Thread(target=load_image_song, daemon=True).start()

        text_frame = Frame(frame, bg="#F7F7DC")
        text_frame.pack(side="left", fill="x", expand=True)

        text_color = "#89A34E"
        title_label = Label(text_frame, text=song.get("trackName", "Unknown"),
                            font=("Coiny Regular", 18), fg=text_color, bg="#F7F7DC")
        title_label.pack(anchor="w")
        artist_label = Label(text_frame, text=song.get("artistName", "Unknown Artist"),
                             font=("Newsreader Regular", 14), fg=text_color, bg="#F7F7DC")
        artist_label.pack(anchor="w")

        track_id = song.get("trackId")
        for widget in (frame, img_label, title_label, artist_label):
            widget.bind("<Button-1>", lambda e, tid=track_id: self.parent.songs.on_song_click(tid))

    def show(self):
        """Hiển thị canvas"""
        self.canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def hide(self):
        """Ẩn canvas"""
        self.canvas.place_forget()

    def scroll_with_mouse(self, event):
        """Cuộn bằng chuột"""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

class Button:
    def __init__(self, parent, canvas, song):
        super().__init__()
        self.parent = parent  # MainScreen instance
        self.canvas = canvas
        self.main_screen = song
        self.songs = song
        self.repeat_mode = 0
        self.volume_slider = None
        self.current_volume = 100
        self.is_playing = False
        self.is_paused = False
        self.is_rotating = False
        self.play_button = None
        self.search_entry = None
        self.volume_icon = None
        self.profile_window = None
        self.image_ids = {}
        self.image_cache = {}
        self.buttons = {}
        self.love_state = "love(0)"
        self.load_icons()
        self.parent.buttons = self
        self.progress_bg = None
        self.progress_fill = None
        self.progress_knob = None
        self.current_time_text = None
        self.total_time_text = None
        self.title_text = None
        self.current_title = "Home"
        self.create_title()
        self.create_home_recommendations()
        self.recommendation_texts = None
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

        self.canvas.tag_bind(self.image_ids["logo 2"], "<Button-1>", lambda e: self.toggle_view("profile"))
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
        else:
            self.canvas.itemconfig(self.title_text, text=self.current_title)

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

    # def toggle_view(self, view_type):
    #     """Chuyển đổi giữa danh sách bài hát, lịch sử nghe và thư viện"""
    #     self.hide_all_views()
    #     self.parent.show_default_content()
    #
    #     if view_type == "profile":
    #         self.parent.open_profile()
    #     elif view_type == "home":
    #         self.show_songs_list()
    #         self.current_title = "Home"
    #     elif view_type == "history":
    #         self.show_history()
    #         self.current_title = "History"
    #     elif view_type == "library":
    #         self.show_library()
    #         self.current_title = "Library"
    #     elif view_type == "report":
    #         self.parent.open_wrapup()
    #     self.create_title()
    def toggle_view(self, view_type):
        """Chuyển đổi giữa các view"""

        # Ẩn artist frame nếu có
        if hasattr(self.parent, 'artist_frame') and self.parent.artist_frame:
            try:
                self.parent.artist_frame.destroy()
                self.parent.artist_frame = None
            except:
                pass

        # Ẩn các frame khác
        self.hide_all_views()

        # Hiển thị content tương ứng
        if view_type == "profile":
            self.parent.open_profile()
            self.current_title = "Profile"
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
            self.current_title = "Report"
        elif view_type == "detail":  # THÊM CASE NÀY CHO ARTIST DETAIL
            self.current_title = "Detail"

        self.create_title()

    def hide_all_views(self):
        """Ẩn tất cả các view"""
        self.hide_songs_list()
        self.hide_library()
        # Ẩn các view khác thông qua Song class
        self.parent.songs.hide_all_views()

    def show_songs_list(self):
        """Hiển thị danh sách bài hát"""
        self.parent.songs.canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def hide_songs_list(self):
        """Ẩn danh sách bài hát"""
        self.parent.songs.canvas.place_forget()

    def show_history(self):
        """Hiển thị danh sách lịch sử"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_history_from_db()

    def show_library(self):
        """Hiển thị thư viện"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_playlists_from_db()
        self.parent.songs.update_library_display()
        self.parent.songs.library_canvas.place(x=103, y=90)
        self.parent.songs.fixed_canvas.place(x=50, y=522)

    def hide_library(self):
        """Ẩn thư viện"""
        self.parent.songs.library_canvas.place_forget()

    def show_owned_songs(self):
        """Hiển thị bài hát sở hữu"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_owned_songs_from_db()

    def show_liked_songs(self):
        """Hiển thị bài hát yêu thích"""
        if not session.current_user:
            print("❌ Lỗi: Chưa có user đăng nhập")
            return
        self.parent.songs.load_liked_songs_from_db()

    def init_progress_bar(self):
        """Tạo thanh tiến trình"""
        c = self.parent.songs.fixed_canvas
        elements = {
            "progress_bg": ("rectangle", (308, 55, 750, 62), "#D9D9D9"),
            "progress_fill": ("rectangle", (308, 55, 318, 62), "#FFFFFF"),
            "progress_knob": ("oval", (308, 53, 320, 65), "#FFFFFF"),
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

        self.love_state = "love(1)"
        for key, (x, y) in button_positions.items():
            image = self.image_cache[self.love_state] if key == "love" else self.image_cache[key]
            self.buttons[key] = c.create_image(x, y, image=image)

        c = self.parent.songs.fixed_canvas
        c.tag_bind(
            self.buttons["sleeptimer"],
            "<Button-1>",
            lambda e: (print("🩵 SleepTimer icon clicked!"), self.parent.open_sleeptimer())
        )

    def toggle_play(self, event=None):
        """Chỉ đổi icon giữa Play ↔ Pause, không điều khiển nhạc"""
        if self.is_playing:
            self.is_playing = False
            self.canvas.itemconfig(self.buttons["play"], image=self.image_cache["play"])
        else:
            self.is_playing = True
            self.canvas.itemconfig(self.buttons["play"], image=self.image_cache["pause"])

    @staticmethod
    def create_rounded_rectangle(width, height, radius, color):
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((0, 0, width, height), radius=radius,
                               fill=color)
        return ImageTk.PhotoImage(img)

    def search_music(self):
        self.image_cache["search_box"] = self.create_rounded_rectangle(235, 30, 15, "#F586A3")
        self.canvas.create_image(851, 42, image=self.image_cache["search_box"])
        self.image_cache["search"] = PhotoImage(file=relative_to_assets("search.png"))
        self.canvas.create_image(755, 42, image=self.image_cache["search"])
        self.search_entry = Entry(self.canvas, font=("Newsreader Regular", 14),
                                  fg="#000000", bg="#F586A3", bd=0)
        self.search_entry.place(x=773, y=30, width=188, height=27)
        # 1. Bind khi gõ phím (KeyRelease)
        self.search_entry.bind("<KeyRelease>", lambda event: self.main_screen.show_search_suggestions())

        # 2. Bind khi click ra ngoài (FocusOut)
        self.search_entry.bind("<FocusOut>", lambda e: self.main_screen.hide_suggestions_on_focus_out())

        # 3. Bind khi click vào (FocusIn)
        self.search_entry.bind("<FocusIn>", lambda e: self.main_screen.show_search_suggestions())

    def volume(self):
        c = self.parent.songs.fixed_canvas
        self.image_cache["volume"] = PhotoImage(file=relative_to_assets(
            "medium-volume.png"))
        self.volume_icon = c.create_image(820, 55,
                                          image=self.image_cache["volume"])
        c.tag_bind(self.volume_icon, "<Button-1>", self.toggle_volume_slider)

    def toggle_volume_slider(self, event=None):
        """Hiện hoặc ẩn thanh volume khi nhấn vào icon"""
        if self.volume_slider and self.volume_slider.winfo_ismapped():
            self.volume_slider.place_forget()
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
        self.volume_slider.place(x=890, y=555)

    def set_volume(self, value):
        """Cập nhật âm lượng của trình phát nhạc"""
        self.current_volume = int(value)
        if hasattr(self.parent, "player") and self.parent.player is not None:
            self.parent.player.audio_set_volume(self.current_volume)


class Song:
    def __init__(self, parent, controller, button=None):
        super().__init__()
        self.controller = controller
        self.parent = parent  # MainScreen instance
        self.button = button
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.songs_list = []
        self.song_data = {}
        self.history_list = []
        self.playlist_count = 0
        self.playlists = []
        self.image_cache = {}

        self.current_index = -1
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.repeat_mode = 0
        self.repeat_once_flag = False

        self.current_song_image = None
        self.clip_canvas = None
        self.buttons = None

        self.current_time = 0
        self.total_time = 0
        self.paused_time = 0
        self.start_time = 0

        # Khởi tạo SongListManager cho các danh sách - truyền self.parent (MainScreen)
        self.history_manager = SongListManager(self.parent, controller, "history")
        self.owned_songs_manager = SongListManager(self.parent, controller, "owned_songs")
        self.liked_songs_manager = SongListManager(self.parent, controller, "liked_songs")

        # Canvas chính cho home
        self.canvas = Canvas(self.parent, width=1000, height=408, bg="#F7F7DC",
                             bd=0, highlightthickness=0)
        self.canvas.place(x=103, y=90)

        self.canvas.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<MouseWheel>", self.scroll_with_mouse)

        # Canvas thư viện
        self.library_canvas = Canvas(self.parent, width=1000, height=408,
                                     bg="#F7F7DC", bd=0, highlightthickness=0)
        self.library_canvas.place(x=103, y=90)
        self.library_canvas.place_forget()
        self.library_frame = Frame(self.library_canvas, bg="#F7F7DC")
        self.library_canvas_window = self.library_canvas.create_window((0, 0), window=self.library_frame,
                                                                       anchor="nw", width=844)

        self.library_canvas.bind("<Enter>",
                                 lambda e: self.library_canvas.bind_all(
                                     "<MouseWheel>", self.scroll_with_mouse))
        self.library_canvas.bind("<Leave>",
                                 lambda e: self.library_canvas.unbind_all(
                                     "<MouseWheel>"))

        self.current_index = -1
        self.songs_list = []
        self.fixed_canvas = Canvas(self.parent, bg="#F7F7DC", height=78,
                                   width=950, bd=0, highlightthickness=0)
        self.fixed_canvas.place(x=50, y=522)

        self.artist_recommendations_cache = None
        self.artist_items = []
        self.artist_images_cache = {}

        # Tạo artist recommendations sau khi khởi tạo
        self.parent.after(500, self.create_artist_recommendations)

    def create_artist_recommendations(self):
        """Tạo khu vực hiển thị nghệ sĩ được gợi ý - VỊ TRÍ TRÁI"""
        try:
            # TRÁNH TRÙNG LẶP
            if hasattr(self, 'artist_container') and self.artist_container and self.artist_container.winfo_exists():
                return

            print("🔄 Đang tạo artist recommendations...")

            # Tạo container chính
            self.artist_container = Frame(self.canvas, bg="#F7F7DC")

            # 🎯 VỊ TRÍ TRÁI HƠN - GIẢM x XUỐNG
            self.artist_canvas_id = self.canvas.create_window(
                0, 560,  # 🆕 x=30 (trái hơn), y=540 (sau text "Recommended Artists")
                window=self.artist_container,
                anchor="nw",
                width=900,  # 🆕 Tăng width lên để chiếm nhiều không gian hơn
                height=200
            )

            # Canvas để cuộn ngang
            self.artist_canvas = Canvas(
                self.artist_container,
                bg="#F7F7DC",
                height=180,
                width=900,  # 🆕 Đồng bộ width
                highlightthickness=0
            )
            self.artist_canvas.pack(fill="both", expand=True)

            # Frame chứa các artist item
            self.artist_frame = Frame(self.artist_canvas, bg="#F7F7DC")
            self.artist_canvas.create_window((0, 0), window=self.artist_frame, anchor="nw")

            # MOUSE WHEEL CHO SCROLL NGANG
            def on_artist_mousewheel(event):
                """Scroll ngang khi dùng mouse wheel trên artist area"""
                self.artist_canvas.xview_scroll(-1 * (event.delta // 120), "units")

            def on_artist_enter(event):
                """Khi chuột vào artist area - bind mouse wheel để scroll ngang"""
                self.artist_canvas.bind_all("<MouseWheel>", on_artist_mousewheel)

            def on_artist_leave(event):
                """Khi chuột rời artist area - unbind để trả lại scroll dọc"""
                self.artist_canvas.unbind_all("<MouseWheel>")

            # Bind events cho scroll bằng mouse wheel
            self.artist_canvas.bind("<Enter>", on_artist_enter)
            self.artist_canvas.bind("<Leave>", on_artist_leave)
            self.artist_frame.bind("<Enter>", on_artist_enter)
            self.artist_frame.bind("<Leave>", on_artist_leave)

            # Bind drag scroll (kéo chuột để scroll)
            # self.artist_canvas.bind("<ButtonPress-1>", self.start_artist_drag)
            # self.artist_canvas.bind("<B1-Motion>", self.do_artist_drag)
            # self.artist_canvas.bind("<ButtonRelease-1>", self.stop_artist_drag)

            # Tải dữ liệu
            self.load_recommended_artists()

            print("✅ Artist recommendations đã được tạo thành công")

        except Exception as e:
            print(f"❌ Lỗi khi tạo artist recommendations: {e}")

            # MOUSE WHEEL CHO SCROLL NGANG
            def on_artist_mousewheel(event):
                self.artist_canvas.xview_scroll(-1 * (event.delta // 120), "units")

            def on_artist_enter(event):
                self.artist_canvas.bind_all("<MouseWheel>", on_artist_mousewheel)

            def on_artist_leave(event):
                self.artist_canvas.unbind_all("<MouseWheel>")

            # Bind events
            self.artist_canvas.bind("<Enter>", on_artist_enter)
            self.artist_canvas.bind("<Leave>", on_artist_leave)
            self.artist_frame.bind("<Enter>", on_artist_enter)
            self.artist_frame.bind("<Leave>", on_artist_leave)

            # Bind drag scroll
            self.artist_canvas.bind("<ButtonPress-1>", self.start_artist_drag)
            self.artist_canvas.bind("<B1-Motion>", self.do_artist_drag)
            self.artist_canvas.bind("<ButtonRelease-1>", self.stop_artist_drag)

            # Tải dữ liệu
            self.load_recommended_artists()

            print("✅ Artist recommendations đã được tạo thành công")

        except Exception as e:
            print(f"❌ Lỗi khi tạo artist recommendations: {e}")

            # 🆕 QUAN TRỌNG: ENABLE MOUSE WHEEL CHO SCROLL NGANG
            def on_artist_mousewheel(event):
                # Scroll ngang khi dùng mouse wheel trên artist area
                self.artist_canvas.xview_scroll(-1 * (event.delta // 120), "units")

            def on_artist_enter(event):
                # Khi chuột vào artist area, bind mouse wheel để scroll ngang
                self.artist_canvas.bind_all("<MouseWheel>", on_artist_mousewheel)

            def on_artist_leave(event):
                # Khi chuột rời artist area, unbind để trả lại scroll dọc
                self.artist_canvas.unbind_all("<MouseWheel>")

            # Bind events
            self.artist_canvas.bind("<Enter>", on_artist_enter)
            self.artist_canvas.bind("<Leave>", on_artist_leave)
            self.artist_frame.bind("<Enter>", on_artist_enter)
            self.artist_frame.bind("<Leave>", on_artist_leave)

            # Bind drag scroll
            self.artist_canvas.bind("<ButtonPress-1>", self.start_artist_drag)
            self.artist_canvas.bind("<B1-Motion>", self.do_artist_drag)
            self.artist_canvas.bind("<ButtonRelease-1>", self.stop_artist_drag)

            # Tải dữ liệu
            self.load_recommended_artists()

            print("✅ Artist recommendations đã được tạo thành công")

        except Exception as e:
            print(f"❌ Lỗi khi tạo artist recommendations: {e}")

    def load_recommended_artists(self):
        """Tải danh sách nghệ sĩ được gợi ý"""
        if not session.current_user:
            print("⚠️ Chưa có user đăng nhập")
            return

        user_id = session.current_user.get("userId")
        if not user_id:
            print("⚠️ Không tìm thấy user ID")
            return

        # Kiểm tra cache trước
        if self.artist_recommendations_cache and self.artist_recommendations_cache.get('user_id') == user_id:
            print("🎵 Using cached artist recommendations")
            self.controller.after(0, lambda: self.display_artists(self.artist_recommendations_cache['data']))
            return

        def load_data():
            try:
                from FinalProject.moo_d.Recommendation_artist import recommend_for_user
                print(f"🔄 Đang tải recommendations cho user: {user_id}")
                recommendations = recommend_for_user(user_id)

                # Lưu vào cache
                self.artist_recommendations_cache = {
                    'user_id': user_id,
                    'data': recommendations
                }

                print(f"✅ Đã tải được {len(recommendations)} recommendations")
                self.controller.after(0, lambda: self.display_artists(recommendations))

            except Exception as e:
                print(f"❌ Lỗi khi load recommendations: {e}")

        threading.Thread(target=load_data, daemon=True).start()

    def display_artists(self, recommendations):
        """Hiển thị danh sách nghệ sĩ - PHIÊN BẢN ĐƠN GIẢN"""
        if not hasattr(self, 'artist_frame') or not self.artist_frame.winfo_exists():
            print("⚠️ artist_frame không tồn tại")
            return

        # Xóa items cũ
        self.clear_artist_recommendations()

        if not recommendations:
            print("⚠️ Không có recommendations")
            no_data_label = Label(
                self.artist_frame,
                text="No artist recommendations available",
                font=("Inter", 12),
                fg="#89A34E",
                bg="#F7F7DC"
            )
            no_data_label.pack(pady=20)
            return

        print(f"🎨 Đang hiển thị {len(recommendations)} nghệ sĩ")

        # Kích thước và khoảng cách
        item_width = 160
        item_height = 180
        item_margin = 20

        # Hiển thị các nghệ sĩ
        for i, artist_data in enumerate(recommendations[:8]):
            x_pos = i * (item_width + item_margin)
            self.create_artist_item(artist_data, x_pos, 0, item_width, item_height, i)

        # Tính toán total width
        total_width = len(recommendations[:8]) * (item_width + item_margin)

        # 🎯 CẤU HÌNH KÍCH THƯỚC CHO SCROLL NGANG
        self.artist_frame.config(width=total_width, height=item_height)

        # 🎯 CẬP NHẬT SCROLLREGION - QUAN TRỌNG!
        self.artist_frame.update_idletasks()
        self.artist_canvas.config(
            scrollregion=(0, 0, total_width, item_height)
        )

        # Cập nhật scrollregion cho canvas chính
        self.update_scroll_region()

        print(f"✅ Artist scroll configured: total_width={total_width}")

    def create_artist_item(self, artist_data, x, y, width, height, index):
        """Tạo một item artist - FIX POSITION"""
        frame = Frame(self.artist_frame, bg="#F7F7DC", width=width, height=height + 20)
        frame.pack_propagate(False)
        frame.place(x=x, y=y)

        bg_color = "#F7F7DC"
        text_color = "#89A34E"

        # Label cho ảnh
        img_label = Label(frame, bg=bg_color, width=120, height=120)
        img_label.pack(pady=8)

        # Tải ảnh bất đồng bộ
        threading.Thread(
            target=self.load_artist_image,
            args=(artist_data["artist"], img_label, (120, 120)),
            daemon=True
        ).start()

        artist_name = artist_data["artist"]
        artist_type = artist_data.get("type", "Recommended")

        # Hiển thị thông tin
        name_label = Label(frame, text=artist_name,
                           font=("Inter", 11, "bold"),
                           fg=text_color, bg=bg_color,
                           wraplength=width - 15, justify="center")
        name_label.pack(padx=8, pady=3)

        # Lưu thông tin
        artist_info = {
            'name': artist_name,
            'type': artist_type,
            'frame': frame,
            'name_label': name_label,
            'img_label': img_label
        }

        self.artist_items.append(artist_info)

        # Thêm sự kiện hover và click
        for widget in [frame, img_label, name_label]:
            widget.bind("<Button-1>", lambda e, name=artist_name: self.on_artist_click(name))
            widget.bind("<Enter>", lambda e, w=widget: self.on_artist_hover(w, True))
            widget.bind("<Leave>", lambda e, w=widget: self.on_artist_hover(w, False))

    def load_artist_image(self, artist_name, img_label, size):
        """Tải ảnh nghệ sĩ bất đồng bộ"""
        try:
            db = self.controller.get_db()

            # Tìm bài hát của nghệ sĩ để lấy ảnh
            track = db.db["tracks"].find_one(
                {"artistName": artist_name},
                {"artworkUrl100": 1, "artworkUrl600": 1}
            )

            image_url = None
            if track:
                image_url = track.get("artworkUrl600") or track.get("artworkUrl100")

            if image_url:
                # Tải và resize ảnh
                image_bytes = urlopen(image_url).read()
                pil_image = Image.open(BytesIO(image_bytes))
                pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)

                # Lưu vào cache
                self.artist_images_cache[artist_name] = photo

                def update_ui():
                    if img_label.winfo_exists():
                        img_label.config(image=photo)
                        img_label.image = photo

                self.controller.after(0, update_ui)
            else:
                self.load_default_artist_image(img_label, size)

        except Exception as e:
            print(f"⚠️ Lỗi tải ảnh nghệ sĩ {artist_name}: {e}")
            self.load_default_artist_image(img_label, size)

    def load_default_artist_image(self, img_label, size):
        """Tải ảnh mặc định"""
        try:
            default_img = Image.open(relative_to_assets("artist_default.png"))
            default_img = default_img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(default_img)

            def update_ui():
                if img_label.winfo_exists():
                    img_label.config(image=photo)
                    img_label.image = photo

            self.controller.after(0, update_ui)
        except Exception as e:
            print(f"⚠️ Lỗi tải ảnh mặc định: {e}")

    def on_artist_click(self, artist_name):
        """Xử lý khi click vào nghệ sĩ - CẬP NHẬT TITLE"""
        print(f"🎵 Clicked artist: {artist_name}")

        # Gọi phương thức của MainScreen và cập nhật title
        if hasattr(self.parent, 'show_artist_detail'):
            self.parent.show_artist_detail(artist_name)
        elif hasattr(self.parent, 'buttons'):
            # Fallback: cập nhật title trực tiếp
            self.parent.buttons.current_title = "Detail"
            self.parent.buttons.create_title()
    # def on_artist_click(self, artist_name):
    #     """Xử lý khi click vào nghệ sĩ - MỞ ARTIST DETAIL"""
    #     print(f"🎵 Clicked artist: {artist_name}")
    #
    #     try:
    #         from FinalProject.moo_d.ui.ArtistDetail_UI import ArtistDetailFrame
    #
    #         # Ẩn HomeScreen content NHƯNG GIỮ LẠI TOOLBAR
    #         self.parent.songs.canvas.place_forget()  # Chỉ ẩn content của songs
    #
    #         # Tạo và hiển thị ArtistDetailFrame CHỈ ở content area
    #         artist_detail_frame = ArtistDetailFrame(
    #             parent=self.parent,  # MainScreen
    #             controller=self.controller,
    #             artist_name=artist_name
    #         )
    #         # KHÔNG dùng relwidth=1, relheight=1 mà chỉ chiếm content area
    #         artist_detail_frame.place(x=103, y=90, width=897, height=408)
    #
    #         print(f"✅ Đã mở ArtistDetail cho: {artist_name}")
    #
    #     except Exception as e:
    #         print(f"❌ Lỗi khi mở ArtistDetail: {e}")
    #         import traceback
    #         traceback.print_exc()
    # def on_artist_click(self, artist_name):
    #     """Xử lý khi click vào nghệ sĩ - MỞ ARTIST DETAIL"""
    #     print(f"🎵 Clicked artist: {artist_name}")
    #
    #     try:
    #         # Import và mở ArtistDetailFrame
    #         from FinalProject.moo_d.ui.ArtistDetail_UI import ArtistDetailFrame
    #
    #         # Ẩn HomeScreen content
    #         self.parent.show_default_content()
    #
    #         # Tạo và hiển thị ArtistDetailFrame
    #         artist_detail_frame = ArtistDetailFrame(
    #             parent=self.parent,  # MainScreen
    #             controller=self.controller,
    #             artist_name=artist_name
    #         )
    #         artist_detail_frame.place(x=0, y=0, relwidth=1, relheight=1)
    #
    #         print(f"✅ Đã mở ArtistDetail cho: {artist_name}")
    #
    #     except Exception as e:
    #         print(f"❌ Lỗi khi mở ArtistDetail: {e}")
    #         import traceback
    #         traceback.print_exc()
    # def on_artist_click(self, artist_name):
    #     """Xử lý khi click vào nghệ sĩ"""
    #     print(f"🎵 Clicked artist: {artist_name}")
    #     # Có thể mở trang chi tiết nghệ sĩ ở đây

    def on_artist_hover(self, widget, is_enter):
        """Hiệu ứng hover - ĐỔI MÀU CẢ KHUNG CHỮ"""
        if is_enter:
            widget.config(cursor="hand2")
            if isinstance(widget, Frame):
                # 🎯 ĐỔI MÀU NỀN FRAME
                widget.config(bg="#F1EBD0")
                # 🎯 ĐỔI MÀU NỀN TẤT CẢ WIDGET CON TRONG FRAME
                for child in widget.winfo_children():
                    if hasattr(child, 'config'):
                        try:
                            child.config(bg="#F1EBD0")
                        except:
                            pass
            elif hasattr(widget, 'config'):
                try:
                    current_bg = widget.cget('bg')
                    if current_bg == "#F7F7DC":
                        widget.config(bg="#F1EBD0")
                except:
                    pass
        else:
            if isinstance(widget, Frame):
                # 🎯 TRỞ LẠI MÀU GỐC CHO FRAME
                widget.config(bg="#F7F7DC")
                # 🎯 TRỞ LẠI MÀU GỐC CHO TẤT CẢ WIDGET CON
                for child in widget.winfo_children():
                    if hasattr(child, 'config'):
                        try:
                            child.config(bg="#F7F7DC")
                        except:
                            pass
            elif hasattr(widget, 'config'):
                try:
                    current_bg = widget.cget('bg')
                    if current_bg == "#F1EBD0":
                        widget.config(bg="#F7F7DC")
                except:
                    pass
    def clear_artist_recommendations(self):
        """Xóa tất cả artist recommendations"""
        for item in self.artist_items:
            if 'frame' in item and item['frame'].winfo_exists():
                item['frame'].destroy()
        self.artist_items.clear()

        # Các hàm hỗ trợ cuộn

    def start_artist_drag(self, event):
        """Bắt đầu kéo để scroll ngang"""
        self.artist_canvas.scan_mark(event.x, event.y)
        self.artist_canvas.config(cursor="fleur")

    def do_artist_drag(self, event):
        """Kéo để scroll ngang"""
        self.artist_canvas.scan_dragto(event.x, event.y, gain=1)

    def stop_artist_drag(self, event):
        """Kết thúc kéo"""
        self.artist_canvas.config(cursor="")

    def on_artist_mousewheel(self, event):
        """Xử lý cuộn bằng chuột"""
        if hasattr(self, 'artist_canvas'):
            self.artist_canvas.xview_scroll(-1 * (event.delta // 120), "units")

    def clear_cache(self):
        """Xóa cache khi cần (ví dụ khi logout)"""
        self.artist_recommendations_cache = None
        self.artist_images_cache.clear()

    def hide_artist_recommendations(self):
        """Ẩn artist recommendations khi không ở home"""
        if hasattr(self, 'artist_container') and self.artist_container:
            self.artist_container.place_forget()
            # Hoặc nếu dùng create_window:
            self.canvas.delete(self.artist_canvas_id)
    # def open_artist_detail(self, artist_name):
    #     """Mở giao diện chi tiết nghệ sĩ khi click vào Recommended Artist"""
    #     from FinalProject.moo_d.ui.ArtistDetail_UI import ArtistDetailFrame
    #
    #     try:
    #         # Ẩn khung chính (nếu đang hiển thị)
    #         self.show_default_content()
    #
    #         # Nếu frame chi tiết chưa tồn tại thì tạo mới
    #         if not hasattr(self, "artist_detail_frame") or self.artist_detail_frame is None:
    #             self.artist_detail_frame = ArtistDetailFrame(
    #                 parent=self, controller=self.controller, artist_name=artist_name
    #             )
    #             self.artist_detail_frame.place(x=0, y=0, relwidth=1, relheight=1)
    #         else:
    #             # Cập nhật nếu đã có frame
    #             self.artist_detail_frame.update_artist(artist_name)
    #             self.artist_detail_frame.lift()
    #
    #         print(f"🎨 Opened detail for artist: {artist_name}")
    #
    #     except Exception as e:
    #         import traceback
    #         print(f"❌ Lỗi khi mở giao diện chi tiết nghệ sĩ: {e}")
    #         traceback.print_exc()

    def on_artist_mousewheel(self, event):
        """Xử lý cuộn bằng chuột cho artist recommendations"""
        if hasattr(self, 'artist_canvas'):
            self.artist_canvas.xview_scroll(-1 * (event.delta // 120), "units")

    def on_artist_scan_mark(self, event):
        """Hàm cuộn (drag-scroll) - Bắt đầu nhấn"""
        if hasattr(self, 'artist_canvas'):
            self.artist_canvas.scan_mark(event.x, 0)

    def on_artist_scan_drag(self, event):
        """Hàm cuộn (drag-scroll) - Kéo chuột"""
        if hasattr(self, 'artist_canvas'):
            self.artist_canvas.scan_dragto(event.x, 0, gain=1)

    def set_buttons(self, buttons):
        self.buttons = buttons

    def hide_all_views(self):
        """Ẩn tất cả các view"""
        # Ẩn canvas chính
        self.canvas.place_forget()

        # Ẩn library
        self.library_canvas.place_forget()

        # Ẩn các manager
        self.history_manager.hide()
        self.owned_songs_manager.hide()
        self.liked_songs_manager.hide()

    def load_history_from_db(self):
        """Tải lịch sử từ database"""
        self.history_manager.load_from_db("user_history", sort_field="LastPlayedAt")

    def load_owned_songs_from_db(self):
        """Tải bài hát sở hữu từ database"""
        self.owned_songs_manager.load_from_db("purchase", sort_field="purchased_at")

    def load_liked_songs_from_db(self):
        """Tải bài hát yêu thích từ database"""
        self.liked_songs_manager.load_from_db("user_favorite",sort_field="added_at")

    def show_history(self):
        """Hiển thị lịch sử"""
        self.history_manager.show()
    def hide_history(self):
        """Ẩn lịch sử"""
        self.history_manager.hide()

    def show_owned_songs(self):
        """Hiển thị bài hát sở hữu"""
        self.owned_songs_manager.show()
    def hide_owned_songs(self):
        """Ẩn bài hát sở hữu"""
        self.owned_songs_manager.hide()

    def show_liked_songs(self):
        """Hiển thị bài hát yêu thích"""
        self.liked_songs_manager.show()
    def hide_liked_songs(self):
        """Ẩn bài hát yêu thích"""
        self.liked_songs_manager.hide()

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
        # Ẩn tất cả các view trước khi hiển thị view mới
        self.hide_all_views()

        if card_type == "owned_songs":
            self.load_owned_songs_from_db()  # Chỉ cần load, manager tự show
        elif card_type == "liked_songs":
            self.load_liked_songs_from_db()  # Chỉ cần load, manager tự show

    def create_playlist_card(self, x, y, label, image_file="chăm hoa 1.png"):
        img = load_image(image_file, size=(175, 150), round_corner=10)
        img_id = None
        if img:
            img_id = self.library_canvas.create_image(x, y, image=img, anchor="nw")
            self.image_cache[label] = img

        text_id = self.library_canvas.create_text(x + 15, y + 160, text=label, fill="#89A34E", font=("Inter", 18),
                                                  anchor="nw")

        self.library_canvas.tag_bind(img_id, "<Button-1>", lambda e, name=label: self.controller.open_playlist(name))
        self.library_canvas.tag_bind(text_id, "<Button-1>", lambda e, name=label: self.controller.open_playlist(name))

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
        db = self.controller.get_db()
        try:
            song = db.db["tracks"].find_one({"trackId": int(track_id)})

            if not song:
                print(f"⚠️ Không tìm thấy trackId={track_id} trong MongoDB.tracks")
                return

            self.fixed_canvas.delete("song_info")

            image_url = song.get("artworkUrl100", "")
            try:
                image_bytes = urlopen(image_url).read()
                pil_image = Image.open(BytesIO(image_bytes)).convert("RGBA")
                resized_image = pil_image.resize((68, 68), Resampling.LANCZOS)
                img = ImageTk.PhotoImage(resized_image)
                self.current_song_image = img
            except Exception as e:
                print(f"⚠️ Lỗi tải ảnh cho trackId={track_id}: {e}")
                self.current_song_image = PhotoImage(file="../images/White_bg.png")

            text_color = "#F586A3"
            x_min, x_max = 104, 255
            y_track, y_artist = 27, 50

            self.fixed_canvas.create_image(20, 5, anchor="nw",
                                           image=self.current_song_image, tags="song_info")

            self.clip_canvas = tkinter.Canvas(
                self.fixed_canvas,
                width=x_max - x_min,
                height=50,
                bg="#F7F7DC",
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

            self.scroll_text(self.clip_canvas, track_text, x_max - x_min)
            self.scroll_text(self.clip_canvas, artist_text, x_max - x_min)
            print(f"🎵 Đã hiển thị bài hát: {track_name} - {artist_name}")
            self.play_song(song)

        except Exception as e:
            print(f"❌ Lỗi khi truy vấn bài hát từ MongoDB: {e}")

    def scroll_text(self, canvas, text_id, visible_width, speed=2, delay=50):
        bbox = canvas.bbox(text_id)
        if not bbox:
            return

        text_width = bbox[2] - bbox[0]
        if text_width <= visible_width:
            return

        def animate(direction=-1):
            canvas.move(text_id, speed * direction, 0)
            x1, y1, x2, y2 = canvas.bbox(text_id)
            if x2 <= visible_width or x1 >= 0:
                direction *= -1
            canvas.after(delay, animate, direction)

        animate()

    def update_scroll_region(self, event=None):
        """Cập nhật kích thước vùng cuộn - FIXED"""
        # 🆕 CẬP NHẬT SCROLLREGION CHO CANVAS CHÍNH
        try:
            # Lấy tất cả items trên canvas
            all_items = self.canvas.find_all()
            if all_items:
                # Tính bounding box của tất cả items
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.configure(scrollregion=bbox)
        except Exception as e:
            print(f"⚠️ Lỗi update scroll region: {e}")

        # Cập nhật các canvas khác
        self.history_manager.canvas.configure(scrollregion=self.history_manager.canvas.bbox("all"))
        self.owned_songs_manager.canvas.configure(scrollregion=self.owned_songs_manager.canvas.bbox("all"))
        self.liked_songs_manager.canvas.configure(scrollregion=self.liked_songs_manager.canvas.bbox("all"))
        self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all"))
    # def update_scroll_region(self, event=None):
    #     self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    #     self.history_manager.canvas.configure(scrollregion=self.history_manager.canvas.bbox("all"))
    #     self.owned_songs_manager.canvas.configure(scrollregion=self.owned_songs_manager.canvas.bbox("all"))
    #     self.liked_songs_manager.canvas.configure(scrollregion=self.liked_songs_manager.canvas.bbox("all"))
    #     self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all"))

    # def scroll_with_mouse(self, event):
    #     active_managers = [
    #         self.history_manager,
    #         self.owned_songs_manager,
    #         self.liked_songs_manager
    #     ]
    #
    #     for manager in active_managers:
    #         if manager.canvas.winfo_ismapped():
    #             manager.scroll_with_mouse(event)
    #             return
    #
    #     if self.library_canvas.winfo_ismapped():
    #         self.library_canvas.yview_scroll(-1 * (event.delta // 120), "units")
    #     else:
    #         self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
    def scroll_with_mouse(self, event):
        """Cuộn danh sách bằng chuột - FIXED"""
        # 🆕 ƯU TIÊN: Cuộn canvas chính trước
        if self.canvas.winfo_ismapped():
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
            return

        # Sau đó mới kiểm tra các canvas khác
        active_managers = [
            self.history_manager,
            self.owned_songs_manager,
            self.liked_songs_manager
        ]

        for manager in active_managers:
            if manager.canvas.winfo_ismapped():
                manager.scroll_with_mouse(event)
                return

        if self.library_canvas.winfo_ismapped():
            self.library_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def play_song(self, song):
        try:
            song_url = song.get("previewUrl") or song.get("filePath")
            if not song_url:
                print("  Không có URL hoặc filePath hợp lệ để phát.")
                return

            media = self.instance.media_new(song_url)
            self.player.set_media(media)
            self.player.play()

            self.current_song = song
            self.is_playing = True
            self.is_paused = False
            self.start_time = time.time()
            self.total_time = song.get("trackTimeMillis", 0) / 1000

            self.fixed_canvas.itemconfig(
                self.buttons.buttons["play"],  # Lấy nút 'play' từ self.buttons
                image=self.buttons.image_cache["pause"]
            )

            print(f"🎶 Playing now: {song.get('trackName')} - {song.get('artistName')}")

        except Exception as e:
            print(f"❌ Lỗi khi phát nhạc: {e}")

    def resume_song(self):
        if self.is_paused:
            self.player.play()
            self.is_paused = False
            self.start_time = time.time() - self.paused_time
            self.paused_time = 0
            self.parent.buttons.update_progress_bar()


class ProfileFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        # KHAI BÁO TRƯỚC TẤT CẢ WIDGETS
        self.update_button = None
        self.change_photo_button = None
        self.name_entry = None
        self.email_entry = None
        self.username_entry = None
        self.password_entry = None

        # Canvas chính
        self.canvas = Canvas(self, bg="#FFFFFF", height=600, width=950,
                             bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # Hiển thị profile content
        self.load_background()
        self.create_widgets()


    def load_background(self):
        """Tải ảnh nền cho giao diện"""
        self.image_cache["profile_bg"] = load_image("profile1.png", opacity=0.8, size=(736, 1308), rotate=90)
        self.image_cache["content_box"] = load_image("profile2.png", size=(550, 600))
        self.image_cache["profile_box"] = load_image("profile3.png", size=(450, 360))


        self.canvas.create_image(325, 300, image=self.image_cache["profile_bg"])
        self.canvas.create_image(675, 300, image=self.image_cache["content_box"])
        self.canvas.create_image(680, 290, image=self.image_cache["profile_box"])


    def create_widgets(self):
        # Text
        self.canvas.create_text(585, 40, anchor="nw", text="Profile", fill="#F2829E",
                                font=("Inter Bold", 40, "bold"))
        self.canvas.create_text(480, 130, text="Name:", font=("Inter Bold", 18, "bold"),
                                fill="#F2829E", anchor="nw")
        self.canvas.create_text(480, 210, text="E-mail:", font=("Inter Bold", 18, "bold"),
                                fill="#F2829E", anchor="nw")
        self.canvas.create_text(480, 290, text="Username:", font=("Inter Bold", 18, "bold"),
                                fill="#F2829E", anchor="nw")
        self.canvas.create_text(480, 370, text="Password:", font=("Inter Bold", 18, "bold"),
                                fill="#F2829E", anchor="nw")

        # User input
        user = session.current_user or {}
        name = user.get("name", "")
        email = user.get("email", "N/A")
        username = user.get("username", "Unknown")
        password = user.get("password", "******")
        profile_path = user.get("profile_picture")

        # Entry
        self.name_entry = CTkEntry(
            master=self, width=400, height=45,
            font=("Inter", 18, "bold"), fg_color="#D1E0AB",
            text_color="#F2829E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FBE8DD"
        )
        self.name_entry.insert(0, name)
        self.name_entry.place(x=475, y=160)

        self.email_entry = CTkEntry(
            master=self, width=400, height=45,
            font=("Inter", 18, "bold"), fg_color="#D1E0AB",
            text_color="#F2829E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FBE8DD"
        )
        self.email_entry.insert(0, email)
        self.email_entry.place(x=475, y=240)

        self.email_entry.bind("<Key>", lambda e: "break")
        self.email_entry.bind("<Button-3>", lambda e: "break")

        # Entry cho username
        self.username_entry = CTkEntry(
            master=self, width=400, height=45,
            font=("Inter", 18, "bold"), fg_color="#D1E0AB",
            text_color="#F2829E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FBE8DD"
        )
        self.username_entry.insert(0, username)
        self.username_entry.place(x=475, y=320)

        # Entry cho password
        self.password_entry = CTkEntry(
            master=self, width=400, height=45,
            font=("Inter", 18, "bold"), fg_color="#D1E0AB",
            text_color="#F2829E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FBE8DD", show="*"
        )
        self.password_entry.insert(0, password)
        self.password_entry.place(x=475, y=400)

        # Hiển thị ảnh Profile
        if not profile_path or not Path(profile_path).exists():
            profile_path = str(relative_to_assets("profile_default.jpg"))

        self.load_profile_image(profile_path)

        # Nút thay đổi ảnh profile
        self.change_photo_button = CTkButton(
            self,
            text="Change profile picture",
            command=self.change_profile_picture,
            fg_color="#FBE8DD",
            hover_color="#F3829C",
            text_color="#89A34E",
            font=("Inter Bold", 18, "bold"),
            width=300,
            height=40
        )
        self.change_photo_button.place(x=57, y=450)

        # Nút Update
        self.update_button = CTkButton(
            self,
            width=200,
            height=40,
            text="Update profile",
            command=self.update_info,
            fg_color="#FBE8DD",
            hover_color="#F3829C",
            bg_color="#FEFBE5",
            text_color="#89A34E",
            font=("Inter Bold", 18, "bold"),
            corner_radius=10
        )
        self.update_button.place(x=570, y=490)


    def update_info(self):
        """Cập nhật thông tin người dùng và lưu vào file JSON"""
        user = session.current_user or {}
        current_email = user.get("email", "N/A")
        new_name = self.name_entry.get().strip()
        new_username = self.username_entry.get().strip()
        new_password = self.password_entry.get().strip()

        if not new_name or not new_username or not new_password:
            messagebox.showerror("Error", "Please enter all fields!")
            return

        # Kiểm tra username đã tồn tại chưa (trừ user hiện tại)
        existing_user = db.find_one("user", {"username": new_username})
        if existing_user and existing_user.get("email") != current_email:
            messagebox.showerror("Error", "Username already exists!")
            return

        try:
            # Cập nhật trong MongoDB
            update_data = {
                "name": new_name,
                "username": new_username,
                "password": new_password
            }

            db.update_one("user", {"email": current_email}, update_data)

            # Cập nhật session
            updated_user = db.find_one("user", {"email": current_email})
            session.current_user = updated_user
            messagebox.showinfo("Success", "Information has been updated!")


        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def load_profile_image(self, path):
        """Tải ảnh profile từ đường dẫn và hiển thị trên canvas"""
        try:
            if not Path(path).exists():
                path = str(relative_to_assets("profile_default.png"))

            # Tạo cache key duy nhất với timestamp
            cache_key = f"profile_{Path(path).name}_{int(datetime.now().timestamp())}"
            self.image_cache[cache_key] = load_image(path, size=(300, 300))

            # Xóa ảnh cũ và hiển thị ảnh mới
            self.canvas.delete("profile_pic")
            self.canvas.create_image(57, 100, anchor="nw",
                                     image=self.image_cache[cache_key],
                                     tags="profile_pic")

            # Force update canvas
            self.canvas.update_idletasks()

        except Exception as e:
            # Fallback to default image
            self.load_profile_image(str(relative_to_assets("profile_default.png")))

    def change_profile_picture(self):
        """Mở hộp thoại chọn ảnh, cập nhật ảnh profile"""
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[("Ảnh PNG", "*.png"), ("Ảnh JPG", "*.jpg"), ("Ảnh JPEG", "*.jpeg"),
                       ("Tất cả ảnh", "*.png;*.jpg;*.jpeg")]
        )

        if not file_path:
            return

        user_email = session.current_user['email']
        new_file_name = f"{user_email.replace('@', '_').replace('.', '_')}.png"
        new_file_path = PROFILE_PIC_PATH / new_file_name

        # Xóa ảnh cũ (trừ ảnh default)
        old_picture = session.current_user.get("profile_picture")
        if (old_picture not in old_picture and
                Path(old_picture).exists() and
                old_picture != str(new_file_path)):
            try:
                os.remove(old_picture)
            except Exception:
                pass  # Ignore delete errors

        try:
            # Copy ảnh mới
            shutil.copy(file_path, new_file_path)

            # Cập nhật database và hiển thị
            self.update_user_profile_picture(str(new_file_path))

        except Exception as e:
            messagebox.showerror("Error", f"Không thể lưu ảnh: {e}")

    def update_user_profile_picture(self, new_picture_path):
        """Cập nhật ảnh profile trong MongoDB"""
        try:
            user_email = session.current_user.get("email")
            if not user_email:
                return

            # Cập nhật MongoDB
            db.update_one("user",
                          {"email": user_email},
                          {"profile_picture": new_picture_path})

            # Cập nhật session và hiển thị
            session.current_user["profile_picture"] = new_picture_path
            self.load_profile_image(new_picture_path)

        except Exception as e:
            messagebox.showerror("Error", f"Cập nhật thất bại: {e}")

from tkinter import Frame, Canvas, messagebox
from customtkinter import CTkButton
from FinalProject.moo_d.functions import load_image
from FinalProject.moo_d.Connection.connector import db
from FinalProject.moo_d import session
from FinalProject.moo_d.generate_wrapup_data import generate_user_wrapup
from datetime import datetime, timedelta
import requests, io
from PIL import Image, ImageTk



class SleeptimerFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E1CFE3")
        self.controller = controller
        self.sleep_timer_running = False
        self.sleep_time = 0
        self.image_cache = {}

        frame = Canvas(self, bg="#FBE8DD", width=300, height=200, highlightthickness=0)
        self.canvas = frame
        self.image_cache["bg_sleep"] = load_image("bg_sleep.png", opacity=0.6, size=(300, 200))
        frame.create_image(480, 300, image=self.image_cache["bg_sleep"])
        self.canvas.create_text (140,40, text = "Sleep Timer", font = ("Inter", 16, "bold"), fill = "#FEFFFD")
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




