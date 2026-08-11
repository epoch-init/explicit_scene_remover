import os
import subprocess

def extract_media(video_path, base_temp_dir, fps=1.0):
    """Extracts frames and mono 16kHz audio from a video using FFmpeg."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    os.makedirs(base_temp_dir, exist_ok=True)
    frames_dir = os.path.join(base_temp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    audio_path = os.path.join(base_temp_dir, "audio.wav")
    
    # FFmpeg frame extraction command
    # -y: overwrite, -qscale:v 2: high quality jpeg
    frame_cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vf", f"fps={fps}", 
        "-qscale:v", "2", 
        os.path.join(frames_dir, "frame_%06d.jpg")
    ]
    
    # FFmpeg audio extraction command
    # 16kHz mono WAV is standard and highly optimized for AI models like Whisper/YAMNet
    audio_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", 
        "-acodec", "pcm_s16le", 
        "-ar", "16000", 
        "-ac", "1", 
        audio_path
    ]
    
    try:
        # We use check=True so it throws CalledProcessError on failure
        subprocess.run(frame_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(audio_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "Unknown FFmpeg Error"
        raise RuntimeError(f"FFmpeg extraction failed: {error_msg}")
        
    return {
        "frames_dir": frames_dir,
        "audio_path": audio_path
    }
