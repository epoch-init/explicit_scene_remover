import os
import gc
import torch
from PIL import Image
from transformers import pipeline

class VisionModelWrapper:
    def __init__(self, model_path="models/vision_nsfw"):
        self.model_path = os.path.join(os.getcwd(), model_path)
        # Check if CUDA is available, otherwise fallback to CPU
        self.device = 0 if torch.cuda.is_available() else -1

    def analyze(self, frames_dir, fps, threshold=0.7):
        """Processes extracted frames and returns NSFW timestamps."""
        print(f"Loading Vision model to GPU ({'CUDA' if self.device == 0 else 'CPU'})...")
        classifier = pipeline("image-classification", model=self.model_path, device=self.device)
        
        results = []
        
        # Sort frames to ensure chronological order
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        for frame_file in frame_files:
            # frame_000001.jpg -> index 1
            frame_idx = int(frame_file.split('_')[1].split('.')[0])
            timestamp_sec = frame_idx / fps
            
            img_path = os.path.join(frames_dir, frame_file)
            image = Image.open(img_path).convert("RGB")
            
            # Predict
            preds = classifier(image)
            
            # Find NSFW label score
            for pred in preds:
                if pred['label'] == 'nsfw' and pred['score'] >= threshold:
                    results.append({
                        "start": timestamp_sec - (1/fps), 
                        "end": timestamp_sec,
                        "label": "Nudity/NSFW",
                        "confidence": float(pred['score'])
                    })
                    break
        
        # --- STRICT 2GB VRAM FLUSH ---
        print("Unloading Vision model from VRAM...")
        del classifier
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return results
