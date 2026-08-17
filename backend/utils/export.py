import os
import subprocess
import pysrt

def export_clean_media(video_path, srt_path, cuts, output_dir, mode="fast"):
    """
    Exports the cleaned video and shifts the subtitles.
    mode: 'fast' (stream copy, keyframe snap) or 'accurate' (re-encode).
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_video_path = os.path.join(output_dir, f"{base_name}_clean.mp4")
    
    # 1. GENERATE FFMPEG CONCAT FILE
    # Convert 'cuts' (what to remove) into 'keeps' (what to keep)
    keeps = []
    current_time = 0.0
    
    # Sort cuts chronologically just in case
    cuts = sorted(cuts, key=lambda x: x['start'])
    
    for cut in cuts:
        if cut['start'] > current_time:
            keeps.append({"start": current_time, "end": cut['start']})
        current_time = max(current_time, cut['end'])
    
    # Add the final segment (from the last cut to the end of the video)
    keeps.append({"start": current_time, "end": None})

    concat_file_path = os.path.join(output_dir, "concat.txt")
    with open(concat_file_path, 'w') as f:
        for keep in keeps:
            f.write(f"file '{os.path.abspath(video_path)}'\n")
            f.write(f"inpoint {keep['start']}\n")
            if keep['end'] is not None:
                f.write(f"outpoint {keep['end']}\n")

    # 2. EXECUTE FFMPEG
    # -f concat -safe 0: Reads the text file of segments
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-f", "concat", 
        "-safe", "0", 
        "-i", concat_file_path
    ]

    if mode == "fast":
        # Stream copy (Lossless, fast, subject to keyframe snapping)
        ffmpeg_cmd.extend(["-c", "copy"])
    else:
        # Frame-Accurate Re-encode (Exact cuts, but takes longer)
        # Using fast preset and crf 18 to maintain high visual quality
        ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac"])
    
    ffmpeg_cmd.append(out_video_path)
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"FFmpeg Export Failed: {error_msg}")

    # 3. PROCESS SUBTITLES (If provided)
    out_srt_path = None
    if srt_path and os.path.exists(srt_path):
        out_srt_path = os.path.join(output_dir, f"{base_name}_clean.srt")
        process_subtitles(srt_path, cuts, out_srt_path)

    return {
        "video": out_video_path,
        "subtitle": out_srt_path
    }

def process_subtitles(in_srt, cuts, out_srt):
    """Deletes subtitles during cuts and shifts subsequent subtitles back."""
    subs = pysrt.open(in_srt)
    clean_subs = pysrt.SubRipFile()

    for sub in subs:
        sub_start_sec = sub.start.ordinal / 1000.0
        sub_end_sec = sub.end.ordinal / 1000.0
        
        is_cut = False
        shift_amount = 0.0

        for cut in cuts:
            # If the subtitle falls entirely or partially inside a cut, remove it
            if (sub_start_sec >= cut['start'] and sub_start_sec <= cut['end']) or \
               (sub_end_sec >= cut['start'] and sub_end_sec <= cut['end']):
                is_cut = True
                break
            
            # If the subtitle happens AFTER a cut, it needs to shift left (earlier)
            if sub_start_sec > cut['end']:
                shift_amount += (cut['end'] - cut['start'])

        if not is_cut:
            # Apply shift
            sub.start.ordinal -= int(shift_amount * 1000)
            sub.end.ordinal -= int(shift_amount * 1000)
            clean_subs.append(sub)

    # Re-index and save
    clean_subs.clean_indexes()
    clean_subs.save(out_srt, encoding='utf-8')
