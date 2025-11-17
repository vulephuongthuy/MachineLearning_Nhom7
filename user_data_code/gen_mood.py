import json
import random
from collections import Counter
from pathlib import Path

# === Load JSON an toàn ===
def load_json(file):
    if not Path(file).exists():
        print(f" File {file} không tồn tại.")
        return []
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

# ===  Đọc file user.json ===
users = load_json("user.json")
# Dùng get để tránh lỗi nếu thiếu user_type, mặc định "medium"
user_types = {u["userId"]: u.get("user_type", "medium") for u in users}
print(f"🧍 Tổng số user thật: {len(users)}")

# ===  Đọc file history cho 2 tháng ===
months = ["2025-09", "2025-10"]
all_summaries = []

# Tỷ lệ mood giả lập theo từng nhóm user
MOOD_PROFILES = {
    "top": {"Happy": 0.5, "Neutral": 0.25, "Intense": 0.15, "Sad": 0.1},
    "medium": {"Happy": 0.4, "Neutral": 0.3, "Sad": 0.2, "Intense": 0.1},
    "low": {"Neutral": 0.5, "Sad": 0.3, "Happy": 0.15, "Intense": 0.05}
}

for month in months:
    history_file = f"history_{month}.json"
    history = load_json(history_file)
    if not history:
        continue

    print(f" Xử lý {history_file} ({len(history)} dòng)...")

    # Đếm lượt nghe thật theo user
    play_counts = Counter(str(h["user_id"]) for h in history if h.get("user_id"))
    print(f" Có {len(play_counts)} user có hoạt động trong tháng {month}")

    summaries = []
    for uid, plays in play_counts.items():
        if uid not in user_types:
            continue  # chỉ giữ user thật

        user_type = user_types[uid]
        mood_profile = MOOD_PROFILES.get(user_type, MOOD_PROFILES["medium"])

        # Giả lập tổng số log (bám theo lượt nghe thật)
        total_entries = max(5, int(plays * random.uniform(0.05, 0.15)))  # 5–15% số lần nghe

        # Giả lập phân bố mood dựa trên profile + noise ngẫu nhiên
        noise = {m: v + random.uniform(-0.05, 0.05) for m, v in mood_profile.items()}
        total = sum(max(v, 0) for v in noise.values())
        mood_breakdown = {m: round(max(v, 0) / total, 2) for m, v in noise.items()}

        dominant_mood = max(mood_breakdown, key=mood_breakdown.get)

        summaries.append({
            "user_id": uid,
            "month": month,
            "total_entries": total_entries,
            "dominant_mood": dominant_mood,
            "mood_breakdown": mood_breakdown
        })

    # Lưu file riêng từng tháng
    out_file = f"mood_monthly_summary_{month}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    print(f"Đã tạo {out_file} ({len(summaries)} user)")

    all_summaries.extend(summaries)

# ===  Gộp file tổng hợp ===
with open("mood_monthly_summary.json", "w", encoding="utf-8") as f:
    json.dump(all_summaries, f, indent=2, ensure_ascii=False)

print(f"\n🎉 Đã tạo file mood_monthly_summary.json ({len(all_summaries)} records)")
