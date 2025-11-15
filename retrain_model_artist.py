import pandas as pd
import numpy as np
from pymongo import MongoClient
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import pickle
import os

# ===================== CONFIG =====================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "moo_d"
MODEL_DIR = "models"
MODEL_FILE = "model_artist.pkl"
PIVOT_FILE = "pivot_artist.pkl"
# ==================================================

print("🔄 Kết nối MongoDB...")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# 1) LOAD DATA
print("📥 Đang tải user_history & user_favorite & tracks...")
user_history = pd.DataFrame(list(db.user_history.find({}, {
    "userId": 1, "artistName": 1, "PlayCount": 1,
    "LastPlayedAt": 1, "_id": 0
})))

user_favorite = pd.DataFrame(list(db.user_favorite.find({}, {
    "userId": 1, "artistName": 1, "_id": 0
})))

tracks = pd.DataFrame(list(db.tracks.find({}, {
    "artistName": 1, "popularity": 1, "_id": 0
})))

if user_history.empty:
    print("❌ Không có dữ liệu user_history → Dừng retrain.")
    exit()

# 2) FIX DATA TYPE
user_history["userId"] = user_history["userId"].astype(str)
user_favorite["userId"] = user_favorite["userId"].astype(str)

print("⏳ Chuẩn hoá LastPlayedAt...")
user_history["LastPlayedAt"] = pd.to_datetime(user_history["LastPlayedAt"], errors="coerce")
user_history = user_history.dropna(subset=["LastPlayedAt"])

# 3) TRAIN = 80% cũ nhất, TEST = 20% mới nhất
print("✂️ Chia dữ liệu theo thời gian...")
user_history = user_history.sort_values(by=["userId", "LastPlayedAt"])
user_history["rank"] = user_history.groupby("userId")["LastPlayedAt"].rank()
user_max = user_history.groupby("userId")["rank"].max()
user_history["cutoff"] = user_history["userId"].map(user_max * 0.8)

history_train = user_history[user_history["rank"] <= user_history["cutoff"]].copy()
fav_train = user_favorite.copy()

# 4) RECENCY WEIGHT
print("🎧 Tính Recency Weight + WeightedPlay...")
latest = history_train["LastPlayedAt"].max()
history_train["RecencyWeight"] = history_train["LastPlayedAt"].apply(
    lambda x: np.exp(-((latest - x).days / 90))
)

hist_weighted = (
    history_train.groupby(["userId", "artistName"])
    .apply(lambda df: (df["PlayCount"] * df["RecencyWeight"]).sum())
    .reset_index(name="WeightedPlay")
)

# 5) FAVORITE COUNT
fav_count = fav_train.groupby(["userId", "artistName"]).size().reset_index(name="favCount")

# 6) MERGE
user_artist = pd.merge(hist_weighted, fav_count, on=["userId", "artistName"], how="outer").fillna(0)

# 7) POPULARITY WEIGHT
pop_mean = tracks.groupby("artistName")["popularity"].mean().reset_index()
user_artist = pd.merge(user_artist, pop_mean, on="artistName", how="left").fillna(0)
user_artist["popularity_norm"] = user_artist["popularity"] / max(user_artist["popularity"].max(), 1)

# 8) FINAL SCORE
user_artist["score"] = user_artist["WeightedPlay"] + 2 * user_artist["favCount"]
user_artist["final_score"] = user_artist["score"] / (1 + user_artist["popularity_norm"] ** 1.2)

print(f"✅ Feature engineering hoàn tất: {len(user_artist)} dòng.")

# 9) PIVOT MATRIX
pivot = user_artist.pivot(index="userId", columns="artistName", values="final_score").fillna(0)
pivot_sparse = csr_matrix(pivot.values)

# 10) TRAIN MODEL (COSINE KNN)
print("🤖 Đang huấn luyện KNN-CF...")
model = NearestNeighbors(metric='cosine', algorithm='brute')
model.fit(pivot_sparse.T)

# 11) SAVE MODEL
os.makedirs(MODEL_DIR, exist_ok=True)
pickle.dump(model, open(f"{MODEL_DIR}/{MODEL_FILE}", "wb"))
pickle.dump(pivot, open(f"{MODEL_DIR}/{PIVOT_FILE}", "wb"))

print("\n🎉 Retrain hoàn tất!")
print(f"📦 model → {MODEL_DIR}/{MODEL_FILE}")
print(f"📦 pivot → {MODEL_DIR}/{PIVOT_FILE}")
