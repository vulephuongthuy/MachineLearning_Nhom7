from datetime import datetime
from Connection.connector import Connector
from session import current_user


class RatingManager:
    def __init__(self):
        self.db = Connector()

    def save_rating(self, track_id, rating, user_id=None):
        """Lưu rating vào MongoDB collection user_rating"""
        try:
            # 🔥 LẤY USER_ID TỪ CURRENT_USER NẾU KHÔNG CÓ
            if not user_id:
                if current_user:
                    user_id = current_user.get("userId")
                else:
                    print("❌ Chưa có user đăng nhập")
                    return False

            if not user_id:
                print("❌ Không có user_id")
                return False

            print(f"[RATING] 💾 Saving rating for user_id: {user_id}")

            rating_data = {
                "userId": str(user_id),
                "trackId": track_id,
                "rating": rating,
                "ratedAt": datetime.now().isoformat()
            }

            # 🔥 DÙNG COLLECTION "user_rating"
            collection = self.db.db["user_rating"]
            result = collection.update_one(
                {"trackId": track_id, "userId": str(user_id)},
                {"$set": rating_data},
                upsert=True
            )

            print(f"✅ Đã lưu rating {rating}⭐ cho user {user_id}, bài hát {track_id}")
            return True

        except Exception as e:
            print(f"❌ Lỗi lưu rating: {e}")
            return False

    def get_rating(self, track_id, user_id=None):
        """Lấy rating từ MongoDB collection user_rating"""
        try:
            # 🔥 LẤY USER_ID TỪ CURRENT_USER NẾU KHÔNG CÓ
            if not user_id:
                if current_user:
                    user_id = current_user.get("userId")
                else:
                    return 0

            if not user_id:
                return 0

            # 🔥 DÙNG COLLECTION "user_rating"
            rating_data = self.db.db["user_rating"].find_one({
                "trackId": track_id,
                "userId": str(user_id)
            })

            return rating_data.get("rating", 0) if rating_data else 0

        except Exception as e:
            print(f"❌ Lỗi lấy rating: {e}")
            return 0