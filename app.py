from ui.homescreen import MainScreen
from ui.Login_UI import *
from Connection.connector import db
import subprocess
import threading


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Moo_d Music")
        self.geometry("1000x600+120+15")
        self.iconbitmap(relative_to_assets("logo.ico"))
        self.configure(bg="white")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Dùng Frame làm container
        self.container = Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Kết nối database (Singleton)
        self.db = db

        # Dictionary để lưu trữ frames
        self.frames = {}
        self.current_frame = None

        # Hiển thị frame đầu tiên
        self.show_frame("LoginFrame")
        # self.show_frame("ProfileFrame")

    def get_db(self):
        return self.db

    def process_payment(self, song):
        """Xử lý mua bài hát - có thể gọi từ mọi frame"""
        track = song.get("trackName", "Unknown Song")
        artist = song.get("artistName", "Unknown Artist")
        print(f"Người dùng nhấn mua: {track} - {artist}")

        # Hiển thị frame Payment
        self.show_frame("Payment")

        # Truyền dữ liệu bài hát sang Payment frame
        payment_frame = self.frames["Payment"]
        payment_frame.set_track(song)

    def show_frame(self, page_name):
        """Hiển thị frame với lazy loading"""
        print(f"Switching to: {page_name}")

        # Tạo frame nếu chưa có hoặc đã bị hủy
        if page_name not in self.frames or not self.frames[page_name].winfo_exists():
            print(f"Creating new frame: {page_name}")
            frame_class = self.get_frame_class(page_name)
            frame = frame_class(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Hiển thị frame
        frame = self.frames[page_name]
        frame.tkraise()
        self.current_frame = frame

        # Gọi callback
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def get_frame_class(self, page_name):
        """Map tên frame tới class"""
        frames_map = {
            "LoginFrame": LoginFrame,
            "SignUpFrame": SignUpFrame,
            "MoodTracker": MoodTracker,
            "LoadingPage": LoadingPage,
            "HomeScreen": MainScreen,
            "Payment": Payment
        }
        return frames_map[page_name]

    def destroy_frame(self, page_name):
        """Hủy frame để giải phóng bộ nhớ"""
        if page_name in self.frames:
            # Không hủy frame đang hiện tại
            # if self.current_frame and self.current_frame.__class__.__name__ == page_name:
            #     print(f"Cannot destroy current frame: {page_name}")
            #     return

            self.frames[page_name].destroy()
            del self.frames[page_name]
            print(f" Destroyed: {page_name}")

    import threading
    import subprocess
    import os

    def retrain_background(self):
        """Chạy retrain nền bằng thread + Popen."""

        def _run():
            try:
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retrain_model_artist.py")
                subprocess.Popen(["python", script_path])
                print(" Retrain đang chạy ngầm…")
            except Exception as e:
                print(f" Retrain thất bại: {e}")

        threading.Thread(target=_run, daemon=True).start()

    def logout(self):
        """Logout - hiển thị LoginFrame và hủy các frame khác"""
        print("Logging out...")

        threading.Thread(target=self.retrain_background, daemon=True).start()

        # Hiển thị LoginFrame trước
        self.show_frame("LoginFrame")

        # Reset session data
        if hasattr(self, 'session'):
            self.session.current_user = None

        # Hủy các frame không phải LoginFrame
        frames_to_destroy = [name for name in list(self.frames.keys()) if name != "LoginFrame"]

        for frame_name in frames_to_destroy:
            print(f"Destroying: {frame_name}")
            self.destroy_frame(frame_name)

        print(" Logout successful")

    def on_close(self):
        """Thoát ứng dụng"""
        # ĐÓNG KẾT NỐI DATABASE
        threading.Thread(target=self.retrain_background, daemon=True).start()

        try:
            self.db.close_connection()
        except Exception as e:
            print(f"Lỗi khi đóng kết nối DB: {e}")

        self.quit()
        self.destroy()
        sys.exit()
