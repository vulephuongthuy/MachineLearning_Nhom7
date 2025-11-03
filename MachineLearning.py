# 🎵 Hybrid Music Recommender - User Mới với Top Genre/Artist toàn hệ thống
# =========================================

# 1️⃣ Import thư viện
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor
import numpy as np

data_dir = '/content/moo_d/data'

# 2️⃣ Đọc dữ liệu JSON
tracks = pd.read_json(os.path.join(data_dir, 'tracks.json'))
users = pd.read_json(os.path.join(data_dir, 'user.json'))
favorites = pd.read_json(os.path.join(data_dir, 'user_favorite.json'))
ratings = pd.read_json(os.path.join(data_dir, 'user_rating.json'))
purchased = pd.read_json(os.path.join(data_dir, 'purchase.json'))
mood_hist = pd.read_json(os.path.join(data_dir, 'mood_tracking_history.json'))
song_mood = pd.read_json(os.path.join(data_dir, 'song_mood_community.json'))

# 3️⃣ Tiền xử lý dữ liệu
favorites_with_artist = favorites.merge(
    tracks[['trackId', 'artistId']],  # CHỈ LẤY artistId và artistName
    on='trackId',
    how='left'
)

rating_avg = ratings.groupby("trackId")["rating"].mean().reset_index()
rating_avg["rating_score"] = rating_avg["rating"] / 5

# Tạo df chính từ favorites_with_artist (đã có primaryGenreName)
df = favorites_with_artist.merge(song_mood[["trackId", "mood_community"]],
                                 on="trackId", how="left")
df = df.merge(rating_avg[["trackId", "rating_score"]], on="trackId", how="left")

tracks["releaseDate"] = pd.to_datetime(tracks["releaseDate"],
                                       errors="coerce").dt.tz_localize(None)
tracks["recency"] = (pd.Timestamp.now() - tracks["releaseDate"]).dt.days
df = df.merge(tracks[["trackId", "recency"]], on="trackId", how="left")
df["recency_score"] = 1 / (1 + df["recency"].fillna(df["recency"].max()))

# 4️⃣ Mood hiện tại
current_mood = (
    mood_hist.sort_values("timestamp", ascending=False)
    .groupby("userId")
    .first()
    .reset_index()[["userId", "moodID"]]
)
df = df.merge(current_mood, on="userId", how="left")

# 5️⃣ Tính CF score
cf_counts = favorites_with_artist.groupby("trackId")[
    "userId"].count().reset_index()
cf_counts.columns = ["trackId", "cf_score"]
cf_counts["cf_score"] = cf_counts["cf_score"] / cf_counts["cf_score"].max()
df = df.merge(cf_counts, on="trackId", how="left")

# 6️⃣ Tạo artist/genre match feature - CHUYỂN SANG ARTISTID
print("🔄 Pre-computing artist and genre similarity với artistId...")

user_artist_counts = favorites_with_artist.groupby(
    ['userId', 'artistId']).size().reset_index(name='artist_count')

user_genre_counts = favorites_with_artist.groupby(
    ['userId', 'primaryGenreName']).size().reset_index(name='genre_count')
user_total_favs = favorites_with_artist.groupby('userId').size().reset_index(
    name='total_favs')

# Merge pre-computed counts vào df
df = df.merge(user_artist_counts, on=['userId', 'artistId'], how='left')
df = df.merge(user_genre_counts, on=['userId', 'primaryGenreName'], how='left')
df = df.merge(user_total_favs, on='userId', how='left')

# 🎯 TÍNH similarity bằng vectorization (NHANH)
df['artist_count'] = df['artist_count'].fillna(0)
df['genre_count'] = df['genre_count'].fillna(0)
df['total_favs'] = df['total_favs'].fillna(1)  # Tránh chia 0

df["artist_similarity"] = (0.7 * (df['artist_count'] > 0).astype(float) +
                           0.3 * (df['artist_count'] / df['total_favs']))
df["genre_similarity"] = (0.7 * (df['genre_count'] > 0).astype(float) +
                          0.3 * (df['genre_count'] / df['total_favs']))

# Xóa temp columns
df = df.drop(['artist_count', 'genre_count', 'total_favs'], axis=1)


def calc_mood_similarity(row):
    """Tính độ tương đồng mood - Binary match hoàn toàn"""
    return 1.0 if row["moodID"] == row["mood_community"] else 0.0


# Áp dụng mood similarity (vẫn cần vì phụ thuộc mood hiện tại)
df["mood_similarity"] = df.apply(calc_mood_similarity, axis=1)

df = df.fillna({
    "rating_score": 0,
    "recency_score": 0.5,
    "cf_score": 0,
    "mood_similarity": 0,
    "artist_similarity": 0,
    "genre_similarity": 0
})

# 7️⃣ Xây dựng mô hình LightGBM với features liên tục
feature_cols = ["recency_score", "rating_score", "artist_similarity",
                "genre_similarity"]
target_col = "cf_score"  # implicit feedback

X = df[["userId"] + feature_cols]
y = df[target_col]

# 🎯 THÊM: Chia lại train/test với data mới
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                    random_state=42)

print("🔄 Training model mới với features đã cập nhật...")
model = LGBMRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    num_leaves=31,
    random_state=42
)
model.fit(X_train[feature_cols], y_train)


# =========================================
# 🎯 Đánh giá bằng Ranking Metrics
# =========================================

def ndcg_at_k(y_true, y_score, k=10):
    """Normalized Discounted Cumulative Gain"""
    if len(y_true) < k:
        k = len(y_true)
    order = np.argsort(y_score)[::-1]
    y_true = np.take(y_true, order[:k])
    gains = (2 ** y_true - 1) / np.log2(np.arange(2, k + 2))
    dcg = np.sum(gains)
    ideal_gains = (2 ** np.sort(y_true)[::-1] - 1) / np.log2(
        np.arange(2, k + 2))
    idcg = np.sum(ideal_gains)
    return dcg / idcg if idcg > 0 else 0.0


def average_precision_at_k(y_true, y_score, k=10):
    """Mean Average Precision"""
    if len(y_true) < k:
        k = len(y_true)
    order = np.argsort(y_score)[::-1]
    y_true = np.take(y_true, order[:k])
    hits = np.cumsum(y_true)
    precision = hits / (np.arange(len(y_true)) + 1)
    return np.sum(precision * y_true) / np.sum(y_true) if np.sum(
        y_true) > 0 else 0.0


def hit_rate_at_k(y_true, y_score, k=10):
    """Hit Rate"""
    if len(y_true) < k:
        k = len(y_true)
    order = np.argsort(y_score)[::-1]
    y_true = np.take(y_true, order[:k])
    return 1.0 if np.sum(y_true) > 0 else 0.0


# =========================================
# 🔍 Tính metrics theo user
# =========================================
ndcg_scores, map_scores, hit_scores = [], [], []

# Lấy y_true từ y_test dựa theo index group
for user_id, group in X_test.groupby("userId"):
    if len(group) < 2:
        continue
    # ✅ Lấy y_true khớp index của group
    y_true = y_test.loc[group.index].values
    y_pred = model.predict(group[feature_cols])

    ndcg_scores.append(ndcg_at_k(y_true, y_pred, k=10))
    map_scores.append(average_precision_at_k(y_true, y_pred, k=10))
    hit_scores.append(hit_rate_at_k(y_true, y_pred, k=10))

# =========================================
# 📊 Kết quả tổng hợp
# =========================================
print(f"✅ NDCG@10 = {np.mean(ndcg_scores):.4f}")
print(f"✅ MAP@10 = {np.mean(map_scores):.4f}")
print(f"✅ HitRate@10 = {np.mean(hit_scores):.4f}")


# =========================================
# 🆕 PHẦN MỚI: Xử lý User Mới với Top Genre/Artist toàn hệ thống
# =========================================

def is_new_user(user_id):
    """Kiểm tra user có phải là user mới không"""
    return user_id not in favorites_with_artist['userId'].values


def get_system_top_artists_genres(top_n=20):
    """Lấy top artists và genres phổ biến nhất toàn hệ thống - SỬ DỤNG ARTISTID"""

    # Top artists toàn hệ thống - SỬ DỤNG ARTISTID
    top_artists = favorites_with_artist.groupby(
        ['artistId', 'artistName']).size().reset_index(name='total_favs')
    top_artists = top_artists.nlargest(top_n, 'total_favs')

    top_genres = favorites_with_artist.groupby(
        'primaryGenreName').size().reset_index(name='total_favs')
    top_genres = top_genres.nlargest(top_n, 'total_favs')
    top_genres_set = set(top_genres['primaryGenreName'])
    genre_scores_dict = dict(
        zip(top_genres['primaryGenreName'], top_genres['total_favs']))

    return {
        'top_artists': set(top_artists['artistId']),
        'top_genres': top_genres_set,
        'artist_scores': dict(
            zip(top_artists['artistId'], top_artists['total_favs'])),
        'genre_scores': genre_scores_dict
    }


def calculate_new_user_score(track_row, system_top):
    """Tính điểm cho bài hát với user mới - SỬ DỤNG ARTISTID"""

    score = 0.0
    weights = {
        'recency': 0.40,  # Tăng weight cho recency
        'rating': 0.30,  # Tăng weight cho rating
        'top_artist': 0.15,  # Artist phổ biến
        'top_genre': 0.15  # Genre phổ biến
    }

    # 1. Recency score (bài hát mới)
    if 'recency' in track_row and pd.notnull(track_row['recency']):
        days = track_row['recency']
        if days <= 30:  # ≤ 30 ngày: điểm cao
            recency_score = 1.0
        elif days <= 90:  # ≤ 3 tháng: điểm trung bình
            recency_score = 0.7
        elif days <= 180:  # ≤ 6 tháng: điểm thấp
            recency_score = 0.3
        elif days <= 365:  # ≤ 1 năm: điểm rất thấp
            recency_score = 0.1
        else:  # > 1 năm: gần như 0
            recency_score = 0.01
    else:
        recency_score = 0
    score += weights['recency'] * recency_score

    # 2. Rating score (bài hát được đánh giá cao)
    rating_score = track_row[
                       'avg_rating'] / 5.0 if 'avg_rating' in track_row and pd.notnull(
        track_row['avg_rating']) else 0
    score += weights['rating'] * rating_score

    # 3. Top artist score - ĐƠN GIẢN HÓA
    artist_score = 0.0
    if 'artistId' in track_row and pd.notnull(track_row['artistId']):
        artist_popularity = system_top['artist_scores'].get(
            track_row['artistId'], 0)
        max_artist_pop = max(system_top['artist_scores'].values()) if \
        system_top['artist_scores'] else 1
        artist_score = artist_popularity / max_artist_pop if max_artist_pop > 0 else 0

    score += weights['top_artist'] * artist_score

    # 4. Top genre score - ĐƠN GIẢN HÓA
    genre_score = 0.0
    if 'primaryGenreName' in track_row and pd.notnull(
            track_row['primaryGenreName']):
        genre_popularity = system_top['genre_scores'].get(
            track_row['primaryGenreName'], 0)
        max_genre_pop = max(system_top['genre_scores'].values()) if system_top[
            'genre_scores'] else 1
        genre_score = genre_popularity / max_genre_pop if max_genre_pop > 0 else 0

    score += weights['top_genre'] * genre_score

    return score


def recommend_for_new_user(user_id, top_n=10, diversity_weight=0.15):
    system_top = get_system_top_artists_genres()
    # Lấy mood hiện tại của user
    user_mood_data = current_mood[current_mood["userId"] == user_id][
        "moodID"].values
    if len(user_mood_data) == 0:
        mood_id = 1  # Mood mặc định
    else:
        mood_id = user_mood_data["moodID"].values[0]

    # Tạo candidate pool từ tất cả bài hát - KIỂM TRA CÁC CỘT TỒN TẠI
    available_columns = ['trackId', 'trackName', 'artistId', 'recency'] + [c for
                                                                           c in
                                                                           [
                                                                               'artistName',
                                                                               'primaryGenreName']
                                                                           if
                                                                           c in tracks.columns]
    candidate_pool = tracks[available_columns].copy()

    # Thêm thông tin rating
    candidate_pool = candidate_pool.merge(
        ratings.groupby('trackId')['rating'].mean().reset_index(
            name='avg_rating'),
        on='trackId', how='left'
    )

    # Thêm thông tin mood - QUAN TRỌNG!
    candidate_pool = candidate_pool.merge(
        song_mood[['trackId', 'mood_community']],
        on='trackId', how='left'
    )

    # 🎯 QUAN TRỌNG: CHỈ CHỌN BÀI HÁT MATCH MOOD 100%
    mood_matched_pool = candidate_pool[
        candidate_pool['mood_community'] == mood_id].copy()

    if len(mood_matched_pool) == 0:
        mood_matched_pool = candidate_pool.copy()
    else:
        print(
            f"✅ Đã tìm thấy {len(mood_matched_pool)} bài hát match mood {mood_id}")

    # Thêm thông tin popularity từ favorites - CHỈ LẤY fav_count
    fav_counts = favorites_with_artist.groupby('trackId').size().reset_index(
        name='fav_count')
    mood_matched_pool = mood_matched_pool.merge(
        fav_counts[['trackId', 'fav_count']], on='trackId', how='left')
    mood_matched_pool['fav_count'] = mood_matched_pool['fav_count'].fillna(0)

    # Loại bỏ bài hát user đã mua
    user_purchased = set(purchased[purchased["userId"] == user_id]["trackId"])
    final_candidates = mood_matched_pool[
        ~mood_matched_pool["trackId"].isin(user_purchased)]

    if len(final_candidates) == 0:
        return pd.DataFrame()

    # Tính điểm cho từng bài hát (bây giờ TẤT CẢ đều đã match mood)
    final_candidates['new_user_score'] = final_candidates.apply(
        lambda row: calculate_new_user_score(row, system_top),
        axis=1
    )

    # Đa dạng hóa recommendations - SỬ DỤNG ARTISTID (luôn tồn tại)
    artist_diversity_penalty = final_candidates.groupby(
        "artistId").cumcount() * diversity_weight
    final_candidates["final_score"] = final_candidates[
                                          "new_user_score"] - artist_diversity_penalty

    # Lấy top recommendations
    final_recommendations = final_candidates.nlargest(top_n * 2, "final_score")
    final_recommendations = final_recommendations.head(top_n)

    # Chọn các cột có sẵn để trả về - CHỈ LẤY CÁC CỘT TỒN TẠI
    available_columns = ["trackId", "trackName", "artistId", "new_user_score",
                         "final_score", "avg_rating", "recency",
                         "mood_community"]
    if 'artistName' in final_recommendations.columns:
        available_columns.insert(3, "artistName")
    if 'primaryGenreName' in final_recommendations.columns:
        available_columns.insert(4, "primaryGenreName")

    return final_recommendations[available_columns]


# =========================================
# 8️⃣ Gợi ý bài hát cho user
# =========================================

def recommend_for_user(user_id, top_n=10, diversity_weight=0.1):
    # 🆕 KIỂM TRA USER MỚI
    if is_new_user(user_id):
        return recommend_for_new_user(user_id, top_n, diversity_weight)

    user_mood = current_mood[current_mood["userId"] == user_id]["moodID"].values
    if len(user_mood) == 0:
        mood_id = 1  # Mood mặc định
    else:
        mood_id = user_mood[0]

    user_purchased = set(purchased[purchased["userId"] == user_id]["trackId"])
    candidate_df = tracks[~tracks["trackId"].isin(user_purchased)].copy()
    candidate_df["userId"] = user_id

    candidate_df = candidate_df.merge(
        df[["trackId", "rating_score", "recency_score", "cf_score",
            "mood_community", "artist_similarity", "genre_similarity"]],
        on="trackId", how="left"
    ).drop_duplicates(subset="trackId")

    # 🎯 CHỈ CHỌN BÀI HÁT MATCH MOOD
    mood_matched_df = candidate_df[
        candidate_df["mood_community"] == mood_id].copy()

    if len(mood_matched_df) == 0:
        default_mood = 1
        mood_matched_df = candidate_df[
            candidate_df["mood_community"] == default_mood].copy()

        # Nếu vẫn không có, dùng tất cả bài hát
        if len(mood_matched_df) == 0:
            mood_matched_df = candidate_df.copy()

    # 🎯 KHÔNG cần tính similarity nữa (đã pre-computed)
    mood_matched_df = mood_matched_df.fillna({
        "rating_score": 0,
        "recency_score": 0.5,
        "cf_score": 0,
        "artist_similarity": 0,
        "genre_similarity": 0
    })

    # Dự đoán và sắp xếp
    mood_matched_df["pred_score"] = model.predict(mood_matched_df[feature_cols])
    # Đa dạng hóa dựa trên artistId
    artist_diversity_penalty = mood_matched_df.groupby(
        "artistId").cumcount() * diversity_weight
    mood_matched_df["diversity_score"] = mood_matched_df[
                                             "pred_score"] - artist_diversity_penalty

    final_recommendations = mood_matched_df.sort_values("diversity_score",
                                                        ascending=False).head(
        top_n)

    return final_recommendations[
        ["trackId", "trackName", "artistId", "artistName", "pred_score",
         "artist_similarity", "genre_similarity"]]


# =========================================
# 🔥 DEMO & TESTING
# =========================================

import matplotlib.pyplot as plt

# Feature importance
feature_imp = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': model.feature_importances_
}).sort_values('Importance', ascending=False)

plt.figure(figsize=(10, 6))
plt.barh(feature_imp['Feature'], feature_imp['Importance'])
plt.gca().invert_yaxis()
plt.title('Feature Importance với Continuous Features')
plt.xlabel('Importance')
plt.show()

# 🔥 Test với cả user cũ và user mới
print("\n" + "=" * 60)
print("🎧 DEMO RECOMMENDATIONS - USER MỚI ĐA TIÊU CHÍ")
print("=" * 60)

# User cũ
print("\n📊 User CŨ (có favorites):")
user_id_old = 112366
recommendations_old = recommend_for_user(user_id_old, top_n=10)
print(recommendations_old)

# User mới (giả sử ID không tồn tại trong favorites)
print("\n📊 User MỚI (chưa có favorites) - ĐA TIÊU CHÍ:")
user_id_new = 113345  # ID giả định không có trong favorites
recommendations_new = recommend_for_user(user_id_new, top_n=10)
print(recommendations_new)
