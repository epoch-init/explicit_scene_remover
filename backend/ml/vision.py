import os
import gc
from nudenet import NudeDetector
import torch

# NudeNet detects many things (including COVERED_BREAST_F, EXPOSED_BELLY, etc.)
# We only want to trigger cuts on actual explicit exposure.
EXPLICIT_CLASSES = [
    "EXPOSED_ANUS",
    "EXPOSED_BREAST_F",
    "EXPOSED_BUTTOCKS",
    "EXPOSED_GENITALIA_F",
    "EXPOSED_GENITALIA_M"
]

class VisionModelWrapper:
    def __init__(self):
        # NudeNet automatically loads from its local ~/.NudeNet/ directory
        pass

    def analyze(self, frames_dir, fps, threshold=0.6):
        """Uses YOLOv8 object detection to find specific exposed anatomy in frames."""
        print("Loading NudeNet Vision model to Memory...")
        detector = NudeDetector()
        
        results = []
        
        # Sort frames to ensure chronological order
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        for frame_file in frame_files:
            frame_idx = int(frame_file.split('_')[1].split('.')[0])
            timestamp_sec = frame_idx / fps
            
            img_path = os.path.join(frames_dir, frame_file)
            
            # Predict bounding boxes
            preds = detector.detect(img_path)
            
            # preds is a list of dictionaries, e.g.:
            # [{'class': 'EXPOSED_BREAST_F', 'score': 0.85, 'box': [x, y, w, h]}]
            for pred in preds:
                if pred['class'] in EXPLICIT_CLASSES and pred['score'] >= threshold:
                    results.append({
                        "start": timestamp_sec - (1/fps), 
                        "end": timestamp_sec,
                        "label": "Nudity/NSFW", # Keep this label standard for the Aggregator
                        "confidence": float(pred['score']),
                        "details": pred['class'] # E.g., 'EXPOSED_BREAST_F'
                    })
                    break # Found nudity in this frame, we can move to the next frame
        
        # --- STRICT VRAM/RAM FLUSH ---
        print("Unloading NudeNet Vision model...")
        del detector
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return results
