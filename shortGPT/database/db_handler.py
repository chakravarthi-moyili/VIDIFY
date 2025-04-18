import threading
import os
import json

class VideoMetadataDB:
    # Singleton instance and thread lock to ensure only one instance is created
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of this class is created.
        This is thread-safe to prevent race conditions when used in multithreaded environments.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize_db()   # Initialize database only once
        return cls._instance

    def _initialize_db(self):
        """Creates the folder and file for storing video data if they don't exist.
        Loads data into memory."""
        try:
            # Ensure the database directory exists
            db_dir = './videosDatabase'
            os.makedirs(db_dir, exist_ok=True)  # Create if not exists
            
            self.db_path = os.path.join(db_dir, 'videos_database.json')
            # Create file and initialize with empty structure if it doesn't exist
            if not os.path.exists(self.db_path):
                with open(self.db_path, 'w') as f:
                    json.dump({"videos": []}, f)  # Initialize with empty list
            
            # Load existing data from the file into memory
            self.data = self._load_data()
        except Exception as e:
            print(f"Error initializing database: {e}")

    def _load_data(self):
        """Loads the video metadata from the JSON file into memory.
        Returns the loaded data or an empty structure on failure."""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return {"videos": []}

    def insert_video_data(self, video_data):
        """Adds a new video metadata entry to the database.

        Args:
            video_data (dict): Dictionary containing video metadata.
        
        Returns:
            bool: True if insertion is successful, False otherwise.
        """
        try:
            document = {
                "_id": video_data["generate_vid_id"],   # Unique ID for the video
                "data": video_data  # Store the whole data dictionary
            }
            
            with self._lock:    # Ensure thread-safe write
                self.data["videos"].append(document)
                self._save_data()
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False

    def _save_data(self):
        """Save data to the JSON file."""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving database: {e}")

    def get_video_data(self, video_id):
        """
        Retrieves video metadata by its unique ID.

        Args:
            video_id (str): The video ID to search for.
        
        Returns:
            dict or None: The video metadata if found, otherwise None.
        """
        with self._lock:    # Thread-safe read
            for video in self.data["videos"]:
                if video["_id"] == video_id:
                    return video["data"]
            return None

    def update_video_data(self, video_id, updates):
        """
        Updates metadata for a specific video ID.

        Args:
            video_id (str): ID of the video to update.
            updates (dict): Updated metadata dictionary.
        
        Returns:
            bool: True if update is successful, False otherwise.
        """
        try:
            with self._lock:
                for video in self.data["videos"]:
                    if video["_id"] == video_id:
                        video["data"] = updates # Replace the existing data
                        self._save_data()
                        return True
            return False
        except Exception as e:
            print(f"Database update error: {e}")
            return False

    def delete_video_data(self, video_id):
        """Deletes a video's metadata from the database.

        Args:
            video_id (str): The ID of the video to delete.
        
        Returns:
            bool: True if deletion is successful, False otherwise."""
        try:
            with self._lock:
                # Keep only videos whose ID doesn't match the one to delete
                self.data["videos"] = [video for video in self.data["videos"] if video["_id"] != video_id]
                self._save_data()   # Save after deletion
                return True
        except Exception as e:
            print(f"Database delete error: {e}")
            return False

    def list_all_videos(self):
        """
        Returns a list of all video metadata entries in the database.

        Returns:
            list: List of video documents (each containing _id and data).
        """
        try:
            with self._lock:
                return self.data["videos"]  # Return the full list
        except Exception as e:
            print(f"Database list error: {e}")
            return []