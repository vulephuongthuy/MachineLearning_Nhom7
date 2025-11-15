
# # recommendation_engine.py
import pickle
import numpy as np
import time
from collections import OrderedDict
#
#
# class ContentRecommendationEngine:
#     def __init__(self, model_path, tracks_db, purchases_db):
#         print("🔄 Loading CONTENT-BASED model with PURCHASE FILTER...")
#
#         # Load model từ file .pkl
#         with open(model_path, 'rb') as f:
#             self.model = pickle.load(f)
#
#         # Kết nối MongoDB
#         self.tracks_db = tracks_db
#         self.purchases_db = purchases_db  # Collection purchases
#
#         # Cache cho purchased tracks
#         self.purchase_cache = OrderedDict()
#         self.cache_max_size = 1000
#         self.cache_ttl = 300  # 5 minutes
#
#         print(f"✅ Content model loaded: {self.model['metadata']['similarity_coverage']}")
#
#     def get_user_purchased_tracks(self, user_id):
#         """Lấy danh sách track_id mà user đã mua từ collection purchases"""
#         # Kiểm tra cache trước
#         if user_id in self.purchase_cache:
#             cache_time, purchased_tracks = self.purchase_cache[user_id]
#             if time.time() - cache_time < self.cache_ttl:
#                 return purchased_tracks
#
#         # Query purchases collection
#         try:
#             purchases = self.purchases_db.find({"userId": user_id})
#             purchased_track_ids = set()
#
#             for purchase in purchases:
#                 track_id = purchase.get("trackId")
#                 if track_id:
#                     purchased_track_ids.add(track_id)
#
#             # Lưu vào cache
#             if len(self.purchase_cache) >= self.cache_max_size:
#                 self.purchase_cache.popitem(last=False)
#
#             self.purchase_cache[user_id] = (time.time(), purchased_track_ids)
#
#             print(f"📦 User {user_id} has {len(purchased_track_ids)} purchased tracks")
#             return purchased_track_ids
#
#         except Exception as e:
#             print(f"❌ Error getting user purchases: {e}")
#             return set()
#
#     def get_track_info(self, track_id):
#         """Lấy thông tin track từ MongoDB"""
#         try:
#             track = self.tracks_db.find_one({"trackId": track_id})
#             if track:
#                 return {
#                     'trackId': track_id,
#                     'trackName': track.get('trackName', 'Unknown'),
#                     'artistName': track.get('artistName', 'Unknown'),
#                     'genre': track.get('primaryGenreName', 'Unknown'),
#                     'artworkUrl100': track.get('artworkUrl100', ''),
#                     'trackTimeMillis': track.get('trackTimeMillis', 0)
#                 }
#             return None
#         except Exception as e:
#             print(f"❌ Error getting track info: {e}")
#             return None
#
#     def get_recommendations(self, current_track_id, user_mood, user_id, limit=8):
#         """Lấy recommendations - TỰ ĐỘNG LOẠI TRỪ BÀI ĐÃ MUA"""
#         print(f"🎯 Getting recommendations for user {user_id}...")
#
#         # Lấy danh sách bài đã mua
#         purchased_tracks = self.get_user_purchased_tracks(user_id)
#
#         # ƯU TIÊN FULL MATRIX
#         if current_track_id in self.model['similarity_dict']:
#             return self._get_from_full_matrix(current_track_id, user_mood, limit, purchased_tracks)
#         else:
#             print("⚠️ Track not in matrix, using cold start")
#             return self._get_cold_start_recommendations(user_mood, limit, purchased_tracks)
#
#     def _get_from_full_matrix(self, current_track_id, user_mood, limit, purchased_tracks):
#         """Từ full matrix - LOẠI TRỪ BÀI ĐÃ MUA"""
#         sim_data = self.model['similarity_dict'][current_track_id]
#
#         scored_tracks = []
#         purchased_count = 0
#
#         for i, similar_track_id in enumerate(sim_data['track_ids']):
#             # 🚨 QUAN TRỌNG: Skip nếu user đã mua bài này
#             if similar_track_id in purchased_tracks:
#                 purchased_count += 1
#                 continue
#
#             similarity_score = sim_data['similarities'][i]
#
#             # Kết hợp mood score
#             mood_score = self.model['mood_weights'].get(similar_track_id, {}).get(user_mood, 0.1)
#             total_score = similarity_score * 0.7 + mood_score * 0.3
#
#             if total_score > 0.1:
#                 track_info = self.get_track_info(similar_track_id)
#                 if track_info:
#                     scored_tracks.append({
#                         **track_info,
#                         'score': total_score,
#                         'reason': 'content_based'
#                     })
#
#             if len(scored_tracks) >= limit * 2:
#                 break
#
#         scored_tracks.sort(key=lambda x: x['score'], reverse=True)
#         result = scored_tracks[:limit]
#
#         print(f"✅ FULL-MATRIX: {len(result)} recs (filtered out {purchased_count} purchased tracks)")
#         return result
#
#     def _get_cold_start_recommendations(self, user_mood, limit, purchased_tracks):
#         """Cold start - LOẠI TRỪ BÀI ĐÃ MUA"""
#         try:
#             candidates = []
#             filtered_count = 0
#
#             # Popular tracks (loại trừ đã mua)
#             for track_id in self.model['popular_tracks'][:50]:
#                 if track_id not in purchased_tracks:
#                     candidates.append(track_id)
#                 else:
#                     filtered_count += 1
#                 if len(candidates) >= 30:
#                     break
#
#             # Mood tracks (loại trừ đã mua)
#             mood_candidates = []
#             for track_id, weights in list(self.model['mood_weights'].items())[:100]:
#                 if (track_id not in purchased_tracks and
#                         weights.get(user_mood, 0) > 0.3):
#                     mood_candidates.append(track_id)
#                 else:
#                     filtered_count += 1
#                 if len(mood_candidates) >= 20:
#                     break
#
#             candidates.extend(mood_candidates)
#
#             # Lấy track info và score
#             scored_tracks = []
#             for track_id in list(set(candidates))[:50]:
#                 track_info = self.get_track_info(track_id)
#                 if track_info:
#                     mood_score = self.model['mood_weights'].get(track_id, {}).get(user_mood, 0.1)
#                     popularity_score = 1.0 if track_id in self.model['popular_tracks'][:50] else 0.3
#                     total_score = mood_score * 0.7 + popularity_score * 0.3
#
#                     scored_tracks.append({
#                         **track_info,
#                         'score': total_score,
#                         'reason': 'cold_start'
#                     })
#
#             scored_tracks.sort(key=lambda x: x['score'], reverse=True)
#             result = scored_tracks[:limit]
#
#             print(f"✅ COLD-START: {len(result)} recs (filtered out {filtered_count} purchased tracks)")
#             return result
#
#         except Exception as e:
#             print(f"❌ Cold start error: {e}")
#             return []
#
#     def get_fallback_recommendations(self, user_id, limit=8):
#         """Fallback - LOẠI TRỪ BÀI ĐÃ MUA"""
#         try:
#             purchased_tracks = self.get_user_purchased_tracks(user_id)
#             fallback_tracks = []
#             filtered_count = 0
#
#             for track_id in self.model['popular_tracks']:
#                 if track_id in purchased_tracks:
#                     filtered_count += 1
#                     continue
#
#                 track_info = self.get_track_info(track_id)
#                 if track_info:
#                     fallback_tracks.append({
#                         **track_info,
#                         'score': 0.8,
#                         'reason': 'fallback'
#                     })
#
#                 if len(fallback_tracks) >= limit:
#                     break
#
#             print(f"🔄 FALLBACK: {len(fallback_tracks)} recs (filtered out {filtered_count} purchased tracks)")
#             return fallback_tracks[:limit]
#         except Exception as e:
#             print(f"❌ Fallback error: {e}")
#             return []
#
#     def invalidate_purchase_cache(self, user_id):
#         """Xóa cache khi user mua bài mới"""
#         if user_id in self.purchase_cache:
#             del self.purchase_cache[user_id]
#             print(f"🔄 Cleared purchase cache for user {user_id}")

class ContentRecommendationEngine:
    def __init__(self, model_path, tracks_db, purchases_db):
        print("🔄 Loading CONTENT-BASED model with PURCHASE FILTER + REAL-TIME...")

        # Load model từ file .pkl
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        # Kết nối MongoDB
        self.tracks_db = tracks_db
        self.purchases_db = purchases_db

        # Cache cho purchased tracks
        self.purchase_cache = OrderedDict()
        self.similarity_cache = OrderedDict()  # NEW: Cache cho real-time similarity
        self.cache_max_size = 1000
        self.cache_ttl = 300  # 5 minutes

        # Tạo indexes cho performance
        self._create_indexes()

        print(f"✅ Content model loaded: {self.model['metadata'].get('similarity_coverage', 'N/A')}")

    def _create_indexes(self):
        """Tạo index để tăng tốc query real-time"""
        try:
            self.tracks_db.create_index([("primaryGenreName", 1)])
            self.tracks_db.create_index([("artistName", 1)])
            self.tracks_db.create_index([("trackId", 1)])
            self.purchases_db.create_index([("userId", 1)])
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")

    def get_user_purchased_tracks(self, user_id):
        """Lấy danh sách track_id mà user đã mua - FIX QUERY"""
        user_id_str = str(user_id)

        # Kiểm tra cache trước
        if user_id_str in self.purchase_cache:
            cache_time, purchased_tracks = self.purchase_cache[user_id_str]
            if time.time() - cache_time < self.cache_ttl:
                return purchased_tracks

        # Query purchases collection - ĐẢM BẢO QUERY ĐÚNG
        try:
            # 🔥 QUERY VỚI STRING (vì database lưu string)
            purchases = list(self.purchases_db.find({"userId": user_id_str}))
            purchased_track_ids = set()

            for purchase in purchases:
                track_id = purchase.get("trackId")
                if track_id:
                    purchased_track_ids.add(track_id)

            print(f"🔍 [PURCHASE QUERY] Found {len(purchases)} purchases for user {user_id_str}")

            # Lưu vào cache
            if len(self.purchase_cache) >= self.cache_max_size:
                self.purchase_cache.popitem(last=False)

            self.purchase_cache[user_id_str] = (time.time(), purchased_track_ids)

            print(f"📦 User {user_id_str} has {len(purchased_track_ids)} purchased tracks")
            return purchased_track_ids

        except Exception as e:
            print(f"❌ Error getting user purchases: {e}")
            return set()
    def get_track_info(self, track_id):
        """Lấy thông tin track từ MongoDB"""
        try:
            track = self.tracks_db.find_one({"trackId": track_id})
            if track:
                return {
                    'trackId': track_id,
                    'trackName': track.get('trackName', 'Unknown'),
                    'artistName': track.get('artistName', 'Unknown'),
                    'genre': track.get('primaryGenreName', 'Unknown'),
                    'artworkUrl100': track.get('artworkUrl100', ''),
                    'trackTimeMillis': track.get('trackTimeMillis', 0),
                    'previewUrl': track.get('previewUrl', ''),
                    'popularity': track.get('popularity', 0)
                }
            return None
        except Exception as e:
            print(f"❌ Error getting track info: {e}")
            return None

    # def get_recommendations(self, current_track_id, user_mood, user_id, limit=8):
    #     """🎯 PHIÊN BẢN MỚI - Kết hợp pre-train + real-time + AUTO BLOCK PURCHASED"""
    #     print(f"🎯 Getting OPTIMIZED recommendations for user {user_id}...")
    #
    #     # Lấy danh sách bài đã mua (CƠ CHẾ CHẶN)
    #     purchased_tracks = self.get_user_purchased_tracks(user_id)
    #
    #     # 🚀 LAYER 1: Pre-trained model (SIÊU NHANH - ƯU TIÊN)
    #     if current_track_id in self.model['similarity_dict']:
    #         recs = self._get_from_full_matrix(current_track_id, user_mood, limit, purchased_tracks)
    #         if recs:
    #             print("✅ Used PRE-TRAINED model")
    #             return recs
    #
    #     # 🚀 LAYER 2: Real-time similarity từ MongoDB (CHO USER MỚI)
    #     recs = self._get_realtime_track_similarity(current_track_id, user_mood, limit, purchased_tracks)
    #     if recs:
    #         print("✅ Used REAL-TIME similarity")
    #         return recs
    #
    #     # 🚀 LAYER 3: Smart cold start
    #     print("✅ Used SMART COLD START")
    #     return self._get_smart_cold_start(user_id, user_mood, limit, purchased_tracks)

    def get_recommendations(self, current_track_id, user_mood, user_id, limit=8):
        """🎯 GIỮ NGUYÊN LAYER + FIX FILTER TRIỆT ĐỂ"""
        print(f"🎯 Getting OPTIMIZED recommendations for user {user_id}...")

        # 🔥 LUÔN CLEAR CACHE trước khi lấy purchased tracks
        user_id_str = str(user_id)
        if user_id_str in self.purchase_cache:
            del self.purchase_cache[user_id_str]
            print(f"🔄 [CACHE] Force cleared cache for user {user_id_str}")

        # Lấy danh sách bài đã mua (MỚI NHẤT)
        purchased_tracks = self.get_user_purchased_tracks(user_id)
        print(f"🔍 [MAIN] Purchased tracks: {len(purchased_tracks)}")

        # 🚀 LAYER 1: Pre-trained model
        if current_track_id in self.model['similarity_dict']:
            recs = self._get_from_full_matrix(current_track_id, user_mood, limit * 3, purchased_tracks)
            if recs:
                print("✅ Used PRE-TRAINED model")
                # 🔥 FILTER CUỐI CÙNG - BẮT BUỘC
                final_recs = self._force_purchase_filter(recs, purchased_tracks, limit)
                return final_recs

        # 🚀 LAYER 2: Real-time similarity
        recs = self._get_realtime_track_similarity(current_track_id, user_mood, limit * 3, purchased_tracks)
        if recs:
            print("✅ Used REAL-TIME similarity")
            # 🔥 FILTER CUỐI CÙNG - BẮT BUỘC
            final_recs = self._force_purchase_filter(recs, purchased_tracks, limit)
            return final_recs

        # 🚀 LAYER 3: Smart cold start
        print("✅ Used SMART COLD START")
        recs = self._get_smart_cold_start(user_id, user_mood, limit * 3, purchased_tracks)
        # 🔥 FILTER CUỐI CÙNG - BẮT BUỘC
        final_recs = self._force_purchase_filter(recs, purchased_tracks, limit)
        return final_recs

    def _force_purchase_filter(self, recommendations, purchased_tracks, limit):
        """🔒 FILTER BẮT BUỘC - ĐẢM BẢO KHÔNG CÓ BÀI ĐÃ MUA"""
        if not recommendations:
            return []

        final_recommendations = []
        removed_count = 0

        print(f"🔒 [FORCE FILTER] Checking {len(recommendations)} recommendations...")

        for track in recommendations:
            if track['trackId'] in purchased_tracks:
                removed_count += 1
                print(f"🚫 [FORCE FILTER] REMOVED: {track['trackName']} - {track['artistName']}")
                continue
            final_recommendations.append(track)

        print(f"🔒 [FORCE FILTER] Removed {removed_count} purchased tracks, {len(final_recommendations)} remaining")

        return final_recommendations[:limit]


    # def _get_from_full_matrix(self, current_track_id, user_mood, limit, purchased_tracks):
    #     """NATURAL BALANCE: Phân bố artist tự nhiên (3-2-1-2, 2-3-2-1, etc.)"""
    #     sim_data = self.model['similarity_dict'][current_track_id]
    #
    #     scored_tracks = []
    #     purchased_count = 0
    #
    #     # Convert numpy array sang list nếu cần
    #     original_similarities = sim_data['similarities']
    #     if hasattr(original_similarities, 'tolist'):
    #         original_similarities = original_similarities.tolist()
    #
    #     # Dùng rank-based scoring
    #     for i, similar_track_id in enumerate(sim_data['track_ids']):
    #         if similar_track_id in purchased_tracks:
    #             purchased_count += 1
    #             continue
    #
    #         # Rank-based score
    #         rank_score = 0.9 - (i * 0.02)  # Giảm rất chậm
    #         if rank_score < 0.6:
    #             rank_score = 0.6
    #
    #         mood_score = self.model['mood_weights'].get(similar_track_id, {}).get(user_mood, 0.1)
    #         total_score = rank_score * 0.7 + mood_score * 0.3
    #
    #         if total_score > 0.1:
    #             track_info = self.get_track_info(similar_track_id)
    #             if track_info:
    #                 scored_tracks.append({
    #                     **track_info,
    #                     'score': total_score,
    #                     'reason': 'content_based_natural'
    #                 })
    #
    #         if len(scored_tracks) >= 150:  # Lấy nhiều hơn để có lựa chọn
    #             break
    #
    #     # Phân tích artist distribution
    #     scored_tracks.sort(key=lambda x: x['score'], reverse=True)
    #
    #     artist_tracks = {}
    #     for track in scored_tracks:
    #         artist = track['artistName']
    #         if artist not in artist_tracks:
    #             artist_tracks[artist] = []
    #         artist_tracks[artist].append(track)
    #
    #     # Sắp xếp artists theo số lượng tracks
    #     artists_by_track_count = sorted(artist_tracks.keys(),
    #                                     key=lambda x: len(artist_tracks[x]),
    #                                     reverse=True)
    #
    #     final_results = []
    #     artist_count = {}
    #
    #     # 🆕 FIX: Tạo phân bố tự nhiên (randomized distribution)
    #     import random
    #
    #     # Các pattern phân bố tự nhiên
    #     natural_patterns = [
    #         [3, 2, 2, 1],  # 3-2-2-1
    #         [3, 3, 1, 1],  # 3-3-1-1
    #         [2, 2, 2, 2],  # 2-2-2-2
    #         [3, 2, 1, 2],  # 3-2-1-2
    #         [2, 3, 2, 1],  # 2-3-2-1
    #         [4, 2, 1, 1],  # 4-2-1-1
    #         [2, 2, 3, 1],  # 2-2-3-1
    #     ]
    #
    #     # Chọn pattern ngẫu nhiên
    #     selected_pattern = random.choice(natural_patterns)
    #     target_artists_count = len(selected_pattern)
    #
    #     print(f"   🎯 Selected pattern: {selected_pattern}")
    #
    #     # Bước 1: Lấy tracks theo pattern đã chọn
    #     artists_used = []
    #
    #     for i, track_count in enumerate(selected_pattern):
    #         if len(final_results) >= limit:
    #             break
    #
    #         # Tìm artist phù hợp
    #         suitable_artist = None
    #         for artist in artists_by_track_count:
    #             if artist in artists_used:
    #                 continue
    #             if len(artist_tracks[artist]) >= track_count:
    #                 suitable_artist = artist
    #                 break
    #
    #         if suitable_artist:
    #             artists_used.append(suitable_artist)
    #             tracks = artist_tracks[suitable_artist]
    #             # Lấy số tracks theo pattern
    #             for j in range(min(track_count, len(tracks))):
    #                 if len(final_results) < limit and j < len(tracks):
    #                     track = tracks[j]
    #                     final_results.append(track)
    #                     artist_count[suitable_artist] = artist_count.get(suitable_artist, 0) + 1
    #
    #     # Bước 2: Nếu chưa đủ, lấy thêm từ artists đã có (tăng số tracks)
    #     if len(final_results) < limit:
    #         for artist in artists_used:
    #             if len(final_results) >= limit:
    #                 break
    #             current_count = artist_count.get(artist, 0)
    #             available_tracks = [t for t in artist_tracks[artist] if t not in final_results]
    #             if available_tracks:
    #                 track = available_tracks[0]
    #                 final_results.append(track)
    #                 artist_count[artist] = current_count + 1
    #
    #     # Bước 3: Nếu vẫn chưa đủ, lấy từ artists mới
    #     if len(final_results) < limit:
    #         for artist in artists_by_track_count:
    #             if len(final_results) >= limit:
    #                 break
    #             if artist not in artists_used:
    #                 tracks = artist_tracks[artist]
    #                 if tracks:
    #                     track = tracks[0]
    #                     final_results.append(track)
    #                     artist_count[artist] = 1
    #                     artists_used.append(artist)
    #
    #     # Tính genres
    #     genre_count = {}
    #     for track in final_results:
    #         genre = track['genre']
    #         genre_count[genre] = genre_count.get(genre, 0) + 1
    #
    #     print(f"✅ NATURAL-BALANCE: {len(final_results)} recs, {len(artist_count)} artists, {len(genre_count)} genres")
    #
    #     # Hiển thị phân bố artist chi tiết
    #     distribution = {}
    #     for artist, count in artist_count.items():
    #         distribution[artist] = count
    #
    #     print(f"   🎵 Distribution: {distribution}")
    #
    #     return final_results[:limit]

    def _get_from_full_matrix(self, current_track_id, user_mood, limit, purchased_tracks):
        """NATURAL BALANCE với DOUBLE FILTER"""
        sim_data = self.model['similarity_dict'][current_track_id]

        scored_tracks = []
        purchased_count = 0

        # 🔥 DEBUG: Kiểm tra purchased tracks
        print(f"🔍 [FILTER ANALYSIS] Purchased tracks: {len(purchased_tracks)}")

        # VÒNG LẶP CHÍNH VỚI FILTER
        for i, similar_track_id in enumerate(sim_data['track_ids']):
            if i >= 150:  # Giới hạn xử lý
                break

            # FILTER 1: Trong vòng lặp chính
            if similar_track_id in purchased_tracks:
                purchased_count += 1
                track_info = self.get_track_info(similar_track_id)
                if track_info:
                    print(f"🚫 [IN-LOOP FILTER] {track_info['trackName']} - {track_info['artistName']}")
                continue

            # Rank-based score
            rank_score = 0.9 - (i * 0.02)
            if rank_score < 0.6:
                rank_score = 0.6

            mood_score = self.model['mood_weights'].get(similar_track_id, {}).get(user_mood, 0.1)
            total_score = rank_score * 0.7 + mood_score * 0.3

            if total_score > 0.1:
                track_info = self.get_track_info(similar_track_id)
                if track_info:
                    scored_tracks.append({
                        **track_info,
                        'score': total_score,
                        'reason': 'content_based_natural'
                    })

            if len(scored_tracks) >= limit * 2:  # Lấy nhiều hơn để final filter
                break

        print(f"🔍 [IN-LOOP FILTER] Filtered {purchased_count} tracks, {len(scored_tracks)} remaining")

        # Phân bố artist (giữ nguyên logic cũ)
        scored_tracks.sort(key=lambda x: x['score'], reverse=True)

        artist_tracks = {}
        for track in scored_tracks:
            artist = track['artistName']
            if artist not in artist_tracks:
                artist_tracks[artist] = []
            artist_tracks[artist].append(track)

        artists_by_track_count = sorted(artist_tracks.keys(),
                                        key=lambda x: len(artist_tracks[x]),
                                        reverse=True)

        final_results = []
        artist_count = {}

        import random
        natural_patterns = [
            [3, 2, 2, 1], [3, 3, 1, 1], [2, 2, 2, 2],
            [3, 2, 1, 2], [2, 3, 2, 1], [4, 2, 1, 1], [2, 2, 3, 1],
        ]

        selected_pattern = random.choice(natural_patterns)
        print(f"   🎯 Selected pattern: {selected_pattern}")

        # Bước 1: Lấy tracks theo pattern
        artists_used = []
        for i, track_count in enumerate(selected_pattern):
            if len(final_results) >= limit:
                break

            suitable_artist = None
            for artist in artists_by_track_count:
                if artist in artists_used:
                    continue
                if len(artist_tracks[artist]) >= track_count:
                    suitable_artist = artist
                    break

            if suitable_artist:
                artists_used.append(suitable_artist)
                tracks = artist_tracks[suitable_artist]
                for j in range(min(track_count, len(tracks))):
                    if len(final_results) < limit and j < len(tracks):
                        track = tracks[j]
                        final_results.append(track)
                        artist_count[suitable_artist] = artist_count.get(suitable_artist, 0) + 1

        # Bước 2: Lấy thêm nếu chưa đủ
        if len(final_results) < limit:
            for artist in artists_used:
                if len(final_results) >= limit:
                    break
                available_tracks = [t for t in artist_tracks[artist] if t not in final_results]
                if available_tracks:
                    track = available_tracks[0]
                    final_results.append(track)
                    artist_count[artist] = artist_count.get(artist, 0) + 1

        # Bước 3: Lấy từ artists mới
        if len(final_results) < limit:
            for artist in artists_by_track_count:
                if len(final_results) >= limit:
                    break
                if artist not in artists_used:
                    tracks = artist_tracks[artist]
                    if tracks:
                        track = tracks[0]
                        final_results.append(track)
                        artist_count[artist] = 1
                        artists_used.append(artist)

        print(f"✅ NATURAL-BALANCE: {len(final_results)} recs, {len(artist_count)} artists")
        print(f"   🎵 Distribution: {artist_count}")

        return final_results

    def _get_realtime_track_similarity(self, current_track_id, user_mood, limit, purchased_tracks):
        """FIXED: Real-time similarity với diversity"""

        cache_key = f"similar_{current_track_id}"
        if cache_key in self.similarity_cache:
            cached_time, cached_results = self.similarity_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_results

        try:
            current_track = self.tracks_db.find_one(
                {"trackId": current_track_id},
                {'primaryGenreName': 1, 'artistName': 1, 'trackName': 1}
            )

            if not current_track:
                return None

            current_genre = current_track.get('primaryGenreName', '')
            current_artist = current_track.get('artistName', '')

            if not current_genre:
                return None

            # 🚨 FIX: Tìm đa dạng genres hơn
            related_genres = self._get_related_genres(current_genre)

            query = {
                "$or": [
                    {"primaryGenreName": current_genre},
                    {"primaryGenreName": {"$in": related_genres}},
                    {"artistName": current_artist}
                ],
                "trackId": {"$ne": current_track_id}
            }

            if purchased_tracks:
                query["trackId"]["$nin"] = list(purchased_tracks)

            similar_tracks_cursor = self.tracks_db.find(query).limit(limit * 5)  # Lấy nhiều hơn

            # 🚨 FIX: Scoring đa dạng hơn
            scored_tracks = []
            selected_artists = set()
            selected_genres = set()

            for track in similar_tracks_cursor:
                track_id = track['trackId']

                # Tính score đa dạng
                score = 0.3  # Base score thấp hơn

                # Bonus cho cùng genre chính
                if track.get('primaryGenreName') == current_genre:
                    score += 0.3
                # Bonus cho related genres
                elif track.get('primaryGenreName') in related_genres:
                    score += 0.2

                # Bonus cho cùng artist
                if track.get('artistName') == current_artist:
                    score += 0.2

                # Bonus cho popularity
                popularity = track.get('popularity', 0) or 0
                score += min(popularity / 200, 0.2)  # Giảm weight popularity

                # Bonus diversity
                artist = track.get('artistName', '')
                genre = track.get('primaryGenreName', '')

                if artist not in selected_artists:
                    score += 0.1
                if genre not in selected_genres:
                    score += 0.05

                # Mood score
                mood_score = self.model['mood_weights'].get(track_id, {}).get(user_mood, 0.1)
                score += mood_score * 0.1

                track_info = self.get_track_info(track_id)
                if track_info:
                    scored_tracks.append({
                        **track_info,
                        'score': score,
                        'reason': 'real_time_diverse'
                    })
                    selected_artists.add(artist)
                    selected_genres.add(genre)

            # Diversity-aware selection
            scored_tracks.sort(key=lambda x: x['score'], reverse=True)

            # Lấy đa dạng
            final_results = []
            final_artists = set()
            final_genres = set()

            for track in scored_tracks:
                if len(final_results) >= limit:
                    break
                artist = track['artistName']
                genre = track['genre']

                if len(final_results) < limit // 2 or artist not in final_artists or genre not in final_genres:
                    final_results.append(track)
                    final_artists.add(artist)
                    final_genres.add(genre)

            # Cache
            if len(self.similarity_cache) >= self.cache_max_size:
                self.similarity_cache.popitem(last=False)
            self.similarity_cache[cache_key] = (time.time(), final_results)

            print(
                f"🎯 REAL-TIME-FIXED: {len(final_results)} recs, {len(final_artists)} artists, {len(final_genres)} genres")
            return final_results

        except Exception as e:
            print(f"❌ Real-time similarity error: {e}")
            return None

    def _get_related_genres(self, genre):
        """Lấy các genres liên quan"""
        genre_groups = {
            'Hip-Hop/Rap': ['R&B/Soul', 'Pop', 'Electronic'],
            'Pop': ['Dance', 'R&B/Soul', 'Rock'],
            'Rock': ['Alternative', 'Metal', 'Indie'],
            'Electronic': ['Dance', 'House', 'Techno'],
            'Alternative': ['Indie', 'Rock', 'Pop'],
            'R&B/Soul': ['Hip-Hop/Rap', 'Pop', 'Jazz']
        }
        return genre_groups.get(genre, [])

    def _get_smart_cold_start(self, user_id, user_mood, limit, purchased_tracks):
        """🎯 NEW: Cold start thông minh - kết hợp purchased tracks analysis"""
        try:
            candidates = []

            # Phân tích genre từ các bài đã mua
            purchased_genres = set()
            for track_id in purchased_tracks:
                track = self.tracks_db.find_one(
                    {"trackId": track_id},
                    {'primaryGenreName': 1}
                )
                if track and track.get('primaryGenreName'):
                    purchased_genres.add(track.get('primaryGenreName'))

            # Ưu tiên 1: Tracks cùng genre với purchased tracks
            if purchased_genres:
                genre_tracks = self.tracks_db.find({
                    "primaryGenreName": {"$in": list(purchased_genres)},
                    "trackId": {"$nin": list(purchased_tracks)}
                }).limit(limit)

                for track in genre_tracks:
                    track_info = self.get_track_info(track['trackId'])
                    if track_info:
                        candidates.append({
                            **track_info,
                            'score': 0.8,  # High score for same genre
                            'reason': 'similar_to_purchased'
                        })

            # Ưu tiên 2: Mood-based từ pre-trained model
            mood_candidates = []
            for track_id, weights in list(self.model['mood_weights'].items())[:50]:
                if (track_id not in purchased_tracks and
                        weights.get(user_mood, 0) > 0.5):
                    track_info = self.get_track_info(track_id)
                    if track_info:
                        mood_candidates.append({
                            **track_info,
                            'score': weights.get(user_mood, 0),
                            'reason': 'mood_match'
                        })
                if len(mood_candidates) >= 10:
                    break

            candidates.extend(mood_candidates)

            # Ưu tiên 3: Popular tracks (fallback)
            if len(candidates) < limit:
                for track_id in self.model['popular_tracks'][:30]:
                    if track_id not in purchased_tracks:
                        track_info = self.get_track_info(track_id)
                        if track_info:
                            candidates.append({
                                **track_info,
                                'score': 0.6,
                                'reason': 'popular'
                            })
                    if len(candidates) >= limit:
                        break

            # Remove duplicates và sort
            unique_candidates = {}
            for candidate in candidates:
                if candidate['trackId'] not in unique_candidates:
                    unique_candidates[candidate['trackId']] = candidate

            final_candidates = list(unique_candidates.values())
            final_candidates.sort(key=lambda x: x['score'], reverse=True)

            result = final_candidates[:limit]
            print(f"🎯 SMART-COLD: {len(result)} recs (analyzed {len(purchased_genres)} purchased genres)")
            return result

        except Exception as e:
            print(f"❌ Smart cold start error: {e}")
            return self._get_cold_start_recommendations(user_mood, limit, purchased_tracks)

    def _get_cold_start_recommendations(self, user_mood, limit, purchased_tracks):
        """Cold start gốc (dự phòng)"""
        try:
            candidates = []
            filtered_count = 0

            # Popular tracks (loại trừ đã mua)
            for track_id in self.model['popular_tracks'][:50]:
                if track_id not in purchased_tracks:
                    candidates.append(track_id)
                else:
                    filtered_count += 1
                if len(candidates) >= 30:
                    break

            # Mood tracks (loại trừ đã mua)
            mood_candidates = []
            for track_id, weights in list(self.model['mood_weights'].items())[:100]:
                if (track_id not in purchased_tracks and
                        weights.get(user_mood, 0) > 0.3):
                    mood_candidates.append(track_id)
                else:
                    filtered_count += 1
                if len(mood_candidates) >= 20:
                    break

            candidates.extend(mood_candidates)

            # Lấy track info và score
            scored_tracks = []
            for track_id in list(set(candidates))[:50]:
                track_info = self.get_track_info(track_id)
                if track_info:
                    mood_score = self.model['mood_weights'].get(track_id, {}).get(user_mood, 0.1)
                    popularity_score = 1.0 if track_id in self.model['popular_tracks'][:50] else 0.3
                    total_score = mood_score * 0.7 + popularity_score * 0.3

                    scored_tracks.append({
                        **track_info,
                        'score': total_score,
                        'reason': 'cold_start'
                    })

            scored_tracks.sort(key=lambda x: x['score'], reverse=True)
            result = scored_tracks[:limit]

            print(f"✅ COLD-START: {len(result)} recs (filtered out {filtered_count} purchased tracks)")
            return result

        except Exception as e:
            print(f"❌ Cold start error: {e}")
            return []

    def get_fallback_recommendations(self, user_id, limit=8):
        """Fallback - LOẠI TRỪ BÀI ĐÃ MUA"""
        try:
            purchased_tracks = self.get_user_purchased_tracks(user_id)
            fallback_tracks = []
            filtered_count = 0

            for track_id in self.model['popular_tracks']:
                if track_id in purchased_tracks:
                    filtered_count += 1
                    continue

                track_info = self.get_track_info(track_id)
                if track_info:
                    fallback_tracks.append({
                        **track_info,
                        'score': 0.8,
                        'reason': 'fallback'
                    })

                if len(fallback_tracks) >= limit:
                    break

            print(f"🔄 FALLBACK: {len(fallback_tracks)} recs (filtered out {filtered_count} purchased tracks)")
            return fallback_tracks[:limit]
        except Exception as e:
            print(f"❌ Fallback error: {e}")
            return []

    def invalidate_purchase_cache(self, user_id):
        """Xóa cache khi user mua bài mới - MẠNH MẼ HƠN"""
        user_id_str = str(user_id)

        print(f"🔄 [CACHE INVALIDATE] BEFORE: {list(self.purchase_cache.keys())}")

        # 🔥 XÓA TẤT CẢ CACHE LIÊN QUAN
        if user_id_str in self.purchase_cache:
            del self.purchase_cache[user_id_str]
            print(f"🔄 [CACHE INVALIDATE] Cleared purchase cache for user {user_id_str}")

        # 🔥 XÓA SIMILARITY CACHE
        keys_to_remove = [key for key in self.similarity_cache.keys() if f"similar_" in key]
        for key in keys_to_remove:
            del self.similarity_cache[key]

        print(f"🔄 [CACHE INVALIDATE] Cleared {len(keys_to_remove)} similarity cache entries")

        print(f"🔄 [CACHE INVALIDATE] AFTER: {list(self.purchase_cache.keys())}")