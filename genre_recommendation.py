# ===============================================
# recommendation_genre.py
# ===============================================
import pickle
import random
import pandas as pd
from pymongo import MongoClient
import os

# --- KẾT NỐI DATABASE ---
client = MongoClient("mongodb://localhost:27017/")
db = client["moo_d"]

# --- TẢI MÔ HÌNH ĐÃ TRAIN ---
base_dir = os.path.dirname(os.path.abspath(__file__))
master_feature_path = os.path.join(base_dir, "models/master_features.pkl")
mf_model_path = os.path.join(base_dir, "models/mf_model.pkl")

try:
    with open(master_feature_path, 'rb') as f:
        master_features = pickle.load(f)
    with open(mf_model_path, 'rb') as f:
        mf_model = pickle.load(f)
    print("✅ Mô hình genre recommendation đã sẵn sàng.")
except Exception as e:
    print("⚠️ Lỗi khi tải model:", e)
    master_features = mf_model = None


# ===============================================
# HÀM TIỆN ÍCH - DATA ACCESS
# ===============================================

def is_cold_start_user(user_id):
    """Kiểm tra user có phải cold start không (ít lịch sử nghe)"""
    try:
        played_count = db.user_history.count_documents({'userId': str(user_id)})
        is_cold = played_count < 5
        print(f"🔍 User {user_id}: {played_count} bài đã nghe -> Cold: {is_cold}")
        return is_cold
    except Exception as e:
        print(f"⚠️ Lỗi khi kiểm tra cold start user {user_id}: {e}")
        return True


def get_popular_genres(limit=4):
    """Lấy top genres phổ biến nhất toàn hệ thống"""
    try:
        if master_features is not None and not master_features.empty:
            genre_counts = master_features['primaryGenreName'].value_counts()
            popular_genres = genre_counts.head(limit).index.tolist()
            print(f"🏆 Top {limit} genres từ hệ thống: {popular_genres}")
            return popular_genres
        else:
            fallback_genres = ['Pop', 'Rock', 'Hip-Hop/Rap', 'Electronic']
            print(f"🏆 Sử dụng fallback genres: {fallback_genres}")
            return fallback_genres
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy popular genres: {e}")
        return ['Pop', 'Rock', 'Hip-Hop/Rap', 'Electronic']


def get_user_purchased_tracks(user_id):
    """Lấy danh sách tracks user đã mua"""
    try:
        purchased_tracks = list(db.db["purchase"].find(  # ✅ SỬA: db["purchase"]
            {'userId': str(user_id)},
            {'trackId': 1}
        ))
        purchased_ids = [str(track['trackId']) for track in purchased_tracks]
        return purchased_ids
    except Exception as e:
        print(f"❌ Lỗi khi lấy purchased tracks: {e}")
        return []


def get_purchased_artists(user_id):
    """Trả về danh sách artistId mà user đã mua bài"""
    try:
        purchased_ids = get_user_purchased_tracks(user_id)
        if not purchased_ids:
            return []

        tracks_info = list(db.db["tracks"].find(
            {'trackId': {'$in': purchased_ids}},
            {'artistId': 1, '_id': 0}
        ))

        artist_ids = [t['artistId'] for t in tracks_info if 'artistId' in t]
        return list(set(artist_ids))
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách artistId đã mua: {e}")
        return []

def get_user_played_tracks(user_id):
    """Lấy danh sách tracks user đã nghe"""
    try:
        played_tracks = list(db.db["user_history"].find(
            {'userId': str(user_id)},
            {'trackId': 1}
        ))
        played_ids = [str(track['trackId']) for track in played_tracks]
        return played_ids
    except Exception as e:
        print(f"❌ Lỗi khi lấy played tracks: {e}")
        return []


# ===============================================
# HÀM COLD START - ĐƠN GIẢN & HIỆU QUẢ
# ===============================================

def get_cold_start_recommendations(user_id, limit_per_genre=10):
    """Cold start đơn giản: lấy top tracks của mỗi genre (loại trừ đã mua)"""
    try:
        print(f"🎯 Cold start đơn giản cho user {user_id}")

        # Lấy danh sách tracks đã mua
        purchased_tracks = get_user_purchased_tracks(user_id)

        popular_genres = get_popular_genres(4)
        all_recommendations = []
        total_tracks = 0

        for genre in popular_genres:
            genre_tracks = get_top_tracks_for_genre(genre, limit_per_genre, purchased_tracks)

            all_recommendations.append({
                'genre': genre,
                'tracks': genre_tracks,
                'track_count': len(genre_tracks)
            })
            total_tracks += len(genre_tracks)
            print(f"✅ {genre}: {len(genre_tracks)} tracks (đã loại trừ {len(purchased_tracks)} tracks đã mua)")

        return {
            'user_id': user_id,
            'user_type': 'cold_start',
            'top_genres': popular_genres,
            'recommendations': all_recommendations,
            'total_recommended_tracks': total_tracks,
            'message': f'Cold start - {total_tracks} tracks phổ biến nhất (đã loại trừ tracks đã mua)'
        }

    except Exception as e:
        print(f"❌ Lỗi cold start: {e}")
        return {
            'user_id': user_id,
            'user_type': 'cold_start',
            'error': str(e),
            'recommendations': [],
            'total_recommended_tracks': 0
        }


def get_top_tracks_for_genre(genre, limit=10, exclude_tracks=None):
    """Lấy top tracks của genre - loại trừ tracks đã mua"""
    try:
        if exclude_tracks is None:
            exclude_tracks = []

        if master_features is not None:
            # Lọc ra tracks thuộc genre và không nằm trong danh sách loại trừ
            genre_tracks = master_features[
                (master_features['primaryGenreName'] == genre) &
                (~master_features['trackId'].isin(exclude_tracks))
            ].copy()
        else:
            # Fallback: query từ database với điều kiện loại trừ
            genre_tracks = pd.DataFrame(list(db.tracks.find({
                'primaryGenreName': genre,
                'trackId': {'$nin': exclude_tracks}
            }, limit=limit * 3)))  # Lấy nhiều hơn để đề phòng bị loại trừ nhiều

        if genre_tracks.empty:
            print(f"📭 Không có tracks nào cho genre {genre} sau khi loại trừ")
            return []

        # Sắp xếp theo popularity_score và lấy top
        genre_tracks = genre_tracks.sort_values('popularity_score', ascending=False)
        top_tracks = genre_tracks.head(limit)

        results = []
        for _, track in top_tracks.iterrows():
            results.append({
                'trackId': track['trackId'],
                'trackName': track['trackName'],
                'artistName': track['artistName'],
                'primaryGenreName': track['primaryGenreName'],
                'popularity_score': track['popularity_score'],
                'avg_rating': track.get('avg_rating', 3.0),
                'score': track['popularity_score'],
                'recommendation_type': 'cold_start_top_popular'
            })
        print(f"🎵 Genre {genre}: tìm thấy {len(results)}/{limit} tracks sau khi loại trừ")
        return results

    except Exception as e:
        print(f"❌ Lỗi lấy top tracks cho {genre}: {e}")
        return []


# ===============================================
# HÀM CHO REGULAR USER - CÓ LỊCH SỬ
# ===============================================

def get_user_top_genres(user_id, limit=50):
    """Lấy top genres của user từ lịch sử nghe gần nhất"""
    try:
        if is_cold_start_user(user_id):
            print(f"🎯 User {user_id} là cold start, sử dụng top genres hệ thống")
            return get_popular_genres(4)

        user_history = list(db.user_history.find(
            {'userId': str(user_id)},
            sort=[('LastPlayedAt', -1)],
            limit=limit
        ))

        if not user_history:
            return []

        user_df = pd.DataFrame(user_history)
        user_df['trackId'] = user_df['trackId'].astype(str)
        master_features['trackId'] = master_features['trackId'].astype(str)

        user_tracks = user_df.merge(
            master_features[['trackId', 'primaryGenreName']],
            on='trackId',
            how='left'
        )

        genre_counts = user_tracks.groupby('primaryGenreName').agg({
            'PlayCount': 'sum',
            'trackId': 'count'
        }).reset_index()

        genre_counts['weighted_score'] = (
                0.7 * genre_counts['PlayCount'] +
                0.3 * genre_counts['trackId']
        )

        top_genres = genre_counts.nlargest(4, 'weighted_score')['primaryGenreName'].tolist()
        return top_genres

    except Exception as e:
        print(f"❌ Lỗi khi lấy top genres cho user {user_id}: {e}")
        return []


def calculate_track_score(user_id, track):
    """Tính điểm cho track - kết hợp MF, popularity, rating"""
    score = 0.0
    track_id_str = str(track['trackId'])

    # 1. Matrix Factorization Score
    mf_score = 0
    if (mf_model and str(user_id) in mf_model['user_idx_map']
            and track_id_str in mf_model['track_idx_map']):
        user_idx = mf_model['user_idx_map'][str(user_id)]
        track_idx = mf_model['track_idx_map'][track_id_str]
        mf_score = max(0, mf_model['R_pred'][user_idx, track_idx])

    mf_contribution = 0.45 * (mf_score * 1.4 if mf_score > 0 else 0.5)
    score += mf_contribution

    # 2. Popularity Score
    pop_score = track['popularity_score']
    score += 0.25 * (pop_score * 1.2 if pop_score < 0.6 else pop_score)

    # 3. Rating Score
    rating_score = track['avg_rating'] / 5.0
    score += 0.15 * (rating_score * 1.3 if rating_score < 0.7 else rating_score)

    # 4. Recency Score
    score += 0.15 * track['recency_score']

    # 5. Randomness for diversity
    score += 0.05 * random.uniform(0.3, 1.0)

    # 6. Ưu tiên nghệ sĩ đã mua
    try:
        purchased_artists = get_purchased_artists(user_id)
        track_artist_id = str(track.get('artistId', ''))
        if track_artist_id in purchased_artists:
            score += 0.2
    except Exception as e:
        print(f"⚠️ Lỗi khi tính ưu tiên nghệ sĩ đã mua: {e}")

    return min(1.0, max(0.4, score))


def recommend_tracks_for_genre(user_id, genre, limit=10):
    """Gợi ý tracks cho genre cụ thể với diversity cân bằng"""
    try:
        purchased_tracks = get_user_purchased_tracks(user_id)
        played_tracks = get_user_played_tracks(user_id)
        master_features['trackId'] = master_features['trackId'].astype(str)

        available_tracks = master_features[
            (master_features['primaryGenreName'] == genre) &
            (~master_features['trackId'].isin(purchased_tracks)) &
            (~master_features['trackId'].isin(played_tracks))
            ]

        if available_tracks.empty:
            return []

        # Tính điểm và sắp xếp
        scored_tracks = []
        for _, track in available_tracks.iterrows():
            score = calculate_track_score(user_id, track)
            scored_tracks.append({
                'track': track,
                'score': score,
                'artist': track['artistName']
            })

        scored_tracks.sort(key=lambda x: x['score'], reverse=True)
        return select_tracks_with_diversity(scored_tracks, limit)

    except Exception as e:
        print(f"❌ Lỗi khi gợi ý tracks cho genre {genre}: {e}")
        return []


def select_tracks_with_diversity(scored_tracks, limit):
    """Lựa chọn tracks với cân bằng chất lượng và diversity"""
    if not scored_tracks:
        return []

    final_tracks = []
    artist_count = {}
    top_tracks = scored_tracks[:limit * 3]

    # Ưu tiên chất lượng cao + đa dạng nghệ sĩ
    for track_data in top_tracks:
        if len(final_tracks) >= limit:
            break

        artist = track_data['artist']
        current_count = artist_count.get(artist, 0)

        if current_count < 2:
            final_tracks.append(create_track_result(track_data))
            artist_count[artist] = current_count + 1

    # Nếu chưa đủ, lấy thêm không quan tâm diversity
    if len(final_tracks) < limit:
        remaining = [t for t in scored_tracks if create_track_result(t) not in final_tracks]
        for track_data in remaining[:limit - len(final_tracks)]:
            final_tracks.append(create_track_result(track_data))

    return final_tracks


def create_track_result(track_data):
    """Tạo kết quả track chuẩn hóa"""
    track = track_data['track']
    return {
        'trackId': track['trackId'],
        'trackName': track['trackName'],
        'artistName': track['artistName'],
        'primaryGenreName': track['primaryGenreName'],
        'score': track_data['score'],
        'popularity_score': track['popularity_score'],
        'recency_score': track['recency_score'],
        'avg_rating': track['avg_rating']
    }


# ===============================================
# HÀM CHÍNH - ĐIỂM VÀO CỦA HỆ THỐNG
# ===============================================

def get_genre_recommendations(user_id, limit_per_genre=10):
    """Hàm chính lấy recommendations - tự động xử lý cold start"""
    try:
        # Kiểm tra cold start
        if is_cold_start_user(user_id):
            print(f"🎯 User {user_id} là cold start")
            return get_cold_start_recommendations(user_id, limit_per_genre)

        # Xử lý regular user
        top_genres = get_user_top_genres(user_id)

        if not top_genres:
            return get_cold_start_recommendations(user_id, limit_per_genre)

        all_recommendations = []
        total_tracks = 0

        for genre in top_genres:
            genre_tracks = recommend_tracks_for_genre(user_id, genre, limit_per_genre)

            all_recommendations.append({
                'genre': genre,
                'tracks': genre_tracks,
                'track_count': len(genre_tracks)
            })
            total_tracks += len(genre_tracks)

        return {
            'user_id': user_id,
            'user_type': 'regular_user',
            'top_genres': top_genres,
            'recommendations': all_recommendations,
            'total_recommended_tracks': total_tracks
        }

    except Exception as e:
        print(f"❌ Lỗi trong get_genre_recommendations: {e}")
        # Fallback: dùng cold start
        return get_cold_start_recommendations(user_id, limit_per_genre)


# ===============================================
# HÀM HIỂN THỊ & TEST
# ===============================================

def display_recommendations(result):
    """Hiển thị kết quả recommendations"""
    if 'error' in result:
        print(f"❌ Lỗi: {result['error']}")
        return

    if not result['recommendations']:
        print("ℹ️ Không có recommendations nào.")
        return

    print(f"\n🎵 RECOMMENDATIONS CHO USER: {result['user_id']}")
    print("=" * 60)
    print(f"📊 User type: {result['user_type']}")
    print(f"🎯 Top genres: {', '.join(result['top_genres'])}")
    print(f"🎵 Tổng số bài hát: {result['total_recommended_tracks']}")
    if 'message' in result:
        print(f"💡 {result['message']}")
    print("=" * 60)

    for i, genre_rec in enumerate(result['recommendations'], 1):
        print(f"\n{i}. 🎼 GENRE: {genre_rec['genre']}")
        print(f"   📊 Số bài hát: {genre_rec['track_count']}")
        print("   " + "-" * 50)

        for j, track in enumerate(genre_rec['tracks'], 1):
            print(f"   {j:2d}. {track['trackName'][:40]:40} - {track['artistName'][:25]:25}")
            print(f"        ⭐ Score: {track['score']:.3f}")


if __name__ == "__main__":
    print("🎵 TESTING GENRE RECOMMENDATION SYSTEM")
    print("=" * 50)

    # Test với user cụ thể
    user_id = "113345"
    result = get_genre_recommendations(user_id)
    display_recommendations(result)

