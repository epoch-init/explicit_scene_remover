import os

def get_directory_contents(target_path):
    """Safely retrieves contents of a directory, filtering for valid media/subtitle files."""
    if not target_path or not os.path.exists(target_path):
        return {"error": "Path does not exist", "path": target_path}
    
    if not os.path.isdir(target_path):
        return {"error": "Path is not a directory", "path": target_path}

    try:
        items = os.listdir(target_path)
    except PermissionError:
        return {"error": "Permission denied", "path": target_path}

    directories = []
    files = []

    # Allowed video extensions
    VALID_EXTENSIONS = ['.mp4', '.avi', '.srt']

    for item in items:
        full_path = os.path.join(target_path, item)
        if os.path.isdir(full_path):
            directories.append({"name": item, "path": full_path, "type": "directory"})
        elif os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in VALID_EXTENSIONS:
                files.append({"name": item, "path": full_path, "type": "file", "extension": ext})

    # Sort alphabetically for a better UX
    directories.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())

    parent_path = os.path.dirname(target_path)
    
    return {
        "current_path": target_path,
        "parent_path": parent_path if parent_path != target_path else target_path,
        "directories": directories,
        "files": files
    }
