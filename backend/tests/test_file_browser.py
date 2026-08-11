import os
from utils.file_browser import get_directory_contents

def test_file_browser_success(tmp_path):
    # Create mock directories and files
    (tmp_path / "folder1").mkdir()
    (tmp_path / "movie.mp4").touch()
    (tmp_path / "subs.srt").touch()
    (tmp_path / "image.jpg").touch() # Should be ignored
    
    result = get_directory_contents(str(tmp_path))
    
    assert "error" not in result
    assert result["current_path"] == str(tmp_path)
    assert len(result["directories"]) == 1
    assert result["directories"][0]["name"] == "folder1"
    
    # Should only contain .mp4 and .srt, ignoring .jpg
    assert len(result["files"]) == 2
    extensions = [f["extension"] for f in result["files"]]
    assert ".mp4" in extensions
    assert ".srt" in extensions
    assert ".jpg" not in extensions

def test_file_browser_not_found():
    result = get_directory_contents("/path/that/does/not/exist/123")
    assert "error" in result
    assert result["error"] == "Path does not exist"
