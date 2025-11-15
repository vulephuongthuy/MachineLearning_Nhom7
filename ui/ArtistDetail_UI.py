import tkinter as tk
from tkinter import Frame, Canvas, Label
from urllib.request import urlopen

from customtkinter import CTkButton

import session
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
        self.place(x=80, y=90)

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
        self.albums_count_label.grid(row=2, column=0, sticky="w", padx=(18, 5), pady=(0, 25))

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

    def on_album_click(self, album_name):
        """Khi click album -> hiển thị danh sách bài hát"""
        if not self._is_destroyed:
            print(f"🎵 Clicked album: {album_name}")
            self.show_album_tracks(album_name)

    def show_album_tracks(self, album_name):
        """Hiển thị danh sách bài hát trong album"""
        if self._is_destroyed:
            return

        # Ẩn albums container
        self.albums_container.grid_forget()

        # Load và hiển thị tracks TRỰC TIẾP trong content_frame
        self.load_album_tracks(album_name)

    def load_album_tracks(self, album_name):
        """Load danh sách bài hát từ album"""
        try:
            tracks = list(db.db["tracks"].find(
                {"collectionName": album_name}
            ).sort("trackNumber", 1))

            print(f"🎵 Found {len(tracks)} tracks in album: {album_name}")
            self.display_album_tracks(tracks)

        except Exception as e:
            print(f"❌ Error loading album tracks: {e}")
            self.show_tracks_error_message()

    def display_album_tracks(self, tracks):
        """Hiển thị danh sách bài hát TRỰC TIẾP trong content_frame"""
        if self._is_destroyed:
            return

        # Tạo container cho tracks NGAY trong content_frame
        self.tracks_container = Frame(self.content_frame, bg="#F7F7DC")
        self.tracks_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # Với mỗi track, tạo track item
        for track in tracks:
            self.create_album_track_item(track)

    def create_album_track_item(self, track):
        """Tạo track item cho album - giống y hệt genre tracks"""
        # Lấy full song data
        song_data = self.get_full_track_data(track)

        # Tạo UI frame
        frame = Frame(self.tracks_container, bg="#F7F7DC", padx=10, pady=5)
        frame.pack(fill="x", expand=True)

        # Tạo image label và load ảnh
        img_label = Label(frame, bg="#F7F7DC", width=100, height=100)
        img_label.pack(side="left", padx=10)
        self.load_track_image_async(track, song_data, img_label)

        # Tạo text info
        text_frame = Frame(frame, bg="#F7F7DC")
        text_frame.pack(side="left", fill="x", expand=True)

        track_name = self.truncate_text(track.get("trackName", "Unknown"), 40)
        artist_name = self.truncate_text(track.get("artistName", "Unknown Artist"), 30)

        text_color = "#89A34E"
        title_label = Label(text_frame, text=track_name,
                            font=("Coiny Regular", 18), fg=text_color, bg="#F7F7DC")
        title_label.pack(anchor="w")

        artist_label = Label(text_frame, text=artist_name,
                             font=("Newsreader Regular", 14), fg=text_color, bg="#F7F7DC")
        artist_label.pack(anchor="w")

        # Widgets list để bind events
        widgets = [frame, img_label, title_label, artist_label]

        # Kiểm tra purchase status và bind events
        self.check_and_bind_purchase_events(widgets, track, song_data)

    def truncate_text(self, text, max_length):
        """Cắt ngắn text nếu quá dài"""
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def show_tracks_error_message(self):
        """Hiển thị thông báo lỗi khi load tracks"""
        if self._is_destroyed:
            return

        error_label = Label(
            self.content_frame,
            text="❌ Error loading tracks",
            bg="#F7F7DC",
            fg="#FF6B6B",
            font=("Inter", 16)
        )
        error_label.grid(row=2, column=0, padx=20, pady=50)

    def get_full_track_data(self, track):
        """Lấy full track data từ MongoDB"""
        try:
            db = self.controller.get_db()
            track_id = track.get('trackId')
            return db.db["tracks"].find_one({"trackId": int(track_id)}) or track
        except Exception as e:
            print(f"❌ Error loading song data: {e}")
            return track

    def load_track_image_async(self, track, song_data, img_label):
        """Tải ảnh bất đồng bộ"""

        def load_image():
            try:
                img = None
                if song_data and song_data.get("artworkUrl100"):
                    url = song_data.get("artworkUrl100")

                    if url in self.image_cache:
                        img = self.image_cache[url]
                    else:
                        image_bytes = urlopen(url).read()
                        pil_image = Image.open(BytesIO(image_bytes))
                        pil_image = pil_image.resize((100, 100), Image.Resampling.LANCZOS)
                        img = ImageTk.PhotoImage(pil_image)
                        self.image_cache[url] = img

                self.parent.after(0, lambda: self.update_image_label(img_label, img, track))

            except Exception as e:
                print(f"❌ Error loading image: {e}")
                self.parent.after(0, lambda: self.update_image_label(img_label, None, track))

        threading.Thread(target=load_image, daemon=True).start()

    def update_image_label(self, img_label, img, track):
        """Cập nhật image label"""
        if img_label.winfo_exists():
            if img:
                img_label.config(image=img)
                img_label.image = img
            else:
                img_label.config(text="🎵", font=("Arial", 24), fg="#89A34E")

    def check_and_bind_purchase_events(self, widgets, track, song_data):
        """Kiểm tra purchase status và bind events"""

        def check_purchase():
            try:
                db = self.controller.get_db()
                user_id = session.current_user.get("userId")

                if not user_id:
                    return

                purchased = db.db["purchase"].find_one({
                    "userId": user_id,
                    "trackId": track.get('trackId')
                })

                self.parent.after(0, lambda: self.bind_events_based_on_purchase(
                    widgets, purchased, track, song_data
                ))

            except Exception as e:
                print(f"❌ Error checking purchase: {e}")
                self.parent.after(0, lambda: self.bind_payment_events(widgets, song_data))

        threading.Thread(target=check_purchase, daemon=True).start()

    def bind_events_based_on_purchase(self, widgets, purchased, track, song_data):
        """Bind events dựa trên trạng thái purchase"""
        frame, img_label, title_label, artist_label = widgets
        if purchased:
            self.bind_play_events(widgets, track.get('trackId'))
        else:
            self.bind_payment_events(widgets, song_data)
            # Thêm nút mua hàng
            self.add_buy_button(frame, song_data)

    def add_buy_button(self, parent_frame, song_data):
        """Thêm nút mua hàng vào frame"""
        try:
            # Tạo ảnh cho nút giá
            self.image_cache["buy_btn"] = load_image("Buy_button.png")

            buy_btn = CTkButton(
                parent_frame,
                image=self.image_cache["buy_btn"],
                text="",
                hover_color="#F7F7DC",
                fg_color="#F7F7DC",
                bg_color="#F7F7DC",
                border_width=0,
                corner_radius=0,
                cursor="hand2",
                command=lambda s=song_data: self.controller.process_payment(s)
            )
            buy_btn.pack(side="right", padx=(0, 10))

        except Exception as e:
            print(f"❌ Lỗi khi tạo nút mua hàng: {e}")

    def bind_play_events(self, widgets, track_id):
        """Bind sự kiện phát nhạc - sử dụng songs từ parent"""

        def play_handler(event, t_id=track_id):
            print(f"🎵 Playing track {t_id}")

            # 🔥 DEBUG: KIỂM TRA CẤU TRÚC
            print(f"   - Có parent: {hasattr(self, 'parent')}")
            if hasattr(self, 'parent'):
                print(f"   - Có songs: {hasattr(self.parent, 'songs')}")
                print(f"   - Type của songs: {type(self.parent.songs)}")
                print(f"   - Có on_song_click: {hasattr(self.parent.songs, 'on_song_click')}")

            # 🔥 SỬ DỤNG SONGS TỪ PARENT
            if hasattr(self, 'parent') and hasattr(self.parent, 'songs'):
                if hasattr(self.parent.songs, 'on_song_click'):
                    self.parent.songs.on_song_click(t_id)
                    print("✅ Đã gọi on_song_click thành công")
                else:
                    print("❌ songs không có hàm on_song_click")
            else:
                print("❌ Không tìm thấy songs từ parent")

        for widget in widgets:
            widget.bind("<Button-1>", play_handler)
            widget.config(cursor="hand2")

    def bind_payment_events(self, widgets, song_data):
        """Bind sự kiện mua hàng"""
        for widget in widgets:
            widget.bind("<Button-1>", lambda e, data=song_data: self.controller.process_payment(data))
            widget.config(cursor="hand2")
