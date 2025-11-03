import requests
import json
import time

BASE_URL = "https://itunes.apple.com/lookup"

# Đọc danh sách nghệ sĩ từ file JSON
with open("data/artists_with_ids.json", "r", encoding="utf-8") as f:
    artists = json.load(f)

all_collections = []
all_tracks = []

for artist in artists:
    artist_id = artist["artistId"]
    artist_name = artist["artistName"]
    print(f"▶ Fetching collections for {artist_name} ({artist_id})")

    # Step 1: Lấy tất cả collection (album/ep/single) của nghệ sĩ
    resp = requests.get(BASE_URL, params={
        "id": artist_id,
        "entity": "album",
        "limit": 10
    })
    data = resp.json()

    if "results" not in data:
        continue

    collections = [c for c in data["results"] if c["wrapperType"] == "collection"]
    for col in collections:
        collection_id = col["collectionId"]

        # Thêm vào list collections
        all_collections.append({
            "collectionId": col["collectionId"],
            "collectionName": col.get("collectionName"),
            "artistId": col.get("artistId"),
            "artistName": col.get("artistName"),
            "releaseDate": col.get("releaseDate"),
            "primaryGenreName": col.get("primaryGenreName"),
            "trackCount": col.get("trackCount")
        })

        print(f"   ➕ Album: {col['collectionName']} ({collection_id})")

        # Step 2: Lấy tracks thuộc collection đó
        track_resp = requests.get(BASE_URL, params={
            "id": collection_id,
            "entity": "song"
        })
        track_data = track_resp.json()

        if "results" not in track_data:
            continue

        tracks = [t for t in track_data["results"] if t["wrapperType"] == "track"]
        for t in tracks:
            all_tracks.append({
                "trackId": t["trackId"],
                "trackName": t.get("trackName"),
                "artistId": t.get("artistId"),
                "artistName": t.get("artistName"),
                "collectionId": t.get("collectionId"),
                "collectionName": t.get("collectionName"),
                "previewUrl": t.get("previewUrl"),
                "trackTimeMillis": t.get("trackTimeMillis"),
                "releaseDate": t.get("releaseDate"),
                "primaryGenreName": t.get("primaryGenreName"),
                "trackNumber": t.get("trackNumber"),
                "artworkUrl100": t.get("artworkUrl100")
            })

        # Sleep tránh bị chặn API
        time.sleep(0.5)

    time.sleep(1)

# Lưu ra file JSON
with open("data/collections.json", "w", encoding="utf-8") as f:
    json.dump(all_collections, f, indent=2, ensure_ascii=False)

with open("data/tracks.json", "w", encoding="utf-8") as f:
    json.dump(all_tracks, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Saved {len(all_collections)} collections and {len(all_tracks)} tracks.")
