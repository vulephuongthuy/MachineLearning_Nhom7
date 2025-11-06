
import pickle
import pandas as pd
from pymongo import MongoClient
from scipy.sparse import csr_matrix
import os

# --- KẾT NỐI DATABASE ---
client = MongoClient("mongodb://localhost:27017/")
db = client["moo_d"]

# --- TẢI MÔ HÌNH CF (đã train sẵn từ Colab) ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "models/model_artist.pkl")
pivot_path = os.path.join(base_dir, "models/pivot_artist.pkl")

try:
    model_artist = pickle.load(open(model_path, "rb"))
    pivot_artist = pickle.load(open(pivot_path, "rb"))
    pivot_sparse = csr_matrix(pivot_artist.values)
    print("Mô hình Recommended Artist đã sẵn sàng.")
except Exception as e:
    print("Lỗi khi tải model CF:", e)
    model_artist = pivot_artist = pivot_sparse = None


#  HÀM FALLBACK CHO USER MỚI
def get_popular_artists(top_n=10):
    """
    Dành cho user mới (chưa có lịch sử nghe)
    → Gợi ý nghệ sĩ được nghe nhiều nhất toàn hệ thống.
    """
    try:
        user_history = pd.DataFrame(list(db.user_history.find({}, {"artistName": 1, "_id": 0})))
        if user_history.empty:
            return []

        #SỬA: Đơn giản hóa logic tránh duplicate columns
        pop = (
            user_history["artistName"]
            .value_counts()
            .head(top_n)
            .reset_index()
        )
        # Đặt tên cột rõ ràng
        pop.columns = ["artist", "count"]
        pop["type"] = "Popular"

        return pop[["artist", "type"]].to_dict(orient="records")

    except Exception as e:
        print("Lỗi khi tạo fallback:", e)
        return []

#  HÀM GỢI Ý CHÍNH
def recommend_for_user(user_id, top_n=8, n_neighbors=60, months_back=3, verbose=False):
    """
    Gợi ý nghệ sĩ cho user dựa trên lịch sử nghe + CF + đa dạng hóa
    """
    try:
        if model_artist is None or pivot_artist is None:
            print("Model chưa được load.")
            return get_popular_artists(top_n)

        # Lấy dữ liệu từ MongoDB
        history_all = pd.DataFrame(list(db.user_history.find({}, {"userId": 1, "artistName": 1, "PlayCount": 1, "LastPlayedAt": 1, "_id": 0})))
        if history_all.empty:
            return get_popular_artists(top_n)

        history_all["LastPlayedAt"] = pd.to_datetime(history_all["LastPlayedAt"], errors="coerce")
        history_all = history_all.dropna(subset=["LastPlayedAt"])

        # Dữ liệu riêng của user
        user_hist = history_all[history_all["userId"] == str(user_id)]
        if user_hist.empty:
            if verbose: print(f"User {user_id} chưa có lịch sử nghe → fallback.")
            return get_popular_artists(top_n)

        # Phần 1: Lấy lịch sử 3 tháng gần nhất
        latest_date = user_hist["LastPlayedAt"].max()
        cutoff_date = latest_date - pd.DateOffset(months=months_back)
        recent_df = user_hist[user_hist["LastPlayedAt"] >= cutoff_date]
        if recent_df.empty:
            recent_df = user_hist

        top_recent_artists = recent_df["artistName"].value_counts().head(10).index.tolist()
        recent_artists_set = set(recent_df["artistName"].value_counts().head(50).index.tolist())

        if verbose:
            print(f"Top nghệ sĩ {user_id} nghe gần đây: {top_recent_artists}")

        # Phần 2: Candidate retrieval (CF-based)
        recs = []
        for idx, artist in enumerate(top_recent_artists[:3]):
            if artist not in pivot_artist.columns:
                continue
            idx_col = pivot_artist.columns.get_loc(artist)
            dist, ind = model_artist.kneighbors(pivot_sparse.T[idx_col], n_neighbors=n_neighbors + 1)
            weight = 1 - (idx * 0.15)
            for d, i in zip(dist[0][1:], ind[0][1:]):
                recs.append({"artist": pivot_artist.columns[i], "sim": 1 - d, "weight": weight})

        if not recs:
            if verbose: print(f"Không tạo được gợi ý cho user {user_id}.")
            return get_popular_artists(top_n)

        rec_df = pd.DataFrame(recs)
        rec_df["weighted_sim"] = rec_df["sim"] * rec_df["weight"]
        rec_df = rec_df.groupby("artist", as_index=False)["weighted_sim"].sum()

        # --- Phần 3: Tính trọng số đa dạng ---
        artist_freq = history_all["artistName"].value_counts(normalize=True)
        rec_df["global_freq"] = rec_df["artist"].map(artist_freq).fillna(0)
        rec_df["diversity_weight"] = 1 / (1 + 5 * rec_df["global_freq"])

        # Phần 4: Tính điểm tổng hợp ---
        rec_df["final_score"] = rec_df["weighted_sim"]
        rec_df["discovery_score"] = rec_df["final_score"] * rec_df["diversity_weight"]

        # Phần 5: Chia nhóm Quen / Mới
        top_recent_set = set(recent_df["artistName"].value_counts().head(10).index.tolist())

        # Lấy TOP top_n artists từ rec_df, KHÔNG phân chia familiar/new
        hybrid_df = rec_df.sort_values("final_score", ascending=False).head(top_n * 2)  # Lấy dư để filter

        # Gán type dựa trên có trong top_recent_set hay không
        hybrid_df["type"] = hybrid_df["artist"].apply(
            lambda a: " Familiar (CF)" if a in top_recent_set else "New (Diversity)"
        )

        # Đảm bảo có sự cân bằng (ít nhất 2-3 artists mới)
        familiar_count = sum(hybrid_df["type"] == " Familiar (CF)")
        new_count = sum(hybrid_df["type"] == " New (Diversity)")

        print(f" DEBUG: familiar_count: {familiar_count}, new_count: {new_count}")

        # ếu không đủ artists mới, điều chỉnh
        if new_count < 3 and len(rec_df) > top_n:
            # Lấy thêm artists mới từ phần còn lại của rec_df
            remaining_new = rec_df[~rec_df["artist"].isin(hybrid_df["artist"]) &
                                   ~rec_df["artist"].isin(top_recent_set)]
            remaining_new = remaining_new.sort_values("discovery_score", ascending=False).head(3 - new_count)

            if len(remaining_new) > 0:
                remaining_new["type"] = "New (Diversity)"
                hybrid_df = pd.concat([hybrid_df, remaining_new]).drop_duplicates("artist")
                hybrid_df = hybrid_df.sort_values("final_score", ascending=False).head(top_n)

        # Cắt chính xác top_n
        hybrid_df = hybrid_df.head(top_n)

        print(f"FINAL: Có {len(hybrid_df)} recommendations")
        for _, row in hybrid_df.iterrows():
            print(f"   - {row['artist']} ({row['type']})")

        return hybrid_df[["artist", "type", "final_score", "discovery_score"]].to_dict(orient="records")

        #  Phần 6: Gộp kết quả ---
        hybrid_df = pd.concat([familiar_candidates, new_candidates]).drop_duplicates("artist")
        hybrid_df["type"] = hybrid_df["artist"].apply(
            lambda a: " Familiar (CF)" if a in top_recent_set else " New (Diversity)"
        )

        hybrid_df = hybrid_df.sort_values("final_score", ascending=False).head(top_n)
        return hybrid_df[["artist", "type", "final_score", "discovery_score"]].to_dict(orient="records")

    except Exception as e:
        print(f"Lỗi khi tạo gợi ý cho user {user_id}: {e}")
        return get_popular_artists(top_n)