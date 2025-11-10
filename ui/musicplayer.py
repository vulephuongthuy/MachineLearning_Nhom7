import random
import threading
import tkinter as tk
import sys
from tkinter import *
import json, requests
from io import BytesIO
import requests
import vlc
from PIL import Image, ImageTk, ImageDraw, ImageOps
import time

import session
from functions import *
from Rating_manager import RatingManager
from tooltips import Tooltip
from Connection import connector
from Connection.connector import Connector
from Song_mood_manager import MoodManager
from session import current_user
from recommendation_player import ContentRecommendationEngine


class MoodPlayerFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent

        self.frame = self
        self.configure(bg="#C5D7A1")

        # 🔥 THÊM RATING AREA CHO FALLBACK
        self.rating_area = Frame(self, bg="#F7F7DC")
        self.rating_frame = None

        self.rating_manager = RatingManager()
        self.tracklist_images = []
        self.image_cache = {}

        # 🔥 THÊM MOOD AREA
        self.mood_area = Frame(self, bg="#F7F7DC")
        self.mood_frame = None

        self.mood_manager = MoodManager()

        # 🔥 BỎ CÁC BIẾN STATE TRÙNG - chỉ giữ biến UI
        self.songs = None  # 🔥 THÊM DÒNG NÀY
        self.progress_loop_id = None  # Giữ vì là UI-specific
        self.duration = 30
        self.current_song = None  # 🔥 THÊM DÒNG NÀY
        self.current_index = -1  # 🔥 THÊM DÒNG NÀY
        self.current_time = 0  # 🔥 THÊM DÒNG NÀY
        self.is_playing = False  # 🔥 THÊM DÒNG NÀY


        db_connector = Connector()
        tracks_db = db_connector.db["tracks"]
        purchase_db = db_connector.db["purchase"]

        self.engine = ContentRecommendationEngine(
            'models/content_based_model.pkl',
            tracks_db,
            purchase_db
        )
        print("✅ FULL MATRIX Engine initialized!")

        # 🔥 BỎ load songs - MainScreen đã load rồi
        self.main_callbacks = []  # 🔥 CALLBACKS ĐẾN MAINSCREEN
        self.setup_ui()

        # Bind auto-recommend
        # self.bind("<<ShowFrame>>", self.on_show_frame)

    # def on_show_frame(self, event=None):
    #     """TỰ ĐỘNG rec khi frame hiển thị"""
    #     print("🎵 Auto-generating recommendations...")
    #     recommendations = self.get_recommendations_for_display(limit=8, purpose="log")

    # def get_recommendations_for_display(self, limit=8, purpose="display"):
    #     """Hàm của Frame - đặt tên khác để không override engine"""
    #     try:
    #         # Lấy data
    #         current_user = self.get_current_user()
    #         user_id = current_user.get("userId") if current_user else "113025"
    #
    #         current_track_id = None
    #
    #         print("🔍 ===== DEBUG CURRENT TRACK ===== ")
    #
    #         # 🔍 DEBUG 1: Kiểm tra shared_state
    #         print(f"🔍 [1] hasattr(self, 'shared_state'): {hasattr(self, 'shared_state')}")
    #         if hasattr(self, 'shared_state'):
    #             print(f"🔍 [2] self.shared_state: {self.shared_state}")
    #             if self.shared_state:
    #                 print(
    #                     f"🔍 [3] hasattr(self.shared_state, 'current_song'): {hasattr(self.shared_state, 'current_song')}")
    #                 if hasattr(self.shared_state, 'current_song'):
    #                     print(f"🔍 [4] self.shared_state.current_song: {self.shared_state.current_song}")
    #                     if self.shared_state.current_song:
    #                         current_track_id = self.shared_state.current_song.get("trackId")
    #                         print(f"🔍 [5] trackId from shared_state: {current_track_id}")
    #
    #         # 🔍 DEBUG 2: Kiểm tra current_song trực tiếp
    #         print(f"🔍 [6] hasattr(self, 'current_song'): {hasattr(self, 'current_song')}")
    #         if hasattr(self, 'current_song'):
    #             print(f"🔍 [7] self.current_song: {self.current_song}")
    #             if self.current_song:
    #                 current_track_id_from_direct = self.current_song.get("trackId")
    #                 print(f"🔍 [8] trackId from current_song: {current_track_id_from_direct}")
    #                 if current_track_id_from_direct and not current_track_id:
    #                     current_track_id = current_track_id_from_direct
    #                     print(f"🔍 [9] Using trackId from current_song: {current_track_id}")
    #
    #         # 🔍 DEBUG 3: Kiểm tra controller
    #         print(f"🔍 [10] hasattr(self, 'controller'): {hasattr(self, 'controller')}")
    #         if hasattr(self, 'controller'):
    #             print(
    #                 f"🔍 [11] hasattr(self.controller, 'current_song_id'): {hasattr(self.controller, 'current_song_id')}")
    #             if hasattr(self.controller, 'current_song_id'):
    #                 print(
    #                     f"🔍 [12] self.controller.current_song_id: {getattr(self.controller, 'current_song_id', 'NOT_SET')}")
    #
    #         print(f"🔍 [FINAL] current_track_id: {current_track_id}")
    #         print("🔍 ===== END DEBUG ===== ")
    #
    #         current_mood = "Neutral"
    #
    #         # Log tùy purpose
    #         if purpose == "log":
    #             print(f"🎯 Auto-recommend: user={user_id}, track={current_track_id}")
    #
    #         # Gọi engine
    #         recommendations = self.engine.get_recommendations(
    #             current_track_id, current_mood, user_id, limit
    #         )
    #
    #         if purpose == "log":
    #             print(f"✅ Found {len(recommendations)} recommendations")
    #
    #         return recommendations
    #
    #     except Exception as e:
    #         print(f"❌ Error in get_recommendations_for_display: {e}")
    #         return []
    def get_recommendations_for_display(self, limit=8, purpose="display"):
        """Hàm của Frame - lấy gợi ý bài hát dựa trên bài hiện tại và mood"""
        try:
            # Lấy data
            current_user = self.get_current_user()
            user_id = current_user.get("userId") if current_user else "113025"

            current_track_id = None

            print("🔍 ===== DEBUG CURRENT TRACK ===== ")

            # 🔍 DEBUG 1: Kiểm tra songs_manager (shared_state thật)
            print(f"🔍 [1] hasattr(self, 'songs_manager'): {hasattr(self, 'songs_manager')}")
            if hasattr(self, 'songs_manager'):
                print(f"🔍 [2] self.songs_manager: {self.songs_manager}")
                if self.songs_manager:
                    print(
                        f"🔍 [3] hasattr(self.songs_manager, 'current_song'): {hasattr(self.songs_manager, 'current_song')}")
                    if hasattr(self.songs_manager, 'current_song'):
                        print(f"🔍 [4] self.songs_manager.current_song: {self.songs_manager.current_song}")
                        if self.songs_manager.current_song:
                            current_track_id = self.songs_manager.current_song.get("trackId")
                            print(f"🔍 [5] trackId from songs_manager: {current_track_id}")

            # 🔍 DEBUG 2: Kiểm tra current_song trực tiếp trong frame
            print(f"🔍 [6] hasattr(self, 'current_song'): {hasattr(self, 'current_song')}")
            if hasattr(self, 'current_song'):
                print(f"🔍 [7] self.current_song: {self.current_song}")
                if self.current_song:
                    current_track_id_from_direct = self.current_song.get("trackId")
                    print(f"🔍 [8] trackId from current_song: {current_track_id_from_direct}")
                    if current_track_id_from_direct and not current_track_id:
                        current_track_id = current_track_id_from_direct
                        print(f"🔍 [9] Using trackId from current_song: {current_track_id}")

            # 🔍 DEBUG 3: Kiểm tra controller (nếu có)
            print(f"🔍 [10] hasattr(self, 'controller'): {hasattr(self, 'controller')}")
            if hasattr(self, 'controller'):
                print(
                    f"🔍 [11] hasattr(self.controller, 'current_song_id'): {hasattr(self.controller, 'current_song_id')}")
                if hasattr(self.controller, 'current_song_id'):
                    print(
                        f"🔍 [12] self.controller.current_song_id: {getattr(self.controller, 'current_song_id', 'NOT_SET')}")

            print(f"🔍 [FINAL] current_track_id: {current_track_id}")
            print("🔍 ===== END DEBUG ===== ")

            # Mood mặc định
            current_mood = "Neutral"

            # Log tùy mục đích
            if purpose == "log":
                print(f"🎯 Auto-recommend: user={user_id}, track={current_track_id}")

            # Gọi engine sinh gợi ý
            recommendations = self.engine.get_recommendations(
                current_track_id, current_mood, user_id, limit
            )

            if purpose == "log":
                print(f"✅ Found {len(recommendations)} recommendations")

            return recommendations

        except Exception as e:
            print(f"❌ Error in get_recommendations_for_display: {e}")
            return []

    def get_current_user(self):
        """Lấy current_user theo cách import đặc biệt của bạn"""
        try:
            from FinalProject.session import current_user
            print(f"[REC] current_user from FinalProject.session: {current_user}")
            return current_user
        except ImportError:
            try:
                import session
                current_user = session.current_user
                print(f"[REC] current_user from session: {current_user}")
                return current_user
            except ImportError:
                from main import current_user
                print(f"[REC] current_user from main: {current_user}")
                return current_user

    # def update_recommendations_for_new_track(self, new_track_id):
    #     """Cập nhật recommendations khi user chọn bài mới"""
    #     print(f"🔄 Updating recommendations for new track: {new_track_id}")
    #
    #     # Lấy recommendations mới
    #     current_user = self.get_current_user()
    #     user_id = current_user.get("userId") if current_user else "113025"
    #     current_mood = "Neutral"
    #
    #     new_recommendations = self.engine.get_recommendations(
    #         new_track_id, current_mood, user_id, limit=8
    #     )
    #
    #     # 🔥 CÁCH 2: UPDATE TRỰC TIẾP - đơn giản hơn
    #     self.songs_recommend = new_recommendations  # Gán recommendations mới
    #     self.create_discover_section()  # Tạo lại UI với data mới
    #
    #     print(f"✅ Updated {len(new_recommendations)} recommendations for new track")

    def update_recommendations_for_new_track(self, new_track_id):
        """Cập nhật recommendations khi user chọn bài mới"""
        print(f"🔄 Updating recommendations for new track: {new_track_id}")

        # Lấy recommendations mới TRỰC TIẾP từ engine
        current_user = self.get_current_user()
        user_id = current_user.get("userId") if current_user else "113025"
        current_mood = "Neutral"

        # 🚨 GỌI TRỰC TIẾP ENGINE, KHÔNG qua get_recommendations_for_display
        new_recommendations = self.engine.get_recommendations(
            new_track_id, current_mood, user_id, limit=8
        )

        # Cập nhật recommendations mới
        self.songs_recommend = new_recommendations

        # 🚨 GỌI TRỰC TIẾP create_discover_section để update UI
        self.create_discover_section()

        print(f"✅ Updated {len(new_recommendations)} recommendations for new track")


    def redraw_ui(self):
        """Đảm bảo UI được hiển thị đúng cách"""
        print("[DEBUG] 🔄 Redrawing MoodPlayer UI...")

        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            print("[DEBUG] 🎨 Canvas không tồn tại, tạo mới...")
            self.setup_ui()
        else:
            print("[DEBUG] 🎨 Canvas đã tồn tại, đảm bảo hiển thị...")
            # 🔥 QUAN TRỌNG: ĐẢM BẢO PACK VÀ UPDATE
            self.canvas.pack_forget()  # 🔥 XÓA PACK CŨ TRƯỚC
            self.canvas.pack(fill="both", expand=True)  # 🔥 PACK LẠI
            self.canvas.update_idletasks()
            self.update_idletasks()

            # # 🔥 ĐẢM BẢO CÁC WIDGET CON ĐƯỢC HIỂN THỊ
            # if hasattr(self, 'create_disc_display'):
            #     self.create_disc_display()
            # if hasattr(self, 'create_progress_bar'):
            #     self.create_progress_bar()
            # # ... các method tạo UI khác ...

    def register_main_callback(self, callback):
        """Đăng ký callback đến MainScreen"""
        self.main_callbacks.append(callback)
        print(f"✅ Player đã đăng ký callback với MainScreen")

    def notify_main_song_changed(self, song, source="player"):
        """Thông báo bài hát thay đổi đến MainScreen"""
        print(f"🔔 Player thông báo bài hát mới đến MainScreen: {song.get('trackName', 'Unknown')}")
        for callback in self.main_callbacks:
            try:
                callback(song)
            except Exception as e:
                print(f"❌ Player callback error: {e}")

    def set_shared_state(self, songs_manager):
        """Nhận Song manager - chỉ giữ 1 callback duy nhất"""
        self.songs_manager = songs_manager
        print("🎵 DEBUG: MoodPlayerFrame đã nhận REAL shared state")

        # # 🔥 DEBUG QUAN TRỌNG: XEM THỰC SỰ SONGS_MANAGER LÀ GÌ
        # print(f"   - Type của songs_manager: {type(songs_manager)}")
        # print(f"   - Class name: {songs_manager.__class__.__name__}")
        # print(f"   - Có register_song_change_callback: {hasattr(songs_manager, 'register_song_change_callback')}")
        # print(f"   - Có register_repeat_callback: {hasattr(songs_manager, 'register_repeat_callback')}")

        # 🔥 CHỈ GIỮ 1 CALLBACK DUY NHẤT
        if hasattr(songs_manager, 'register_song_change_callback'):
            # Xóa tất cả callback cũ
            if hasattr(songs_manager, 'song_change_callbacks'):
                songs_manager.song_change_callbacks.clear()
                print("   🧹 Đã xóa tất cả callback cũ")

            songs_manager.register_song_change_callback(self.on_song_changed_from_main)
            print("✅ Đã đăng ký callback với Song manager")
            # 🔥 CALLBACK CHO REPEAT MODE (THÊM MỚI)
        if hasattr(songs_manager, 'register_repeat_callback'):
            songs_manager.register_repeat_callback(self.on_repeat_mode_changed)
            print("✅ Đã đăng ký repeat callback")
            # 🔥 ĐỒNG BỘ REPEAT MODE BAN ĐẦU
            if hasattr(songs_manager, 'repeat_mode'):
                current_mode = songs_manager.repeat_mode
                print(f"🔄 Player: Đồng bộ repeat mode ban đầu: {current_mode}")
                self.update_repeat_button_ui(current_mode)  # Cập nhật UI ngay lập tức
        self.update_player_display()
        if hasattr(songs_manager, "current_song") and songs_manager.current_song:
            print(f"🎯 READY: Có current_song -> auto recommend")
            self.auto_recommend()
        else:
            print("⚠️ Chưa có current_song, bỏ qua recommend lần đầu")
            # 🔥 ĐỒNG BỘ TRẠNG THÁI PHÁT NHẠC BAN ĐẦU
        if hasattr(songs_manager, 'is_playing'):
            print(f"🎵 Player: Đồng bộ trạng thái phát nhạc - is_playing: {songs_manager.is_playing}")
            if songs_manager.is_playing:
                self.start_disc_rotation(reset_angle=True)  # Bắt đầu xoay đĩa nếu đang phát
                self.show_pause_button()  # Hiển thị nút pause
            else:
                self.stop_disc_rotation()  # Dừng xoay đĩa nếu đang dừng
                self.show_play_button()  # Hiển thị nút play
        # 🔥 CALLBACK CHO LOVE SONG (THÊM MỚI)
        if hasattr(songs_manager, 'register_love_callback'):
            songs_manager.register_love_callback(self.on_love_state_changed)
            print("✅ Đã đăng ký love callback")

        # 🔥 ĐỒNG BỘ LOVE STATE BAN ĐẦU
        if hasattr(songs_manager, 'current_song') and songs_manager.current_song:
            self.sync_love_state(songs_manager.current_song)

    def on_love_state_changed(self, song, is_favorite):
        """Callback khi love state thay đổi từ MainScreen"""
        print(f"❤️ Player nhận love state: {song.get('trackName')} -> {is_favorite}")
        self.update_love_button_ui(is_favorite)

    def sync_love_state(self, song):
        """Đồng bộ trạng thái love ban đầu"""
        try:
            if hasattr(self, 'controller'):
                db = self.controller.get_db()
                user_id = int(session.current_user.get("userId"))
                track_id = song.get("trackId")

                existing = db.db["user_favorite"].find_one({
                    "userId": user_id,
                    "trackId": track_id
                })
                is_favorite = existing is not None
                self.update_love_button_ui(is_favorite)
                print(f"❤️ Player đồng bộ love state: {is_favorite}")
        except Exception as e:
            print(f"❌ Lỗi sync love state: {e}")

    def update_love_button_ui(self, is_favorite):
        """Cập nhật UI nút love trong Player"""
        print(f"❤️ Player update love UI: {is_favorite}")

        if hasattr(self, 'love_button') and self.love_button:
            try:
                # 🔥 CHỌN ẢNH THEO TRẠNG THÁI - DÙNG relative_to_assets
                icon_file = "heart (1).png" if is_favorite else "heart.png"
                icon_path = relative_to_assets(icon_file)

                # Load và resize ảnh
                icon_img = Image.open(icon_path).resize((35, 35), Image.Resampling.LANCZOS)
                icon_tk = ImageTk.PhotoImage(icon_img)

                # Cập nhật ảnh cho nút
                self.love_button.config(image=icon_tk)
                self.love_button.image = icon_tk  # Giữ reference

                print(f"✅ Đã cập nhật nút love: {icon_file}")

            except Exception as e:
                print(f"❌ Lỗi cập nhật nút love: {e}")
        else:
            print("❌ Không tìm thấy nút love để cập nhật")

    def setup_repeat_sync(self):
        """Thiết lập đồng bộ hóa repeat mode với SongsManager"""
        if hasattr(self, 'songs_manager'):
            self.songs_manager.register_repeat_callback(self.on_repeat_mode_changed)
            print("✅ Player: Đã đăng ký repeat callback với SongsManager")

    def on_repeat_mode_changed(self, mode):
        """Callback khi repeat mode thay đổi từ SongsManager"""
        print(f"🔄 Player nhận repeat mode: {mode}")
        print(f"   - Có repeat_button: {hasattr(self, 'repeat_button')}")
        print(f"   - Có repeat_images: {hasattr(self, 'repeat_images')}")
        self.update_repeat_button_ui(mode)

    def setup_repeat_images(self):
        """Khởi tạo hình ảnh với PIL"""
        self.repeat_images = {}

        image_paths = {
            0: "images/repeat.png",
            1: "images/repeat one time.png",
            2: "images/repeat always.png"
        }

        for mode, path in image_paths.items():
            try:
                image = Image.open(path)
                image = image.resize((30, 30))  # Resize nếu cần
                self.repeat_images[mode] = ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"❌ Lỗi load hình repeat {mode}: {e}")

    def update_repeat_button_ui(self, mode):
        """Cập nhật hình ảnh với PIL"""
        if hasattr(self, 'repeat_button') and hasattr(self, 'repeat_images'):
            if mode in self.repeat_images:
                self.repeat_button.config(image=self.repeat_images[mode])
                self.repeat_button.image = self.repeat_images[mode]

    def change_repeat_mode(self):
        """Khi người dùng bấm nút repeat ở Player"""
        print("🎵 Player: Nút repeat được click")
        if hasattr(self, 'songs_manager'):
            current_mode = self.songs_manager.repeat_mode
            new_mode = (current_mode + 1) % 3  # 0→1→2→0
            self.songs_manager.set_repeat_mode(new_mode, source="player")
            print(f"🔄 Player: Đã chuyển repeat mode sang {new_mode}")
        else:
            print("❌ Player: Không có songs_manager")
    # def auto_recommend(self):
    #     """Gọi recommendations - cho phép update khi bài thay đổi"""
    #     if not hasattr(self, "songs_manager") or not self.songs_manager:
    #         print("⚠️ Chưa có songs_manager, không thể recommend")
    #         return
    #
    #     # 🎯 KIỂM TRA NẾU BÀI ĐÃ THAY ĐỔI (thay vì chặn hoàn toàn)
    #     current_track_id = self.songs_manager.current_song.get("trackId") if self.songs_manager.current_song else None
    #
    #     if hasattr(self, '_last_recommend_track_id') and self._last_recommend_track_id == current_track_id:
    #         print("⏸️ Recommendations already generated for this track, skipping...")
    #         return
    #
    #     print("🎵 Generating recommendations...")
    #     recommendations = self.get_recommendations_for_display(limit=8, purpose="log")
    #     self.songs_recommend = recommendations
    #
    #     # 🎯 LƯU TRACK ID HIỆN TẠI
    #     self._last_recommend_track_id = current_track_id
    #
    #     # 🚨 TẠO/UPDATE UI
    #     self.create_discover_section()
    #
    #     print(f"✅ Recommendations: {len(recommendations)} bài")

    def auto_recommend(self, force_update=False):  # 🔥 THÊM THAM SỐ NÀY
        """Gọi recommendations - cho phép force update khi mua bài"""
        if not hasattr(self, "songs_manager") or not self.songs_manager:
            print("⚠️ Chưa có songs_manager, không thể recommend")
            return

        # 🎯 KIỂM TRA NẾU BÀI ĐÃ THAY ĐỔI (thay vì chặn hoàn toàn)
        current_track_id = self.songs_manager.current_song.get("trackId") if self.songs_manager.current_song else None

        # 🔥 THÊM ĐIỀU KIỆN force_update
        if not force_update and hasattr(self,
                                        '_last_recommend_track_id') and self._last_recommend_track_id == current_track_id:
            print("⏸️ Recommendations already generated for this track, skipping...")
            return

        print("🎵 Generating recommendations...")
        recommendations = self.get_recommendations_for_display(limit=8, purpose="log")
        self.songs_recommend = recommendations

        # 🎯 LƯU TRACK ID HIỆN TẠI
        self._last_recommend_track_id = current_track_id

        # 🚨 TẠO/UPDATE UI
        self.create_discover_section()

        print(f"✅ Recommendations: {len(recommendations)} bài")


    def on_song_changed_from_main(self, song):
        """Được gọi khi MainScreen thay đổi bài hát"""
        print(f"🔄 MoodPlayer nhận bài hát mới từ MainScreen: {song.get('trackName', 'Unknown')}")
        print(f"   🎯 Đang cập nhật UI Player...")

        # CẬP NHẬT CURRENT_SONG VÀ UI
        self.current_song = song
        self.update_disc(song)
        # self.update_progress(0)
        self.auto_recommend()
        print("🎵 [DEBUG] Calling update_tracklist_dynamically...")
        self.update_tracklist_simple(song)


        print(f"   ✅ Đã cập nhật UI Player cho: {song.get('trackName', 'Unknown')}")

    def update_player_display(self):
        """Cập nhật UI và resume nhạc từ vị trí cũ"""
        if not self.songs_manager:
            return

        current_song = self.songs_manager.current_song
        is_playing = self.songs_manager.is_playing
        current_time = getattr(self.songs_manager, 'current_time', 0)

        print(f"🎵 DEBUG: Resuming playback at {current_time}s...")

        # Cập nhật UI
        if current_song:
            self.update_disc(current_song)

        # 🔥 RESUME NHẠC TỪ VỊ TRÍ CŨ KHI VÀO PLAYER
        if is_playing and current_song:
            try:
                player_state = self.songs_manager.player.get_state()
                if player_state == vlc.State.Paused:
                    print(f"🎵 Resume nhạc từ {current_time}s...")
                    self.songs_manager.player.play()  # Resume từ vị trí cũ
                elif player_state == vlc.State.Stopped:
                    print(f"🎵 Phát lại từ {current_time}s...")
                    self.songs_manager.play_song(current_song)  # Phát lại từ đầu
                    if current_time > 0:
                        self.songs_manager.player.set_time(int(current_time * 1000))

                self.show_pause_button()
            except Exception as e:
                print(f"❌ Lỗi khi resume nhạc: {e}")
        else:
            self.show_play_button()

        self.update_progress(current_time)

    def setup_ui(self):
        """Khởi tạo toàn bộ giao diện player"""
        print("[DEBUG] 🎨 Đang khởi tạo UI MoodPlayer...")

        # === Canvas nền tổng ===
        # CHỈ CÒN EMBEDDED MODE, kích thước 950x600
        self.canvas = tk.Canvas(
            self,
            width=950,
            height=600,
            bg="#C5D7A1",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # # --- Thanh bar công cụ ---
        # self.canvas.create_rectangle(0, 0, 50, 600, fill="#C5D7A1", outline="")

        # # 🔥 QUAN TRỌNG: XÓA TOÀN BỘ NỘI DUNG CŨ TRÊN CANVAS
        # self.canvas.delete("all")

        # --- Khung Recommend song ---
        self.canvas.create_rectangle(0, 0, 303, 600, fill="#F7F7DC", outline="")#F7F7DC

        # --- Khung Tracklist ---
        # Điều chỉnh vị trí vì width chỉ còn 950
        self.canvas.create_rectangle(681, 0, 950, 600, fill="#F7F7DC", outline="")
        #Ảnh nền ở giữa
        # self.load_center_image("images/Starbackground.png", x1=303, x2=681)
        # Cách tốt nhất
        self.load_center_image(relative_to_assets("Starbackground.png"), x1=303, x2=681)
        # Đặt các nút lên bar
        self.create_disc_display()
        self.create_progress_bar()
        self.create_bottom_bar()
        # self.create_sidebar_buttons()
        # self.create_discover_section()
        self.create_tracklist_section()
        self.setup_repeat_images()


        print("[DEBUG] ✅ MoodPlayer UI đã được khởi tạo")

    ##E9F5D8
    def on_enter(self, frame):
        """Khi hover vào frame - ĐỔI MÀU CẢ BUTTON, TRỪ BÀI ĐANG PHÁT"""

        def change_bg(widget):
            try:
                if not widget.winfo_exists():
                    return

                widget_type = str(widget.winfo_class())

                # 🎯 ĐỔI MÀU CẢ BUTTON, NHƯNG KIỂM TRA BÀI ĐANG PHÁT
                if widget_type in ['Frame', 'Label', 'Button']:
                    current_bg = widget.cget('bg')
                    # 🚫 CHẶN: Nếu đang là màu bài đang phát (#E9F5D8) thì KHÔNG ĐỔI
                    if current_bg == "#E9F5D8":
                        return  # Không đổi màu bài đang phát
                    # Chỉ đổi nếu đang là màu gốc
                    if current_bg in ["#F7F7DC"]:
                        widget.config(bg="#F1EBD0")
                        # 🎯 Đổi cả activebackground cho button
                        if widget_type == 'Button':
                            widget.config(activebackground="#F1EBD0")

                # Duyệt qua tất cả children
                for child in widget.winfo_children():
                    change_bg(child)

            except Exception as e:
                pass

        try:
            if frame.winfo_exists():
                current_bg = frame.cget('bg')
                # 🚫 CHẶN: Nếu đang là màu bài đang phát thì KHÔNG ĐỔI
                if current_bg == "#E9F5D8":
                    return
                if current_bg in ["#F7F7DC"]:
                    frame.config(bg="#F1EBD0")
                change_bg(frame)
        except Exception as e:
            print(f"⚠️ On_enter error: {e}")

    def on_leave(self, frame):
        """Khi rời frame - RESET MÀU CẢ BUTTON, TRỪ BÀI ĐANG PHÁT"""

        def reset_bg(widget):
            try:
                if not widget.winfo_exists():
                    return

                widget_type = str(widget.winfo_class())

                # 🎯 RESET MÀU CẢ BUTTON, NHƯNG KIỂM TRA BÀI ĐANG PHÁT
                if widget_type in ['Frame', 'Label', 'Button']:
                    current_bg = widget.cget('bg')
                    # 🚫 CHẶN: Nếu đang là màu bài đang phát thì KHÔNG RESET
                    if current_bg == "#E9F5D8":
                        return  # Giữ nguyên màu bài đang phát
                    if current_bg == "#F1EBD0":
                        # Xác định màu gốc
                        parent_widget = widget.master
                        parent_bg = parent_widget.cget('bg') if hasattr(parent_widget, 'cget') else "#F7F7DC"
                        target_bg = "#E9F5D8" if parent_bg == "#E9F5D8" else "#F7F7DC"
                        widget.config(bg=target_bg)
                        # 🎯 Reset cả activebackground cho button
                        if widget_type == 'Button':
                            widget.config(activebackground="#E9F5D8")

                # Duyệt qua tất cả children
                for child in widget.winfo_children():
                    reset_bg(child)

            except Exception as e:
                pass

        try:
            if frame.winfo_exists():
                current_bg = frame.cget('bg')
                # 🚫 CHẶN: Nếu đang là màu bài đang phát thì KHÔNG RESET
                if current_bg == "#E9F5D8":
                    return
                if current_bg == "#F1EBD0":
                    target_bg = "#E9F5D8" if hasattr(frame, 'is_playing') else "#F7F7DC"
                    frame.config(bg=target_bg)
                reset_bg(frame)
        except Exception as e:
            print(f"⚠️ On_leave error: {e}")

    @staticmethod
    def truncate_text(text, max_length=25):
        """Cắt ngắn chuỗi nếu quá dài"""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def load_center_image(self, image_path, x1=303, x2=681):
        """Load ảnh nền với vị trí xác định"""
        try:
            # Load và resize ảnh
            original_image = Image.open(image_path)
            resized_image = original_image.resize((x2 - x1, 600))  # 🔥 RESIZE THEO KÍCH THƯỚC MỚI
            self.bg_image = ImageTk.PhotoImage(resized_image)

            # Vẽ ảnh vào vị trí mới
            self.canvas.create_image(x1, 0, anchor="nw", image=self.bg_image)
            print(f"[DEBUG] ✅ Đã load ảnh nền tại: {x1}-{x2}")
        except Exception as e:
            print(f"[DEBUG] ❌ Lỗi load ảnh nền: {e}")

    # def create_sidebar_buttons(self):
    #     """Tạo các nút trên thanh bar bên trái (có icon và hiệu ứng hover)"""
    #     # Danh sách nút: (đường dẫn ảnh, toạ độ y)
    #     buttons_info = [
    #         ("images/logo 1.png", 7),
    #         ("images/Avatar.png", 59),
    #         ("Images/home 1.png", 152),
    #         ("Images/heart 1.png", 220),
    #         ("Images/history 1.png", 288),
    #         ("Images/report 1.png", 356),
    #         ("Images/logout 1.png", 549)
    #     ]
    #
    #     self.sidebar_buttons = []
    #     self.sidebar_icons = []  # giữ reference ảnh, tránh bị GC xoá
    #
    #     for icon_path, y in buttons_info:
    #         try:
    #             # --- Load icon và resize về cùng kích thước ---
    #             icon_img = Image.open(icon_path)
    #             icon_img = icon_img.resize((32, 32), Image.Resampling.LANCZOS)
    #             icon_tk = ImageTk.PhotoImage(icon_img)
    #             self.sidebar_icons.append(icon_tk)
    #
    #             # --- Tạo nút ---
    #             btn = Button(
    #                 self.parent,
    #                 image=icon_tk,
    #                 bg="#C5D7A1",
    #                 activebackground="#B8CC8A",  # màu khi nhấn
    #                 bd=0,
    #                 relief="flat",
    #                 cursor="hand2"
    #             )
    #             btn.place(x=8, y=y, width=32, height=32)  # căn giữa thanh 50px
    #
    #             # --- Hiệu ứng hover ---
    #             btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#B8CC8A"))
    #             btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#C5D7A1"))
    #
    #             self.sidebar_buttons.append(btn)
    #         except Exception as e:
    #             print(f"Lỗi khi tải icon {icon_path}:", e)

    # def on_song_click(self, song):
    #     """Player tự xử lý playback cho tracklist của nó"""
    #     try:
    #         print(f"[DEBUG] 🎵 on_song_click được gọi với song:")
    #         print(f"  - trackName: {song.get('trackName', 'Unknown')}")
    #         print(f"  - Type: {type(song)}")
    #         print(f"  - Keys: {list(song.keys()) if isinstance(song, dict) else 'N/A'}")
    #
    #         # 🔥 KIỂM TRA URL CHI TIẾT
    #         song_url = song.get("previewUrl") or song.get("filePath")
    #         if not song_url:
    #             print(f"❌ Bài hát '{song.get('trackName', 'Unknown')}' không có URL phát")
    #             return
    #
    #         print(f"🎵 URL phát: {song_url}")
    #
    #         # 🔥 CẬP NHẬT CURRENT_SONG TRƯỚC KHI PHÁT
    #         self.current_song = song
    #         print(f"[DEBUG] ✅ Đã cập nhật current_song: {self.current_song.get('trackName', 'Unknown')}")
    #
    #         # 🔥 GỌI MainScreen VỚI DIRECT SONG OBJECT
    #         if hasattr(self, 'songs_manager') and self.songs_manager:
    #             # Reset và phát bài mới
    #             self.songs_manager.current_time = 0
    #             self.songs_manager.play_song(song)
    #
    #             # 🔥 UPDATE UI PLAYER
    #             self.update_disc(song)
    #             self.show_pause_button()
    #             self.update_progress(0)
    #             try:
    #                 self.notify_main_song_changed(song, "player_click")
    #             except Exception as notify_error:
    #                 print(f"⚠️ Lỗi khi thông báo đến MainScreen: {notify_error}")
    #
    #             print(f"[DEBUG] ▶️ Phát từ Player tracklist: {song.get('trackName', 'Unknown')}")
    #         else:
    #             print("❌ Không thể phát - MainScreen không available")
    #
    #     except Exception as e:
    #         print(f"❌ Lỗi phát từ Player tracklist: {e}")
    #         import traceback
    #         traceback.print_exc()

    def on_song_click(self, song):
        """Player gọi trực tiếp on_song_click của MainScreen"""
        try:
            print(f"[DEBUG] 🎵 Player on_song_click: {song.get('trackName', 'Unknown')}")

            # 🔥 GỌI TRỰC TIẾP MAINSCREEN ON_SONG_CLICK
            if hasattr(self, 'songs_manager') and self.songs_manager:
                track_id = song.get("trackId")
                if track_id:
                    print(f"🎵 Player gọi MainScreen on_song_click với track_id: {track_id}")

                    # CẬP NHẬT UI CƠ BẢN
                    self.current_song = song
                    self.update_disc(song)
                    self.show_pause_button()
                    self.update_progress(0)  # Tạm thời hiển thị 0s

                    self.update_recommendations_for_new_track(track_id)
                    self.update_tracklist_simple(song)

                    self.stop_disc_rotation()
                    self.start_disc_rotation(reset_angle=True)

                    # GỌI MAINSCREEN ĐỂ PHÁT NHẠC
                    self.songs_manager.on_song_click(track_id)

                    # 🔥 SAU 100ms, CẬP NHẬT PROGRESS BAR VỚI TIME THỰC
                    def update_with_real_time():
                        if hasattr(self.songs_manager, 'current_time'):
                            real_time = self.songs_manager.current_time
                            print(f"🕒 Real time after play: {real_time}s")
                            self.update_progress(real_time)
                        self.start_progress_loop()

                    self.parent.after(100, update_with_real_time)

                    print(f"[DEBUG] ✅ Đã gọi MainScreen on_song_click")
                else:
                    print("❌ Không có trackId trong song object")
            else:
                print("❌ Không thể phát - MainScreen không available")

        except Exception as e:
            print(f"❌ Lỗi phát từ Player: {e}")
            import traceback
            traceback.print_exc()

    def on_buy_click(self, song):
        """Xử lý khi người dùng click nút 'Buy'"""
        track = song.get("trackName", "Unknown Song")
        artist = song.get("artistName", "Unknown Artist")
        print(f"[DEBUG] 🛒 Người dùng nhấn mua: {track} - {artist}")

        if hasattr(self, 'controller') and hasattr(self.controller, 'process_payment'):
            self.controller.process_payment(song)
            print("✅ Đã gọi process_payment từ controller")

            # 🔥 SỬA: Dùng userId ĐÚNG kiểu dữ liệu
            user_id = session.current_user.get("userId")  # ✅ KHÔNG chuyển thành int
            if hasattr(self, 'recommender') and hasattr(self.recommender, 'invalidate_purchase_cache'):
                self.recommender.invalidate_purchase_cache(user_id)
                print(f"🔄 Đã invalidate purchase cache cho user {user_id}")

            # ĐỢI PAYMENT XONG RỒI RECOMMEND
            self.wait_for_payment_confirmation(song)

    def wait_for_payment_confirmation(self, song, attempt=0):
        """Kiểm tra database cho đến khi thấy bài đã được mua"""
        max_attempts = 10  # Giảm xuống
        delay = 1000  # Giảm delay

        print(f"⏳ Chờ payment confirmation... (lần {attempt + 1}/{max_attempts})")

        try:
            db = self.controller.get_db()
            user_id_str = str(session.current_user.get("userId"))
            track_id = song.get("trackId")

            # 🔥 CHỈ QUERY VỚI STRING
            purchased = db.db["purchase"].find_one({
                "userId": user_id_str,
                "trackId": track_id
            })

            if purchased:
                print(f"✅ Tìm thấy purchase: {purchased['trackName']}")

                # 🔥 INVALIDATE CACHE NGAY LẬP TỨC
                user_id = session.current_user.get("userId")
                if hasattr(self, 'recommender') and hasattr(self.recommender, 'invalidate_purchase_cache'):
                    print(f"🔄 INVALIDATE CACHE before recommending...")
                    self.recommender.invalidate_purchase_cache(user_id)

                # 🔥 ĐỢI 0.5 GIÂY ĐỂ ĐẢM BẢO
                time.sleep(0.5)
                self.auto_recommend(force_update=True)
            else:
                if attempt < max_attempts:
                    self.parent.after(delay, lambda: self.wait_for_payment_confirmation(song, attempt + 1))
                else:
                    print("❌ Timeout - vẫn update recommendations...")
                    self.auto_recommend(force_update=True)

        except Exception as e:
            print(f"❌ Lỗi kiểm tra payment: {e}")
            if attempt < max_attempts:
                self.parent.after(delay, lambda: self.wait_for_payment_confirmation(song, attempt + 1))

    def like_song(self):
        """Khi bấm nút love trong Player"""
        print("❤️ Player: Nút love được click")
        if hasattr(self, 'songs_manager') and hasattr(self.songs_manager, 'current_song'):
            song = self.songs_manager.current_song
            if song:
                try:
                    db = self.controller.get_db()
                    user_id = int(session.current_user.get("userId"))
                    track_id = song.get("trackId")

                    existing = db.db["user_favorite"].find_one({
                        "userId": user_id,
                        "trackId": track_id
                    })

                    if existing:
                        # Đã love -> bỏ love
                        self.songs_manager.remove_from_favorite(song)
                        # 🔥 CẬP NHẬT UI NGAY (không đợi callback)
                        self.update_love_button_ui(False)
                    else:
                        # Chưa love -> thêm love
                        self.songs_manager.add_to_favorite(song)
                        # 🔥 CẬP NHẬT UI NGAY (không đợi callback)
                        self.update_love_button_ui(True)

                except Exception as e:
                    print(f"❌ Lỗi like_song: {e}")

    def prev_song(self):
        if not hasattr(self, "songs_track") or not self.songs_track:
            return
        self.current_index = (self.current_index - 1) % len(self.songs_track)
        self.current_song = self.songs_track[self.current_index]
        print(f"[DEBUG] ⏮️ Trước: {self.current_song['trackName']}")
        self.on_song_click(self.current_song)

    def toggle_play(self):
        """Toggle play/pause - điều khiển cả nhạc thật lẫn UI"""
        try:
            if hasattr(self, 'songs_manager') and self.songs_manager:
                # 🔥 GỌI HÀM play_pause() CỦA MAINSCREEN
                self.songs_manager.play_pause()

                # 🔥 UPDATE UI DỰA TRÊN STATE MỚI
                if self.songs_manager.is_playing:
                    print("[DEBUG] ▶️ Tiếp tục phát.")
                    self.start_progress_loop()
                    self.show_pause_button()
                    self.start_disc_rotation(reset_angle=False)
                else:
                    print("[DEBUG] ⏸️ Tạm dừng.")
                    # Dừng progress loop
                    if self.progress_loop_id:
                        self.frame.after_cancel(self.progress_loop_id)
                        self.progress_loop_id = None
                    self.show_play_button()
                    self.stop_disc_rotation()

            else:
                print("❌ Không thể điều khiển nhạc - MainScreen không available")

        except Exception as e:
            print(f"❌ Lỗi toggle_play: {e}")

    def next_song(self):
        if not hasattr(self, "songs_track") or not self.songs_track:
            return
        self.current_index = (self.current_index + 1) % len(self.songs)
        self.current_song = self.songs_track[self.current_index]
        print(f"[DEBUG] ⏭️ Tiếp: {self.current_song['trackName']}")
        self.on_song_click(self.current_song)

    def show_song_menu(self, song, x, y):
        # 🔥 Chỉ show menu nếu song thuộc tracklist
        # if not hasattr(self, 'songs_track') or song not in self.songs_track:
        #     return

        if hasattr(self, 'song_menu_frame') and self.song_menu_frame:
            self.song_menu_frame.destroy()

        actual_song = None

        # Ưu tiên 1: current_song của player
        if hasattr(self, 'current_song') and self.current_song:
            actual_song = self.current_song
            print(f"  ✅ Dùng player current_song: {actual_song.get('trackName')}")

        # Ưu tiên 2: current_song từ songs_manager (MainScreen)
        elif hasattr(self, 'songs_manager') and self.songs_manager and hasattr(self.songs_manager, 'current_song'):
            actual_song = self.songs_manager.current_song
            print(f"  ✅ Dùng songs_manager current_song: {actual_song.get('trackName')}")

        # Ưu tiên 3: song từ param (chỉ dùng nếu các option trên không có)
        elif song and isinstance(song, dict):
            actual_song = song
            print(f"  ✅ Dùng song param: {actual_song.get('trackName')}")

        if not actual_song:
            print("  ❌ Không có bài hát nào để tạo menu!")
            return

        print(f"  🎯 ACTUAL SONG: {actual_song.get('trackName')}")

        # 🔥 TẠO POPUP MENU NHỎ VỚI ẢNH NỀN
        self.song_menu_frame = tk.Toplevel(self.parent)
        self.song_menu_frame.wm_overrideredirect(True)

        menu_width, menu_height = 150, 80
        new_x = x + 200
        new_y = y - 40
        self.song_menu_frame.geometry(f"{menu_width}x{menu_height}+{new_x}+{new_y}")
        # 🔥 CANVAS TRONG SUỐT - DÙNG MÀU ĐẶC BIỆT
        canvas = tk.Canvas(
            self.song_menu_frame,
            width=menu_width,
            height=menu_height,
            highlightthickness=0,
            bg='#123456'  # 🔥 MÀU ĐẶC BIỆT LÀM TRONG SUỐT
        )
        canvas.pack()
        self.song_menu_frame.attributes('-transparentcolor', '#123456')  # 🔥 CÙNG MÀU

        # 🔥 TẢI ẢNH NÚT
        try:
            # Ảnh nút bình thường
            mood_img = Image.open("images/Menu_mood.png").resize((122, 32), Image.Resampling.LANCZOS)
            self.mood_photo = ImageTk.PhotoImage(mood_img)

            rating_img = Image.open("images/Menu_rate.png").resize((122, 32), Image.Resampling.LANCZOS)
            self.rating_photo = ImageTk.PhotoImage(rating_img)

            # Ảnh nút khi hover (nếu có)
            mood_hover_img = Image.open("images/mood_button_hover.png").resize((110, 32), Image.Resampling.LANCZOS)
            self.mood_hover_photo = ImageTk.PhotoImage(mood_hover_img)

            rating_hover_img = Image.open("images/rate_button_hover.png").resize((110, 32), Image.Resampling.LANCZOS)
            self.rating_hover_photo = ImageTk.PhotoImage(rating_hover_img)

        except Exception as e:
            print(f"⚠️ Không tải được ảnh nút: {e}")

        def on_press_button(e, btn, original_y):
            btn.place(relx=0.5, y=original_y + 2, anchor="center")  # 🔥 DỊCH XUỐNG 2px

        def on_release_button(e, btn, original_y, command_func):
            btn.place(relx=0.5, y=original_y, anchor="center")  # 🔥 TRỞ VỀ VỊ TRÍ CŨ
            command_func()

        def close_menu_and_action(action_function):
            """Hàm chung để đóng menu và thực hiện hành động tiếp theo"""

            def wrapper():
                self.song_menu_frame.destroy()  # Đóng menu trước
                action_function()  # Thực hiện hành động tiếp theo

            return wrapper

        # Nút rating
        rating_btn = tk.Label(
            self.song_menu_frame,
            image=self.rating_photo,
            cursor="hand2",
            bd=0
        )
        rating_btn.place(relx=0.5, y=20, anchor="center")
        from functools import partial
        rating_btn.bind("<ButtonPress-1>", lambda e: on_press_button(e, rating_btn, 20))
        rating_btn.bind("<ButtonRelease-1>",
                        lambda e: on_release_button(e, rating_btn, 20,
                                                    close_menu_and_action(partial(self.show_rating_ui, actual_song))))

        # Nút mood
        mood_btn = tk.Label(
            self.song_menu_frame,
            image=self.mood_photo,
            cursor="hand2",
            bd=0
        )
        mood_btn.place(relx=0.5, y=55, anchor="center")
        mood_btn.bind("<ButtonPress-1>", lambda e: on_press_button(e, mood_btn, 55))
        mood_btn.bind("<ButtonRelease-1>",
                      lambda e: on_release_button(e, mood_btn, 92,
                                                  close_menu_and_action(
                                                      partial(self.show_mood_selection, actual_song))))

        # 🔥 HOVER EFFECT CHO NÚT ẢNH
        def on_enter_mood(e):
            mood_btn.config(image=self.mood_hover_photo)

        def on_leave_mood(e):
            mood_btn.config(image=self.mood_photo)

        def on_enter_rating(e):
            rating_btn.config(image=self.rating_hover_photo)

        def on_leave_rating(e):
            rating_btn.config(image=self.rating_photo)

        mood_btn.bind("<Enter>", on_enter_mood)
        mood_btn.bind("<Leave>", on_leave_mood)
        rating_btn.bind("<Enter>", on_enter_rating)
        rating_btn.bind("<Leave>", on_leave_rating)

        # Tự động đóng khi click ra ngoài
        def close_menu(e=None):
            if hasattr(self, 'song_menu_frame') and self.song_menu_frame:
                self.song_menu_frame.destroy()

        self.song_menu_frame.bind("<FocusOut>", close_menu)
        self.song_menu_frame.focus_set()

    # 🔥 SỬA CÁCH GỌI - TRUYỀN TỌA ĐỘ
    # Ví dụ: khi click vào nút menu của bài hát
    # def on_menu_button_click(self, song, event):
    #     x = event.widget.winfo_rootx()
    #     y = event.widget.winfo_rooty() + event.widget.winfo_height()
    #     self.show_song_menu(song, x, y)

    def create_discover_section(self):
        """Tạo phần 'Discover New Music' ở cột trái"""
        # Tiêu đề
        self.canvas.create_text(
            6, 13, anchor="nw",
            text="Discover\nNew Music",
            font=("Roboto", 21, "bold"),
            fill="#94BB7C"
        )
        # --- LOAD DANH SÁCH BÀI HÁT TỪ MONGODB ---
        # try:
        #     db = Connector()
        #
        #     # Thay vì load ALL tracks, chỉ load 8 tracks random từ MongoDB
        #     songs_recommend = list(db.db["tracks"].aggregate([
        #         {"$sample": {"size": 8}},  # Random ngay trên DB
        #         {"$project": {
        #             "trackId": 1,
        #             "trackName": 1,
        #             "artistName": 1,
        #             "artworkUrl100": 1,
        #             "trackTimeMillis": 1,  # 🔥 Thêm field thời lượng
        #             "_id": 0
        #         }}
        #     ]))
        if not hasattr(self, 'songs_recommend') or not self.songs_recommend:
            print("❌ ERROR: create_discover_section called before recommendations ready!")
            # Fallback: gọi recommendations (chỉ cho trường hợp khẩn cấp)
            print("🔄 Emergency: loading recommendations...")
            self.songs_recommend = self.get_recommendations_for_display(limit=8, purpose="display")

        songs_recommend = self.songs_recommend
        print(f"🎵 Displaying {len(songs_recommend)} recommendations in UI")

        self.songs = songs_recommend

        # except Exception as e:
        #     print(f"⚠️ Lỗi load từ MongoDB: {e}")
        #     return

        # --- HIỂN THỊ CÁC BÀI HÁT ---
        y_start = 102
        y_gap = 61
        y_button_start = 113
        self.discover_images = []  # giữ reference ảnh tránh bị xoá
        try:
            price_img = Image.open(relative_to_assets("Buy_button.png"))  # ảnh nút 6.500
            price_img = price_img.resize((55, 28), Image.Resampling.LANCZOS)
            price_photo = ImageTk.PhotoImage(price_img)
            self.price_photo = price_photo
        except Exception as e:
            print("Không tải được ảnh giá:", e)

        for idx, song in enumerate(songs_recommend):  # chỉ hiển thị 8 bài đầu
            y = y_start + idx * y_gap


            song_frame = tk.Frame(self.canvas, bg="#F7F7DC", highlightthickness=0)
            self.canvas.create_window(10, y, anchor="nw", window=song_frame, width=293, height=55)

            # track_name = song.get("trackName", "Unknown Song")
            # artist_name = song.get("artistName", "Unknown Artist")
            duration_ms = song.get("trackTimeMillis", 0)
            artwork = song.get("artworkUrl100", "")

            track_name = self.truncate_text(song.get("trackName", "Unknown"), 10)
            artist_name = self.truncate_text(song.get("artistName", ""), 10)

            # --- Tải ảnh ---
            try:
                response = requests.get(artwork)
                img = Image.open(BytesIO(response.content))
                img = img.resize((50, 50), Image.Resampling.LANCZOS)
                song_photo = ImageTk.PhotoImage(img)
                self.discover_images.append(song_photo)

                img_button = tk.Button(
                    song_frame,
                    image=song_photo,
                    bd=0,
                    bg="#F7F7DC",
                    activebackground="#E9F5D8",
                    cursor="hand2",
                    command=lambda s=song: self.on_buy_click(s)
                )
                self.discover_images.append(song_photo)  # giữ reference
                img_button.place(x=0, y=0, width=50, height=50)
            except Exception:
                print(f"⚠️ Không tải được ảnh: {artwork}")

            # --- Thông tin bài hát ---
            track_label = tk.Label(
                song_frame,
                text=track_name,
                font=("Arial", 10, "bold"),
                bg="#F7F7DC",
                fg="#000000",
                anchor="w",
                cursor="hand2")
            track_label.place(x=57, y=0)

            artist_label = tk.Label(
                song_frame,
                text=artist_name,
                font=("Arial", 9),
                bg="#F7F7DC",
                fg="#6B6B6B",
                anchor="w"
            )
            artist_label.place(x=57, y=18)
            # --- Thời lượng ---
            if duration_ms:
                duration_sec = duration_ms // 1000
                minutes = duration_sec // 60
                seconds = duration_sec % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "--:--"

            duration_label = tk.Label(
                song_frame,
                text=duration_str,
                font=("Arial", 8),
                bg="#F7F7DC",
                fg="#6B6B6B",
                anchor="w"
            )
            duration_label.place(x=57, y=36)
            buy_btn = tk.Button(
                song_frame,
                image=price_photo,
                bd=0,
                relief="flat",
                bg="#F7F7DC",
                activebackground="#E9F5D8",
                cursor="hand2",
                command=lambda s=song: self.on_buy_click(s)  # tạo hàm tạm để sau dùng
            )
            buy_btn.pack(side="right", padx=(0,5))

            for w in (song_frame, track_label, artist_label, duration_label, img_button, buy_btn):
                w.bind("<Enter>", lambda e, f=song_frame: self.on_enter(f))
                w.bind("<Leave>", lambda e, f=song_frame: self.on_leave(f))
            tooltip_text = (
                f"🎵 {song['trackName']}\n"
                f"👤 {song['artistName']}\n"
            )

            Tooltip(track_label, tooltip_text, wrap_length=40)
            Tooltip(artist_label, tooltip_text, wrap_length=40)
            Tooltip(img_button, tooltip_text, wrap_length=40)

    def create_tracklist_section(self):
        """Tạo phần 'Track List' bên phải."""
        # --- TIÊU ĐỀ ---
        self.canvas.create_text(
            700, 13, anchor="nw",
            text="Track List",
            font=("Roboto", 21, "bold"),
            fill="#94BB7C"
        )
        self.canvas.create_text(
            700, 60, anchor="nw",
            text="What's next",
            font=("Roboto", 11, "bold"),
            fill="#94BB7C"
        )

        # --- LOAD DANH SÁCH BÀI HÁT TỪ FILE JSON ---
        # try:
        #     with open("Data/merged_tracks_final.json", "r", encoding="utf-8") as f:
        #         data = json.load(f)
        #     songs = data["songs"] if isinstance(data, dict) and "songs" in data else data
        # except FileNotFoundError:
        #     print("⚠️ Không tìm thấy file songs.json.")
        #     return
        # except json.JSONDecodeError:
        #     print("⚠️ Lỗi định dạng file JSON.")
        #     return
        #
        # print(f"🎵 Đã load {len(songs)} bài hát từ songs.json cho track")

        # --- TẢI ẢNH NÚT ---
        try:
            timer_img = Image.open(relative_to_assets("timer.png"))
            timer_img = timer_img.resize((35, 35), Image.Resampling.LANCZOS)
            timer_photo = ImageTk.PhotoImage(timer_img)
            self.timer_photo = timer_photo

            repeat_img = Image.open(relative_to_assets("repeat.png"))
            repeat_img = repeat_img.resize((30, 30), Image.Resampling.LANCZOS)
            repeat_photo = ImageTk.PhotoImage(repeat_img)
            self.repeat_photo = repeat_photo

            track_img = Image.open(relative_to_assets("Vector.png"))
            track_img = track_img.resize((16, 16), Image.Resampling.LANCZOS)
            track_photo = ImageTk.PhotoImage(track_img)
            self.track_photo = track_photo
        except Exception as e:
            print("⚠️ Không tải được ảnh nút:", e)
            return

        # --- NÚT REPEAT VÀ TIMER ---
        self.repeat_button = tk.Button(  # 🔥 ĐỔI Repeat_btn THÀNH self.repeat_button
            self.canvas,
            image=repeat_photo,
            bd=0,
            relief="flat",
            bg="#F7F7DC",
            activebackground="#E9F5D8",
            cursor="hand2",
            command=self.change_repeat_mode  # 🔥 THÊM COMMAND NÀY
        )
        self.repeat_button.place(x=703, y=99)
        self.repeat_button.image = repeat_photo  # 🔥 GIỮ REFERENCE
        Timer_btn = tk.Button(
            self.canvas,
            image=timer_photo,
            bd=0,
            relief="flat",
            bg="#F7F7DC",
            activebackground="#E9F5D8",
            cursor="hand2",
        )
        Timer_btn.place(x=745, y=96)

        # --- FRAME CHỨA TRACKS CUỘN ĐƯỢC ---
        self.tracklist_canvas = tk.Canvas(
            self.canvas,
            width=280,
            height=480,
            bg="#F7F7DC",
            highlightthickness=0
        )
        self.tracklist_scrollbar = tk.Scrollbar(
            self.canvas,
            orient="vertical",
            command=self.tracklist_canvas.yview
        )
        self.tracklist_canvas.configure(yscrollcommand=self.tracklist_scrollbar.set)

        # Đặt canvas và scrollbar
        self.tracklist_canvas.place(x=681, y=137)
        self.tracklist_scrollbar.place(x=681 + 280 - 25, y=137, height=480)
        # Tạo frame chính bên trong canvas
        self.tracklist_frame = tk.Frame(self.tracklist_canvas, bg="#F7F7DC")
        self.tracklist_window = self.tracklist_canvas.create_window((0, 0), window=self.tracklist_frame, anchor="nw",
                                                                    width=280)
        # ẨN SCROLLBAR KHI CHƯA HOVER
        self.tracklist_scrollbar.place_forget()

        # HÀM HIỆN/ẨN SCROLLBAR KHI HOVER
        def show_scrollbars(e):
            self.tracklist_scrollbar.place(x=681 + 280 - 25, y=137, height=480)

        def hide_scrollbars(e):
            self.tracklist_scrollbar.place_forget()

        self.tracklist_scrollbar.config(
            bg="#F586A3",
            troughcolor="#C5D7A1",
            width=12  # Làm dày hơn cho dễ thấy
        )

        # BIND SỰ KIỆN HOVER
        self.tracklist_canvas.bind("<Enter>", show_scrollbars)
        self.tracklist_canvas.bind("<Leave>", hide_scrollbars)
        self.tracklist_frame.bind("<Enter>", show_scrollbars)
        self.tracklist_frame.bind("<Leave>", hide_scrollbars)

        # --- HÀM CẬP NHẬT SCROLLREGION ---
        def update_scrollregion(event=None):
            self.tracklist_canvas.configure(scrollregion=self.tracklist_canvas.bbox("all"))

            # 🎯 FIX: SET HEIGHT TRONG MỌI TRƯỜNG HỢP
            required_height = self.tracklist_frame.winfo_reqheight()
            canvas_height = self.tracklist_canvas.winfo_height()

            # Luôn set height bằng chiều cao thực tế của frame
            self.tracklist_canvas.itemconfig(self.tracklist_window, height=required_height)

        self.tracklist_frame.bind("<Configure>", update_scrollregion)
        self.tracklist_canvas.bind("<Configure>", update_scrollregion)

        # --- TẠO DANH SÁCH BÀI HÁT ---
        try:
            db = Connector()

            # 🔥 SỬ DỤNG HÀM GET_CURRENT_USER CÓ SẴN
            current_user = self.get_current_user()
            user_id = current_user['userId'] if current_user and 'userId' in current_user else None

            if not user_id:
                print("⚠️ Không có user đăng nhập, không thể load tracklist")
                return

            # 🔥 QUERY TỐI ƯU - CHỈ LẤY CÁC TRƯỜNG CẦN THIẾT
            self.songs_track = list(db.db["purchase"].aggregate([
                {"$match": {"userId": user_id}},
                {"$sort": {"purchased_at": 1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "tracks",
                    "localField": "trackId",
                    "foreignField": "trackId",
                    "as": "trackDetails"
                }},
                {"$unwind": "$trackDetails"},
                {"$project": {  # CHỈ LẤY CÁC TRƯỜNG CẦN THIẾT
                    "trackId": 1,
                    "trackName": 1,
                    "artistName": 1,
                    "artworkUrl100": 1,
                    "previewUrl": "$trackDetails.previewUrl",
                    "purchased_at": 1
                }}
            ]))

            # self.tracklist_images = []
            print(f"🎵 Đã load {len(self.songs_track)} bài hát từ purchase của user {user_id}")

        except Exception as e:
            print(f"⚠️ Lỗi tạo tracklist từ purchase: {e}")
            return
        for idx, song in enumerate(self.songs_track):
            # Tạo frame cho mỗi bài hát
            song_frame = tk.Frame(
                self.tracklist_frame,
                bg="#F7F7DC",
                highlightthickness=0,
                width=270,
                height=70
            )
            song_frame.pack(fill="x", pady=5, padx=0)
            song_frame.pack_propagate(False)

            # Lấy thông tin bài hát
            track_name = self.truncate_text(song.get("trackName", "Unknown"), 15)
            artist_name = self.truncate_text(song.get("artistName", ""), 15)
            artwork = song.get("artworkUrl100", "")
            track_id = song.get("trackId")  # 🎯 THÊM DÒNG NÀY

            # # --- ẢNH BÀI HÁT ---
            # try:
            #     response = requests.get(artwork)
            #     img = Image.open(BytesIO(response.content)).resize((62, 62), Image.Resampling.LANCZOS)
            #     song_photo = ImageTk.PhotoImage(img)
            #     self.tracklist_images.append(song_photo)
            #
            #     img_button = tk.Button(
            #         song_frame,
            #         image=song_photo,
            #         bd=0,
            #         bg="#F7F7DC",
            #         activebackground="#E9F5D8",
            #         cursor="hand2",
            #         command=lambda s=song: self.on_song_click(s)
            #     )
            #     img_button.place(x=40, y=10, width=62, height=62)
            # except Exception:
            #     print(f"⚠️ Không tải được ảnh: {artwork}")
            #     placeholder = tk.Label(
            #         song_frame,
            #         text="🎵",
            #         font=("Arial", 12),
            #         bg="#F7F7DC",
            #         width=5,
            #         height=2
            #     )
            #     placeholder.place(x=40, y=10)
            #
            # # --- THÔNG TIN BÀI HÁT ---
            # info_frame = tk.Frame(song_frame, bg="#F7F7DC")
            # info_frame.place(x=115, y=10, width=140, height=50)
            #
            # track_label = tk.Label(
            #     info_frame,
            #     text=track_name,
            #     font=("Arial", 10, "bold"),
            #     bg="#F7F7DC",
            #     fg="#000000",
            #     anchor="w",
            #     cursor="hand2",
            #     wraplength=140
            # )
            # track_label.pack(anchor="w")
            #
            # artist_label = tk.Label(
            #     info_frame,
            #     text=artist_name,
            #     font=("Arial", 9),
            #     bg="#F7F7DC",
            #     fg="#6B6B6B",
            #     anchor="w",
            #     wraplength=140
            # )
            # artist_label.pack(anchor="w")
            #
            # # --- NÚT TRACK ---
            # track_btn = tk.Button(
            #     song_frame,
            #     image=track_photo,
            #     bd=0,
            #     relief="flat",
            #     bg="#F7F7DC",
            #     activebackground="#E9F5D8",
            #     cursor="hand2",
            #     command=lambda s=song: self.on_buy_click(s)
            # )
            # track_btn.place(x=10, y=32)
            if track_id in self.image_cache:
                # 🚀 DÙNG ẢNH TỪ CACHE - NHANH
                song_photo = self.image_cache[track_id]
                print(f"🎵 [CACHE] {track_name}")
            else:
                # 📥 LOAD ẢNH MỚI
                try:
                    response = requests.get(artwork)
                    img = Image.open(BytesIO(response.content)).resize((62, 62), Image.Resampling.LANCZOS)
                    song_photo = ImageTk.PhotoImage(img)
                    self.image_cache[track_id] = song_photo  # 🎯 LƯU VÀO CACHE
                    self.tracklist_images.append(song_photo)
                    print(f"🎵 [LOAD] Đã load ảnh: {track_name}")
                except Exception:
                    print(f"⚠️ Không tải được ảnh: {artwork}")
                    placeholder = tk.Label(
                        song_frame,
                        text="🎵",
                        font=("Arial", 12),
                        bg="#F7F7DC",
                        width=5,
                        height=2
                    )
                    placeholder.place(x=40, y=10)
                    song_photo = None

            # CHỈ TẠO BUTTON NẾU CÓ ẢNH
            if song_photo:
                img_button = tk.Button(
                    song_frame,
                    image=song_photo,
                    bd=0,
                    bg="#F7F7DC",
                    activebackground="#E9F5D8",
                    cursor="hand2",
                    command=lambda s=song: self.on_song_click(s)
                )
                img_button.place(x=40, y=10, width=62, height=62)

            # --- THÔNG TIN BÀI HÁT ---
            info_frame = tk.Frame(song_frame, bg="#F7F7DC")
            info_frame.place(x=115, y=10, width=140, height=50)

            track_label = tk.Label(
                info_frame,
                text=track_name,
                font=("Arial", 10, "bold"),
                bg="#F7F7DC",
                fg="#000000",
                anchor="w",
                cursor="hand2",
                wraplength=140
            )
            track_label.pack(anchor="w")

            artist_label = tk.Label(
                info_frame,
                text=artist_name,
                font=("Arial", 9),
                bg="#F7F7DC",
                fg="#6B6B6B",
                anchor="w",
                wraplength=140
            )
            artist_label.pack(anchor="w")

            # --- NÚT TRACK ---
            track_btn = tk.Button(
                song_frame,
                image=track_photo,
                bd=0,
                relief="flat",
                bg="#F7F7DC",
                activebackground="#E9F5D8",
                cursor="hand2"
            )
            track_btn.place(x=10, y=32)

            # --- HOVER EFFECT ---
            def make_enter_handler(frame):
                return lambda e: self.on_enter(frame)

            def make_leave_handler(frame):
                return lambda e: self.on_leave(frame)

            for widget in [song_frame, track_label, artist_label]:
                widget.bind("<Enter>", make_enter_handler(song_frame))
                widget.bind("<Leave>", make_leave_handler(song_frame))

            # --- TOOLTIP ---
            tooltip_text = f"🎵 {song['trackName']}\n👤 {song['artistName']}"
            Tooltip(track_label, tooltip_text, wrap_length=40)
            Tooltip(artist_label, tooltip_text, wrap_length=40)
            Tooltip(img_button, tooltip_text, wrap_length=40)

        self.tracklist_frame.after(100, update_scrollregion)  # Cập nhật lại sau 100ms

        # --- THÊM SỰ KIỆN CUỘN BẰNG CHUỘT ---
        # THAY THẾ PHẦN BIND MOUSEWHEEL:
        def on_mousewheel(event):
            if self.tracklist_frame.winfo_height() > self.tracklist_canvas.winfo_height():
                self.tracklist_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")

        # Bind cho cả canvas và frame
        self.tracklist_canvas.bind("<MouseWheel>", on_mousewheel)
        self.tracklist_frame.bind("<MouseWheel>", on_mousewheel)


        self.tracklist_frame.update_idletasks()
        update_scrollregion()

    def update_tracklist_simple(self, new_song):
        """Highlight + auto-load + auto-add bài mới từ history"""
        if not new_song:
            return

        print(f"🎵 Update tracklist: {new_song.get('trackName')}")

        current_track_id = new_song.get("trackId")

        # 🎯 KIỂM TRA NẾU BÀI MỚI KHÔNG CÓ TRONG TRACKLIST
        current_index = self.get_track_index(current_track_id)

        if current_index == -1:
            # 🚀 BÀI MỚI TỪ HISTORY: THÊM VÀO ĐẦU TRACKLIST
            print(f"🎵 Thêm bài mới từ history: {new_song.get('trackName')}")
            self.songs_track = [new_song] + self.songs_track[:-1]  # Thêm đầu, bỏ cuối
            current_index = 0  # Bài mới ở vị trí 0

            # 🎯 THÊM ẢNH VÀO CACHE NGAY
            self.preload_images_smart([new_song])

        # 🎯 LƯU TRACK ID ĐANG PHÁT ĐỂ HIGHLIGHT
        self.current_playing_track_id = current_track_id

        # 🎯 KIỂM TRA NẾU LÀ BÀI CUỐI -> TỰ ĐỘNG LOAD THÊM
        if current_index >= len(self.songs_track) - 3:  # 3 bài cuối
            print("🔔 Đang ở cuối tracklist, loading thêm...")
            self.load_more_tracks_async()

        # Refresh UI với highlight
        self.refresh_tracklist_ui_simple()

    def refresh_tracklist_ui_simple(self):
        """Refresh UI - copy nguyên vòng lặp từ create_tracklist_section"""
        # Xóa UI cũ
        for widget in self.tracklist_frame.winfo_children():
            widget.destroy()

        # 🎯 DEBUG QUAN TRỌNG
        print(f"🎵 [DEBUG REFRESH] Số bài trong songs_track: {len(self.songs_track)}")
        print(f"🎵 [DEBUG REFRESH] Bài đầu: {self.songs_track[0].get('trackName') if self.songs_track else 'None'}")
        print(
            f"🎵 [DEBUG REFRESH] Bài cuối: {self.songs_track[-1].get('trackName') if self.songs_track else 'None'}")
        created_count=0

        for idx, song in enumerate(self.songs_track):
            # Tạo frame cho mỗi bài hát
            try:
                # print(f"🎵 [DEBUG CREATE] Đang tạo bài {idx + 1}: {song.get('trackName')}")
                is_playing = (song.get("trackId") == self.current_playing_track_id)
                frame_bg = "#E9F5D8" if is_playing else "#F7F7DC"
                song_frame = tk.Frame(
                    self.tracklist_frame,
                    bg=frame_bg,
                    highlightthickness=0,
                    width=270,
                    height=70
                )
                song_frame.pack(fill="x", pady=5, padx=0)
                song_frame.pack_propagate(False)

                # Lấy thông tin bài hát
                track_name = self.truncate_text(song.get("trackName", "Unknown"), 15)
                artist_name = self.truncate_text(song.get("artistName", ""), 15)
                artwork = song.get("artworkUrl100", "")
                track_id = song.get("trackId")

                if track_id in self.image_cache:
                    # 🚀 DÙNG ẢNH TỪ CACHE - NHANH
                    song_photo = self.image_cache[track_id]
                    print(f"🎵 [CACHE] {track_name}")
                else:
                    # 📥 LOAD ẢNH MỚI
                    try:
                        response = requests.get(artwork)
                        img = Image.open(BytesIO(response.content)).resize((62, 62), Image.Resampling.LANCZOS)
                        song_photo = ImageTk.PhotoImage(img)
                        self.image_cache[track_id] = song_photo  # 🎯 LƯU VÀO CACHE
                        self.tracklist_images.append(song_photo)
                        print(f"🎵 [LOAD] Đã load ảnh: {track_name}")
                    except Exception:
                        print(f"⚠️ Không tải được ảnh: {artwork}")
                        placeholder = tk.Label(
                            song_frame,
                            text="🎵",
                            font=("Arial", 12),
                            bg=frame_bg,
                            width=5,
                            height=2
                        )
                        placeholder.place(x=40, y=10)
                        song_photo = None

                # CHỈ TẠO BUTTON NẾU CÓ ẢNH
                if song_photo:
                    img_button = tk.Button(
                        song_frame,
                        image=song_photo,
                        bd=0,
                        bg=frame_bg,
                        activebackground="#E9F5D8",
                        cursor="hand2",
                        command=lambda s=song: self.on_song_click(s)
                    )
                    img_button.place(x=40, y=10, width=62, height=62)

                # --- THÔNG TIN BÀI HÁT ---
                info_frame = tk.Frame(song_frame, bg=frame_bg)
                info_frame.place(x=115, y=10, width=140, height=50)

                track_label = tk.Label(
                    info_frame,
                    text=track_name,
                    font=("Arial", 10, "bold"),
                    bg=frame_bg,
                    fg="#000000",
                    anchor="w",
                    cursor="hand2",
                    wraplength=140
                )
                track_label.pack(anchor="w")

                artist_label = tk.Label(
                    info_frame,
                    text=artist_name,
                    font=("Arial", 9),
                    bg=frame_bg,
                    fg="#6B6B6B",
                    anchor="w",
                    wraplength=140
                )
                artist_label.pack(anchor="w")

                # --- NÚT TRACK ---
                # 🎯 SỬA: dùng self.track_photo thay vì track_photo
                track_btn = tk.Button(
                    song_frame,
                    image=self.track_photo,  # 🎯 THÊM self.
                    bd=0,
                    relief="flat",
                    bg=frame_bg,
                    activebackground="#E9F5D8",
                    cursor="hand2",
                    command=lambda s=song: self.on_buy_click(s)
                )
                track_btn.place(x=10, y=32)

                # --- HOVER EFFECT ---
                def make_enter_handler(frame):
                    return lambda e: self.on_enter(frame)

                def make_leave_handler(frame):
                    return lambda e: self.on_leave(frame)

                for widget in [song_frame, track_label, artist_label]:
                    widget.bind("<Enter>", make_enter_handler(song_frame))
                    widget.bind("<Leave>", make_leave_handler(song_frame))

                # --- TOOLTIP ---
                tooltip_text = f"🎵 {song['trackName']}\n👤 {song['artistName']}"
                Tooltip(track_label, tooltip_text, wrap_length=40)
                Tooltip(artist_label, tooltip_text, wrap_length=40)
                if 'img_button' in locals():  # 🎯 KIỂM TRA BIẾN CÓ TỒN TẠI KHÔNG
                    Tooltip(img_button, tooltip_text, wrap_length=40)
                created_count += 1
                # print(f"🎵 [DEBUG CREATE] ĐÃ tạo xong bài {idx + 1}")
            except Exception as e:
                print(f"🚨 [DEBUG ERROR] Lỗi tại bài {idx + 1}: {e}")
                import traceback
                traceback.print_exc()  # 🎯 IN FULL TRACEBACK
                continue  # Tiếp tục bài tiếp theo
        print(f"🎵 [DEBUG REFRESH] KẾT THÚC - Đã tạo {created_count}/{len(self.songs_track)} bài")

        # 🎯 SỬA PHẦN SCROLL - DÙNG HÀM UPDATE_SCROLLREGION CỦA LỚP
        def update_scrollregion(event=None):
            self.tracklist_canvas.configure(scrollregion=self.tracklist_canvas.bbox("all"))

            # 🎯 FIX: SET HEIGHT TRONG MỌI TRƯỜNG HỢP
            required_height = self.tracklist_frame.winfo_reqheight()
            canvas_height = self.tracklist_canvas.winfo_height()

            # Luôn set height bằng chiều cao thực tế của frame
            self.tracklist_canvas.itemconfig(self.tracklist_window, height=required_height)

        self.tracklist_frame.bind("<Configure>", update_scrollregion)
        self.tracklist_canvas.bind("<Configure>", update_scrollregion)

        # --- THÊM SỰ KIỆN CUỘN BẰNG CHUỘT ---
        def on_mousewheel(event):
            if self.tracklist_frame.winfo_height() > self.tracklist_canvas.winfo_height():
                self.tracklist_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")

        self.tracklist_canvas.bind("<MouseWheel>", on_mousewheel)
        self.tracklist_frame.bind("<MouseWheel>", on_mousewheel)

        self.tracklist_frame.update_idletasks()
        update_scrollregion()
        # # 🎯 DEBUG CHI TIẾT CANVAS CONFIG
        # print(
        #     f"🎵 [DEBUG CANVAS] Canvas size: {self.tracklist_canvas.winfo_width()}x{self.tracklist_canvas.winfo_height()}")
        # print(
        #     f"🎵 [DEBUG CANVAS] Frame requested: {self.tracklist_frame.winfo_reqwidth()}x{self.tracklist_frame.winfo_reqheight()}")
        # print(
        #     f"🎵 [DEBUG CANVAS] Frame actual: {self.tracklist_frame.winfo_width()}x{self.tracklist_frame.winfo_height()}")
        # print(f"🎵 [DEBUG CANVAS] BBOX: {self.tracklist_canvas.bbox('all')}")

        # 🎯 FIX: ĐẢM BẢO WINDOW TRONG CANVAS CÓ ĐỦ CHỖ
        self.tracklist_canvas.itemconfig(self.tracklist_window, height=self.tracklist_frame.winfo_reqheight())

        # 🎯 UPDATE SCROLLREGION NHIỀU LẦN
        self.tracklist_frame.update_idletasks()
        self.tracklist_canvas.configure(scrollregion=self.tracklist_canvas.bbox("all"))

        # Force update sau khi render
        # def force_fix():
        #     self.tracklist_canvas.itemconfig(self.tracklist_window, height=self.tracklist_frame.winfo_reqheight())
        #     self.tracklist_canvas.configure(scrollregion=self.tracklist_canvas.bbox("all"))
        #     print(f"🎵 [DEBUG FIX] Window height: {self.tracklist_frame.winfo_reqheight()}")
        #     print(f"🎵 [DEBUG FIX] Scrollregion: {self.tracklist_canvas.bbox('all')}")
        #
        # self.tracklist_frame.after(100, force_fix)
        # self.tracklist_frame.after(200, force_fix)
        print(f"🎵 [DEBUG REFRESH] Đã tạo xong {len(self.songs_track)} bài")

    def load_more_tracks_async(self):
        """Load thêm 10 bài khi gần hết tracklist"""
        import threading

        def load_data():
            try:
                db = Connector()
                current_user = self.get_current_user()
                user_id = current_user['userId'] if current_user and 'userId' in current_user else None

                if not user_id: return

                # Load thêm 10 bài
                more_tracks = list(db.db["purchase"].aggregate([
                    {"$match": {"userId": user_id}},
                    {"$sort": {"purchased_at": 1}},
                    {"$skip": len(self.songs_track)},
                    {"$limit": 10},
                    {"$lookup": {
                        "from": "tracks",
                        "localField": "trackId",
                        "foreignField": "trackId",
                        "as": "trackDetails"
                    }},
                    {"$unwind": "$trackDetails"},
                    {"$project": {
                        "trackId": 1, "trackName": 1, "artistName": 1,
                        "artworkUrl100": 1, "previewUrl": "$trackDetails.previewUrl"
                    }}
                ]))

                if more_tracks:
                    self.songs_track.extend(more_tracks)
                    print(f"✅ Đã load thêm {len(more_tracks)} bài")

                    # Preload 3 ảnh đầu
                    self.preload_images_smart(more_tracks)

                    # 🎯 REFRESH UI ĐỂ HIỂN THỊ BÀI MỚI
                    self.refresh_tracklist_ui_simple()
                else:
                    print("⏹️ Không còn bài nào để load")

            except Exception as e:
                print(f"⚠️ Lỗi load thêm tracks: {e}")

        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()

    def preload_images_smart(self, new_tracks):
        """Preload THÔNG MINH - chỉ 3 ảnh đầu tiên"""
        import threading

        def load_critical_images():
            try:
                # 🎯 CHỈ LOAD 3 ẢNH QUAN TRỌNG NHẤT (bài 1-3 mới thêm)
                for i, track in enumerate(new_tracks[:3]):
                    track_id = track.get("trackId")
                    artwork = track.get("artworkUrl100", "")

                    # Chỉ load nếu chưa có trong cache
                    if track_id not in self.image_cache and artwork:
                        try:
                            response = requests.get(artwork, timeout=5)
                            img = Image.open(BytesIO(response.content)).resize((62, 62), Image.Resampling.LANCZOS)
                            song_photo = ImageTk.PhotoImage(img)
                            self.image_cache[track_id] = song_photo
                            print(f"🎵 [PRELOAD] Đã cache ảnh #{i + 1}: {track.get('trackName')}")
                        except Exception as e:
                            print(f"⚠️ Lỗi preload ảnh {track.get('trackName')}: {e}")

                print("✅ Đã preload 3 ảnh quan trọng")

            except Exception as e:
                print(f"⚠️ Lỗi preload images: {e}")

        thread = threading.Thread(target=load_critical_images, daemon=True)
        thread.start()

    def get_track_index(self, track_id):
        """Tìm index của bài hát trong tracklist"""
        for i, track in enumerate(self.songs_track):
            if track.get("trackId") == track_id:
                return i
        return -1

    # def create_disc_display(self):
    #     """Chuẩn bị ảnh đĩa mặc định"""
    #     # Đĩa mặc định PNG trong suốt
    #     self.default_disc_image = Image.open("Images/Disc.png").convert("RGBA").resize((250, 250))
    #     self.current_disc_photo = ImageTk.PhotoImage(self.default_disc_image)
    #
    #     # Vẽ đĩa mặc định lên canvas chính
    #     self.disc_image_id = self.canvas.create_image(367, 93, anchor="nw", image=self.current_disc_photo)
    #
    #     # Thêm text tên bài và nghệ sĩ (dưới đĩa)
    #     self.song_title_text = self.canvas.create_text(
    #         522, 370,
    #         text="",
    #         font=("Segoe UI", 20, "bold"),
    #         fill="#D56989"
    #     )
    #     self.song_artist_text = self.canvas.create_text(
    #         522, 402,
    #         text="",
    #         font=("Segoe UI", 14),
    #         fill="#D56989"
    #     )
    #
    # # def update_disc(self, song):
    # #     """Cập nhật ảnh đĩa + text"""
    # #
    # #     def load_image():
    # #         try:
    # #             image_url = song.get("artworkUrl100")
    # #             if image_url:
    # #                 response = requests.get(image_url)
    # #                 cover_img = Image.open(BytesIO(response.content)).convert("RGBA")
    # #             else:
    # #                 cover_img = self.default_disc_image
    # #
    # #             # Auto-scale ảnh để vừa với đĩa
    # #             cover_img = ImageOps.fit(cover_img, (250, 250))
    # #
    # #             # Tạo mask tròn (đảm bảo trong suốt)
    # #             mask = Image.new("L", (250, 250), 0)
    # #             draw = ImageDraw.Draw(mask)
    # #             draw.ellipse((0, 0, 250, 250), fill=255)
    # #             cover_img.putalpha(mask)
    # #
    # #             # Ghép với đĩa trong suốt
    # #             final_disc = Image.alpha_composite(self.default_disc_image, cover_img)
    # #
    # #         except Exception as e:
    # #             print("[ERROR] load disc:", e)
    # #             final_disc = self.default_disc_image
    # #
    # #         self.parent.after(0, lambda: self._display_disc(final_disc, song))
    # #
    # #     threading.Thread(target=load_image, daemon=True).start()
    #
    # def update_disc(self, song):
    #     """Cập nhật ảnh đĩa - CHỈ ẢNH BO TRÒN, KHÔNG ĐĨA"""
    #
    #     def load_image_disc():
    #         try:
    #             image_url = song.get("artworkUrl100")
    #             if image_url:
    #                 # 🎯 DÙNG HÀM load_image CÓ SẴN ĐỂ BO TRÒN ẢNH
    #                 final_disc = load_image(
    #                     image_url,
    #                     from_url=True,
    #                     size=(250, 250),
    #                     round_corner=125  # 🎯 BO TRÒN HOÀN TOÀN
    #                 )
    #             else:
    #                 # 🎯 ĐĨA MẶC ĐỊNH CŨNG BO TRÒN
    #                 final_disc = load_image(
    #                     "Images/Disc.png",
    #                     size=(250, 250),
    #                     round_corner=125
    #                 )
    #
    #         except Exception as e:
    #             print("[ERROR] load disc:", e)
    #             final_disc = self.default_disc_image
    #
    #         # 🎯 GIỮ NGUYÊN PHẦN HIỂN THỊ
    #         self.parent.after(0, lambda: self._display_disc_simple(final_disc, song))
    #
    #     threading.Thread(target=load_image_disc, daemon=True).start()
    #
    # def _display_disc_simple(self, disc_photo, song):
    #     """Hiển thị ảnh bo tròn đơn giản"""
    #     self.canvas.delete(self.disc_image_id)
    #
    #     # 🎯 VỊ TRÍ GIỮA (giữ nguyên)
    #     disc_x = 367
    #     disc_y = 93
    #
    #     # Hiển thị ảnh bo tròn
    #     self.disc_image_id = self.canvas.create_image(
    #         disc_x + 125,
    #         disc_y + 125,
    #         image=disc_photo,
    #         anchor="center"
    #     )
    #
    #     # Giữ reference
    #     self.current_disc_photo = disc_photo
    #
    #     # 🎯 GIỮ NGUYÊN PHẦN TEXT
    #     text_x = disc_x + 125
    #     text_y = disc_y + 250 + 20
    #
    #     # --- Auto-scale text ---
    #     def fit_font_size(text, base_size, max_width):
    #         """Giảm font đến khi vừa trong max_width"""
    #         size = base_size
    #         temp = tk.Label(self.parent, font=("Segoe UI", size, "bold"), text=text)
    #         temp.update_idletasks()
    #         while temp.winfo_reqwidth() > max_width and size > 10:
    #             size -= 1
    #             temp.config(font=("Segoe UI", size, "bold"))
    #             temp.update_idletasks()
    #         temp.destroy()
    #         return size
    #
    #     self.canvas.coords(self.song_title_text, text_x, text_y)
    #     self.canvas.coords(self.song_artist_text, text_x, text_y + 25)
    #
    #     title = song.get("trackName", "")
    #     artist = song.get("artistName", "")
    #
    #     # Auto-scale text (giữ nguyên)
    #     title_size = fit_font_size(title, 20, 250)
    #     artist_size = fit_font_size(artist, 14, 250)
    #
    #     self.canvas.itemconfig(self.song_title_text, text=title, font=("Segoe UI", title_size, "bold"))
    #     self.canvas.itemconfig(self.song_artist_text, text=artist, font=("Segoe UI", artist_size))
    #
    # @staticmethod
    # def draw_cd_image(canvas, image, x, y, radius=80, hole_path="Images/Hole_disc.png"):
    #     """Vẽ ảnh dạng đĩa CD có auto-scale và chèn ảnh lỗ trung tâm"""
    #     from PIL import Image, ImageTk, ImageDraw
    #
    #     # Resize ảnh CD theo tỉ lệ để vừa với canvas
    #     image = image.copy()
    #     image.thumbnail((radius * 2, radius * 2))
    #
    #     # Tạo mask hình tròn (để bo tròn ảnh)
    #     mask = Image.new("L", image.size, 0)
    #     draw = ImageDraw.Draw(mask)
    #     draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
    #     image.putalpha(mask)
    #
    #     # ======= 🔽 Thêm phần chèn ảnh lỗ giữa 🔽 =======
    #     try:
    #         hole_img = Image.open(hole_path).convert("RGBA")
    #
    #         # Tự động scale lỗ theo kích thước đĩa
    #         hole_size = int(radius * 0.45)  # bạn có thể chỉnh tỉ lệ này (0.25-0.35)
    #         hole_img = hole_img.resize((hole_size, hole_size))
    #
    #         # Tính toạ độ để dán lỗ ngay giữa đĩa
    #         cx, cy = image.size[0] // 2, image.size[1] // 2
    #         hx, hy = hole_img.size[0] // 2, hole_img.size[1] // 2
    #         image.paste(hole_img, (cx - hx, cy - hy), hole_img)
    #     except Exception as e:
    #         print(f"Lỗi tải hole image: {e}")
    #     # ================================================
    #
    #     # Convert sang ảnh Tkinter
    #     tk_image = ImageTk.PhotoImage(image)
    #
    #     # Vẽ lên canvas
    #     canvas.create_image(x, y, image=tk_image, anchor="center")
    #     canvas.image = tk_image  # tránh bị GC
    #     return tk_image
    def create_disc_display(self):
        """Chuẩn bị ảnh đĩa mặc định"""
        # Tạo ảnh placeholder tròn với lỗ giữa
        placeholder = Image.new("RGBA", (250, 250), (50, 50, 50, 255))
        self.current_disc_photo = self.draw_cd_image(self.canvas, placeholder, 367 + 125, 93 + 125, radius=125)

        # Vẽ đĩa mặc định lên canvas chính
        self.disc_image_id = self.canvas.create_image(367, 93, anchor="nw", image=self.current_disc_photo)

        self.is_disc_rotating = False
        self.disc_rotation_angle = 0
        self.disc_rotation_job = None

        # Thêm text tên bài và nghệ sĩ (dưới đĩa)
        self.song_title_text = self.canvas.create_text(
            522, 370,
            text="",
            font=("Segoe UI", 20, "bold"),
            fill="#D56989"
        )
        self.song_artist_text = self.canvas.create_text(
            522, 402,
            text="",
            font=("Segoe UI", 14),
            fill="#D56989"
        )

    def start_disc_rotation(self, reset_angle=False):
        """Bắt đầu xoay đĩa - reset_angle=True khi bài mới"""
        print(f"🔄 START ROTATION: is_disc_rotating={self.is_disc_rotating}, reset_angle={reset_angle}")

        if not self.is_disc_rotating:
            self.is_disc_rotating = True

            # 🔥 CHỈ RESET GÓC KHI BÀI MỚI
            if reset_angle:
                self.disc_rotation_angle = 0
                print("🔄 Reset góc về 0° (bài mới)")

            def check_and_rotate():
                if hasattr(self, 'current_disc_raw_image') and self.current_disc_raw_image is not None:
                    print(f"🌀 Bắt đầu xoay từ góc: {self.disc_rotation_angle}°")
                    self._rotate_disc()
                else:
                    self.parent.after(100, check_and_rotate)

            check_and_rotate()

    def stop_disc_rotation(self):
        """Dừng xoay đĩa - CHỈ DỪNG, KHÔNG RESET GÓC"""
        print(f"🛑 STOP ROTATION: is_disc_rotating={self.is_disc_rotating}, current_angle={self.disc_rotation_angle}°")
        self.is_disc_rotating = False
        if self.disc_rotation_job:
            self.parent.after_cancel(self.disc_rotation_job)
            self.disc_rotation_job = None

    def _rotate_disc(self):
        """Xoay đĩa - animation loop với xử lý lỗi"""
        try:
            if not self.is_disc_rotating or not hasattr(self, 'disc_image_id'):
                return

            # Cập nhật góc xoay
            self.disc_rotation_angle = (self.disc_rotation_angle + 2) % 360

            # Lấy ảnh gốc và xoay
            if hasattr(self, 'current_disc_raw_image'):
                rotated_image = self.current_disc_raw_image.rotate(
                    -self.disc_rotation_angle,
                    resample=Image.BICUBIC,
                    expand=False
                )

                # Chuyển sang PhotoImage và cập nhật
                tk_image = ImageTk.PhotoImage(rotated_image)
                self.canvas.itemconfig(self.disc_image_id, image=tk_image)
                self.canvas.image = tk_image  # Giữ reference

            # Lặp animation - CHỈ NẾU WINDOW CÒN TỒN TẠI
            if self.winfo_exists():  # 🔥 KIỂM TRA WIDGET CÒN TỒN TẠI
                self.disc_rotation_job = self.parent.after(50, self._rotate_disc)
            else:
                self.is_disc_rotating = False

        except Exception as e:
            print(f"❌ Lỗi trong _rotate_disc: {e}")
            self.is_disc_rotating = False  # 🔥 DỪNG KHI CÓ LỖI

    def update_disc(self, song):
        """Cập nhật ảnh đĩa - ẢNH TRÒN CÓ LỖ GIỮA"""

        def load_image_disc():
            try:
                image_url = song.get("artworkUrl100")
                if image_url:
                    # Tải ảnh từ URL
                    response = requests.get(image_url)
                    cover_img = Image.open(BytesIO(response.content)).convert("RGBA")
                else:
                    # Dùng ảnh mặc định
                    cover_img = Image.new("RGBA", (250, 250), (50, 50, 50, 255))

                # Resize ảnh
                cover_img = cover_img.resize((250, 250), Image.Resampling.LANCZOS)

            except Exception as e:
                print("[ERROR] load disc:", e)
                cover_img = Image.new("RGBA", (250, 250), (50, 50, 50, 255))

            # 🎯 GIỮ NGUYÊN PHẦN HIỂN THỊ
            self.parent.after(0, lambda: self._display_disc_with_hole(cover_img, song))

        threading.Thread(target=load_image_disc, daemon=True).start()

    def _display_disc_with_hole(self, cover_img, song):
        # """Hiển thị ảnh tròn có lỗ giữa"""
        # was_rotating = self.is_disc_rotating
        # current_angle = self.disc_rotation_angle
        # self.stop_disc_rotation()

        # Xóa ảnh cũ
        if hasattr(self, 'disc_image_id'):
            self.canvas.delete(self.disc_image_id)

        # 🎯 VỊ TRÍ GIỮA
        disc_x = 367
        disc_y = 93

        # 🎯 TẠO ẢNH BAN ĐẦU BẰNG HÀM draw_cd_image CÓ SẴN
        self.current_disc_photo = self.draw_cd_image(
            self.canvas,
            cover_img,
            disc_x + 125,
            disc_y + 125,
            radius=125
        )

        # 🎯 LƯU ẢNH GỐC ĐỂ XOAY - DÙNG HÀM MỚI
        self.current_disc_raw_image = self._create_pil_cd_image(cover_img, radius=125)

        # Lưu ID của ảnh
        self.disc_image_id = self.canvas.create_image(
            disc_x + 125,
            disc_y + 125,
            image=self.current_disc_photo,
            anchor="center"
        )

        # 🎯 GIỮ NGUYÊN PHẦN TEXT
        text_x = disc_x + 125
        text_y = disc_y + 250 + 20

        self.canvas.coords(self.song_title_text, text_x, text_y)
        self.canvas.coords(self.song_artist_text, text_x, text_y + 25)

        title = song.get("trackName", "")
        artist = song.get("artistName", "")

        # Auto-scale text
        title_size = self.fit_font_size(title, 20, 250)
        artist_size = self.fit_font_size(artist, 14, 250)

        self.canvas.itemconfig(self.song_title_text, text=title, font=("Segoe UI", title_size, "bold"))
        self.canvas.itemconfig(self.song_artist_text, text=artist, font=("Segoe UI", artist_size))

        # 🔥 BẮT ĐẦU XOAY NẾU ĐANG PHÁT NHẠC
        if hasattr(self.parent, 'songs') and self.parent.songs.is_playing:
            self.start_disc_rotation(reset_angle=True)

        self.canvas.itemconfig(self.song_title_text, text=title, font=("Segoe UI", title_size, "bold"))
        self.canvas.itemconfig(self.song_artist_text, text=artist, font=("Segoe UI", artist_size))

    def fit_font_size(self, text, base_size, max_width):
        """Giảm font đến khi vừa trong max_width"""
        if not text:
            return base_size

        size = base_size
        temp = tk.Label(self.parent, font=("Segoe UI", size, "bold"), text=text)
        temp.update_idletasks()
        while temp.winfo_reqwidth() > max_width and size > 10:
            size -= 1
            temp.config(font=("Segoe UI", size, "bold"))
            temp.update_idletasks()
        temp.destroy()
        return size

    @staticmethod
    def draw_cd_image(canvas, image, x, y, radius=125, hole_path="Hole_disc.png"):
        """Vẽ ảnh dạng đĩa CD có auto-scale và chèn ảnh lỗ trung tâm"""
        from PIL import Image, ImageTk, ImageDraw
        hole_path = relative_to_assets(hole_path)
        # Resize ảnh theo radius
        image = image.copy()
        image = image.resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)

        # Tạo mask hình tròn (để bo tròn ảnh)
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
        image.putalpha(mask)

        # ======= 🔽 Thêm phần chèn ảnh lỗ giữa 🔽 =======
        try:
            hole_img = Image.open(hole_path).convert("RGBA")

            # Tự động scale lỗ theo kích thước đĩa
            hole_size = int(radius * 0.45)  # bạn có thể chỉnh tỉ lệ này (0.25-0.35)
            hole_img = hole_img.resize((hole_size, hole_size))

            # Tính toạ độ để dán lỗ ngay giữa đĩa
            cx, cy = image.size[0] // 2, image.size[1] // 2
            hx, hy = hole_img.size[0] // 2, hole_img.size[1] // 2
            image.paste(hole_img, (cx - hx, cy - hy), hole_img)
        except Exception as e:
            print(f"Lỗi tải hole image: {e}")
        # ================================================

        # Convert sang ảnh Tkinter
        tk_image = ImageTk.PhotoImage(image)

        # Vẽ lên canvas
        canvas.create_image(x, y, image=tk_image, anchor="center")
        canvas.image = tk_image  # tránh bị GC
        return tk_image

    def _create_pil_cd_image(self, image, radius=125, hole_path="Hole_disc.png"):
        """Tạo ảnh CD với lỗ giữa - TRẢ VỀ PIL Image ĐỂ XOAY"""
        hole_path = relative_to_assets(hole_path)
        from PIL import Image, ImageDraw

        # Resize ảnh theo radius
        image = image.copy()
        image = image.resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)

        # Tạo mask hình tròn (để bo tròn ảnh)
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
        image.putalpha(mask)

        # Thêm lỗ giữa
        try:
            hole_img = Image.open(hole_path).convert("RGBA")
            hole_size = int(radius * 0.45)
            hole_img = hole_img.resize((hole_size, hole_size))

            cx, cy = image.size[0] // 2, image.size[1] // 2
            hx, hy = hole_img.size[0] // 2, hole_img.size[1] // 2
            image.paste(hole_img, (cx - hx, cy - hy), hole_img)
        except Exception as e:
            print(f"Lỗi tải hole image: {e}")

        return image

    def create_bottom_bar(self):
        """Tạo thanh điều kiển nhạc - LƯU REFERENCE NÚT LOVE"""
        # --- Danh sách nút: (tên file ảnh, hàm callback) ---
        buttons_info = [
            ("heart.png", self.like_song),  # 🔥 ẢNH MẶC ĐỊNH (CHƯA LOVE)
            ("previous.png", self.prev_song),
            ("pause.png", self.toggle_play),
            ("next.png", self.next_song),
            ("dots.png", lambda: self.show_song_menu(self.current_song, 595, 545)),
        ]

        self.bottom_icons = []  # Giữ reference ảnh
        self.bottom_labels = []  # Giữ reference label để xử lý hover
        self.love_button = None  # 🔥 LƯU REFERENCE NÚT LOVE

        # --- Toạ độ trung tâm + khoảng cách giữa các nút ---
        center_x = (self.canvas.winfo_reqwidth() // 2) + 25 if self.canvas.winfo_reqwidth() > 0 else 500
        y_pos = 520
        spacing = 60

        # --- Load icon và vẽ từng nút ---
        for i, (icon_file, command) in enumerate(buttons_info):
            try:
                icon_path = relative_to_assets(icon_file)
                icon_img = Image.open(icon_path).resize((35, 35), Image.Resampling.LANCZOS)
                icon_tk = ImageTk.PhotoImage(icon_img)
                self.bottom_icons.append(icon_tk)

                # --- Tạo Label làm nút trong suốt ---
                lbl = tk.Label(
                    self.canvas,
                    image=icon_tk,
                    bg=self.canvas["bg"],
                    bd=0,
                    highlightthickness=0,
                    cursor="hand2"
                )
                lbl.image = icon_tk

                # --- Hiệu ứng nhấn ---
                def on_press(e, l=lbl):
                    l.config(bg=self.canvas["bg"], width=32, height=32)

                def on_release(e, cmd=command, l=lbl):
                    l.config(bg=self.canvas["bg"], width=35, height=35)
                    if callable(cmd):
                        cmd()

                lbl.bind("<ButtonPress-1>", on_press)
                lbl.bind("<ButtonRelease-1>", on_release)

                # --- Vẽ lên canvas ---
                x_pos = center_x + (i - 2) * spacing
                self.canvas.create_window(x_pos, y_pos, window=lbl, anchor="center")
                self.bottom_labels.append(lbl)

                # 🔥 LƯU REFERENCE NÚT LOVE (nút đầu tiên)
                if i == 0:
                    self.love_button = lbl
                    print("✅ Đã lưu reference nút love")

            except Exception as e:
                print(f"❌ Lỗi tạo nút {icon_file}: {e}")

    def show_play_button(self):
        """Hiển thị nút play (đổi icon pause → play)"""
        try:
            # 🔥 NÚT PLAY/PAUSE LÀ BUTTON THỨ 3 (index 2)
            if len(self.bottom_labels) > 2:
                lbl = self.bottom_labels[2]
                play_img = Image.open(relative_to_assets("play.png")).resize((35, 35), Image.Resampling.LANCZOS)
                play_tk = ImageTk.PhotoImage(play_img)
                self.bottom_icons[2] = play_tk
                lbl.config(image=play_tk)
                lbl.image = play_tk
            print("[DEBUG] 🎵 Đã đổi thành nút play")
        except Exception as e:
            print(f"❌ Lỗi show_play_button: {e}")

    def show_pause_button(self):
        """Hiển thị nút pause (đổi icon play → pause)"""
        try:
            # 🔥 NÚT PLAY/PAUSE LÀ BUTTON THỨ 3 (index 2)
            if len(self.bottom_labels) > 2:
                lbl = self.bottom_labels[2]
                pause_img = Image.open(relative_to_assets("pause.png")).resize((35, 35), Image.Resampling.LANCZOS)
                pause_tk = ImageTk.PhotoImage(pause_img)
                self.bottom_icons[2] = pause_tk
                lbl.config(image=pause_tk)
                lbl.image = pause_tk
            print("[DEBUG] 🎵 Đã đổi thành nút pause")
        except Exception as e:
            print(f"❌ Lỗi show_pause_button: {e}")

    def create_progress_bar(self):
        """Tạo thanh tiến trình nhạc (nằm trên thanh nút điều khiển)."""
        # 🔥 ĐIỀU CHỈNH VỊ TRÍ: căn giữa khung giữa (303-681)
        progress_area_width = 681 - 303  # = 378px
        self.progress_width = 350  # Giữ nguyên hoặc điều chỉnh nếu cần

        # Tính toán vị trí căn giữa
        self.progress_start_x = 303 + (
                    progress_area_width - self.progress_width) // 2  # = 303 + (378-350)//2 = 303 + 14 = 317
        self.progress_y = 455  # Giữ nguyên hoặc điều chỉnh nếu cần

        # Thanh nền
        self.progress_bg = self.canvas.create_rectangle(
            self.progress_start_x, self.progress_y,
            self.progress_start_x + self.progress_width, self.progress_y + 5,
            fill="#F4EFD7", outline=""
        )
        # Thanh chạy
        self.progress_fg = self.canvas.create_rectangle(
            self.progress_start_x, self.progress_y,
            self.progress_start_x, self.progress_y + 5,
            fill="#F586A3", outline=""
        )
        # Chấm tròn
        self.progress_dot = self.canvas.create_oval(
            self.progress_start_x - 5, self.progress_y - 3,
            self.progress_start_x + 5, self.progress_y + 7,
            fill="#F586A3", outline=""
        )

        # Thời gian
        self.time_start = self.canvas.create_text(
            self.progress_start_x +5, self.progress_y - 15,
            text="0:00", font=("Arial", 10), fill="#555"
        )
        self.time_end = self.canvas.create_text(
            self.progress_start_x + self.progress_width-5, self.progress_y-15,
            text="0:30", font=("Arial", 10), fill="#555"
        )

        # --- Tua bằng kéo chấm ---
        self.canvas.tag_bind(self.progress_dot, "<ButtonPress-1>", self._on_dot_press)
        self.canvas.tag_bind(self.progress_dot, "<B1-Motion>", self._on_dot_drag)
        self.canvas.tag_bind(self.progress_dot, "<ButtonRelease-1>", self._on_dot_release)

    def _on_dot_press(self, event):
        self.dragging = True

    def _on_dot_drag(self, event):
        if not getattr(self, "dragging", False):
            return
        new_x = max(self.progress_start_x,
                    min(event.x, self.progress_start_x + self.progress_width))
        self.canvas.coords(
            self.progress_dot,
            new_x - 5, self.progress_y - 3,
            new_x + 5, self.progress_y + 7
        )
        # cập nhật thanh foreground
        self.canvas.coords(
            self.progress_fg,
            self.progress_start_x, self.progress_y,
            new_x, self.progress_y + 5
        )
        # cập nhật thời gian
        ratio = (new_x - self.progress_start_x) / self.progress_width
        current_time = ratio * self.duration
        self.canvas.itemconfig(self.time_start, text=f"0:{int(current_time):02d}")

    def _on_dot_release(self, event):
        if not getattr(self, "dragging", False):
            return
        self.dragging = False
        new_x = max(self.progress_start_x,
                    min(event.x, self.progress_start_x + self.progress_width))
        ratio = (new_x - self.progress_start_x) / self.progress_width
        new_time = ratio * self.duration
        self.seek_song(new_time)

    def update_progress(self, current_time=None):
        """Cập nhật giao diện thanh tiến trình với time thật từ MainScreen"""
        if hasattr(self, '_is_closing') and self._is_closing:
            return

        try:
            # # 🔥 DEBUG: KIỂM TRA STATE
            # print(f"[PROGRESS DEBUG] 🎵 update_progress called:")
            # print(f"  - current_time param: {current_time}")
            # print(f"  - has songs_manager: {hasattr(self, 'songs_manager')}")
            #
            # if hasattr(self, 'songs_manager') and self.songs_manager:
            #     print(f"  - songs_manager.is_playing: {getattr(self.songs_manager, 'is_playing', 'N/A')}")
            #     print(f"  - songs_manager.current_time: {getattr(self.songs_manager, 'current_time', 'N/A')}")

            # 🔥 LẤY CURRENT_TIME THẬT TỪ MAINSCREEN
            if current_time is None and hasattr(self, 'songs_manager') and self.songs_manager:
                current_time = getattr(self.songs_manager, 'current_time', 0)
                # print(f"  - current_time from songs_manager: {current_time}")

            # 🔥 PREVIEW LUÔN 30 GIÂY
            duration = 30

            ratio = min(current_time / duration, 1)
            new_x = self.progress_start_x + self.progress_width * ratio

            # print(f"  - ratio: {ratio}, new_x: {new_x}")

            # cập nhật thanh foreground
            self.canvas.coords(
                self.progress_fg,
                self.progress_start_x, self.progress_y,
                new_x, self.progress_y + 5
            )
            # cập nhật chấm tròn
            self.canvas.coords(
                self.progress_dot,
                new_x - 5, self.progress_y - 3,
                new_x + 5, self.progress_y + 7
            )
            # cập nhật thời gian
            self.canvas.itemconfig(self.time_start, text=f"0:{int(current_time):02d}")

            # 🔥 TIẾP TỤC LOOP NẾU ĐANG PHÁT
            if hasattr(self, 'songs_manager') and self.songs_manager and self.songs_manager.is_playing:
                # print(f"  - 🔄 Continuing progress loop...")
                # Lấy time mới từ MainScreen sau 100ms
                self.progress_loop_id = self.frame.after(100, self.update_progress)
            else:
                # print(f"  - ⏸️ Stopping progress loop")
                self.progress_loop_id = None

        except tk.TclError:
            print(f"  - ❌ TclError in update_progress")
            self.progress_loop_id = None
        except Exception as e:
            print(f"  - ❌ Other error: {e}")
            self.progress_loop_id = None

    def start_progress_loop(self):
        """Bắt đầu vòng lặp cập nhật progress bar"""
        # print(f"[PROGRESS DEBUG] 🔄 start_progress_loop called")

        # Hủy loop cũ nếu có
        if self.progress_loop_id:
            self.frame.after_cancel(self.progress_loop_id)
            # print(f"  - Cancelled old loop: {self.progress_loop_id}")

        # Bắt đầu loop mới
        self.update_progress()  # 🔥 KHÔNG TRUYỀN THAM SỐ - TỰ LẤY TIME THẬT
        # print(f"  - Started new progress loop")

    def seek_song(self, time_seconds):
        """Tua bài hát - GỌI QUA MAINSCREEN"""
        # 1. DỪNG vòng lặp cũ trước
        if self.progress_loop_id:
            self.frame.after_cancel(self.progress_loop_id)
            self.progress_loop_id = None

        # 2. Cập nhật thời gian mới
        self.current_time = min(max(time_seconds, 0), self.duration)

        # 3. Cập nhật UI
        self.update_progress(self.current_time)

        print(f"[DEBUG] ⏩ Tua đến: {self.current_time:.1f}s")

        # 4. 🔥 GỌI HÀM SEEK CỦA MAINSCREEN (SONG)
        if hasattr(self, 'songs_manager') and hasattr(self.songs_manager, 'seek_song'):
            self.songs_manager.seek_song(time_seconds)
            print(f"✅ Player: Đã gọi seek_song của MainScreen")
        else:
            print("❌ Không thể tua: Không tìm thấy songs_manager hoặc seek_song")

        # 5. Nếu đang playing, tiếp tục vòng lặp từ vị trí mới
        if self.is_playing:
            self.update_progress(self.current_time)

    def on_close(self):
        """Đảm bảo dừng vòng lặp và hủy an toàn khi đóng cửa sổ hoặc gỡ frame."""
        if hasattr(self, "_is_closing") and self._is_closing:
            return
        self._is_closing = True

        print("[DEBUG] 🚨 Bắt đầu đóng cửa sổ...")

        # 1. Dừng vòng lặp progress
        if hasattr(self, "progress_loop_id") and self.progress_loop_id:
            try:
                self.frame.after_cancel(self.progress_loop_id)
                print("[DEBUG] ✅ Đã dừng progress loop")
            except Exception as e:
                print(f"[DEBUG] ❌ Lỗi dừng progress: {e}")
            self.progress_loop_id = None

        # 2. Dừng audio
        if hasattr(self, "audio_manager") and self.audio_manager:
            try:
                self.audio_manager.stop()
                print("[DEBUG] ✅ Đã dừng audio")
            except Exception as e:
                print(f"[DEBUG] ❌ Lỗi dừng audio: {e}")

        # 3. Clear images
        if hasattr(self, "tracklist_images"):
            self.tracklist_images.clear()
            print("[DEBUG] ✅ Đã clear images")

        # 4. Đóng cửa sổ - CÁCH TRIỆT ĐỂ
        if self.is_standalone:
            print("[DEBUG] ❌ Đóng cửa sổ chính.")
            try:
                # Cách an toàn nhất: thoát chương trình
                sys.exit(0)
            except Exception as e:
                print(f"[DEBUG] ❌ Lỗi đóng cửa sổ: {e}")
        else:
            print("[DEBUG] 🔒 Hủy frame player (giao diện con).")
            try:
                self.frame.destroy()
            except Exception as e:
                print(f"[DEBUG] ❌ Lỗi hủy frame: {e}")

    def cleanup(self):
        """Dọn dẹp an toàn"""
        print("[PLAYER] Đang dọn dẹp...")

        # Đánh dấu đang closing
        self._is_closing = True

        # Dừng vòng lặp progress
        if hasattr(self, "progress_loop_id") and self.progress_loop_id:
            try:
                self.frame.after_cancel(self.progress_loop_id)
            except:
                pass
            self.progress_loop_id = None


    def hide_player_ui(self):
        """Ẩn giao diện player chính"""
        print("[DEBUG] 🎭 Đang ẩn player UI")

        if hasattr(self, 'canvas'):
            print(f"[DEBUG] 📏 Canvas trước khi destroy: {self.canvas.winfo_width()}x{self.canvas.winfo_height()}")
            self.canvas.destroy()
            print("[DEBUG] ✅ Đã destroy canvas")

    def back_to_player(self):
        """Quay lại player chính"""
        print("[DEBUG] 🔙 Quay lại player chính")

        # Xóa menu frame
        if hasattr(self, 'song_menu_frame'):
            self.song_menu_frame.destroy()
            delattr(self, 'song_menu_frame')
            print("[DEBUG] ✅ Đã destroy song_menu_frame")

        # Xóa các frame khác
        if hasattr(self, 'mood_frame'):
            self.mood_frame.destroy()
            delattr(self, 'mood_frame')
        if hasattr(self, 'rating_frame'):
            self.rating_frame.destroy()
            delattr(self, 'rating_frame')

        # Tạo lại UI
        print("[DEBUG] 🎨 Đang tạo lại player UI...")
        self.setup_ui()

        # Khôi phục bài hát
        if self.current_song:
            self.update_disc(self.current_song)
            print(f"[DEBUG] ✅ Đã khôi phục bài: {self.current_song['trackName']}")

        print("[DEBUG] 🎉 Đã quay lại player thành công")

    def show_rating_ui(self, song):
        """Gọi rating UI từ HomeScreen"""
        try:
            # 🔥 THỬ CÁC CÁCH IMPORT KHÁC NHAU
            try:
                from FinalProject.session import current_user
                print(f"[MOOD] 🔍 current_user from FinalProject.session: {current_user}")
            except ImportError:
                try:
                    import session
                    current_user = session.current_user
                    print(f"[MOOD] 🔍 current_user from session: {current_user}")
                except ImportError:
                    from main import current_user
                    print(f"[MOOD] 🔍 current_user from main: {current_user}")

            user_id = None
            if current_user:
                user_id = current_user.get("userId")
                print(f"[MOOD] 👤 User ID: {user_id}")
            else:
                print("[MOOD] ⚠️ current_user vẫn là None")
                # Dùng test user tạm thời
                user_id = "113025"

            # 🔥 GỌI _create_rating_ui VỚI user_id
            self._create_rating_ui(song, user_id)

        except Exception as e:
            print(f"[MOOD] ❌ Lỗi import: {e}")
            # Fallback với user_id mặc định
            self._create_rating_ui(song, "113025")


    # def _create_rating_ui(self, song,user_id):
    #     """Luôn tạo rating area mới"""
    #     print(f"[RATING] 🚀 Fallback: Creating rating in player for: {song['trackName']}")
    #
    #     # 🔥 LUÔN TẠO MỚI RATING AREA
    #     if hasattr(self, 'rating_area'):
    #         self.rating_area.destroy()
    #
    #     self.rating_area = Frame(self, bg="#F7F7DC")
    #     self.rating_area.place(x=200, y=100, width=300, height=200)
    #
    #     self.rating_frame = RatingFrame(
    #         parent=self.rating_area,
    #         controller=self.controller,
    #         song=song,
    #         user_id=user_id,
    #     )
    #     self.rating_frame.place(x=0, y=0, width=300, height=200)

    def _create_rating_ui(self, song, user_id):
        """Luôn tạo rating area mới - XỬ LÝ CẢ 2 CONTEXT"""
        print(f"[RATING] 🚀 Creating rating for: {song['trackName']}")

        # 🔥 XÁC ĐỊNH PARENT PHÙ HỢP
        if hasattr(self, 'parent') and hasattr(self.parent, 'mood_player_frame'):
            # Đang ở MainScreen → tạo TRỰC TIẾP trong MainScreen, không phải mood_player_frame
            target_parent = self.parent  # MainScreen chính nó
            print("[RATING] 📍 Context: MainScreen → creating directly in MainScreen")
        else:
            # Đang ở MoodPlayerFrame → tạo trong chính nó
            target_parent = self
            print("[RATING] 📍 Context: MoodPlayerFrame → creating in self")

        # 🔥 LUÔN TẠO MỚI RATING AREA
        if hasattr(target_parent, 'rating_area'):
            target_parent.rating_area.destroy()

        # Tạo rating area mới
        target_parent.rating_area = Frame(target_parent, bg="#F7F7DC")
        target_parent.rating_area.place(x=200, y=100, width=300, height=200)

        # 🔥 TẠO RATING FRAME
        rating_frame = RatingFrame(
            parent=target_parent.rating_area,
            controller=self.controller if hasattr(self, 'controller') else None,
            song=song,
            user_id=user_id,
        )
        rating_frame.place(x=0, y=0, width=300, height=200)

        # Lưu reference
        if hasattr(self, 'rating_frame'):
            self.rating_frame = rating_frame

    def show_mood_selection(self, song):
        """Hiển thị mood selection UI"""
        print(f"[MOOD] 📢 Show mood selection for: {song['trackName']}")

        try:
            # 🔥 THỬ CÁC CÁCH IMPORT KHÁC NHAU
            try:
                from FinalProject.session import current_user
                print(f"[MOOD] 🔍 current_user from FinalProject.session: {current_user}")
            except ImportError:
                try:
                    import session
                    current_user = session.current_user
                    print(f"[MOOD] 🔍 current_user from session: {current_user}")
                except ImportError:
                    from main import current_user
                    print(f"[MOOD] 🔍 current_user from main: {current_user}")

            user_id = None
            if current_user:
                user_id = current_user.get("userId")
                print(f"[MOOD] 👤 User ID: {user_id}")
            else:
                print("[MOOD] ⚠️ current_user vẫn là None")
                user_id = "113025"

            # 🔥 GỌI _create_mood_ui VỚI user_id
            self._create_mood_ui(song, user_id)

        except Exception as e:
            print(f"[MOOD] ❌ Lỗi import: {e}")
            # Fallback với user_id mặc định
            self._create_mood_ui(song, "113025")

    def _create_mood_ui(self, song, user_id):
        """Luôn tạo mood area mới - XỬ LÝ CẢ 2 CONTEXT"""
        print(f"[MOOD] 🚀 Creating mood selection for: {song['trackName']}")

        # 🔥 XÁC ĐỊNH PARENT PHÙ HỢP
        if hasattr(self, 'parent') and hasattr(self.parent, 'mood_player_frame'):
            # Đang ở MainScreen → tạo TRỰC TIẾP trong MainScreen, không phải mood_player_frame
            target_parent = self.parent  # MainScreen chính nó
            print("[MOOD] 📍 Context: MainScreen → creating directly in MainScreen")
        else:
            # Đang ở MoodPlayerFrame → tạo trong chính nó
            target_parent = self
            print("[MOOD] 📍 Context: MoodPlayerFrame → creating in self")

        # 🔥 LUÔN TẠO MỚI MOOD AREA
        if hasattr(target_parent, 'mood_area'):
            target_parent.mood_area.destroy()

        # Tạo mood area mới
        target_parent.mood_area = Frame(target_parent, bg="#F7F7DC", relief="solid", bd=0)
        target_parent.mood_area.place(x=200, y=100, width=300, height=200)

        print(f"[MOOD] 📍 Mood area created at: 200, 100")

        # 🔥 TẠO MOOD SELECTION FRAME
        mood_frame = SongMoodsFrame(
            parent=target_parent.mood_area,
            controller=self.controller if hasattr(self, 'controller') else None,
            song=song,
            user_id=user_id
        )
        mood_frame.place(x=0, y=0, width=300, height=200)

        # Lưu reference
        if hasattr(self, 'mood_frame'):
            self.mood_frame = mood_frame

        print("[MOOD] ✅ Đã tạo SongMoodsFrame")
class RatingFrame(Frame):
    def __init__(self, parent, controller, song,user_id=None):
        super().__init__(parent)
        self.controller = controller
        self.song = song
        self.user_id = user_id
        self.rating_manager = RatingManager()  # 🔥 GIỮ NGUYÊN RATING MANAGER

        print(f"[RATING] 🔥 RatingFrame __init__ called")

        self.configure(bg="#F7F7DC", width=300, height=200)
        self.pack_propagate(False)

        # Biến state
        self.star_rating = 0
        self.star_labels = []

        self.setup_ui()
        print(f"[RATING] ✅ RatingFrame setup completed")
        self.bind("<Button-1>", self.check_click_outside)

    # def setup_ui(self):
    #     """Khởi tạo UI rating"""
    #     print(f"[RATING] 🎨 Setting up RatingFrame UI")
    #     # Header
    #     header = Frame(self, bg="#C5D7A1", height=40)
    #     header.pack(fill="x", pady=(0, 10))
    #
    #     tk.Label(header, text="Đánh giá bài hát",
    #              font=("Arial", 12, "bold"), bg="#C5D7A1", fg="#D56989").pack(pady=10)
    #
    #     # Song info
    #     song_frame = Frame(self, bg="#F7F7DC")
    #     song_frame.pack(fill="x", padx=20, pady=5)
    #
    #     tk.Label(song_frame, text=self.song['trackName'],
    #              font=("Arial", 10, "bold"), bg="#F7F7DC", wraplength=250).pack()
    #     tk.Label(song_frame, text=self.song['artistName'],
    #              font=("Arial", 9), bg="#F7F7DC", fg="#666").pack()
    #
    #     # Rating stars
    #     self.rating_frame = Frame(self, bg="#F7F7DC")
    #     self.rating_frame.pack(pady=15)
    #
    #     # 🔥 LẤY RATING HIỆN TẠI TỪ RATING MANAGER
    #     self.current_rating = self.rating_manager.get_rating(self.song['trackId'])
    #     self.star_rating = self.current_rating
    #
    #     for i in range(1, 6):
    #         star = tk.Label(self.rating_frame, text="☆", font=("Arial", 20),
    #                         bg="#F7F7DC", fg="#FFD700", cursor="hand2")
    #         star.pack(side="left", padx=2)
    #         star.bind("<Button-1>", lambda e, r=i: self.set_rating(r))
    #         self.star_labels.append(star)
    #
    #     self.update_stars()
    #
    #     # Buttons
    #     btn_frame = Frame(self, bg="#F7F7DC")
    #     btn_frame.pack(pady=10, fill="x", padx=20)  # 🔥 THÊM fill="x" VÀ padx
    #
    #     # 🔥 DÙNG grid HOẶC pack VỚI expand
    #     tk.Button(btn_frame, text="Lưu", font=("Arial", 10),
    #               command=self.save_rating, bg="#94BB7C", fg="white", width=10
    #               ).pack(side="left", expand=True, padx=5)  # 🔥 THÊM expand=True
    #
    #     tk.Button(btn_frame, text="Đóng", font=("Arial", 10),
    #               command=lambda: self.master.destroy(),  # 🔥 DESTROY PARENT AREA
    #               bg="#E9F5D8", width=10
    #               ).pack(side="left", expand=True, padx=5)

    def setup_ui(self):
        """Khởi tạo UI rating theo design mới"""
        print(f"[RATING] 🎨 Setting up new RatingFrame UI")

        # 🔥 MÀU BACKGROUND CHÍNH (dùng cho tất cả widget)
        self.main_bg = "#F8F5E6"  # Màu be nhạt đẹp

        # 🔥 TẠO BACKGROUND CHÍNH
        self.bg_canvas = tk.Canvas(self, width=300, height=200, highlightthickness=0, bg=self.main_bg)
        self.bg_canvas.pack(fill="both")

        # 🔥 LOAD VÀ HIỂN THỊ BACKGROUND (thay bằng đường dẫn ảnh thực tế)
        try:
            self.bg_image = Image.open(relative_to_assets("rating_bg.png"))  # Thay bằng ảnh background của bạn
            self.bg_image = self.bg_image.resize((300, 200), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            self.main_bg = ""
        except Exception as e:
            print(f"❌ Không load được background: {e}")
            # Fallback: màu nền đẹp
            self.bg_canvas.configure(bg=self.main_bg)

        # 🔥 TITLE "Rate The Song" - Đặt ở trên cùng
        self.bg_canvas.create_text(150, 18, text="Rate The Song",
                                   font=("Arial", 15, "bold"), fill="#F2829E")

        #🔥 THÔNG TIN BÀI HÁT - Đặt giữa màn hình
        song_text = f"{self.song['trackName']}\n{self.song['artistName']}"
        self.bg_canvas.create_text(150, 60, text=song_text,
                                   font=("Arial", 10), fill="#F2829E",
                                   justify="center", width=250)

        # 🔥 KHU VỰC ĐÁNH GIÁ SAO - Đặt dưới thông tin bài hát
        self.star_frame = tk.Frame(self.bg_canvas, bg="#FEFBE5")
        self.star_frame_window = self.bg_canvas.create_window(150, 100, window=self.star_frame)

        self.star_labels = []
        self.star_rating = self.rating_manager.get_rating(self.song['trackId'],self.user_id)

        # Tạo 5 ngôi sao
        for i in range(1, 6):
            star = tk.Label(self.star_frame, text="☆", font=("Arial", 18),
                            bg="#FEFBE5", fg="#F9F8DE", cursor="hand2")
            star.pack(side="left", padx=3)
            star.bind("<Button-1>", lambda e, r=i: self.set_rating(r))
            self.star_labels.append(star)

        self.update_stars()

        # 🔥 KHU VỰC NÚT - Đặt ở dưới cùng
        self.btn_frame = tk.Frame(self.bg_canvas, bg="#FEFBE5")
        self.btn_frame_window = self.bg_canvas.create_window(150, 140, window=self.btn_frame)

        # 🔥 NÚT SAVE với background đẹp
        try:
            save_img = Image.open(relative_to_assets("save_button.png"))  # Thay bằng ảnh nút Save
            save_img = save_img.resize((60, 30), Image.Resampling.LANCZOS)
            self.save_photo = ImageTk.PhotoImage(save_img)
            save_btn = tk.Button(self.btn_frame, image=self.save_photo,
                                 command=self.save_rating, bd=0, bg="#F9F8DE")
        except:
            # Fallback nếu không load được ảnh
            save_btn = tk.Button(self.btn_frame, text="Save", font=("Arial", 10, "bold"),
                                 command=self.save_rating, bg="#94BB7C", fg="white",
                                 width=8, height=1, bd=0)

        save_btn.pack(side="left", padx=5)

        # # 🔥 NÚT CLOSE với background đẹp
        # try:
        #     close_img = Image.open("assets/close_button.png")  # Thay bằng ảnh nút Close
        #     close_img = close_img.resize((80, 30), Image.Resampling.LANCZOS)
        #     self.close_photo = ImageTk.PhotoImage(close_img)
        #     close_btn = tk.Button(self.btn_frame, image=self.close_photo,
        #                           command=self.close_rating, bd=0, bg="")
        # except:
        #     # Fallback nếu không load được ảnh
        #     close_btn = tk.Button(self.btn_frame, text="Close", font=("Arial", 10, "bold"),
        #                           command=self.close_rating, bg="#E9B6B6", fg="white",
        #                           width=8, height=1, bd=0)
        #
        # close_btn.pack(side="left", padx=10)

    def set_rating(self, rating):
        """Đặt rating và cập nhật sao"""
        self.star_rating = rating
        self.update_stars()

    def update_stars(self):
        """Cập nhật hiển thị sao"""
        for i, star in enumerate(self.star_labels):
            if i < self.star_rating:
                star.config(text="★", fg="#FFD700")  # Sao vàng
            else:
                star.config(text="☆", fg="#CCCCCC")  # Sao xám

    def save_rating(self):
        success = self.rating_manager.save_rating(
            track_id=self.song['trackId'],
            rating=self.star_rating,
            user_id=self.user_id  # 🔥 THÊM user_id
        )
        if success:
            print(f"✅ Đã lưu rating {self.star_rating}⭐")
            # 🔥 DESTROY CẢ PARENT AREA
            if hasattr(self, 'master'):
                self.master.destroy()
            else:
                self.destroy()

    def check_click_outside(self, event):
        """Đóng frame nếu click outside"""
        if not self.winfo_containing(event.x_root, event.y_root):
            self.destroy()

class SongMoodsFrame(Frame):
    def __init__(self, parent, controller, song,user_id=None):
        super().__init__(parent)
        self.controller = controller
        self.song = song
        self.mood_manager = MoodManager()
        self.selected_mood = 0
        self.user_id = user_id
        self.setup_ui()

    def setup_ui(self):
        """Khởi tạo UI mood selection"""
        print(f"[MOOD] 🎨 Setting up MoodSelectionFrame UI for: {self.song['trackName']}")

        self.main_bg = "#FEFBE5"
        # 🔥 TẠO BACKGROUND CHÍNH
        self.bg_canvas = tk.Canvas(self, width=400, height=250, highlightthickness=0, bg=self.main_bg)
        self.bg_canvas.pack(fill="both")
        # 🔥 LOAD BACKGROUND IMAGE
        try:
            self.bg_image = Image.open(relative_to_assets("rating_bg.png"))
            self.bg_image = self.bg_image.resize((300, 200), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            self.main_bg = "#FEFBE5"
        except Exception as e:
            print(f"❌ Không load được mood background: {e}")
            self.bg_canvas.configure(bg=self.main_bg)
        # 🔥 TITLE "Choose Song Mood"
        self.bg_canvas.create_text(150, 18, text="Choose Song Mood",
                                   font=("Arial", 14, "bold"), fill="#F2829E")
        # 🔥 KHU VỰC CHỌN MOOD - 4 nút mood là 4 ảnh
        self.mood_frame = tk.Frame(self.bg_canvas, bg=self.main_bg)
        self.mood_frame_window = self.bg_canvas.create_window(150, 100, window=self.mood_frame)
        # 🔥 LẤY MOOD ĐÃ CHỌN TRƯỚC ĐÓ
        previous_mood = self.mood_manager.get_mood(self.song['trackId'],self.user_id)
        print(f"[MOOD] 🔍 Previous mood for this song: {previous_mood}")

        if previous_mood > 0:
            self.selected_mood = previous_mood
            print(f"[MOOD] ✅ Đã tìm thấy mood trước đó: {previous_mood}")
        else:
            self.selected_mood = 0
            print("[MOOD] ℹ️ Chưa có mood trước đó")

        # 🔥 4 MOOD BUTTONS LÀ ẢNH
        self.mood_buttons = []
        self.mood_images = []

        moods = [
            (1, "Happy", "happy.png"),
            (2, "Sad", "sad.png"),
            (3, "Neutral", "neutral.png"),
            (4, "Intense", "intense.png")
        ]

        # Tạo 4 nút mood (2x2 grid)
        for idx, (mood_id, mood_name, img_file) in enumerate(moods):
            row = idx // 2
            col = idx % 2

            try:
                # Load ảnh mood sử dụng relative_to_assets
                img_path = relative_to_assets(img_file)
                mood_img = Image.open(img_path)
                mood_img = mood_img.resize((50, 50), Image.Resampling.LANCZOS)  # Kích thước ảnh
                mood_photo = ImageTk.PhotoImage(mood_img)
                self.mood_images.append(mood_photo)

                # Tạo nút mood là Label với ảnh
                mood_btn = tk.Label(self.mood_frame,
                                    image=mood_photo,
                                    cursor="hand2",
                                    bg=self.main_bg,
                                    bd=0)

            except Exception as e:
                print(f"❌ Không load được ảnh mood {mood_name}: {e}")
                # Fallback: tạo nút chữ nếu không có ảnh
                mood_btn = tk.Label(self.mood_frame,
                                    text=mood_name,
                                    font=("Arial", 9, "bold"),
                                    bg="#94BB7C",
                                    fg="white",
                                    cursor="hand2",
                                    width=8,
                                    height=3)

            mood_btn.grid(row=row, column=col, padx=10, pady=10)
            # 🔥 CLICK VÀO NÚT LÀ LƯU LUÔN
            mood_btn.bind("<Button-1>", lambda e, m=mood_id: self.select_and_save_mood(m))
            self.mood_buttons.append((mood_id, mood_btn))
            self.show_previous_mood()

        # 🔥 CHỈ CÓ NÚT CLOSE Ở DƯỚI
        self.btn_frame = tk.Frame(self.bg_canvas, bg=self.main_bg)
        self.btn_frame_window = self.bg_canvas.create_window(150, 185, window=self.btn_frame)

        # Nút Close
        tk.Button(self.btn_frame, text="Close", font=("Arial", 10, "bold"),
                  command=self.close_mood, bg="#E9B6B6", fg="white",
                  width=8, height=1, bd=0).pack()

    def select_and_save_mood(self, mood_id):
        """Chọn mood"""
        self.selected_mood = mood_id
        print(f"✅ Đã chọn mood: {mood_id}")
        self.show_previous_mood()

        # Highlight mood được chọn
        for mid, btn in self.mood_buttons:
            if mid == mood_id:
                btn.config(relief="solid", bd=0, bg="#C7C3AA")  # Highlight
            else:
                btn.config(relief="flat", bd=0, bg=self.main_bg)  # Bỏ highlight

    def save_mood(self):
        """Lưu mood vào database"""
        if self.selected_mood == 0:
            return

        try:
            success = self.mood_manager.save_mood(
                track_id=self.song['trackId'],
                user_mood=self.selected_mood,
                user_id=self.user_id
            )

            if success:
                print(f"✅ Đã lưu mood {self.selected_mood} cho: {self.song['trackName']}")
            else:
                print("❌ Lỗi khi lưu mood")

        except Exception as e:
            print(f"❌ Lỗi save_mood: {e}")

    def show_previous_mood(self):
        """Cập nhật hiển thị các nút mood (highlight cái đã chọn)"""
        for mood_id, btn in self.mood_buttons:
            if mood_id == self.selected_mood:
                btn.config(relief="solid", bd=0, bg="#C7C3AA")  # 🔥 HIGHLIGHT - 1 màu
            else:
                btn.config(relief="flat", bd=0, bg=self.main_bg)  # 🔥 BÌNH THƯỜNG - 1 màu

    def close_mood(self):
        """Đóng mood frame và mood area"""
        # 🔥 DESTROY MOOD FRAME TRƯỚC
        self.destroy()

        # 🔥 DESTROY MOOD AREA NẾU CÓ
        if hasattr(self, 'master') and self.master:
            self.master.destroy()

        print("✅ Đã đóng mood selection và mood area")
        self.save_mood()
# if __name__ == "__main__":
#     root = Tk()
#     app = MoodPlayerUI(root)
#     root.mainloop()
