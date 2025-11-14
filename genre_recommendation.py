# ===============================================
# recommendation_genre.py - ĐÃ TỐI GIẢN
# ===============================================
import pickle
import random
import numpy as np
import pandas as pd
import os

from sklearn.compose import ColumnTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler

# --- TẢI MÔ HÌNH ---
base_dir = os.path.dirname(os.path.abspath(__file__))
master_feature_path = os.path.join(base_dir, "models/master_features2.pkl")
mf_model_path = os.path.join(base_dir, "models/mf_model.pkl")

try:
    with open(master_feature_path, 'rb') as f:
        master_features = pickle.load(f)
    with open(mf_model_path, 'rb') as f:
        mf_model = pickle.load(f)
    print("Mô hình genre recommendation đã sẵn sàng.")
except Exception as e:
    print("Lỗi khi tải model:", e)
    master_features = mf_model = None

# ===============================================
# CACHE SYSTEM
# ===============================================
_user_data_cache = {}

def get_cached_user_data(db, user_id):
    """Lấy và cache dữ liệu user"""
    if user_id in _user_data_cache:
        return _user_data_cache[user_id]

    purchased_tracks = get_user_purchased_tracks(db, user_id)
    purchased_artists = get_purchased_artists(db, user_id)

    user_data = {
        'purchased_tracks': purchased_tracks,
        'purchased_artists': purchased_artists,
        'is_cold_start': len(purchased_tracks) < 5
    }

    _user_data_cache[user_id] = user_data
    print(f"Cached: {len(purchased_tracks)} tracks, {len(purchased_artists)} artists")
    return user_data


def clear_user_cache(user_id=None):
    """Xóa cache"""
    global _user_data_cache
    if user_id:
        if user_id in _user_data_cache:
            del _user_data_cache[user_id]
    else:
        _user_data_cache.clear()


# ===============================================
# DATA ACCESS
# ===============================================
def get_user_purchased_tracks(db, user_id):
    """Lấy danh sách tracks user đã mua"""
    try:
        purchased_tracks = list(db.db["purchase"].find(
            {'userId': str(user_id)}, {'trackId': 1}
        ))
        return [str(track['trackId']) for track in purchased_tracks]
    except Exception as e:
        print(f"Lỗi khi lấy purchased tracks: {e}")
        return []


def get_purchased_artists(db, user_id):
    """Lấy danh sách artist user đã mua"""
    try:
        pipeline = [
            {'$match': {'userId': str(user_id)}},
            {'$lookup': {
                'from': 'tracks',
                'localField': 'trackId',
                'foreignField': 'trackId',
                'as': 'track_info'
            }},
            {'$unwind': '$track_info'},
            {'$group': {'_id': '$track_info.artistId'}}
        ]
        artist_cursor = db.db["purchase"].aggregate(pipeline)
        return [doc['_id'] for doc in artist_cursor if doc.get('_id')]
    except Exception as e:
        print(f"Lỗi khi lấy artists: {e}")
        return []


# ===============================================
# COLD START
# ===============================================
def get_cold_start_recommendations(db, user_id, purchased_tracks, limit_per_genre=10):
    """Cold start recommendations"""
    try:
        popular_genres = get_popular_genres()
        all_recommendations = []

        for genre in popular_genres:
            genre_tracks = get_top_tracks_for_genre(db, genre, limit_per_genre, purchased_tracks)
            all_recommendations.append({
                'genre': genre,
                'tracks': genre_tracks,
                'track_count': len(genre_tracks)
            })

        return {
            'user_id': user_id,
            'user_type': 'cold_start',
            'top_genres': popular_genres,
            'recommendations': all_recommendations,
            'total_recommended_tracks': sum(len(rec['tracks']) for rec in all_recommendations)
        }
    except Exception as e:
        print(f"Lỗi cold start: {e}")
        return {'user_id': user_id, 'user_type': 'cold_start', 'recommendations': []}


def get_popular_genres(limit=4):
    """Lấy top genres phổ biến"""
    if master_features is not None and not master_features.empty:
        return master_features['primaryGenreName'].value_counts().head(limit).index.tolist()

def get_top_tracks_for_genre(db, genre, limit=10, exclude_tracks=None):
    """Lấy top tracks của genre"""
    try:
        if exclude_tracks is None:
            exclude_tracks = []

        if master_features is not None:
            genre_tracks = master_features[
                (master_features['primaryGenreName'] == genre) &
                (~master_features['trackId'].isin(exclude_tracks))
                ].copy()
        else:
            genre_tracks = pd.DataFrame(list(db.db["tracks"].find({
                'primaryGenreName': genre,
                'trackId': {'$nin': exclude_tracks}
            }, limit=limit * 3)))

        if genre_tracks.empty:
            return []

        top_tracks = genre_tracks.nlargest(limit, 'popularity_score')

        return [{
            'trackId': track['trackId'],
            'trackName': track['trackName'],
            'artistName': track['artistName'],
            'primaryGenreName': track['primaryGenreName'],
            'popularity_score': track['popularity_score'],
            'avg_rating': track.get('avg_rating', 3.0),
            'score': track['popularity_score'],
            'recommendation_type': 'cold_start_top_popular'
        } for _, track in top_tracks.iterrows()]

    except Exception as e:
        print(f"Lỗi lấy top tracks cho {genre}: {e}")
        return []


# ===============================================
# REGULAR USER
# ===============================================
def get_user_top_genres(db, user_id, limit=50):
    """Lấy top genres của user từ lịch sử gần nhất"""
    try:
        played_tracks = list(db.db["user_history"].find(
            {'userId': str(user_id)}, {'trackId': 1}
        ).sort('LastPlayedAt', -1).limit(limit))

        played_ids = [str(track['trackId']) for track in played_tracks]

        if not played_ids or master_features is None:
            return get_popular_genres()

        user_tracks_df = pd.DataFrame(played_ids, columns=['trackId'])
        master_features['trackId'] = master_features['trackId'].astype(str)

        user_tracks = user_tracks_df.merge(
            master_features[['trackId', 'primaryGenreName']],
            on='trackId',
            how='left'
        )

        if user_tracks.empty:
            return get_popular_genres()

        return user_tracks['primaryGenreName'].value_counts().head(4).index.tolist()

    except Exception as e:
        print(f"Lỗi khi lấy top genres: {e}")
        return get_popular_genres()

def simple_similarity_filtering(purchased_track_ids, candidate_tracks, top_k=50):
    """Lọc tracks bằng similarity"""
    try:
        purchased_tracks_features = master_features[
            master_features['trackId'].isin(purchased_track_ids)
        ]

        if purchased_tracks_features.empty:
            return candidate_tracks.nlargest(top_k, 'popularity_score')

        feature_columns = ['trackTimeMillis','recency_score']
        purchased_features = purchased_tracks_features[feature_columns].fillna(0)
        candidate_features = candidate_tracks[feature_columns].fillna(0)

        # CHUẨN HÓA
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()

        all_features = pd.concat([purchased_features, candidate_features])
        scaler.fit(all_features)

        purchased_scaled = scaler.transform(purchased_features)
        candidate_scaled = scaler.transform(candidate_features)

        similarities = cosine_similarity(purchased_scaled, candidate_scaled)
        avg_similarities = similarities.max(axis=0)

        candidate_tracks = candidate_tracks.copy()
        candidate_tracks['similarity'] = avg_similarities
        return candidate_tracks.nlargest(top_k, 'similarity')

    except Exception as e:
        print(f"Lỗi similarity filtering: {e}")
        return candidate_tracks.nlargest(top_k, 'popularity_score')


def calculate_track_score(user_id, track, purchased_artists=None):
    """Tính điểm gợi ý cho bài hát - OPTIMIZED"""
    score = 0.0
    track_id_str = str(track['trackId'])

    # 1. Matrix Factorization Score - CF
    mf_score = 0
    has_mf_score = False

    if mf_model and str(user_id) in mf_model['user_idx_map'] and track_id_str in mf_model['track_idx_map']:
        u_idx = mf_model['user_idx_map'][str(user_id)]
        i_idx = mf_model['track_idx_map'][track_id_str]
        mf_score = float(mf_model['R_pred'][u_idx, i_idx])
        has_mf_score = True
    elif mf_model and track_id_str in mf_model['track_idx_map']:
        # Warm start: dùng average score của track từ tất cả users
        i_idx = mf_model['track_idx_map'][track_id_str]
        track_scores = mf_model['R_pred'][:, i_idx]
        mf_score = float(np.mean(track_scores[track_scores > 0]))
        # Giảm trọng số vì đây là average
        mf_score *= 0.7

    # 2. Content-based Similarity Score
    content_based_score = track.get('similarity', 0)

    if has_mf_score:
        score += 0.50 * mf_score
        score += 0.40 * content_based_score
    else:
        score += 0.20 * mf_score
        score += 0.80 * content_based_score

    if purchased_artists and str(track.get('artistId', '')) in purchased_artists:
        score += 0.05

    score += 0.05 * random.uniform(0.0, 1.0)

    return float(np.clip(score, 0.1, 1.0))

def recommend_tracks_for_genre(user_id, genre, purchased_tracks, purchased_artists, limit=10):
    """Gợi ý tracks cho genre - OPTIMIZED VERSION"""
    try:
        master_features['trackId'] = master_features['trackId'].astype(str)

        available_tracks = master_features[
            (master_features['primaryGenreName'] == genre) &
            (~master_features['trackId'].isin(purchased_tracks))
            ]

        if available_tracks.empty:
            return []

        prefiltered_tracks = simple_similarity_filtering(
            purchased_tracks, available_tracks, top_k=limit * 5
        )

        if prefiltered_tracks.empty:
            return []

        scored_tracks = []
        for _, track in prefiltered_tracks.iterrows():
            score = calculate_track_score(user_id, track, purchased_artists)
            scored_tracks.append({
                'track': track,
                'score': score,
                'artist': track['artistName']
            })

        scored_tracks.sort(key=lambda x: x['score'], reverse=True)

        # LỰA CHỌN VỚI DIVERSITY LINH HOẠT
        final_tracks = []
        artist_count = {}

        for track_data in scored_tracks:
            if len(final_tracks) >= limit:
                break

            artist = track_data['artist']
            current_score = track_data['score']

            max_per_artist = 3 if current_score > 0.7 else 2 if current_score > 0.25 else 1

            if artist_count.get(artist, 0) < max_per_artist:
                track = track_data['track']
                final_tracks.append({
                    'trackId': track['trackId'],
                    'trackName': track['trackName'],
                    'artistName': track['artistName'],
                    'primaryGenreName': track['primaryGenreName'],
                    'score': current_score,
                    'popularity_score': track['popularity_score'],
                    'recency_score': track['recency_score'],
                    'avg_rating': track['avg_rating']
                })
                artist_count[artist] = artist_count.get(artist, 0) + 1
        print(f"Score range: {min(t['score'] for t in final_tracks):.3f} - {max(t['score'] for t in final_tracks):.3f}")
        return final_tracks

    except Exception as e:
        print(f"Lỗi khi gợi ý tracks: {e}")
        return []

# ===============================================
# HÀM CHÍNH
# ===============================================
def get_genre_recommendations(db, user_id, limit_per_genre=10):
    """Hàm chính lấy recommendations"""
    try:
        user_data = get_cached_user_data(db, user_id)
        purchased_tracks = user_data['purchased_tracks']
        purchased_artists = user_data['purchased_artists']
        is_cold_start = user_data['is_cold_start']

        if is_cold_start:
            result = get_cold_start_recommendations(db, user_id, purchased_tracks, limit_per_genre)
        else:
            top_genres = get_user_top_genres(db, user_id)
            all_recommendations = []

            for genre in top_genres:
                genre_tracks = recommend_tracks_for_genre(
                    user_id, genre, purchased_tracks, purchased_artists, limit_per_genre
                )
                all_recommendations.append({
                    'genre': genre,
                    'tracks': genre_tracks,
                    'track_count': len(genre_tracks)
                })

            result = {
                'user_id': user_id,
                'user_type': 'regular_user',
                'top_genres': top_genres,
                'recommendations': all_recommendations,
                'total_recommended_tracks': sum(len(rec['tracks']) for rec in all_recommendations)
            }

        clear_user_cache(user_id)
        return result

    except Exception as e:
        print(f"Lỗi trong get_genre_recommendations: {e}")
        clear_user_cache(user_id)
        return {'user_id': user_id, 'user_type': 'error', 'recommendations': []}