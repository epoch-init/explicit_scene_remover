import os
import subprocess
import pysrt
import shutil

def export_clean_media(video_path, srt_path, cuts, output_dir, mode="fast"):
    """
    Exports the cleaned video by creating temporary safe segments and concatenating them.
    This bypasses AVI demuxer seeking bugs.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    ext = os.path.splitext(video_path)[1].lower()
    
    # If re-encoding (accurate mode), force output to .mp4 for codec safety
    out_ext = ".mp4" if mode == "accurate" else ext
    out_video_path = os.path.join(output_dir, f"{base_name}_clean{out_ext}")
    
    # Create a temporary directory for the video segments
    segments_dir = os.path.join(output_dir, f"{base_name}_temp_segments")
    os.makedirs(segments_dir, exist_ok=True)
    
    # Convert 'cuts' into 'keeps'
    keeps = []
    current_time = 0.0
    cuts = sorted(cuts, key=lambda x: x['start'])
    
    for cut in cuts:
        if cut['start'] > current_time:
            keeps.append({"start": current_time, "end": cut['start']})
        current_time = max(current_time, cut['end'])
    keeps.append({"start": current_time, "end": None})

    segment_files = []
    
    try:
        # 1. EXTRACT SAFE SEGMENTS
        for idx, keep in enumerate(keeps):
            # E.g., seg_000.avi
            seg_file = os.path.join(segments_dir, f"seg_{idx:03d}{out_ext}")
            segment_files.append(seg_file)
            
            cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", str(keep['start'])]
            
            if keep['end'] is not None:
                cmd.extend(["-to", str(keep['end'])])
                
            if mode == "fast":
                cmd.extend(["-c", "copy"]) # Fast stream copy
            else:
                # Accurate Frame-level Re-encode
                cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac"])
                
            cmd.append(seg_file)
            
            # Run the extraction for this segment
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 2. CONCATENATE THE SEGMENTS
        concat_file_path = os.path.join(segments_dir, "concat.txt")
        with open(concat_file_path, 'w') as f:
            for seg_file in segment_files:
                # Write simple file paths, no inpoints needed anymore
                f.write(f"file '{os.path.abspath(seg_file)}'\n")

        concat_cmd = [
            "ffmpeg", "-y", 
            "-f", "concat", 
            "-safe", "0", 
            "-i", concat_file_path,
            "-c", "copy", # Always copy here since segments are already processed
            out_video_path
        ]
        subprocess.run(concat_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg Export Failed: {error_msg}")
    finally:
        # 3. CLEANUP TEMP SEGMENTS
        if os.path.exists(segments_dir):
            shutil.rmtree(segments_dir)

    # 4. PROCESS SUBTITLES (If provided)
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
            if (sub_start_sec >= cut['start'] and sub_start_sec <= cut['end']) or \
               (sub_end_sec >= cut['start'] and sub_end_sec <= cut['end']):
                is_cut = True
                break
            
            if sub_start_sec > cut['end']:
                shift_amount += (cut['end'] - cut['start'])

        if not is_cut:
            sub.start.ordinal -= int(shift_amount * 1000)
            sub.end.ordinal -= int(shift_amount * 1000)
            clean_subs.append(sub)

    clean_subs.clean_indexes()
    clean_subs.save(out_srt, encoding='utf-8')
