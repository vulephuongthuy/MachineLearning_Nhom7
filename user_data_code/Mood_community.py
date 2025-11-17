import json
from collections import defaultdict


def compute_track_mood_community(user_mood_file, track_file, output_file):
    # Load dữ liệu
    with open(user_mood_file, "r", encoding="utf-8") as f:
        user_moods = json.load(f)
    with open(track_file, "r", encoding="utf-8") as f:
        tracks = json.load(f)

    # map trackId → genre
    track_map = {t["trackId"]: t.get("primaryGenreName", "") for t in tracks}

    # map trackId → list of userMood
    track_moods = defaultdict(list)
    for um in user_moods:
        track_moods[um["trackId"]].append(um["userMood"])

    results = []
    for tid, moods in track_moods.items():
        total = len(moods)
        mood_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for m in moods:
            mood_counts[m] += 1
        mood_weights = {str(k): v / total for k, v in mood_counts.items()}

        # Chọn mood_community → mood có trọng số cao nhất, tie-break chọn mood nhỏ hơn
        max_weight = max(mood_weights.values())
        community_moods = [int(k) for k, v in mood_weights.items() if v == max_weight]
        mood_community = min(community_moods)

        results.append({
            "trackId": tid,
            "genre": track_map.get(tid, ""),
            "mood_weights": mood_weights,
            "mood_community": mood_community
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(results)} track mood_community records")


# ví dụ chạy
compute_track_mood_community("Data/user_moods.json", "Data/merged_tracks_final.json", "Data/track_mood_community.json")
