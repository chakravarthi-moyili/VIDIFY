# Database Module Documentation

The `database` module provides classes for managing database documents and data in the VIDIFY application. The module consists of three files:

- `content_data_manager.py`: Defines the `ContentDataManager` class, which manages the content data for a document in the database.
- `content_database.py`: Defines the `ContentDatabase` class, which provides methods for creating and accessing `ContentDataManager` instances.
- `db_document.py`: Defines the `DatabaseDocument` abstract base class and the `TinyMongoDocument` class, which represents a document in a TinyMongo database.
- `db_handler.py`: Defines the `VideoMetadataDB` class, which manages video metadata using a thread-safe, singleton-based JSON file database. It supports operations to insert, retrieve, update, delete, and list video data.

## File: content_data_manager.py

The `content_data_manager.py` file contains the `ContentDataManager` class, which is responsible for managing the content data for a document in the database.

### Class: ContentDataManager

#### `__init__(self, db_doc: DatabaseDocument, content_type: str, new=False)`

- Initializes a new instance of the `ContentDataManager` class.
- Parameters:
  - `db_doc`: The `DatabaseDocument` instance representing the document in the database.
  - `content_type`: The type of content to be managed by the `ContentDataManager`.
  - `new`: (Optional) A boolean flag indicating whether the document is new or existing. Default is `False`.

#### `save(self, key, value)`

- Saves the specified key-value pair to the document.
- Parameters:
  - `key`: The key of the data to be saved.
  - `value`: The value of the data to be saved.

#### `get(self, key)`

- Retrieves the value associated with the specified key from the document.
- Parameters:
  - `key`: The key of the data to be retrieved.
- Returns:
  - The value associated with the specified key.

#### `_getId(self)`

- Retrieves the ID of the document.
- Returns:
  - The ID of the document.

#### `delete(self)`

- Deletes the document from the database.

#### `__str__(self)`

- Returns a string representation of the document.

## File: content_database.py

The `content_database.py` file contains the `ContentDatabase` class, which provides methods for creating and accessing `ContentDataManager` instances.

### Class: ContentDatabase

#### `instanciateContentDataManager(self, id: str, content_type: str, new=False)`

- Creates a new `ContentDataManager` instance for the specified document ID and content type.
- Parameters:
  - `id`: The ID of the document.
  - `content_type`: The type of content to be managed by the `ContentDataManager`.
  - `new`: (Optional) A boolean flag indicating whether the document is new or existing. Default is `False`.
- Returns:
  - A new `ContentDataManager` instance.

#### `getContentDataManager(self, id, content_type: str)`

- Retrieves an existing `ContentDataManager` instance for the specified document ID and content type.
- Parameters:
  - `id`: The ID of the document.
  - `content_type`: The type of content to be managed by the `ContentDataManager`.
- Returns:
  - The existing `ContentDataManager` instance, or `None` if not found.

#### `createContentDataManager(self, content_type: str) -> ContentDataManager`

- Creates a new `ContentDataManager` instance for a new document with the specified content type.
- Parameters:
  - `content_type`: The type of content to be managed by the `ContentDataManager`.
- Returns:
  - A new `ContentDataManager` instance.

## File: db_document.py

The `db_document.py` file contains the `DatabaseDocument` abstract base class and the `TinyMongoDocument` class, which represents a document in a TinyMongo database.

### Abstract Class: DatabaseDocument

- An abstract base class that defines the interface for a database document.
- Subclasses must implement the abstract methods:
  - `_save(self, key, data)`
  - `_get(self, key)`
  - `_getId(self)`
  - `__str__(self)`
  - `_delete(self)`

### Class: TinyMongoDocument

- Represents a document in a TinyMongo database.
- Inherits from the `DatabaseDocument` abstract base class.

#### `__init__(self, db_name: str, collection_name: str, document_id: str, create=False)`

- Initializes a new instance of the `TinyMongoDocument` class.
- Parameters:
  - `db_name`: The name of the database.
  - `collection_name`: The name of the collection.
  - `document_id`: The ID of the document.
  - `create`: (Optional) A boolean flag indicating whether to create the document if it doesn't exist. Default is `False`.

#### `exists(self)`

- Checks if the document exists in the database.
- Returns:
  - `True` if the document exists, `False` otherwise.

#### `_save(self, data)`

- Saves the specified data to the document.
- Parameters:
  - `data`: The data to be saved.

#### `_get(self, key=None)`

- Retrieves the value associated with the specified key from the document.
- Parameters:
  - `key`: (Optional) The key of the data to be retrieved. If not specified, returns the entire document.
- Returns:
  - The value associated with the specified key, or the entire document if no key is specified.

#### `_delete(self, key)`

- Deletes the specified key from the document.
- Parameters:
  - `key`: The key to be deleted.

#### `_getId(self)`

- Retrieves the ID of the document.
- Returns:
  - The ID of the document.

#### `__str__(self)`

- Returns a string representation of the document.

## File: `db_handler.py`

This file contains the `VideoMetadataDB` class, which is responsible for managing video metadata using a JSON-based storage system. It follows the Singleton pattern and ensures thread-safe access to video records.

### Class: `VideoMetadataDB`

### `__new__(cls)`

- Creates and returns the single instance of `VideoMetadataDB` using the Singleton pattern.
- Ensures thread-safe instantiation across threads.

### `_initialize_db(self)`

- Initializes the database by creating the JSON file and directory if they don’t exist.
- Loads existing video data into memory.

### `_load_data(self)`

- Loads video metadata from the JSON file into memory.
- Returns:
  - A dictionary containing the current state of video metadata.

### `insert_video_data(self, video_data)`

- Inserts a new video metadata record into the database.
- Parameters:
  - `video_data`: A dictionary containing video metadata, including a unique `generate_vid_id`.
- Returns:
  - `True` if insertion is successful, otherwise `False`.

### `_save_data(self)`

- Saves the in-memory video metadata back to the JSON file.

### `get_video_data(self, video_id)`

- Retrieves metadata for a specific video by its ID.
- Parameters:
  - `video_id`: The unique identifier for the video.
- Returns:
  - A dictionary of the video metadata if found, otherwise `None`.

### `update_video_data(self, video_id, updates)`

- Updates the metadata of a specific video.
- Parameters:
  - `video_id`: The unique identifier of the video to update.
  - `updates`: A dictionary containing the updated metadata.
- Returns:
  - `True` if update is successful, otherwise `False`.

### `delete_video_data(self, video_id)`

- Deletes metadata for a specific video by its ID.
- Parameters:
  - `video_id`: The unique identifier of the video to delete.
- Returns:
  - `True` if deletion is successful, otherwise `False`.

### `list_all_videos(self)`
- Returns a list of all video metadata stored in the database.
- Returns:
  - A list of dictionaries, each representing a video's metadata.