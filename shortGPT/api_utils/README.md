# Module: api_utils

The `api_utils` module provides utility functions for working with different APIs. It includes three files: `image_api.py`, `pexels_api.py`, and `eleven_api.py`. Each file contains functions related to a specific API.

## File: image_api.py

This file contains functions for interacting with the Bing Images API and extracting image URLs from the HTML response.

### Functions:

#### `_extractBingImages(html)`

This function takes an HTML response as input and extracts image URLs, widths, and heights from it. It uses regular expressions to find the necessary information. The extracted image URLs are returned as a list of dictionaries, where each dictionary contains the URL, width, and height of an image.

#### `_extractGoogleImages(html)`

This function takes an HTML response as input and extracts image URLs from it. It uses regular expressions to find the necessary information. The extracted image URLs are returned as a list.

#### `getBingImages(query, retries=5)`

This function takes a query string as input and retrieves a list of image URLs from the Bing Images API. It replaces spaces in the query string with `+` and sends a GET request to the API. If the request is successful (status code 200), the HTML response is passed to `_extractBingImages` to extract the image URLs. If the request fails or no images are found, an exception is raised.

## File: pexels_api.py

This file contains functions for interacting with the Pexels Videos API and retrieving video URLs based on a query string.

### Functions:

#### `search_videos(query_string, orientation_landscape=True)`

This function takes a query string and an optional boolean parameter `orientation_landscape` as input. It sends a GET request to the Pexels Videos API to search for videos based on the query string. The orientation of the videos can be specified as landscape or portrait. The function returns the JSON response from the API.

#### `getBestVideo(query_string, orientation_landscape=True, used_vids=[])`

This function takes a query string, an optional boolean parameter `orientation_landscape`, and an optional list `used_vids` as input. It calls the `search_videos` function to retrieve a list of videos based on the query string. It then filters and sorts the videos based on their dimensions and duration, and returns the URL of the best matching video. The `used_vids` parameter can be used to exclude previously used videos from the search results.

## File: pixabay_api.py

This file contains functions for interacting with the Pixabay API and retrieving image and video URLs based on a query string.

### Functions:

### `search_images(query_string, orientation_landscape=True)`

This function takes a query string and an optional boolean parameter `orientation_landscape` as input. It sends a GET request to the Pixabay API to search for images based on the query string. The orientation of the images can be specified as landscape or portrait. The function returns the JSON response from the API.

### `get_best_image(query_string, orientation_landscape=True, used_images=[])`

This function takes a query string, an optional boolean parameter `orientation_landscape`, and an optional list `used_images` as input. It calls the `search_images` function to retrieve a list of images based on the query string. It then filters and sorts the images based on their dimensions and download count, and returns the URL of the best matching image. The `used_images` parameter can be used to exclude previously used images from the search results.

### `search_videos_pixabay(query_string, orientation_landscape=True)`

This function takes a query string and an optional boolean parameter `orientation_landscape` as input. It sends a GET request to the Pixabay Videos API to search for videos based on the query string. The orientation of the videos can be specified as landscape or portrait. The function returns the JSON response from the API.

### `get_best_video_pixabay(query_string, orientation_landscape=True, used_vids=[])`

This function takes a query string, an optional boolean parameter `orientation_landscape`, and an optional list `used_vids` as input. It calls the `search_videos_pixabay` function to retrieve a list of videos based on the query string. It then filters and sorts the videos based on their dimensions and download count, and returns the URL of the best matching video. The `used_vids` parameter can be used to exclude previously used videos from the search results.

## File: own_database:

This file contains functions for searching and retrieving videos from a local database based on a query string.

### Functions:

### `load_local_video_db(file_path="own_video_dataset/dataset_local.json")`
This function takes an optional file path parameter as input and loads a local video database from a JSON file. It returns the loaded JSON data.

### `search_local_videos(query_string, orientation_landscape=True, db=None)`
This function takes a query string, an optional boolean parameter `orientation_landscape`, and an optional database parameter `db` as input. If no database is provided, it calls the `load_local_video_db` function to load the database. It then searches the database for videos that match the query string and the specified orientation. The function returns a list of matching videos.

### `get_best_local_video(query_string, orientation_landscape=True, used_vids=[], db=None)`

This function takes a query string, an optional boolean parameter `orientation_landscape`, an optional list `used_vids`, and an optional database parameter `db` as input. It calls the `search_local_videos` function to retrieve a list of videos that match the query string and orientation. It then filters the videos based on their resolution and whether they have been used before. The function returns the URL of the first matching video, or None if no suitable videos are found.

## File: eleven_api.py

This file contains functions for interacting with the Eleven API and generating voice recordings based on text input.

### Functions:

#### `getVoices(api_key="")`

This function takes an optional API key as input and retrieves a dictionary of available voices from the Eleven API. The voices are returned as a dictionary, where the keys are voice names and the values are voice IDs.

#### `getCharactersFromKey(key)`

This function takes an API key as input and retrieves the remaining character limit for the given key. It sends a GET request to the Eleven API and extracts the character limit and count from the response.

#### `generateVoice(text, character, fileName, stability=0.2, clarity=0.1, api_key="")`

This function takes a text input, a character name, a file name, and optional parameters `stability`, `clarity`, and `api_key` as input. It generates a voice recording using the Eleven API and saves it to the specified file. The character name is used to select the appropriate voice. The stability and clarity parameters control the quality of the voice recording. The API key is required for authentication. If the request is successful, the file name is returned. Otherwise, an empty string is returned.