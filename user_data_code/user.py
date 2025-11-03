import json
import random
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# ======== CẤU HÌNH ========
START_DATE = datetime(2023, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 11, 30, 23, 59, 59, tzinfo=timezone.utc)
CURRENT_DATE = datetime.now(timezone.utc)  # Thời điểm người dùng mở app
CURRENT_MONTH = CURRENT_DATE.strftime("%Y-%m")  # Ví dụ: "2025-10"

# ======== HÀM HỖ TRỢ ========
def random_datetime_between(start_dt, end_dt):
    delta = end_dt - start_dt
    offset = random.randint(0, int(delta.total_seconds()))
    return start_dt + timedelta(seconds=offset)

def ensure_json_file(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    else:
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======== SINH FILE HISTORY THEO THÁNG ========
def generate_monthly_history(purchases_path="data/purchased.json", output_dir="data/history_log"):
    with open(purchases_path, "r", encoding="utf-8") as f:
        purchases = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    monthly_data = defaultdict(list)

    for p in purchases:
        user_id = p["user_id"]
        track_id = p["track_id"]
        track_name = p["trackName"]
        artist_name = p["artistName"]
        artwork = p["artworkUrl100"]
        category = p.get("category", "normal")
        purchase_date = datetime.fromisoformat(p["purchased_at"].replace("Z", "+00:00"))

        # Thời điểm bắt đầu nghe không trước ngày mua và START_DATE
        start_dt = max(purchase_date, START_DATE)

        # Giới hạn số lần nghe tùy loại bài
        if category == "hit":
            listens = random.randint(10, 25)
        elif category == "normal":
            listens = random.randint(4, 10)
        else:
            listens = random.randint(1, 5)

        for _ in range(listens):
            played_at = random_datetime_between(start_dt, END_DATE)
            source = "train" if played_at <= CURRENT_DATE else "future"
            month_str = played_at.strftime("%Y-%m")
            file_key = f"{month_str}"

            monthly_data[file_key].append({
                "user_id": user_id,
                "track_id": track_id,
                "trackName": track_name,
                "artistName": artist_name,
                "artwork_track": artwork,
                "category": category,
                "played_at": played_at.isoformat().replace("+00:00", "Z"),
                "source": source
            })

    # Ghi ra từng file log theo tháng
    total_records = 0
    for month, records in monthly_data.items():
        file_path = os.path.join(output_dir, f"history_{month}.json")
        records.sort(key=lambda x: x["played_at"])
        save_json(file_path, records)
        total_records += len(records)
        print(f"✅ Ghi log tháng {month}: {len(records)} bản ghi → {file_path}")

    print(f"\n🎯 Tổng số bản ghi sinh ra: {total_records}")
    return monthly_data


# ======== SINH FILE USER HISTORY ========
def generate_user_history(log_dir="data/history_log", output_path="data/user_history.json"):
    user_history = defaultdict(lambda: defaultdict(lambda: {
        "TrackName": "",
        "ArtistName": "",
        "Artwork": "",
        "PlayCount": 0,
        "LastPlayedAt": None
    }))

    # Đọc tất cả file log tháng trong thư mục
    for file in os.listdir(log_dir):
        if file.startswith("history_") and file.endswith(".json"):
            path = os.path.join(log_dir, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    month_data = json.load(f)
            except json.JSONDecodeError:
                continue

            for h in month_data:
                uid = h["user_id"]
                tid = h["track_id"]
                played_at = datetime.fromisoformat(h["played_at"].replace("Z", "+00:00"))
                entry = user_history[uid][tid]

                entry["TrackName"] = h["trackName"]
                entry["ArtistName"] = h["artistName"]
                entry["Artwork"] = h["artwork_track"]
                entry["PlayCount"] += 1
                if not entry["LastPlayedAt"] or played_at > entry["LastPlayedAt"]:
                    entry["LastPlayedAt"] = played_at

    # Chuyển về list để ghi file
    result = []
    for uid, tracks_dict in user_history.items():
        tracks = []
        for tid, info in tracks_dict.items():
            tracks.append({
                "TrackId": tid,
                "TrackName": info["TrackName"],
                "ArtistName": info["ArtistName"],
                "Artwork": info["Artwork"],
                "PlayCount": info["PlayCount"],
                "LastPlayedAt": info["LastPlayedAt"].isoformat().replace("+00:00", "")
            })
        result.append({"UserId": uid, "Tracks": tracks})

    save_json(output_path, result)
    print(f"✅ Đã sinh dữ liệu user_history → {output_path}")
    return result


# ======== CẬP NHẬT LOG THÁNG HIỆN TẠI KHI CÓ DỮ LIỆU MỚI ========
def append_new_play(user_id, track_info, played_at=None, log_dir="data/history_log", user_history_path="data/user_history.json"):
    """
    Thêm lượt nghe mới vào log tháng hiện tại và cập nhật user_history.
    Nếu file history.json không còn thì vẫn hoạt động bình thường.
    """
    played_at = played_at or datetime.now(timezone.utc)
    month_str = played_at.strftime("%Y-%m")
    log_path = os.path.join(log_dir, f"history_{month_str}.json")

    # ---- Ghi log tháng ----
    log_data = ensure_json_file(log_path, [])
    new_entry = {
        "user_id": user_id,
        "track_id": track_info["track_id"],
        "trackName": track_info["trackName"],
        "artistName": track_info["artistName"],
        "artwork_track": track_info["artwork_track"],
        "category": track_info.get("category", "normal"),
        "played_at": played_at.isoformat().replace("+00:00", "Z"),
        "source": "train"
    }
    log_data.append(new_entry)
    save_json(log_path, log_data)
    print(f"🎵 Đã thêm lượt nghe vào log tháng {month_str}")

    # ---- Cập nhật user_history ----
    data = ensure_json_file(user_history_path, [])
    user_map = {u["UserId"]: u for u in data}

    if user_id not in user_map:
        user_map[user_id] = {"UserId": user_id, "Tracks": []}

    tracks = {t["TrackId"]: t for t in user_map[user_id]["Tracks"]}
    tid = track_info["track_id"]

    if tid not in tracks:
        tracks[tid] = {
            "TrackId": tid,
            "TrackName": track_info["trackName"],
            "ArtistName": track_info["artistName"],
            "Artwork": track_info["artwork_track"],
            "PlayCount": 1,
            "LastPlayedAt": played_at.isoformat().replace("+00:00", "")
        }
    else:
        tracks[tid]["PlayCount"] += 1
        tracks[tid]["LastPlayedAt"] = played_at.isoformat().replace("+00:00", "")

    user_map[user_id]["Tracks"] = list(tracks.values())
    save_json(user_history_path, list(user_map.values()))
    print(f"🔄 Đã cập nhật user_history cho user {user_id}")


# ======== CHẠY ========
if __name__ == "__main__":
    # 1️⃣ Sinh dữ liệu log tháng từ purchased.json
    generate_monthly_history(
        purchases_path="data/purchased.json",
        output_dir="data/history_log"
    )

    # 2️⃣ Sinh file user_history từ các log tháng
    generate_user_history(
        log_dir="data/history_log",
        output_path="data/user_history.json"
    )

