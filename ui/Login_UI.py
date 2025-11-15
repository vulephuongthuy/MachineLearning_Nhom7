import colorsys
import os
import random
import shutil
import smtplib
import sys
from datetime import datetime, timezone
from pathlib import Path
import qrcode
import requests
from PIL import Image, ImageTk, ImageSequence
from io import BytesIO
# from CTkMessagebox import CTkMessagebox
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from functions import *
from tkinter import Tk, Canvas, messagebox, Frame, filedialog, IntVar, StringVar
import os
from bson import ObjectId
from customtkinter import CTkEntry, CTkButton, CTkCheckBox, CTkRadioButton

import session
from Connection.connector import db


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

        db = self.controller.get_db()

        try:
            user = db.find_one("user", {
                "username": username,
                "password": password
            })
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
            return

        if user:
            # moo_d.session.current_user = user
            session.current_user = user
            self.controller.show_frame("MoodTracker")
            self.controller.destroy_frame("LoginFrame")
            return

        messagebox.showerror("Error", "Incorrect username or password!")

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
        db = self.controller.get_db()
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

        try:
            # Lấy tất cả user và tìm userId lớn nhất
            all_users = db.find_all("user")

            max_id = 0
            for user in all_users:
                if "userId" in user and user["userId"].isdigit():
                    user_id_num = int(user["userId"])
                    if user_id_num > max_id:
                        max_id = user_id_num

            next_user_id = str(max_id + 1)

            # Tạo user mới
            new_user = {
                "userId": next_user_id,
                "name": name,
                "email": email,
                "username": username,
                "password": password,
                "profile_picture": str(relative_to_assets("profile_default.jpg")),
            }

            # Lưu vào MongoDB
            db.insert_one("user", new_user)

            # Gửi email chào mừng
            self.send_welcome_email(email)
            self.go_back()

        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

    def send_welcome_email(self, user_email: str):
        """Gửi email chào mừng khi người dùng đăng ký thành công."""
        SENDER_EMAIL = "thutna23416@st.uel.edu.vn"
        APP_PASSWORD = "wyas ubap nhqv wwap"
        # Validate email
        if "@" not in user_email:
            print(f"Email không hợp lệ: {user_email}")
            return
        # Tạo email multipart
        msg = MIMEMultipart("related")
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email
        msg["Subject"] = "🎧 Welcome to Moo_d Music!"
        image_cid = "welcome_image"
        # HTML Template đẹp + gọn + responsive
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; padding: 0 10px;">
            <h2 style="color:#F2829E;">Welcome to Moo_d Music! 🎶</h2>

            <p>Hi there,</p>
            <p>Thank you for signing up for <b>Moo_d Music</b> – 
            your new favorite place to vibe, discover, and enjoy music that matches your mood.</p>

            <p>
                We're thrilled to have you on board!  
                Here’s a warm welcome from our team:
            </p>

            <div style="text-align:center; margin: 25px 0;">
                <img src="cid:{image_cid}" 
                     alt="Welcome to Moo_d" 
                     style="width:100%; max-width:420px; border-radius:12px;">
            </div>

            <p>
                Stay tuned for curated playlists, mood-based recommendations <br>
                and fresh beats tailored just for you.
            </p>

            <p>Let's set the Moo_d together! 🌙✨</p>

            <p style="margin-top: 35px;">
                Cheers,<br>
                <b>The Moo_d Team</b>
            </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        image_path = Path("images/welcome.png")
        if image_path.exists():
            try:
                with open(image_path, "rb") as f:
                    img_data = f.read()
                img = MIMEImage(img_data, name=image_path.name)
                img.add_header("Content-ID", f"<{image_cid}>")
                msg.attach(img)
            except Exception as e:
                print(f" Lỗi khi đính ảnh: {e}")
        else:
            print(f" Không tìm thấy ảnh tại: {image_path}")

        # Gửi email qua SMTP
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
            print(f"Email chào mừng đã gửi thành công đến {user_email}")
        except Exception as e:
            print(f" Lỗi khi gửi email: {e}")

    def go_back(self):
        """Quay lại màn hình đăng nhập"""
        self.controller.show_frame("LoginFrame")
        self.controller.destroy_frame("SignUpFrame")


class MoodTracker(Frame):
    MOOD_MAP = {
        "Happy": 1,
        "Sad": 2,
        "Neutral": 3,
        "Intense": 4
    }
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
        username = session.current_user.get("name","") if session.current_user else "User"
        self.username = username

        self.canvas.create_text(
            49, 66,
            anchor="nw",
            text=f"Hello {self.username},",
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
        from datetime import datetime

        self.canvas.itemconfig(mood, image=self.image_cache[f"{mood}_hover"])
        print(f"{mood} pressed!")

        user_id = session.current_user.get("userId")
        now = datetime.now()
        month_key = now.strftime("%Y-%m")
        mood_id = self.MOOD_MAP[mood]

        # ===== Auto historyID không cần counter =====
        last = db.db.mood_tracking_history.find_one(sort=[("historyID", -1)])
        history_id = last["historyID"] + 1 if last else 1

        # ===== Lưu lịch sử =====
        db.db.mood_tracking_history.insert_one({
            "historyID": history_id,
            "userId": user_id,
            "moodID": mood_id,
            "moodName": mood,
            "timestamp": now.isoformat() + "Z"
        })

        #  Lấy summary tháng hiện tại
        summary = db.db.mood_monthly_summary.find_one(
            {"userId": user_id, "month": month_key}
        )
        #  Nếu chưa có → tạo mới đầy đủ cấu trúc
        if not summary:
            summary = {
                "userId": user_id,
                "month": month_key,
                "total_entries": 0,
                "mood_count": {m: 0 for m in self.MOOD_MAP.keys()},
                "mood_breakdown": {},
                "dominant_mood": None
            }

        #ĐẢM BẢO mood_count luôn có đủ keys (fix cho data cũ)
        for m in self.MOOD_MAP.keys():
            if m not in summary["mood_count"]:
                summary["mood_count"][m] = 0

        # Cập nhật dữ liệu tháng
        summary["total_entries"] += 1
        summary["mood_count"][mood] += 1

        total = summary["total_entries"]
        summary["mood_breakdown"] = {
            m: round(summary["mood_count"][m] / total, 2)
            for m in self.MOOD_MAP.keys()
        }

        summary["dominant_mood"] = max(
            summary["mood_breakdown"], key=summary["mood_breakdown"].get
        )

        # ===== Lưu lại vào DB =====
        db.db.mood_monthly_summary.update_one(
            {"userId": user_id, "month": month_key},
            {"$set": summary},
            upsert=True
        )

        # ===== Lưu vào session (để HomeScreen lấy mood hiện tại) =====
        session.current_user["current_mood"] = {
            "moodID": mood_id,
            "moodName": mood,
            "timestamp": now
        }

        self.controller.show_frame("HomeScreen")
        self.controller.show_frame("LoadingPage")
        self.controller.destroy_frame("MoodTracker")

class LoadingPage(Frame):
    MOOD_QUOTES = {
        "Happy": [
            "Your laughter echoed through every moment.",
            "You danced through the days like sunlight on water.",
            "Smiles followed you like petals in spring.",
            "You turned ordinary hours into golden memories.",
            "Joy wasn't just felt — it was shared."
        ],
        "Sad": [
            "You carried the weight, but never lost your grace.",
            "Even in silence, your strength spoke volumes.",
            "The shadows didn't break you — they shaped you.",
            "You gave yourself permission to feel — and that's brave.",
            "Sadness softened your edges, but never dimmed your light."
        ],
        "Neutral": [
            "You held steady while the world spun fast.",
            "Calm was your quiet superpower.",
            "You moved with intention, not impulse.",
            "Still waters ran deep in your story.",
            "You didn't chase highs — you embraced clarity."
        ],
        "Intense": [
            "You roared through the chaos with purpose.",
            "Every step you took left sparks behind.",
            "You didn't just show up — you made impact.",
            "Your energy rewrote the rhythm of the room.",
            "You burned through limits like they were paper walls."
        ]
    }

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}
        self.canvas = Canvas(
            self, bg="#FFFFFF", height=600, width=1000,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        self.load_background()
        self.load_gif()

        self.mood_quote = self.get_mood_quote()

        # Bắt đầu chạy animation
        self.frame_index = 0
        self.animate_gif()

        # Tạo hai dòng text riêng biệt
        self.text_label1 = self.canvas.create_text(
            500, 280,
            text="Waiting while your mood gets in tune",
            fill="#F2829E",
            font=("Inter", 30, "bold"),
            state="hidden"
        )

        self.text_label2 = self.canvas.create_text(
            500, 280,
            text=self.mood_quote,
            fill="#F2829E",
            font=("Inter", 30, "bold"),
            state="hidden"
        )

        # Biến để theo dõi trạng thái hiển thị
        self.current_text = 0  # 0: chưa hiển thị, 1: đang hiển thị dòng 1, 2: đang hiển thị dòng 2
        self.text_timer = 0

        # Bắt đầu hiệu ứng chuyển đổi text
        self.animate_text_sequence()

        # Sau 10 giây -> qua HomeScreen
        self.after(10000, self.goto_home)

    def get_mood_quote(self):
        """Lấy random quote dựa trên current mood"""
        try:
            from app import session
            current_mood = session.current_user.get("current_mood", {})
            mood_name = current_mood.get("moodName", "Neutral")

            # Lấy quotes cho mood hiện tại, mặc định là Neutral nếu không tìm thấy
            quotes = self.MOOD_QUOTES.get(mood_name, self.MOOD_QUOTES["Neutral"])

            # Chọn random một quote
            import random
            return random.choice(quotes)

        except Exception as e:
            print(f"Lỗi khi lấy mood quote: {e}")
            # Trả về quote mặc định nếu có lỗi
            return "Every moment tells a story worth remembering."

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

    def load_gif(self):
        """Load GIF động gốc, giữ nguyên tốc độ"""
        try:
            self.gif = Image.open(relative_to_assets("loading_page.gif"))

            # Lưu frame và delay thật
            self.frames = []
            self.delays = []
            for frame in ImageSequence.Iterator(self.gif):
                self.frames.append(ImageTk.PhotoImage(frame.copy()))
                delay = frame.info.get("duration", 90)  # giữ đúng thời lượng frame
                self.delays.append(delay)

            # Hiển thị frame đầu tiên
            self.gif_label = self.canvas.create_image(500, 330, image=self.frames[0])

        except Exception as e:
            print(f"Lỗi khi load GIF: {e}")

    def animate_gif(self):
        if hasattr(self, "frames") and self.frames:
            frame = self.frames[self.frame_index]
            self.canvas.itemconfig(self.gif_label, image=frame)

            # tốc độ phát nhanh hơn
            fixed_delay = 30  # 20 fps
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.after(fixed_delay, self.animate_gif)

    def animate_text_sequence(self):
        """Hiệu ứng chuyển đổi giữa 2 dòng text, mỗi dòng hiện 1 lần"""
        self.text_timer += 100

        if self.text_timer <= 2000:  # 0-2 giây: Hiển thị dòng 1
            if self.current_text != 1:
                self.canvas.itemconfig(self.text_label1, state="normal")
                self.canvas.itemconfig(self.text_label2, state="hidden")
                self.current_text = 1

        elif self.text_timer <= 10000:  # 2-10 giây: Hiển thị dòng 2
            if self.current_text != 2:
                self.canvas.itemconfig(self.text_label1, state="hidden")
                self.canvas.itemconfig(self.text_label2, state="normal")
                self.current_text = 2

        else:  # Sau 10 giây: Ẩn cả hai
            self.canvas.itemconfig(self.text_label1, state="hidden")
            self.canvas.itemconfig(self.text_label2, state="hidden")
            return

        # Tiếp tục cập nhật sau 100ms
        self.after(100, self.animate_text_sequence)

    def goto_home(self):
        """Chuyển sang HomeScreen"""
        try:
            self.controller.destroy_frame("LoadingPage")
        except Exception as e:
            print(f"Lỗi khi chuyển sang HomeScreen: {e}")


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
        # user = moo_d.session.current_user or {}
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
        # user = moo_d.session.current_user or {}
        user = session.current_user or {}
        current_email = user.get("email", "N/A")
        new_name = self.name_entry.get().strip()
        new_username = self.username_entry.get().strip()
        new_password = self.password_entry.get().strip()

        if not new_name or not new_username or not new_password:
            messagebox.showerror("Error", "Please enter all fields!")
            return

        db = self.controller.get_db()

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
            # moo_d.session.current_user = updated_user
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

        # user_email = moo_d.session.current_user['email']
        user_email = session.current_user['email']
        new_file_name = f"{user_email.replace('@', '_').replace('.', '_')}.png"
        new_file_path = PROFILE_PIC_PATH / new_file_name

        # Xóa ảnh cũ (trừ ảnh default)
        # old_picture = moo_d.session.current_user.get("profile_picture")
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
            # user_email = moo_d.session.current_user.get("email")
            user_email = session.current_user.get("email")
            if not user_email:
                return

            db = self.controller.get_db()

            # Cập nhật MongoDB
            db.update_one("user",
                          {"email": user_email},
                          {"profile_picture": new_picture_path})

            # Cập nhật session và hiển thị
            # moo_d.session.current_user["profile_picture"] = new_picture_path
            session.current_user["profile_picture"] = new_picture_path
            self.load_profile_image(new_picture_path)

        except Exception as e:
            messagebox.showerror("Error", f"Cập nhật thất bại: {e}")

class Payment(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_cache = {}

        self.payment_var = StringVar(value="")
        # self.countdown_seconds = 0
        # self.is_countdown_running = False

        # GIẢ LẬP: Lấy track data đầu tiên từ MongoDB
        self.track_data = {}

        # Canvas chính
        self.canvas = Canvas(self, bg="#FEFBE5", height=600, width=1000,
                             bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # Hiển thị profile content
        self.load_background()
        self.create_widgets()
        self.create_payment_methods()


    def set_track(self, track_data):
        """Nhận thông tin track từ MoodPlayerFrame"""
        self.track_data = track_data or {}
        self.update_track_fields()

    def update_track_fields(self):
        """Cập nhật các entry và artwork khi đổi bài"""
        try:
            self.track_entry.delete(0, "end")
            self.track_entry.insert(0, self.track_data.get("trackName", ""))

            self.artist_entry.delete(0, "end")
            self.artist_entry.insert(0, self.track_data.get("artistName", ""))

            self.album_entry.delete(0, "end")
            self.album_entry.insert(0, self.track_data.get("collectionName", ""))

            artwork_url = self.track_data.get("artworkUrl100", "").replace("100x100bb", "300x300bb")
            if artwork_url:
                self.load_track_artwork(artwork_url)

        except Exception as e:
            print(f"Lỗi khi cập nhật track: {e}")
    # def get_sample_track_data(self):
    #     """Lấy track data từ MongoDB với điều kiện cụ thể"""
    #     try:
    #         db = self.controller.get_db()
    #
    #         # Truy cập client trực tiếp
    #         collection = db.db["tracks"]  # db.db là database object
    #
    #         # Dùng aggregation pipeline với $sample
    #         pipeline = [{"$sample": {"size": 1}}]
    #         result = list(collection.aggregate(pipeline))
    #
    #         if result:
    #             random_track = result[0]
    #             print("Đã lấy track ngẫu nhiên từ MongoDB:")
    #             print(f"   - Track: {random_track.get('trackName')}")
    #             return random_track
    #
    #     except Exception as e:
    #         print(f"Lỗi MongoDB: {e}")
    #         return

    def load_background(self):
        """Tải ảnh nền cho giao diện"""
        self.image_cache["payment_bg"] = load_image("payment_bg.png")
        self.image_cache["payment1"] = load_image("payment1.png", size=(1000,70))
        self.image_cache["payment2"] = load_image("payment2.png", size=(445,280))
        self.image_cache["payment3"] = load_image("payment3.png")
        self.image_cache["payment4"] = load_image("payment4.png")
        self.image_cache["payment5"] = load_image("payment5.png")
        self.image_cache["payment_close"] = load_image("payment_close.png")

        self.canvas.create_image(500, 320, image=self.image_cache["payment_bg"])
        self.canvas.create_image(500, 20, image=self.image_cache["payment1"])
        self.canvas.create_image(300, 340, image=self.image_cache["payment2"])
        self.canvas.create_image(750, 197, image=self.image_cache["payment3"])
        self.canvas.create_image(750, 347, image=self.image_cache["payment4"])

    def create_widgets(self):
        # Text
        self.canvas.create_text(590, 142, text="CONTACT", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(590, 287, text="PAYMENT METHOD", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(100, 303, text="Song:", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(100, 343, text="Artist:", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(100, 383, text="Album:", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(100, 430, text="TOTAL", font=("Roboto", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(430, 430, text="6.500đ", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(640, 330, text="Momo", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.create_text(640, 370, text="Banking", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")

        # Thêm nút dạng ảnh
        self.purchase_button_bg = self.canvas.create_image(750, 457, image=self.image_cache["payment5"])
        self.canvas.tag_bind(self.purchase_button_bg, "<Button-1>", lambda e: self.purchase_now())
        self.btn_text = self.canvas.create_text(680, 443, text="Purchase Now", font=("Inter", 15, "bold"),
                                fill="#FFFFFF", anchor="nw")
        self.canvas.tag_bind(self.btn_text, "<Button-1>", lambda e: self.purchase_now())

        self.close_btn = self.canvas.create_image(30, 23, image=self.image_cache["payment_close"])
        self.canvas.tag_bind(self.close_btn, "<Button-1>", lambda e: self.close_payment_frame())

        # User input
        user = session.current_user or {}
        name = user.get("name", "")
        email = user.get("email", "N/A")


        # Entry
        self.name_entry = CTkEntry(
            master=self, width=320, height=30,
            font=("Inter", 15, "bold"), fg_color="#F7F7DC",
            text_color="#89A34E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FEB4C6"
        )
        self.name_entry.insert(0, name)
        self.name_entry.place(x=590, y=172)
        self.name_entry.bind("<Key>", lambda e: "break")
        self.name_entry.bind("<Button-3>", lambda e: "break")

        self.email_entry = CTkEntry(
            master=self, width=320, height=30,
            font=("Inter", 15, "bold"), fg_color="#F7F7DC",
            text_color="#89A34E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FEB4C6"
        )
        self.email_entry.insert(0, email)
        self.email_entry.place(x=590, y=212)

        self.email_entry.bind("<Key>", lambda e: "break")
        self.email_entry.bind("<Button-3>", lambda e: "break")

        self.track_entry = CTkEntry(
            master=self, width=320, height=30,
            font=("Inter", 15, "bold"), fg_color="#F7F7DC",
            text_color="#89A34E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FEB4C6"
        )
        self.track_entry.insert(0, self.track_data.get("trackName", ""))
        self.track_entry.place(x=180, y=300)
        self.track_entry.bind("<Key>", lambda e: "break")
        self.track_entry.bind("<Button-3>", lambda e: "break")

        self.artist_entry = CTkEntry(
            master=self, width=320, height=30,
            font=("Inter", 15, "bold"), fg_color="#F7F7DC",
            text_color="#89A34E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FEB4C6"
        )
        self.artist_entry.insert(0, self.track_data.get("artistName", ""))
        self.artist_entry.place(x=180, y=340)
        self.artist_entry.bind("<Key>", lambda e: "break")
        self.artist_entry.bind("<Button-3>", lambda e: "break")

        self.album_entry = CTkEntry(
            master=self, width=320, height=30,
            font=("Inter", 15, "bold"), fg_color="#F7F7DC",
            text_color="#89A34E", border_width=1,
            border_color="#F2829E", corner_radius=20,
            bg_color="#FEB4C6"
        )
        self.album_entry.insert(0, self.track_data.get("collectionName", ""))
        self.album_entry.place(x=180, y=380)
        self.album_entry.bind("<Key>", lambda e: "break")
        self.album_entry.bind("<Button-3>", lambda e: "break")

        # Load artwork
        artwork_url = self.track_data.get("artworkUrl100", "").replace("100x100bb", "300x300bb")
        if artwork_url:
            self.load_track_artwork(artwork_url)

    def load_track_artwork(self, artwork_url):
        """Tải ảnh artwork từ URL"""
        try:
            if artwork_url:
                response = requests.get(artwork_url)
                response.raise_for_status()

                # Dùng hàm load_image có sẵn
                artwork_image = load_image(response.content, size=(200, 200), round_corner=10, from_url=True)
                if artwork_image:
                    self.image_cache["track_artwork"] = artwork_image
                    self.canvas.create_image(220, 180, image=self.image_cache["track_artwork"])

        except Exception as e:
            print(f"Lỗi khi tải artwork: {e}")

    def create_payment_methods(self):
        """Tạo các lựa chọn phương thức thanh toán - TỐI ƯU HÓA HOÀN TOÀN"""
        payment_methods = [
            {"name": "Momo", "x": 600, "y": 327},
            {"name": "Banking", "x": 600, "y": 367}
        ]

        for method in payment_methods:
            CTkRadioButton(
                self,
                text="",
                width=25,
                height=30,
                radiobutton_width=30,
                radiobutton_height=30,
                corner_radius=30,
                border_width_checked=8,
                border_width_unchecked=3,
                border_color="#F2829E",
                fg_color="#89A34E",
                hover_color="#89A34E",  # Hiệu ứng hover có sẵn
                bg_color="#FEB4C6",
                variable=self.payment_var,
                value=method["name"].lower(),
                command=lambda v=method["name"].lower(): print(f"Selected: {v}")
            ).place(x=method["x"], y=method["y"])

    def purchase_now(self):
        """Xử lý khi nhấn nút PURCHASE NOW"""
        try:
            if not self.payment_var.get():
                messagebox.showwarning("Warning", "Please select a payment method!",
                             icon="warning")
                return

            # Tạo và hiển thị QR code
            qr_image = self.generate_qr_code()
            if qr_image:
                self.show_qr_interface(qr_image)

        except Exception as e:
            print(f"Lỗi khi xử lý thanh toán: {e}")
            messagebox.showerror("Error","Payment processing failed!",
                          icon="cancel")

    def generate_qr_code(self):
        """Tạo QR code với thông tin thanh toán"""
        try:
            payment_info = {
                "track": self.track_data.get("trackName", ""),
                "artist": self.track_data.get("artistName", ""),
                "amount": "6500",
                "currency": "VND",
                "payment_method": self.payment_var.get()
            }

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=7,
                border=4,
            )

            qr_data = f"MOOD_MUSIC_PAYMENT\nTrack: {payment_info['track']}\nAmount: {payment_info['amount']} {payment_info['currency']}\nMethod: {payment_info['payment_method']}"
            qr.add_data(qr_data)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="#F2829E", back_color="#FEFBE5")
            qr_image = qr_image.resize((300, 300), Image.LANCZOS)
            return qr_image

        except Exception as e:
            print(f"Lỗi khi tạo QR code: {e}")
            return None

    def show_qr_interface(self, qr_image):
        """Hiển thị giao diện QR trong frame - tạo canvas mới đè lên"""
        try:
            # TẠO CANVAS MỚI ĐÈ LÊN TRÊN CÙNG
            self.qr_canvas = Canvas(self, bg="#FEFBE5", height=600, width=1000,
                                    bd=0, highlightthickness=0, relief="ridge")
            self.qr_canvas.place(x=0, y=0)

            # Load background lên canvas mới
            self.qr_canvas.create_image(500, 320, image=self.image_cache["payment_bg"])
            self.qr_canvas.create_image(500, 20, image=self.image_cache["payment1"])

            # Chuyển QR image sang PhotoImage
            self.qr_photo = ImageTk.PhotoImage(qr_image)

            # Hiển thị QR code và các element trên canvas mới
            self.qr_canvas.create_image(500, 300, image=self.qr_photo)
            self.qr_canvas.create_text(500, 100, text="SCAN QR CODE",
                                       font=("Inter", 20, "bold"), fill="#F2829E")
            self.qr_canvas.create_text(500, 130, text="Please scan the QR code to complete payment",
                                       font=("Inter", 14), fill="#89A34E")

            close_btn = self.qr_canvas.create_image(30, 23, image=self.image_cache["payment_close"])
            self.qr_canvas.tag_bind(close_btn, "<Button-1>", lambda e: self.close_payment_frame())

            # Nút Confirm
            confirm_btn = self.qr_canvas.create_image(300, 510, image=self.image_cache["payment5"])
            self.qr_canvas.create_text(300, 507, text="CONFIRM PAYMENT",
                                       font=("Inter Bold", 16, "bold"),
                                       fill="#FFFFFF")
            self.qr_canvas.tag_bind(confirm_btn, "<Button-1>", lambda e: self.payment_successful())

            # Nút Cancel
            cancel_btn = self.qr_canvas.create_image(700, 510, image=self.image_cache["payment5"])
            self.qr_canvas.create_text(700, 507, text="CANCEL",
                                       font=("Inter Bold", 16, "bold"),
                                       fill="#FFFFFF")
            self.qr_canvas.tag_bind(cancel_btn, "<Button-1>", lambda e: self.cancel_qr())

        except Exception as e:
            print(f"Lỗi khi hiển thị QR: {e}")

    def cancel_qr(self):
        """Huỷ giao diện QR"""
        try:
            if hasattr(self, 'qr_canvas'):
                self.qr_canvas.destroy()
        except Exception as e:
            print(f"Lỗi khi huỷ QR: {e}")

    def add_to_purchase(self, song=None):
        """Thêm bài hát vào danh sách purchase (khi thanh toán thành công)"""
        song = self.track_data
        if not song:
            print("Không có bài hát để thêm vào purchase.")
            return False

        try:
            db = self.controller.get_db()
            user_id = str(session.current_user.get("userId"))
            track_id = song.get("trackId")

            # Kiểm tra đã mua trước đó chưa
            if db.db["purchase"].find_one({"userId": user_id, "trackId": track_id}):
                print("Bài hát đã được mua trước đó.")
                return True

            # Tạo ObjectId mới
            purchase_object_id = ObjectId()

            purchased_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

            # Dữ liệu purchase mới
            new_purchase = {
                "_id": purchase_object_id,
                "purchaseId": str(purchase_object_id)[-6:],
                "userId": user_id,
                "trackId": track_id,
                "trackName": song.get("trackName"),
                "artistName": song.get("artistName"),
                "artworkUrl100": song.get("artworkUrl100", "assets/default.png"),
                "purchased_at": purchased_time
            }

            # Lưu vào MongoDB
            db.insert_one("purchase", new_purchase)
            return True

        except Exception as e:
            print(f"Lỗi khi thêm purchase: {e}")
            return False

    # PHIÊN BẢN TỐI ƯU - ĐỌC TRỰC TIẾP TỪ DB
    def payment_successful(self):
        """Xử lý khi thanh toán thành công - Phiên bản tối ưu"""
        try:
            # XÓA CANVAS QR TRƯỚC
            self.add_to_purchase()
            if hasattr(self, 'qr_canvas'):
                self.qr_canvas.destroy()

            # TẠO CANVAS SUCCESS MỚI
            self.success_canvas = Canvas(self, bg="#FEFBE5", height=600,
                                         width=1000,
                                         bd=0, highlightthickness=0,
                                         relief="ridge")
            self.success_canvas.place(x=0, y=0)

            # Load background
            self.success_canvas.create_image(500, 320, image=self.image_cache["payment_bg"])
            self.success_canvas.create_image(500, 20, image=self.image_cache["payment1"])

            # Hiển thị success message
            self.success_canvas.create_text(500, 250,
                                            text="PAYMENT SUCCESSFUL!",
                                            font=("Inter", 24, "bold"),
                                            fill="#89A34E")
            self.success_canvas.create_text(500, 300,
                                            text="Thank you for your purchase!",
                                            font=("Inter", 16), fill="#F2829E")

            print("Payment successful - MainScreen sẽ kiểm tra DB trực tiếp")

            # Tự động quay về home sau 2 giây
            self.after(2000, self.close_payment_frame)

        except Exception as e:
            print(f"Lỗi khi xử lý thành công: {e}")

    def close_payment_frame(self):
        """Đóng payment frame và quay về MainScreen"""
        try:
            self.controller.destroy_frame("Payment")
        except Exception as e:
            print(f"Lỗi khi đóng payment frame: {e}")







