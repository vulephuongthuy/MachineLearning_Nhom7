import json
import random
import numpy as np
import datetime
import os

# ===== HÀM HỖ TRỢ =====
def random_datetime_between(start_dt, end_dt):
    """
    Sinh ngẫu nhiên thời gian trong khoảng start_dt → end_dt (UTC).
    """
    if start_dt > end_dt:
        return end_dt
    delta = end_dt - start_dt
    offset = random.randint(0, int(delta.total_seconds()))
    return start_dt + datetime.timedelta(seconds=offset)

# ===== HÀM CHÍNH =====
def simulate_purchases_from_popularity(
    tracks_path,
    users_path,
    output_path="data/purchased.json",
    seed=42
):
    """
    Sinh dữ liệu mua bài hát dựa theo phân vị popularity và weighted user_type.
    user_type: "top" → mua nhiều, "medium" → mua vừa, "low" → mua ít.
    Tất cả lượt mua chỉ từ 2023 trở đi nhưng không thay đổi release date.
    """
    random.seed(seed)
    np.random.seed(seed)

    # ===== Đọc dữ liệu =====
    with open(tracks_path, "r", encoding="utf-8") as f:
        tracks = json.load(f)
    with open(users_path, "r", encoding="utf-8") as f:
        users = json.load(f)

    # ===== Chuẩn bị weighted user list =====
    weighted_user_ids = []
    for u in users:
        if u.get("user_type") == "top":
            weighted_user_ids.extend([u["userId"]]*20)
        elif u.get("user_type") == "medium":
            weighted_user_ids.extend([u["userId"]]*5)
        else:  # low
            weighted_user_ids.extend([u["userId"]]*1)

    # ===== Tính phân vị popularity =====
    pops = sorted([t.get("popularity", 0) for t in tracks])
    q95 = np.percentile(pops, 95)   # top 5% → hit
    q25 = np.percentile(pops, 25)   # dưới 25% → rare
    print(f"Phân vị popularity → 95%: {q95:.2f}, 25%: {q25:.2f}")

    purchases = []
    purchase_id = 1
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # ===== Sinh dữ liệu mua =====
    for t in tracks:
        pop = t.get("popularity", 0)

        # Phân loại theo phân vị
        if pop >= q95:
            category = "hit"
            num_buyers = random.randint(50, 200)
        elif pop < q25:
            category = "rare"
            num_buyers = random.randint(0, 5)
        else:
            category = "normal"
            num_buyers = random.randint(5, 40)

        if num_buyers <= 0:
            continue

        # Chuyển release_str sang datetime
        release_str = t.get("releaseDate")
        try:
            release_dt = datetime.datetime.fromisoformat(release_str.replace("Z", "+00:00"))
        except Exception:
            release_dt = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)

        # ===== Chọn buyers weighted theo user_type =====
        buyers = set()
        while len(buyers) < num_buyers:
            uid = random.choice(weighted_user_ids)
            buyers.add(uid)
        buyers = list(buyers)

        # ===== Sinh purchased_at từ 2023 trở đi nhưng không thay đổi release date =====
        for uid in buyers:
            start_dt = max(release_dt, datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc))
            purchased_at = random_datetime_between(start_dt, now_utc)
            purchases.append({
                "purchase_id": purchase_id,
                "user_id": uid,
                "track_id": t["trackId"],
                "trackName": t["trackName"],
                "artistName": t["artistName"],
                "artworkUrl100": t.get("artworkUrl100"),
                "category": category,
                "purchased_at": purchased_at.isoformat().replace("+00:00", "Z")
            })
            purchase_id += 1

    # =====  Ghi file JSON =====
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(purchases, f, ensure_ascii=False, indent=2)

    # =====  Báo cáo nhanh =====
    cat_counts = {}
    for p in purchases:
        cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1
    total = sum(cat_counts.values())
    for k, v in cat_counts.items():
        print(f"  {k:7s}: {v:5d} ({v/total*100:4.1f}%)")

# ===== CHẠY THỬ =====
if __name__ == "__main__":
    simulate_purchases_from_popularity(
        tracks_path="data/tracks.json",
        users_path="data/users_for_ml.json",
        output_path="data/purchased.json"
    )
