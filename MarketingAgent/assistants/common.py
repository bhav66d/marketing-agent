from pathlib import Path


def save_image_to_cache(
    image_bytes: bytes, filename: str, cache_dir: str = ".cache"
) -> str:
    """Save image bytes to a cache directory for easier future access.

    Args:
        image_bytes: The raw binary image data to save
        filename: The name to give the saved file
        cache_dir: The directory to save the file in (defaults to ".cache")

    Returns:
        The full path to the saved image file
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    file_path = cache_path / filename

    try:
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        return str(file_path)

    except Exception as e:
        print(f"Error saving image to cache: {e}")
        return ""
