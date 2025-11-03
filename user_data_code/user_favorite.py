import pandas as pd
import random
from datetime import timedelta
import numpy as np


# ------------------------------------------------------------
# 🧩 Sinh giả lập bảng user_favorite (phẳng như user_history_flat)
# ------------------------------------------------------------
def generate_user_favorite(user_purchased_df, user_history_flat_df, tracks_df):
    """
    Sinh dữ liệu user_favorite từ purchased + history với ràng buộc:
    - Mỗi user có ít nhất 5 bài yêu thích, tối đa 40% số bài đã nghe.
    - Xác suất chọn bài dựa vào PlayCount (PlayCount cao → khả năng được chọn cao hơn).
    - added_at sinh ngẫu nhiên trong khoảng [purchased_at, LastPlayedAt].
    """

    # 🔹 Chuẩn hóa tên cột cho đồng nhất
    user_purchased_df = user_purchased_df.rename(columns={
        "user_id": "userId",
        "track_id": "trackId"
    })

    user_history_flat_df = user_history_flat_df.rename(columns={
        "UserId": "userId",
        "TrackId": "trackId",
        "TrackName": "trackName",
        "ArtistName": "artistName",
        "Artwork": "artworkUrl100"
    })

    tracks_df = tracks_df.rename(columns={
        "trackId": "trackId",
        "primaryGenreName": "primaryGenreName"
    })

    favorites = []

    # 🔹 Duyệt từng user
    for user_id, purchased_tracks in user_purchased_df.groupby("userId"):
        history = user_history_flat_df[user_history_flat_df["userId"] == user_id]

        merged = pd.merge(
            purchased_tracks,
            history,
            on=["userId", "trackId"],
            how="inner",
            suffixes=("_purchased", "_history")
        )

        if merged.empty:
            continue

        total_tracks = len(merged)
        if total_tracks == 0:
            continue

        # 🔹 Tính xác suất chọn bài theo PlayCount
        play_counts = merged["PlayCount"].astype(float)
        probs = play_counts / play_counts.sum()

        # 🔹 Tính số lượng bài yêu thích cho user này
        min_fav = 5
        max_fav = max(min_fav, int(total_tracks * 0.35))  # tối đa 35% số bài
        # từng nghe
        num_fav = random.randint(min_fav, max_fav)

        num_fav = min(num_fav, total_tracks)  # không vượt quá tổng bài user từng nghe

        # 🔹 Chọn ngẫu nhiên bài có trọng số xác suất theo PlayCount
        selected_indices = np.random.choice(
            merged.index,
            size=num_fav,
            replace=False,
            p=probs
        )

        for _, row in merged.loc[selected_indices].iterrows():
            purchased_at = pd.to_datetime(row["purchased_at"], utc=True)
            last_played = pd.to_datetime(row["LastPlayedAt"], utc=True)

            # Đảm bảo thứ tự thời gian hợp lệ
            if purchased_at > last_played:
                purchased_at, last_played = last_played, purchased_at

            delta = (last_played - purchased_at).total_seconds()
            random_offset = random.uniform(0, delta)
            added_at = purchased_at + timedelta(seconds=random_offset)

            # 🔹 Lấy dữ liệu hiển thị ưu tiên từ history
            track_name = row.get("trackName_history") or row.get("trackName_purchased")
            artist_name = row.get("artistName_history") or row.get("artistName_purchased")
            artwork = row.get("artworkUrl100_history") or row.get("artworkUrl100_purchased")

            # 🔹 Lấy genre từ bảng tracks
            genre = tracks_df.loc[tracks_df["trackId"] == row["trackId"], "primaryGenreName"]
            genre = genre.iloc[0] if not genre.empty else None

            favorites.append({
                "userId": row["userId"],
                "trackId": row["trackId"],
                "trackName": track_name,
                "artistName": artist_name,
                "primaryGenreName": genre,
                "artworkUrl100": artwork,
                "added_at": added_at.isoformat().replace("+00:00", "Z")
            })

    return pd.DataFrame(favorites)


# ---------------- Example ----------------
if __name__ == "__main__":
    purchased_df = pd.read_json("../data/purchased.json")
    history_df = pd.read_json("../data/user_history_flat.json")
    tracks_df = pd.read_json("../data/tracks.json")

    user_favorite_df = generate_user_favorite(purchased_df, history_df, tracks_df)

    user_favorite_df.to_json(
        "../data/user_favorite.json",
        orient="records",
        indent=2,
        force_ascii=False
    )

    print(f"✅ Đã tạo xong file user_favorite.json với {len(user_favorite_df)} bản ghi.")
