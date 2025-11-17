import os
import pickle
from typing import List, Dict, Any

import pandas as pd
from pymongo import MongoClient
from scipy.sparse import csr_matrix


# KẾT NỐI DB & TẢI MODEL
client = MongoClient("mongodb://localhost:27017/")
db = client["moo_d"]

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "../models/model_artist.pkl")
pivot_path = os.path.join(base_dir, "../models/pivot_artist.pkl")

try:
    model_artist = pickle.load(open(model_path, "rb"))
    pivot_artist: pd.DataFrame = pickle.load(open(pivot_path, "rb"))  # pivot rows=user, cols=artist
    pivot_sparse = csr_matrix(pivot_artist.values)
    print("Mô hình Recommended Artist đã sẵn sàng.")
except Exception as e:
    print("Lỗi khi tải model CF:", e)
    model_artist = None
    pivot_artist = None
    pivot_sparse = None


#  TIỆN ÍCH
def _safe_to_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        df = df.dropna(subset=[col])
    return df


def get_popular_artists(top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Fallback chung hệ thống: Top-N nghệ sĩ xuất hiện nhiều nhất trong user_history.
    Trả về list dict: {"artist": str, "type": "Popular"}
    """
    try:
        user_history = pd.DataFrame(
            list(db.user_history.find({}, {"artistName": 1, "_id": 0}))
        )
        if user_history.empty:
            return []

        pop = (
            user_history["artistName"]
            .value_counts()
            .head(top_n)
            .reset_index()
        )
        pop.columns = ["artist", "count"]
        pop["type"] = "Popular"
        return pop[["artist", "type"]].to_dict(orient="records")
    except Exception as e:
        print("Lỗi khi tạo fallback Popular:", e)
        return []


#CORE RECOMMENDER
def recommend_for_user(user_id, top_n=8, n_neighbors=60, months_back=3, verbose=False):
    try:
        if model_artist is None or pivot_artist is None:
            return get_popular_artists(top_n)
        # --- LOAD USER HISTORY ---
        user_hist = pd.DataFrame(list(db.user_history.find(
            {"userId": str(user_id)},
            {"artistName": 1, "PlayCount": 1, "LastPlayedAt": 1, "_id": 0}
        )))
        if user_hist.empty:
            return get_popular_artists(top_n)

        user_hist["LastPlayedAt"] = pd.to_datetime(user_hist["LastPlayedAt"], errors="coerce")
        user_hist = user_hist.dropna(subset=["LastPlayedAt"])
        history_count = len(user_hist)

        # Determine listener level
        if history_count >= 200:
            mode = "heavy"
        elif history_count >= 50:
            mode = "medium"
        else:
            mode = "light"

        # --- RECENT LISTENING WINDOW ---
        latest_date = user_hist["LastPlayedAt"].max()
        cutoff_date = latest_date - pd.DateOffset(months=months_back)
        recent_df = user_hist[user_hist["LastPlayedAt"] >= cutoff_date]
        if recent_df.empty:
            recent_df = user_hist
        top_recent_artists = recent_df["artistName"].value_counts().head(10).index.tolist()

        # --- CF SIMILARITY RETRIEVAL ---
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
            return get_popular_artists(top_n)

        rec_df = pd.DataFrame(recs).groupby("artist", as_index=False)["weight"].sum()
        rec_df.rename(columns={"weight": "final_score"}, inplace=True)

        # --- DIVERSITY WEIGHT ---
        history_all = pd.DataFrame(list(db.user_history.find({}, {"artistName": 1, "_id": 0})))
        artist_freq = history_all["artistName"].value_counts(normalize=True)
        rec_df["global_freq"] = rec_df["artist"].map(artist_freq).fillna(0)
        rec_df["discovery_score"] = rec_df["final_score"] / (1 + 5 * rec_df["global_freq"])

        listened_ever = set(user_hist["artistName"].unique())

        # Familiar (đã nghe, hợp gu)
        familiar = rec_df[rec_df["artist"].isin(listened_ever)].sort_values("final_score", ascending=False)

        # Re-discover (từng nghe nhiều + lâu không nghe)
        play_count = user_hist.groupby("artistName")["PlayCount"].sum()
        last_play = user_hist.groupby("artistName")["LastPlayedAt"].max()
        rediscover_score = (latest_date - last_play).dt.days * play_count
        rediscover = (rec_df[rec_df["artist"].isin(rediscover_score.index)]
                      .assign(rd=lambda x: x["artist"].map(rediscover_score))
                      .sort_values("rd", ascending=False))

        # New diversity
        new_div = rec_df[~rec_df["artist"].isin(listened_ever)].sort_values("discovery_score", ascending=False)

        # ================== APPLY STRATEGY ==================
        if mode == "heavy":
            selected = pd.concat([familiar.head(5), rediscover.head(3)])

        elif mode == "medium":
            selected = pd.concat([familiar.head(4), rediscover.head(2), new_div.head(2)])

        else:  # light user
            pop = pd.DataFrame(get_popular_artists(50))
            # 3 familiar + 5 popular/diversity
            f = familiar.head(3)

            # 5 từ phổ biến (để đảm bảo dễ nghe, không shock gu)
            p = pop[~pop["artist"].isin(f["artist"])].head(5)
            selected = pd.concat([f, p])
            # NEW: EP FILL ĐỦ 8 NGƯỜI
            if len(selected) < 8:
                need = 8 - len(selected)

                # chọn từ new diversity
                fill = new_div[~new_div["artist"].isin(selected["artist"])].head(need)
                selected = pd.concat([selected, fill])

            # nếu vẫn thiếu → fallback toàn hệ thống
            if len(selected) < 8:
                need = 8 - len(selected)
                extra_pop = pop[~pop["artist"].isin(selected["artist"])].head(need)
                selected = pd.concat([selected, extra_pop])

        # Drop trùng và giữ đúng số lượng
        selected = selected.drop_duplicates("artist").head(top_n)

        # Assign type label
        selected["type"] = selected["artist"].apply(lambda a:
            "Familiar (CF)" if a in familiar["artist"].values else
            "Re-discover (Long time no listen)" if a in rediscover["artist"].values else
            "New (Exploration)"
        )

        result = selected[["artist", "type"]].to_dict(orient="records")

        # DEBUG LOG
        print(f"\n🎧 USER {user_id} • Mode: {mode.upper()} • {history_count} plays")
        print("→ Final Output:", result, "\n")

        return result

    except Exception as e:
        print(f"Lỗi recommend_for_user({user_id}): {e}")
        return get_popular_artists(top_n)
