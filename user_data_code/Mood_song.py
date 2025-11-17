import json
import random
from datetime import datetime, timezone, timedelta

# Mapping genre → mood
GENRE_TO_MOOD_PROBS = {
    # Happy
    "Pop": {1:0.7, 2:0.0, 3:0.2, 4:0.1},
    "Dance": {1:0.8, 2:0.0, 3:0.15, 4:0.05},
    "K-Pop": {1:0.6, 2:0.05, 3:0.15, 4:0.2},
    "J-Pop": {1:0.6, 2:0.1, 3:0.1, 4:0.2},
    "Mandopop": {1:0.5, 2:0.2, 3:0.2, 4:0.1},
    "Cantopop": {1:0.4, 2:0.3, 3:0.25, 4:0.05},
    "Pop Latino": {1:0.75, 2:0.0, 3:0.2, 4:0.05},
    "Teen Pop": {1:0.8, 2:0.0, 3:0.15, 4:0.05},
    "T-Pop": {1:0.75, 2:0.0, 3:0.2, 4:0.05},
    "Tai-Pop": {1:0.75, 2:0.0, 3:0.2, 4:0.05},
    "Latin": {1:0.7, 2:0.0, 3:0.25, 4:0.05},
    "Música tropical": {1:0.8, 2:0.0, 3:0.15, 4:0.05},
    "Afrobeats": {1:0.8, 2:0.0, 3:0.15, 4:0.05},
    "Afro-Pop": {1:0.75, 2:0.0, 3:0.2, 4:0.05},
    "Worldwide": {1:0.6, 2:0.0, 3:0.3, 4:0.1},
    "Children's Music": {1:0.9, 2:0.0, 3:0.1, 4:0.0},
    "Karaoke": {1:0.8, 2:0.0, 3:0.15, 4:0.05},
    "Christmas: Pop": {1:0.85, 2:0.0, 3:0.1, 4:0.05},

    # Sad
    "Singer/Songwriter": {1:0.05, 2:0.7, 3:0.2, 4:0.05},
    "R&B/Soul": {1:0.1, 2:0.6, 3:0.2, 4:0.1},
    "Soul": {1:0.1, 2:0.6, 3:0.2, 4:0.1},
    "Jazz": {1:0.05, 2:0.7, 3:0.2, 4:0.05},
    "Blues": {1:0.05, 2:0.7, 3:0.2, 4:0.05},
    "Indie Pop": {1:0.3, 2:0.5, 3:0.15, 4:0.05},
    "Folk": {1:0.2, 2:0.6, 3:0.15, 4:0.05},
    "Alternative Folk": {1:0.15, 2:0.6, 3:0.2, 4:0.05},
    "Contemporary Folk": {1:0.2, 2:0.6, 3:0.15, 4:0.05},
    "Traditional Folk": {1:0.1, 2:0.7, 3:0.15, 4:0.05},
    "Vocal": {1:0.25, 2:0.6, 3:0.1, 4:0.05},
    "Christian": {1:0.3, 2:0.5, 3:0.15, 4:0.05},
    "Classical Crossover": {1:0.2, 2:0.6, 3:0.15, 4:0.05},
    "Classical": {1:0.1, 2:0.7, 3:0.15, 4:0.05},
    "Country": {1:0.25, 2:0.6, 3:0.1, 4:0.05},
    "Holiday": {1:0.5, 2:0.4, 3:0.1, 4:0.0},
    "Christmas: Classical": {1:0.3, 2:0.6, 3:0.1, 4:0.0},
    "Christmas: R&B": {1:0.2, 2:0.7, 3:0.1, 4:0.0},

    # Neutral
    "Alternative": {1:0.1, 2:0.2, 3:0.6, 4:0.1},
    "Pop/Rock": {1:0.2, 2:0.15, 3:0.6, 4:0.05},
    "Adult Contemporary": {1:0.2, 2:0.2, 3:0.55, 4:0.05},
    "Soundtrack": {1:0.1, 2:0.2, 3:0.65, 4:0.05},
    "TV Soundtrack": {1:0.1, 2:0.2, 3:0.65, 4:0.05},
    "Musicals": {1:0.3, 2:0.2, 3:0.45, 4:0.05},
    "Asia": {1:0.3, 2:0.2, 3:0.45, 4:0.05},
    "Chinese": {1:0.25, 2:0.25, 3:0.45, 4:0.05},
    "国语流行": {1:0.25, 2:0.25, 3:0.45, 4:0.05},
    "Chinese Rock": {1:0.15, 2:0.25, 3:0.55, 4:0.05},
    "Britpop": {1:0.2, 2:0.15, 3:0.6, 4:0.05},
    "Prog-Rock/Art Rock": {1:0.1, 2:0.2, 3:0.65, 4:0.05},

    # Intense
    "Hip-Hop/Rap": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Hip-Hop": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Rap": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Korean Hip-Hop": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Alternative Rap": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Electronic": {1:0.1, 2:0.05, 3:0.3, 4:0.55},
    "Electronica": {1:0.1, 2:0.05, 3:0.3, 4:0.55},
    "House": {1:0.1, 2:0.05, 3:0.3, 4:0.55},
    "Dubstep": {1:0.05, 2:0.05, 3:0.2, 4:0.7},
    "Metal": {1:0.05, 2:0.05, 3:0.2, 4:0.7},
    "Modern Dancehall": {1:0.1, 2:0.05, 3:0.25, 4:0.6},
    "Reggae": {1:0.2, 2:0.05, 3:0.3, 4:0.45},
    "Urbano latino": {1:0.2, 2:0.05, 3:0.25, 4:0.5},
    "Rock y Alternativo": {1:0.1, 2:0.15, 3:0.5, 4:0.25},
    "Video Game": {1:0.1, 2:0.05, 3:0.25, 4:0.6},
}

def generate_user_moods_prob(purchase_file, track_file, output_file,
                             mood_probability=0.3, mapping_ratio=0.85):
    with open(purchase_file, "r", encoding="utf-8") as f:
        purchases = json.load(f)
    with open(track_file, "r", encoding="utf-8") as f:
        tracks = json.load(f)

    track_map = {t["trackId"]: t for t in tracks}
    user_moods = []
    user_track_set = set()  # tránh trùng (user, track)

    for p in purchases:
        track = track_map.get(p["track_id"])
        if not track:
            continue

        uid, tid = p["user_id"], track["trackId"]
        if (uid, tid) in user_track_set:
            continue

        if random.random() > mood_probability:
            continue  # user này không gán mood cho track này

        genre = track.get("primaryGenreName", "")
        mood_probs = GENRE_TO_MOOD_PROBS.get(genre, {1:0.25,2:0.25,3:0.25,4:0.25})
        moods, weights = list(mood_probs.keys()), list(mood_probs.values())

        # chọn mood: 85% theo genre, 15% random hoàn toàn
        if random.random() < mapping_ratio:
            mood = random.choices(moods, weights=weights, k=1)[0]
        else:
            mood = random.choice([1,2,3,4])

        # parse purchase time
        purchase_str = p.get("purchased_at")
        try:
            purchase_dt = datetime.fromisoformat(purchase_str.replace("Z", "+00:00"))
        except Exception:
            purchase_dt = datetime.now(timezone.utc)

        # mood timestamp xảy ra sau purchase 0–7 ngày, bias gần hơn
        delta_seconds = int(random.random() ** 2 * 7 * 24 * 3600)
        mood_dt = purchase_dt + timedelta(seconds=delta_seconds)

        user_moods.append({
            "trackId": tid,
            "userId": uid,
            "genre": genre,
            "userMood": mood,
            "timestamp": mood_dt.isoformat().replace("+00:00", "Z")
        })
        user_track_set.add((uid, tid))

    # ghi file output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(user_moods, f, ensure_ascii=False, indent=2)

    # thống kê nhanh
    mood_counts = {}
    for um in user_moods:
        mood_counts[um["userMood"]] = mood_counts.get(um["userMood"], 0) + 1

    print(f"Generated {len(user_moods)} user_mood records")
    print("Phân bố theo mood:")
    for m, c in sorted(mood_counts.items()):
        print(f"  Mood {m}: {c} ({c/len(user_moods)*100:.1f}%)")


# ví dụ chạy
if __name__ == "__main__":
    generate_user_moods_prob(
        "Data/purchased.json",
        "Data/merged_tracks_final.json",
        "Data/user_moods.json"
    )