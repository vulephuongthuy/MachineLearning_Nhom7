import tkinter as tk
from tkinter import Frame, Canvas, Label
from customtkinter import CTkButton
from functions import load_image, relative_to_assets
from Connection.connector import db
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading


class ArtistDetailFrame(Frame):
    def __init__(self, parent, controller, artist_name):
        super().__init__(parent)
        self.parent = parent  # MainScreen instance
        self.controller = controller
        self.artist_name = artist_name
        self.image_cache = {}
        self.album_widgets = []
        self.photo_images = []
        self._is_destroyed = False

        # CHỈ chiếm phần content area, không đè lên toolbar và search
        self.configure(bg="#F7F7DC", width=900, height=410)
        self.place(x=100, y=90)

        self.setup_scrollable_frame()

        # QUAN TRỌNG: Đăng ký frame với MainScreen để quản lý
        self._register_with_parent()

        self.setup_ui()
        self.load_artist_data()

    def setup_scrollable_frame(self):
        """Tạo scrollable frame chỉ dùng mouse wheel"""
        # Tạo canvas
        self.canvas = Canvas(
            self,
            width=897,
            height=408,
            bg="#F7F7DC",
            bd=0,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Tạo frame chứa nội dung
        self.content_frame = Frame(self.canvas, bg="#F7F7DC")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw",
            width=897
        )

        # Bind sự kiện cuộn - QUAN TRỌNG: tự xử lý scroll
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_frame_configure(self, event):
        """Cập nhật scrollregion"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _register_with_parent(self):
        """Đăng ký frame với MainScreen để quản lý visibility"""
        if hasattr(self.parent, '_active_frames'):
            self.parent._active_frames.append(self)
        else:
            self.parent._active_frames = [self]

    def _unregister_from_parent(self):
        """Hủy đăng ký khỏi MainScreen"""
        if hasattr(self.parent, '_active_frames') and self in self.parent._active_frames:
            self.parent._active_frames.remove(self)

    def hide(self):
        """Ẩn frame mà không destroy"""
        if not self._is_destroyed and self.winfo_exists():
            self.place_forget()

    def show(self):
        """Hiển thị frame"""
        if not self._is_destroyed:
            self.place(x=100, y=90)

    def setup_ui(self):
        if self._is_destroyed:
            return

        # Nút back với style đẹp hơn - DÙNG CONTENT_FRAME
        self.back_button = CTkButton(
            self.content_frame,
            text="← Back to Home",
            command=self.go_back,
            fg_color="#89A34E",
            hover_color="#7A9345",
            text_color="#FFFFFF",
            font=("Inter", 14, "bold"),
            width=120,
            height=35,
            corner_radius=8
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=20, pady=20)

        # Tiêu đề với style đẹp hơn - DÙNG CONTENT_FRAME
        self.title_label = Label(
            self.content_frame,
            text=f"{self.artist_name}",
            bg="#F7F7DC",
            fg="#89A34E",
            font=("Inter", 22, "bold")
        )
        self.title_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

    def load_artist_data(self):
        if self._is_destroyed:
            return
        print(f" Đang tải thông tin nghệ sĩ: {self.artist_name}")
        try:
            # CÁCH 1: Query trực tiếp từ collection "collections" để lấy đầy đủ album
            albums_from_collections = list(db.db["collections"].find(
                {"artistName": self.artist_name}
            ))
            # CÁCH 2: Vẫn query từ "tracks" để lấy artwork (fallback)
            tracks = list(db.db["tracks"].find(
                {"artistName": self.artist_name}
            ))
            print(f"Tìm thấy {len(albums_from_collections)} album từ collections")
            print(f"Tìm thấy {len(tracks)} bài hát từ tracks")
            # Kết hợp dữ liệu từ cả 2 collections
            albums = {}
            # Ưu tiên lấy từ collections trước (có đầy đủ thông tin album)
            for album in albums_from_collections:
                album_name = album.get("collectionName", "Unknown Album")
                if album_name and album_name not in albums:
                    albums[album_name] = {
                        'track_count': album.get("trackCount", 0),
                        'release_date': album.get("releaseDate", ""),
                        'genre': album.get("primaryGenreName", ""),
                        'artwork_url': ""  # Tạm thời để trống
                    }
            # Bổ sung artwork từ tracks
            for track in tracks:
                album_name = track.get("collectionName", "Unknown Album")
                artwork_url = track.get("artworkUrl100", "")

                if album_name in albums and artwork_url:
                    # Có artwork từ tracks, cập nhật vào album
                    high_res_url = artwork_url.replace("100x100", "300x300")
                    albums[album_name]['artwork_url'] = high_res_url
                elif album_name not in albums:
                    # Album không có trong collections, thêm từ tracks
                    albums[album_name] = {
                        'track_count': 1,  # Ước lượng
                        'release_date': track.get("releaseDate", ""),
                        'genre': track.get("primaryGenreName", ""),
                        'artwork_url': artwork_url.replace("100x100", "300x300") if artwork_url else ""
                    }

            print(f"🎵 Tổng hợp được {len(albums)} album của {self.artist_name}")

            self.display_all_albums(albums)

        except Exception as e:
            if not self._is_destroyed:
                print(f"Lỗi khi tải thông tin nghệ sĩ: {e}")
                self.show_error_message()

    def display_all_albums(self, albums):
        if self._is_destroyed:
            return

        if not albums:
            self.show_no_albums_message()
            return

        # Hiển thị thông báo số lượng album với style đẹp hơn - DÙNG CONTENT_FRAME
        self.albums_count_label = Label(
            self.content_frame,
            text=f"{len(albums)} Albums Found",
            bg="#F7F7DC",
            fg="#F586A3",
            font=("Inter", 16, "bold")
        )
        self.albums_count_label.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 25))

        self.clear_album_widgets()

        # Tạo frame cho grid album - DÙNG CONTENT_FRAME
        self.albums_container = Frame(self.content_frame, bg="#F7F7DC")
        self.albums_container.grid(row=3, column=0, sticky="w", padx=0, pady=(0, 20))

        albums_list = list(albums.items())

        for i, (album_name, album_data) in enumerate(albums_list):
            if self._is_destroyed:
                break
            row = i // 4
            col = i % 4
            self.create_album_item(row, col, album_name, album_data)

    def create_album_item(self, row, col, album_name, album_data):
        if self._is_destroyed:
            return

        # Frame chứa album
        album_frame = Frame(
            self.albums_container,
            bg="#F1EBD0",
            padx=18,
            pady=18,
            relief="raised",
            bd=1
        )
        album_frame.grid(row=row, column=col, sticky="nsew", padx=15, pady=15)

        # Canvas cho ảnh album
        album_size = 150
        album_canvas = Canvas(
            album_frame,
            width=album_size,
            height=album_size,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#E5E5E5",
            bd=0
        )
        album_canvas.pack()

        # Khung ảnh
        album_canvas.create_rectangle(
            2, 2, album_size - 2, album_size - 2,
            fill="#F8F8F8",
            outline="#DDDDDD",
            width=1
        )

        loading_text = album_canvas.create_text(
            album_size / 2, album_size / 2,
            text="",
            fill="#89A34E",
            font=("Inter", 16)
        )

        # Xử lý tên album dài
        display_name = album_name
        if len(album_name) > 22:
            display_name = album_name[:20] + "..."

        # Tên album
        name_label = Label(
            album_frame,
            text=display_name,
            bg="#F1EBD0",
            fg="#2D3748",
            font=("Inter", 11, "bold"),
            wraplength=album_size - 10,
            justify="center",
            cursor="hand2"
        )
        name_label.pack(pady=(8, 0))

        # THÊM THÔNG TIN ALBUM (track count, genre)
        track_count = album_data.get('track_count', 0)

        info_text = f"{track_count} track"
        if track_count > 1:
            info_text += "s"
        info_label = Label(
            album_frame,
            text=info_text,
            bg="#F1EBD0",
            fg="#89A34E",
            font=("Inter", 9),
            cursor="hand2"
        )
        info_label.pack(pady=(2, 0))

        album_widget = {
            'frame': album_frame,
            'canvas': album_canvas,
            'loading_text': loading_text,
            'name_label': name_label,
            'info_label': info_label,
            'album_name': album_name
        }
        self.album_widgets.append(album_widget)

        # Tải ảnh
        artwork_url = album_data.get('artwork_url', '')
        if artwork_url:
            threading.Thread(
                target=self.load_album_artwork,
                args=(album_widget, artwork_url, album_size),
                daemon=True
            ).start()
        else:
            self.show_placeholder_image(album_widget, album_size)

        self.add_hover_effect(album_widget)

    def load_album_artwork(self, album_widget, url, size):
        if self._is_destroyed:
            return

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(BytesIO(image_data))
                image = image.resize((size - 4, size - 4), Image.Resampling.LANCZOS)

                if not self._is_destroyed:
                    self.after(0, self.update_album_image, album_widget, image, size)
            else:
                if not self._is_destroyed:
                    self.after(0, self.show_placeholder_image, album_widget, size)

        except Exception as e:
            if not self._is_destroyed:
                print(f" Lỗi khi tải ảnh: {e}")
                self.after(0, self.show_placeholder_image, album_widget, size)

    def update_album_image(self, album_widget, image, size):
        if self._is_destroyed:
            return

        try:
            photo = ImageTk.PhotoImage(image)
            self.photo_images.append(photo)
            album_widget['canvas'].delete("all")

            # Vẽ background trước
            album_widget['canvas'].create_rectangle(
                2, 2, size - 2, size - 2,
                fill="#F8F8F8",
                outline="#DDDDDD",
                width=1
            )

            # Hiển thị ảnh
            album_widget['canvas'].create_image(
                size / 2, size / 2,
                image=photo,
                anchor="center"
            )
        except Exception as e:
            if not self._is_destroyed:
                print(f" Lỗi khi cập nhật ảnh: {e}")
                self.show_placeholder_image(album_widget, size)

    def show_placeholder_image(self, album_widget, size):
        if self._is_destroyed:
            return

        try:
            album_widget['canvas'].delete("all")
            # Background
            album_widget['canvas'].create_rectangle(
                2, 2, size - 2, size - 2,
                fill="#F8F8F8",
                outline="#DDDDDD",
                width=1
            )
            # Icon nhạc
            album_widget['canvas'].create_text(
                size / 2, size / 2,
                text="🎵",
                font=("Inter", 20),
                fill="#89A34E"
            )
        except:
            pass

    def add_hover_effect(self, album_widget):
        if self._is_destroyed:
            return

        def on_enter(e):
            if not self._is_destroyed:
                album_widget['frame'].config(bg="#F0F7E4", relief="sunken")
                album_widget['name_label'].config(bg="#F0F7E4", fg="#F586A3")
                album_widget['info_label'].config(bg="#F0F7E4", fg="#F586A3")
                album_widget['canvas'].config(highlightbackground="#89A34E")

        def on_leave(e):
            if not self._is_destroyed:
                album_widget['frame'].config(bg="#F1EBD0", relief="raised")
                album_widget['name_label'].config(bg="#F1EBD0", fg="#2D3748")
                album_widget['info_label'].config(bg="#F1EBD0", fg="#89A34E")
                album_widget['canvas'].config(highlightbackground="#E5E5E5")

        def on_click(e):
            if not self._is_destroyed:
                self.on_album_click(album_widget['album_name'])

        # Bind events cho tất cả widgets
        for widget in [album_widget['frame'], album_widget['canvas'],
                       album_widget['name_label'], album_widget['info_label']]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def on_album_click(self, album_name):
        if not self._is_destroyed:
            print(f"🎵 Clicked album: {album_name}")

    # THÊM CÁC PHƯƠNG THỨC CÒN THIẾU
    def clear_album_widgets(self):
        """Xóa tất cả widget album cũ"""
        for widget_data in self.album_widgets:
            try:
                if not self._is_destroyed:
                    widget_data['frame'].destroy()
            except:
                pass
        self.album_widgets.clear()
        self.photo_images.clear()

    def show_no_albums_message(self):
        """Hiển thị thông báo khi không có album"""
        if self._is_destroyed:
            return

        no_albums_label = Label(
            self.content_frame,
            text="🎵 No albums found for this artist",
            bg="#F7F7DC",
            fg="#89A34E",
            font=("Inter", 16)
        )
        no_albums_label.grid(row=3, column=0, padx=20, pady=50)

    def show_error_message(self):
        """Hiển thị thông báo lỗi"""
        if self._is_destroyed:
            return

        error_label = Label(
            self.content_frame,
            text="❌ Error loading artist data",
            bg="#F7F7DC",
            fg="#FF6B6B",
            font=("Inter", 16)
        )
        error_label.grid(row=3, column=0, padx=20, pady=50)

    def go_back(self):
        """Quay lại HomeScreen - FIX: HIỂN THỊ LẠI HOME CONTENT"""
        if not self._is_destroyed:
            self._is_destroyed = True

            # QUAN TRỌNG: Hiển thị lại home content trước
            if hasattr(self.parent, 'songs'):
                self.parent.songs.canvas.place(x=103, y=90)
                self.parent.songs.fixed_canvas.place(x=50, y=522)

            # Cập nhật title về "Home"
            if hasattr(self.parent, 'buttons'):
                self.parent.buttons.current_title = "Home"
                self.parent.buttons.create_title()

            # Cleanup
            try:
                self.canvas.unbind_all("<MouseWheel>")
            except:
                pass

            self._unregister_from_parent()
            self.destroy()

    def destroy(self):
        self._is_destroyed = True
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except:
            pass
        self._unregister_from_parent()
        super().destroy()