import threading
import tinymongo
from tinymongo import TinyMongoClient
import os
import json

class VideoMetadataDB:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:  
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        """Initialize the TinyMongo database."""
        try:
            # Ensure the database directory exists
            db_dir = './.database'
            os.makedirs(db_dir, exist_ok=True)  # Create if not exists
            
            self.db_path = os.path.join(db_dir, 'videos_database.json')
            if not os.path.exists(self.db_path):
                with open(self.db_path, 'w') as f:
                    json.dump({"videos": []}, f)  # Initialize with empty list
            
            self.data = self._load_data()
        except Exception as e:
            print(f"Error initializing database: {e}")

    def _load_data(self):
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return {"videos": []}

    def insert_video_data(self, video_data):
        """Insert video metadata into the database."""
        try:
            document = {
                "_id": video_data["generate_vid_id"],
                "data": video_data
            }
            
            with self._lock:
                self.data["videos"].append(document)
                self._save_data()
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False

    def _save_data(self):
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving database: {e}")

    def get_video_data(self, video_id):
        """Retrieve video metadata by ID."""
        with self._lock:
            for video in self.data["videos"]:
                if video["_id"] == video_id:
                    return video["data"]
            return None

    def update_video_data(self, video_id, updates):
        """Update video metadata."""
        try:
            with self._lock:
                for video in self.data["videos"]:
                    if video["_id"] == video_id:
                        video["data"] = updates
                        self._save_data()
                        return True
            return False
        except Exception as e:
            print(f"Database update error: {e}")
            return False

    def delete_video_data(self, video_id):
        """Delete video metadata by ID."""
        try:
            with self._lock:
                self.data["videos"] = [video for video in self.data["videos"] if video["_id"] != video_id]
                self._save_data()
                return True
        except Exception as e:
            print(f"Database delete error: {e}")
            return False

    def list_all_videos(self):
        """List all videos in the database."""
        try:
            with self._lock:
                return self.data["videos"]
        except Exception as e:
            print(f"Database list error: {e}")
            return []
