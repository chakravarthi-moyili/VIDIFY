import json
import os

# Path to your JSON file
JSON_FILE_PATH = "videosDatabase/videos_database.json"

# Global data store
video_data = []

# Function to load JSON data
def load_gallery_data(json_path):
    """Load gallery data from a JSON file."""
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return {"videos": []}

# Function to prepare gallery thumbnails
def prepare_gallery():
    """Prepare gallery thumbnails from JSON data and store data globally."""
    global video_data
    data = load_gallery_data(JSON_FILE_PATH)
    video_data = data.get("videos", [])
    
    # Format for gr.Gallery
    gallery_images = []
    
    for video in video_data:
        # Get thumbnail path - assuming thumbnails are in a "thumbnails" directory
        thumbnail = video.get("data", {}).get("thumbnail", "")
        # If thumbnail exists, add it to gallery
        if thumbnail:
            gallery_images.append(thumbnail)
        else:
            # Use a placeholder if no thumbnail is available
            gallery_images.append(None)
    
    return gallery_images

# Function to show video details when selected
def show_selected_video(evt):
    """Display video title and script for the selected video."""
    selected_index = evt.index
    
    if 0 <= selected_index < len(video_data):
        selected_video = video_data[selected_index]
        data = selected_video.get("data", {})
        title = data.get("generated_video_title", "Untitled")
        script = data.get("used_script", "No script available")
        video_path = data.get("generated_video", "")
        
        # Prepare markdown content
        markdown_content = f"## {title}\n\n{script}"
        
        return markdown_content, video_path
    
    return "No video selected", None

# Function to clear video details when deselected
def clear_video_details():
    """Clear video details when a video is deselected."""
    return "", None

# Function to refresh gallery
def refresh_gallery():
    """Reload gallery data from JSON file."""
    thumbnails = prepare_gallery()
    return thumbnails, "", None

# Check if JSON file exists, create example if it doesn't
def initialize_json_file():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Warning: {JSON_FILE_PATH} not found. Please create this file with your video data.")