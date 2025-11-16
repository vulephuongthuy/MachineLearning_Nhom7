
from pymongo import MongoClient
from collections import Counter
from datetime import datetime, timedelta
import random

# ===== ✨ Quotes theo mood =====
MOOD_QUOTES = {
    "Happy": [
        "You found joy in little things — keep shining.",
        "Happiness suits you perfectly.",
        "Your smile lit up the month.",
        "Every tune you played was full of sunshine.",
        "Joy blooms where your heart goes."
    ],
    "Sad": [
        "Even the rain helps flowers bloom.",
        "It’s okay to slow down — healing takes time.",
        "Tears water the seeds of strength.",
        "You faced your storms — and you’re still standing.",
        "Sometimes, sadness makes the music softer — but more real."
    ],
    "Neutral": [
        "Balance is beautiful — you stayed calm amid chaos.",
        "You’ve mastered the art of peace.",
        "Serenity became your soundtrack this month.",
        "Neither high nor low — just steady and strong.",
        "Sometimes stillness is the most powerful vibe."
    ],
    "Intense": [
        "Your fire burned bright this month.",
        "You chased your passions with unstoppable energy.",
        "Every beat echoed your boldness.",
        "You lived loud, felt deeply, and burned brightly.",
        "Intensity makes your story unforgettable."
    ]
}

# ===== ⚙️ Kết nối MongoDB =====
client = MongoClient("mongodb://localhost:27017/")
db = client["moo_d"]

def generate_user_wrapup(userId: str):
    """Sinh hoặc tải wrap-up của user cho tháng hiện tại - 1."""
    # === Xác định tháng wrap-up ===
    now = datetime.now()
    last_month_date = now.replace(day=1) - timedelta(days=1)
    last_month = last_month_date.strftime("%Y-%m")
    history_collection = f"history_{last_month}"

    # === Kiểm tra xem wrap-up đã có trong DB chưa ===
    existing_wrapup = db["user_wrapup"].find_one({"userId": userId, "month": last_month})
    if existing_wrapup:
        print(f"🟢 Wrap-up for user {userId} month {last_month} already exists.")
        return existing_wrapup

    # === Nếu chưa có, tạo wrap-up mới ===
    if history_collection not in db.list_collection_names():
        print(f"⚠️ No listening history found for month {last_month}.")
        return None

    records = list(db[history_collection].find({"userId": userId}))
    if not records:
        print(f"⚠️ User {userId} has no listening data in {last_month}.")
        return None

    print(f"🎧 Generating wrap-up for user {userId} in {last_month}...")

    # === Tính top nghệ sĩ & bài hát ===
    artist_counts = Counter(r["artistName"] for r in records)
    song_counts = Counter(r["trackName"] for r in records)

    top_artists = [
        {"ArtistName": name, "PlayCount": count}
        for name, count in artist_counts.most_common(5)
    ]

    fav_songs = []
    for name, count in song_counts.most_common(5):
        # Lấy tất cả record có cùng trackName
        same_tracks = [r for r in records if r["trackName"] == name]

        # Ưu tiên track có artworkUrl100 (ảnh bài hát)
        track = next((r for r in same_tracks if r.get("artworkUrl100")), same_tracks[0])
        artwork = track.get("artworkUrl100", "https://example.com/default_art.png")

        fav_songs.append({
            "TrackName": name,
            "ArtistName": track.get("artistName"),
            "Artwork": artwork,
            "PlayCount": count
        })

    # === Lấy dữ liệu mood ===
    mood_record = db["mood_monthly_summary"].find_one({"userId": userId, "month": last_month})
    if mood_record:
        dominant_mood = mood_record["dominant_mood"]
        mood_count = {
            mood: round(ratio * mood_record.get("total_entries", 30))
            for mood, ratio in mood_record["mood_breakdown"].items()
        }
        quote = random.choice(MOOD_QUOTES.get(dominant_mood, ["Keep going — you’re doing great."]))
    else:
        dominant_mood, mood_count, quote = None, {}, None

    # === Tạo document wrap-up ===
    wrapup_doc = {
        "userId": userId,
        "month": last_month,
        "generated_at": datetime.now(),
        "mood_count": mood_count,
        "dominant_mood": dominant_mood,
        "dominant_mood_quote": quote,
        "top_artists": top_artists,
        "favourite_songs": fav_songs
    }

    # === Lưu vào MongoDB ===
    db["user_wrapup"].insert_one(wrapup_doc)
    print(f"✅ New wrap-up generated & saved for user {userId} ({last_month}).")

    return wrapup_doc

# # Chạy thử (khi chạy riêng file)
# if __name__ == "__main__":
#     current_user_id = "112345"  # user hiện đang đăng nhập (hoặc lấy từ session)
#     wrapup = generate_user_wrapup(current_user_id)

# from generate_wrapup_from_mongo import generate_user_wrapup
#
# wrapup_data = generate_user_wrapup(session.current_user["_id"])
#
# if wrapup_data:
#     show_wrapup_UI(wrapup_data)  # hiển thị trực tiếp trên UI
# else:
#     messagebox.showinfo("Wrap-up", "Không có dữ liệu nghe nhạc cho tháng vừa rồi")