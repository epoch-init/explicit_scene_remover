import os
import gc
import torch
from PIL import Image
from transformers import pipeline, CLIPProcessor, CLIPModel

class VisionModelWrapper:
    def __init__(self, model_folder="models/vision_clip"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, model_folder)
        
        config_file = os.path.join(self.model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Model config not found at {config_file}.")
            
        self.device = 0 if torch.cuda.is_available() else -1

    def analyze(self, frames_dir, fps, threshold=0.6):
        """Uses OpenAI CLIP to classify cinematic frames via natural language context."""
        print(f"Loading Vision model (CLIP) to GPU ({'CUDA' if self.device == 0 else 'CPU'})...")
        
        processor = CLIPProcessor.from_pretrained(self.model_path, local_files_only=True)
        model = CLIPModel.from_pretrained(self.model_path, local_files_only=True)
        
        classifier = pipeline(
            "zero-shot-image-classification", 
            model=model, 
            tokenizer=processor.tokenizer,
            image_processor=processor.image_processor, 
            device=self.device
        )
        
        # We define highly contextual natural language labels. 
        candidate_labels = [
            "explicit cinematic nudity or sex scene",
            "safe for work movie scene",
            "people kissing or making out"
        ]
        
        TARGET_LABEL = "explicit cinematic nudity or sex scene"
        
        results = []
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        for frame_file in frame_files:
            frame_idx = int(frame_file.split('_')[1].split('.')[0])
            timestamp_sec = frame_idx / fps
            
            img_path = os.path.join(frames_dir, frame_file)
            image = Image.open(img_path).convert("RGB")
            
            # Predict
            preds = classifier(image, candidate_labels=candidate_labels)
            
            # Find the target label score
            for pred in preds:
                if pred['label'] == TARGET_LABEL and pred['score'] >= threshold:
                    results.append({
                        "start": max(0.0, timestamp_sec - (1/fps)), 
                        "end": timestamp_sec,
                        "label": "Nudity/NSFW", 
                        "confidence": float(pred['score'])
                    })
                    break
        
        # --- STRICT VRAM FLUSH ---
        print("Unloading Vision model from VRAM...")
        del classifier
        del model
        del processor
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return results
