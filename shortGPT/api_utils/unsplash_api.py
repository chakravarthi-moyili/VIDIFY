import requests
from shortGPT.config.api_db import ApiKeyManager

def search_images_unsplash(query_string, orientation_landscape=True):
    """Searches for images on Unsplash."""
    url = "https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {ApiKeyManager.get_api_key('UNSPLASH_API_KEY')}"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15,
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    return json_data

def get_best_image_unsplash(query_string, orientation_landscape=True, used_images=[]):
    """Gets the best image from Unsplash based on criteria."""
    images = search_images_unsplash(query_string, orientation_landscape)
    if not images or 'results' not in images:
        print("No images found for this query:", query_string)
        return None

    filtered_images = []
    for image in images['results']:
        if orientation_landscape:
            if image['width'] >= 1920 and image['height'] >= 1080 and abs(image['width'] / image['height'] - 16 / 9) < 0.1:
                filtered_images.append(image)
        else:
            if image['width'] >= 1080 and image['height'] >= 1920 and abs(image['height'] / image['width'] - 16 / 9) < 0.1:
                filtered_images.append(image)

    if not filtered_images:
        print("No suitable images found for query:", query_string)
        return None

    # Sort by downloads or likes (you can adjust this)
    sorted_images = sorted(filtered_images, key=lambda x: x['likes'], reverse=True)

    for image in sorted_images:
        image_url = image.get('urls', {}).get('full')
        if image_url and image_url not in used_images:
            return image_url

    print("NO LINKS found for this round of search with query :", query_string)
    return None

def search_videos_unsplash(query_string, orientation_landscape=True):
    """Searches for videos on Unsplash."""
    url = "https://api.unsplash.com/search/videos"
    headers = {
        "Authorization": f"Client-ID {ApiKeyManager.get_api_key('UNSPLASH_API_KEY')}"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15,
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    return json_data

def get_best_video_unsplash(query_string, orientation_landscape=True, used_vids=[]):
    """Gets the best video from Unsplash based on criteria."""
    videos = search_videos_unsplash(query_string, orientation_landscape)
    if not videos or 'results' not in videos:
        print("No videos found for this query:", query_string)
        return None

    filtered_videos = []
    for video in videos['results']:
        if orientation_landscape:
            if video['width'] >= 1920 and video['height'] >= 1080 and abs(video['width'] / video['height'] - 16 / 9) < 0.1:
                filtered_videos.append(video)
        else:
            if video['width'] >= 1080 and video['height'] >= 1920 and abs(video['height'] / video['width'] - 16 / 9) < 0.1:
                filtered_videos.append(video)

    if not filtered_videos:
        print("No suitable videos found for query:", query_string)
        return None

    # Sort by downloads or likes (you can adjust this)
    sorted_videos = sorted(filtered_videos, key=lambda x: x['likes'], reverse=True)

    for video in sorted_videos:
        video_url = video.get('urls', {}).get('full')
        if video_url and video_url not in used_vids:
            return video_url

    print("NO LINKS found for this round of search with query :", query_string)
    return None