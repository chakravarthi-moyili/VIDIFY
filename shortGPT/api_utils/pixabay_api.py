import requests

from shortGPT.config.api_db import ApiKeyManager


def search_images(query_string, orientation_landscape=True):
    """Searches for images on Pixabay."""
    url = "https://pixabay.com/api/"
    headers = {}  # Pixabay API doesn't require specific headers
    params = {
        "key": ApiKeyManager.get_api_key("PIXABAY_API_KEY"),
        "q": query_string,
        "orientation": "horizontal" if orientation_landscape else "vertical",
        "per_page": 15,
        "image_type": "photo" # Only get photos
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    return json_data


def get_best_image(query_string, orientation_landscape=True, used_images=[]):
    """Gets the best image from Pixabay based on criteria."""
    images = search_images(query_string, orientation_landscape)
    if not images or 'hits' not in images:
        print("No images found for this query:", query_string)
        return None

    filtered_images = []
    for image in images['hits']:
        if orientation_landscape:
            if image['imageWidth'] >= 1920 and image['imageHeight'] >= 1080 and abs(image['imageWidth'] / image['imageHeight'] - 16 / 9) < 0.1:
                filtered_images.append(image)
        else:
            if image['imageWidth'] >= 1080 and image['imageHeight'] >= 1920 and abs(image['imageHeight'] / image['imageWidth'] - 16 / 9) < 0.1:
                filtered_images.append(image)

    if not filtered_images:
        print("No suitable images found for query:", query_string)
        return None

    # Sort by downloads or likes (you can adjust this)
    sorted_images = sorted(filtered_images, key=lambda x: x['downloads'], reverse=True)

    for image in sorted_images:
        image_url = image.get('largeImageURL')
        if image_url and image_url not in used_images:
            return image_url

    print("NO LINKS found for this round of search with query :", query_string)
    return None

def search_videos_pixabay(query_string, orientation_landscape=True):
    """Searches for videos on Pixabay."""
    url = "https://pixabay.com/api/videos/"
    headers = {}
    params = {
        "key": ApiKeyManager.get_api_key("PIXABAY_API_KEY"),
        "q": query_string,
        "orientation": "horizontal" if orientation_landscape else "vertical",
        "per_page": 15,
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    return json_data

def get_best_video_pixabay(query_string, orientation_landscape=True, used_vids=[]):
    """Gets the best video from Pixabay based on criteria."""
    videos = search_videos_pixabay(query_string, orientation_landscape)
    if not videos or 'hits' not in videos:
        print("No videos found for this query:", query_string)
        return None

    filtered_videos = []
    for video in videos['hits']:
        if orientation_landscape:
            if video['videos']['large']['width'] >= 1920 and video['videos']['large']['height'] >= 1080 and abs(video['videos']['large']['width'] / video['videos']['large']['height'] - 16 / 9) < 0.1:
                filtered_videos.append(video)
        else:
            if video['videos']['large']['width'] >= 1080 and video['videos']['large']['height'] >= 1920 and abs(video['videos']['large']['height'] / video['videos']['large']['width'] - 16 / 9) < 0.1:
                filtered_videos.append(video)

    if not filtered_videos:
        print("No suitable videos found for query:", query_string)
        return None

    # Sort by downloads or likes (you can adjust this)
    sorted_videos = sorted(filtered_videos, key=lambda x: x['downloads'], reverse=True)

    for video in sorted_videos:
        video_url = video['videos']['large']['url']
        if video_url and video_url not in used_vids:
            return video_url

    print("NO LINKS found for this round of search with query :", query_string)
    return None