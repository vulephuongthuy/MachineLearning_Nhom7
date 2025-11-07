import pandas as pd

def load_data_from_mongodb(db_connection):
    """Load và xử lý data - SIÊU NGẮN GỌN & NHANH"""

    # Định nghĩa projections
    projections = {
        'tracks': {'trackId': 1, 'artistId': 1, 'trackName': 1,
                   'releaseDate': 1, 'artistName': 1, 'primaryGenreName': 1},
        'user': {'userId': 1},
        'user_favorite': {'userId': 1, 'trackId': 1, 'artistName': 1, 'primaryGenreName': 1},
        'user_rating': {'userId': 1, 'trackId': 1, 'rating': 1},
        'purchase': {'userId': 1, 'trackId': 1},
        'mood_tracking_history': {'userId': 1, 'moodID': 1, 'timestamp': 1},
        'song_mood_community': {'trackId': 1, 'mood_community': 1}
    }

    # Load tất cả data trong 1 khối - SIÊU NGẮN
    collections = ['tracks', 'user', 'user_favorite', 'user_rating', 'purchase',
                   'mood_tracking_history', 'song_mood_community']
    tracks, users, favorites, ratings, purchased, mood_hist, song_mood = [
        pd.DataFrame(list(db_connection.db[col].find({}, projections[col])))
        for col in collections
    ]

    # Convert userId to string - NGẮN GỌN
    for df in [favorites, ratings, purchased, mood_hist, users]:
        df['userId'] = df['userId'].astype(str)

    # Tính toán chính - GIỮ NGUYÊN LOGIC
    favorites_with_artist = favorites.merge(tracks[['trackId', 'artistId']],
                                            on='trackId', how='left')
    rating_avg = ratings.groupby("trackId")["rating"].mean().reset_index()
    rating_avg["rating_score"] = rating_avg["rating"] / 5

    df = favorites_with_artist.merge(song_mood[["trackId", "mood_community"]],
                                     on="trackId", how="left")
    df = df.merge(rating_avg[["trackId", "rating_score"]], on="trackId",
                  how="left")

    # Recency
    tracks["releaseDate"] = pd.to_datetime(tracks["releaseDate"],
                                           errors="coerce").dt.tz_localize(None)
    tracks["recency"] = (pd.Timestamp.now() - tracks["releaseDate"]).dt.days
    df = df.merge(tracks[["trackId", "recency"]], on="trackId", how="left")
    df["recency_score"] = 1 / (1 + df["recency"].fillna(df["recency"].max()))

    # Current mood
    current_mood = (mood_hist.sort_values("timestamp", ascending=False).groupby(
        "userId").first().reset_index()[["userId", "moodID"]])
    current_mood['userId'] = current_mood['userId'].astype(str)
    df['userId'] = df['userId'].astype(str)
    df = df.merge(current_mood, on="userId", how="left")

    # CF score
    cf_counts = favorites_with_artist.groupby("trackId")[
        "userId"].count().reset_index()
    cf_counts.columns = ["trackId", "cf_score"]
    cf_counts["cf_score"] = cf_counts["cf_score"] / cf_counts["cf_score"].max()
    df = df.merge(cf_counts, on="trackId", how="left")

    # Artist/genre features
    user_artist_counts = favorites_with_artist.groupby(
        ['userId', 'artistId']).size().reset_index(name='artist_count')
    user_genre_counts = favorites_with_artist.groupby(
        ['userId', 'primaryGenreName']).size().reset_index(name='genre_count')
    user_total_favs = favorites_with_artist.groupby(
        'userId').size().reset_index(name='total_favs')

    df = df.merge(user_artist_counts, on=['userId', 'artistId'], how='left')
    df = df.merge(user_genre_counts, on=['userId', 'primaryGenreName'],
                  how='left')
    df = df.merge(user_total_favs, on='userId', how='left')

    df['artist_count'] = df['artist_count'].fillna(0)
    df['genre_count'] = df['genre_count'].fillna(0)
    df['total_favs'] = df['total_favs'].fillna(1)

    df["artist_similarity"] = (
                0.7 * (df['artist_count'] > 0).astype(float) + 0.3 * (
                    df['artist_count'] / df['total_favs']))
    df["genre_similarity"] = (
                0.7 * (df['genre_count'] > 0).astype(float) + 0.3 * (
                    df['genre_count'] / df['total_favs']))

    df = df.drop(['artist_count', 'genre_count', 'total_favs'], axis=1)

    # Mood similarity
    df["mood_similarity"] = df.apply(
        lambda row: 1.0 if row["moodID"] == row["mood_community"] else 0.0,
        axis=1)

    # Fill NaN
    df = df.fillna({"rating_score": 0, "recency_score": 0.5, "cf_score": 0,
                    "mood_similarity": 0, "artist_similarity": 0,
                    "genre_similarity": 0})

    # Tracks with features
    feature_cols = ["recency_score", "rating_score", "artist_similarity",
                    "genre_similarity"]
    features_to_merge = ['trackId'] + feature_cols + ['mood_community']
    tracks_with_features = tracks.merge(
        df[features_to_merge].drop_duplicates(subset=['trackId']), on='trackId',
        how='left')

    for feat in feature_cols:
        tracks_with_features[feat] = tracks_with_features[feat].fillna(0)
    tracks_with_features['mood_community'] = tracks_with_features[
        'mood_community'].fillna(1)

    return {
        'tracks': tracks_with_features, 'users': users, 'favorites': favorites,
        'ratings': ratings,
        'purchased': purchased, 'mood_hist': mood_hist, 'song_mood': song_mood,
        'favorites_with_artist': favorites_with_artist, 'df': df,
        'current_mood': current_mood
    }

def is_new_user(user_id, favorites_with_artist):
    """Kiểm tra user có phải là user mới không - GIỐNG GỐC"""
    return user_id not in favorites_with_artist['userId'].values

def get_system_top_artists_genres(favorites_with_artist, top_n=20):
    """Lấy top artists và genres phổ biến nhất toàn hệ thống - GIỐNG GỐC"""
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
    """Tính điểm cho bài hát với user mới - GIỐNG GỐC"""
    score = 0.0
    weights = {'recency': 0.40, 'rating': 0.30, 'top_artist': 0.15,
               'top_genre': 0.15}

    # Recency score
    if 'recency' in track_row and pd.notnull(track_row['recency']):
        days = track_row['recency']
        if days <= 30:
            recency_score = 1.0
        elif days <= 90:
            recency_score = 0.7
        elif days <= 180:
            recency_score = 0.3
        elif days <= 365:
            recency_score = 0.1
        else:
            recency_score = 0.01
    else:
        recency_score = 0
    score += weights['recency'] * recency_score

    # Rating score
    rating_score = track_row[
                       'avg_rating'] / 5.0 if 'avg_rating' in track_row and pd.notnull(
        track_row['avg_rating']) else 0
    score += weights['rating'] * rating_score

    # Top artist score
    artist_score = 0.0
    if 'artistId' in track_row and pd.notnull(track_row['artistId']):
        artist_popularity = system_top['artist_scores'].get(
            track_row['artistId'], 0)
        max_artist_pop = max(system_top['artist_scores'].values()) if \
        system_top['artist_scores'] else 1
        artist_score = artist_popularity / max_artist_pop if max_artist_pop > 0 else 0
    score += weights['top_artist'] * artist_score

    # Top genre score
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


def recommend_for_new_user(user_id, components, db_connection, top_n=10,
                           diversity_weight=0.15):
    """Recommendations cho user MỚI - LẤY MOOD TỪ MONGODB"""
    mongodb_data = load_data_from_mongodb(db_connection)

    # Lấy data từ mongodb_data thay vì components
    tracks_df = mongodb_data['tracks']
    song_mood_df = mongodb_data['song_mood']
    ratings_df = mongodb_data['ratings']
    favorites_df = mongodb_data['favorites_with_artist']

    # 🎯 LẤY MOOD MỚI NHẤT TỪ MONGODB
    try:
        latest_mood = db_connection.db["mood_tracking_history"].find_one(
            {"userId": user_id}, sort=[("timestamp", -1)]
        )
        current_mood_id = latest_mood.get("moodID", 1) if latest_mood else 1
        print(
            f"🎭 Latest moodID from MongoDB for user {user_id}: {current_mood_id}")
    except Exception as e:
        print(f"❌ Error getting mood from MongoDB: {e}")
        current_mood_id = 1

    system_top = get_system_top_artists_genres(favorites_df)

    # 🎯 SỬ DỤNG MOOD TỪ MONGODB ĐỂ SO MOOD
    mood_id = current_mood_id

    # 🎯 GIỐNG GỐC: Tạo candidate pool
    available_columns = ['trackId', 'trackName', 'artistId', 'recency'] + [c for
                                                                           c in
                                                                           [
                                                                               'artistName',
                                                                               'primaryGenreName']
                                                                           if
                                                                           c in tracks_df.columns]
    candidate_pool = tracks_df[available_columns].copy()

    candidate_pool = candidate_pool.merge(
        ratings_df.groupby('trackId')['rating'].mean().reset_index(
            name='avg_rating'),
        on='trackId', how='left'
    )
    candidate_pool = candidate_pool.merge(
        song_mood_df[['trackId', 'mood_community']], on='trackId', how='left')

    # 🎯 GIỐNG GỐC: Lọc theo mood (SO MOOD VỚI MONGODB)
    mood_matched_pool = candidate_pool[
        candidate_pool['mood_community'] == mood_id].copy()
    if len(mood_matched_pool) == 0:
        mood_matched_pool = candidate_pool.copy()

    # 🎯 GIỐNG GỐC: Thêm fav_count
    fav_counts = favorites_df.groupby('trackId').size().reset_index(
        name='fav_count')
    mood_matched_pool = mood_matched_pool.merge(
        fav_counts[['trackId', 'fav_count']], on='trackId', how='left')
    mood_matched_pool['fav_count'] = mood_matched_pool['fav_count'].fillna(0)

    # Lấy purchased từ MongoDB thay vì components
    try:
        # Lấy danh sách trackId đã mua từ MongoDB (giữ nguyên int)
        user_purchased_tracks = db_connection.db["purchase"].find(
            {"userId": user_id},
            {"trackId": 1}
        )
        user_purchased = set(
            [doc["trackId"] for doc in user_purchased_tracks])  # Giữ nguyên int
        print(
            f"📦 Loaded {len(user_purchased)} purchased tracks from MongoDB for user {user_id}")
    except Exception as e:
        print(f"❌ Error getting purchased tracks from MongoDB: {e}")
        user_purchased = set()

    # 🎯 GIỐNG GỐC: Loại bỏ bài đã mua
    final_candidates = mood_matched_pool[
        ~mood_matched_pool["trackId"].isin(user_purchased)].copy()

    if len(final_candidates) == 0:
        return pd.DataFrame()

    # 🎯 GIỐNG GỐC: Tính điểm
    final_candidates['new_user_score'] = final_candidates.apply(
        lambda row: calculate_new_user_score(row, system_top), axis=1
    )

    # 🎯 GIỐNG GỐC: Đa dạng hóa
    artist_diversity_penalty = final_candidates.groupby(
        "artistId").cumcount() * diversity_weight
    final_candidates["final_score"] = final_candidates[
                                          "new_user_score"] - artist_diversity_penalty

    final_recommendations = final_candidates.nlargest(top_n * 2,
                                                      "final_score").head(top_n)

    # 🎯 GIỐNG GỐC: Chọn columns
    available_columns = ["trackId", "trackName", "artistId", "new_user_score",
                         "final_score", "avg_rating", "recency",
                         "mood_community"]
    if 'artistName' in final_recommendations.columns: available_columns.insert(
        3, "artistName")
    if 'primaryGenreName' in final_recommendations.columns: available_columns.insert(
        4, "primaryGenreName")

    return final_recommendations[available_columns]


def recommend_for_user(user_id, components, db_connection, top_n=10,
                       diversity_weight=0.1):
    """Recommendations cho user CŨ - LẤY MOOD TỪ MONGODB"""
    mongodb_data = load_data_from_mongodb(db_connection)

    favorites_with_artist = mongodb_data['favorites_with_artist']
    tracks_df = mongodb_data['tracks']

    # Lấy data từ components
    model = components['model']
    feature_cols = components['feature_cols']

    # 🎯 LẤY MOOD MỚI NHẤT TỪ MONGODB
    try:
        latest_mood = db_connection.db["mood_tracking_history"].find_one(
            {"userId": user_id}, sort=[("timestamp", -1)]
        )
        current_mood_id = latest_mood.get("moodID", 1) if latest_mood else 1
        print(
            f"🎭 Latest moodID from MongoDB for user {user_id}: {current_mood_id}")
    except Exception as e:
        print(f"❌ Error getting mood from MongoDB: {e}")
        current_mood_id = 1

    # 🎯 GIỐNG GỐC: Kiểm tra user mới
    if is_new_user(user_id, favorites_with_artist):
        return recommend_for_new_user(user_id, components, db_connection, top_n,
                                      diversity_weight)

    # 🎯 SỬ DỤNG MOOD TỪ MONGODB ĐỂ SO MOOD
    mood_id = current_mood_id

    # Lấy purchased từ MongoDB thay vì components
    try:
        # Lấy danh sách trackId đã mua từ MongoDB (giữ nguyên int)
        user_purchased_tracks = db_connection.db["purchase"].find(
            {"userId": user_id},
            {"trackId": 1}
        )
        user_purchased = set(
            [doc["trackId"] for doc in user_purchased_tracks])  # Giữ nguyên int
    except Exception as e:
        print(f"❌ Error getting purchased tracks from MongoDB: {e}")
        user_purchased = set()

    # 🎯 GIỐNG GỐC: Lọc bài chưa mua
    tracks_df["trackId"] = tracks_df["trackId"].astype(int)
    candidate_df = tracks_df[~tracks_df["trackId"].isin(user_purchased)].copy()
    candidate_df["userId"] = user_id

    # 🎯 GIỐNG GỐC: Merge với features từ df gốc
    candidate_df = candidate_df.drop_duplicates(subset="trackId")

    # 🎯 GIỐNG GỐC: Lọc theo mood (SO MOOD VỚI MONGODB)
    mood_matched_df = candidate_df[
        candidate_df["mood_community"] == mood_id].copy()
    if len(mood_matched_df) == 0:
        default_mood = 1
        mood_matched_df = candidate_df[
            candidate_df["mood_community"] == default_mood].copy()
        if len(mood_matched_df) == 0:
            mood_matched_df = candidate_df.copy()

    # 🎯 GIỐNG GỐC: Fill NaN
    mood_matched_df = mood_matched_df.fillna({
        "rating_score": 0, "recency_score": 0.5, "cf_score": 0,
        "artist_similarity": 0, "genre_similarity": 0
    })

    # 🎯 GIỐNG GỐC: Dự đoán
    mood_matched_df["pred_score"] = model.predict(mood_matched_df[feature_cols])

    # 🎯 GIỐNG GỐC: Đa dạng hóa
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