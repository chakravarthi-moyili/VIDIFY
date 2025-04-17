import json

def load_local_video_db(file_path="own_video_dataset/dataset_local.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_local_videos(query_string, orientation_landscape=True, db=None):
    if db is None:
        db = load_local_video_db()
    
    orientation = "landscape" if orientation_landscape else "portrait"
    query_keywords = query_string.lower().split()

    results = []
    for video in db["videos"]:
        if video["orientation"].lower() != orientation:
            continue
        tags_lower = [tag.strip().lower() for tag in video["tags"]]
        # Check if any keyword is in the tags (partial matches included)
        if any(any(q in tag for tag in tags_lower) for q in query_keywords):
            results.append(video)
    return results

def get_best_local_video(query_string, orientation_landscape=True, used_vids=[], db=None):
    videos = search_local_videos(query_string, orientation_landscape, db)

    # target_resolution = "1080x1920" if orientation_landscape else "1920x1080"
    target_resolution = "1920x1080" if orientation_landscape else "1080x1920"

    filtered_videos = [
        video for video in videos
        if video["resolution"] == target_resolution and video["url"] not in used_vids
    ]

    if filtered_videos:
        return filtered_videos[0]["url"]

    print("NO LINKS found for this round of search with query:", query_string)
    return None

























# import json

# def load_local_video_db(file_path="own_video_dataset/dataset_local.json"):
#     with open(file_path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def search_local_videos(query_string, orientation_landscape=True, db=None):
#     if db is None:
#         db = load_local_video_db()
    
#     orientation = "landscape" if orientation_landscape else "portrait"
#     query_keywords = query_string.lower().split()

#     # Filter based on orientation and if any query keyword appears in tags
#     results = []
#     for video in db["videos"]:
#         if video["orientation"] != orientation:
#             continue
#         tags_lower = [tag.lower() for tag in video["tags"]]
#         if any(q in tags_lower for q in query_keywords):
#             results.append(video)
#     return results


# def get_best_local_video(query_string, orientation_landscape=True, used_vids=[], db=None):
#     videos = search_local_videos(query_string, orientation_landscape, db)

#     # Define resolution check
#     target_resolution = "1920x1080" if orientation_landscape else "1080x1920"

#     # Filter by resolution and not already used
#     filtered_videos = [
#         video for video in videos
#         if video["resolution"] == target_resolution and video["url"].split("?")[0] not in used_vids
#     ]

#     if filtered_videos:
#         return filtered_videos[0]["url"]  # Return first valid match

#     print("NO LINKS found for this round of search with query:", query_string)
#     return None
