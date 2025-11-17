
from datetime import datetime
from Connection.connector import Connector
from session import current_user


class MoodManager:
    def __init__(self):
        self.db=Connector()

    def save_mood(self, track_id, user_mood, user_id=None, genre=None):
        """Lưu mood vào database theo user đang đăng nhập"""
        try:
            # SỬ DỤNG USER_ID ĐƯỢC TRUYỀN VÀO
            if not user_id:
                print("Không có user_id được cung cấp")
                return False

            if not genre:
                genre = self.get_song_genre(track_id)
                if not genre:
                    genre = "Unknown"

            print(f"[MOOD] Saving mood for user_id: {user_id}")

            mood_data = {
                "trackId": track_id,
                "userId": str(user_id),
                "genre": genre,
                "userMood": user_mood,
                "timestamp": datetime.now().isoformat()
            }

            result = self.db.db["song_moods"].update_one(
                {"trackId": track_id, "userId": str(user_id)},
                {"$set": mood_data},
                upsert=True
            )
            print(f"Đã lưu mood cho user {user_id}, bài hát {track_id}")
            return True

        except Exception as e:
            print(f"Lỗi lưu mood: {e}")
            return False

    def get_mood(self, track_id, user_id=None):
        """Lấy mood từ database theo user_id được truyền vào hoặc current_user"""
        try:
            #  ƯU TIÊN user_id ĐƯỢC TRUYỀN VÀO
            if not user_id:
                from session import current_user
                if current_user:
                    user_id = current_user.get("userId")
                    print(f"[MOOD] get_mood using current_user: {user_id}")
                else:
                    print("Chưa có user đăng nhập")
                    return 0

            if not user_id:
                return 0

            print(f"[MOOD] Searching mood for user_id: {user_id}, track_id: {track_id}")

            mood_data = self.db.db["song_moods"].find_one({
                "trackId": track_id,
                "userId": str(user_id)
            })

            found_mood = mood_data.get("userMood", 0) if mood_data else 0
            print(f"[MOOD] Found mood: {found_mood}")
            return found_mood

        except Exception as e:
            print(f"Lỗi lấy mood: {e}")
            return 0

    def get_song_genre(self, track_id):
        """Lấy genre từ collection tracks"""
        try:
            # Tìm bài hát trong collection tracks
            song_data = self.db.db["tracks"].find_one({"trackId": track_id})
            if song_data and "genre" in song_data:
                return song_data["genre"]

            # Hoặc từ primaryGenreName nếu có
            if song_data and "primaryGenreName" in song_data:
                return song_data["primaryGenreName"]

            return "Unknown"
        except Exception as e:
            print(f"Lỗi lấy genre: {e}")
            return "Unknown"


