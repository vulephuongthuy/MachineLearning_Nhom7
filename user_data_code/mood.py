import json, random
from datetime import datetime, timedelta
from collections import Counter

# === Đọc danh sách user ===
with open("user.json", "r", encoding="utf-8") as f:
    users = json.load(f)

MOODS = [
    {"id": 1, "name": "Happy"},
    {"id": 2, "name": "Sad"},
    {"id": 3, "name": "Neutral"},
    {"id": 4, "name": "Intense"},
]

START = datetime(2023, 1, 1)
END = datetime(2025, 11, 30)

activity_cfg = {
    "top": {"prob": 0.9, "entries": (3, 5)},
    "medium": {"prob": 0.6, "entries": (1, 3)},
    "low": {"prob": 0.3, "entries": (0, 2)},
}

history, monthly = [], []
hid = 1  # Tăng dần ID

for user in users:
    uid = f"user_{user['userId']}"
    utype = user.get("user_type", "medium")
    cfg = activity_cfg[utype]
    current = START
    user_month_data = {}

    while current <= END:
        if random.random() < cfg["prob"]:
            for _ in range(random.randint(*cfg["entries"])):
                mood = random.choices(
                    MOODS,
                    weights=[0.45, 0.2, 0.25, 0.1] if utype == "top" else
                            [0.3, 0.3, 0.3, 0.1] if utype == "medium" else
                            [0.2, 0.4, 0.3, 0.1],
                    k=1
                )[0]

                history.append({
                    "historyID": hid,
                    "user_id": uid,
                    "moodID": mood["id"],
                    "moodName": mood["name"],
                    "timestamp": current.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
                hid += 1

                # Gom theo tháng
                month = current.strftime("%Y-%m")
                user_month_data.setdefault(month, []).append(mood["name"])
        current += timedelta(days=1)

    # Tính tóm tắt tháng
    for month, moods in user_month_data.items():
        total = len(moods)
        counts = Counter(moods)
        breakdown = {m: round(v / total, 2) for m, v in counts.items()}
        dominant = max(counts, key=counts.get)
        monthly.append({
            "user_id": uid,
            "month": month,
            "total_entries": total,
            "dominant_mood": dominant,
            "mood_breakdown": breakdown
        })

# === Ghi file JSON ===
with open("mood_tracking_history.json", "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

with open("mood_monthly_summary.json", "w", encoding="utf-8") as f:
    json.dump(monthly, f, ensure_ascii=False, indent=2)

print(" Generated mood_tracking_history.json & mood_monthly_summary.json")
