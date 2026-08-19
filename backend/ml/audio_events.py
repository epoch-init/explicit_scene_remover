import os
import gc
import torch
import soundfile as sf
import numpy as np
from transformers import pipeline, AutoFeatureExtractor, AutoModelForAudioClassification

# AudioSet categories highly correlated with explicit scenes
TARGET_SOUNDS = ["Moan", "Groan", "Pant", "Breathing", "Sigh"]

class AudioEventModelWrapper:
    def __init__(self, model_folder="models/audio_events_ast"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, model_folder)
        
        config_file = os.path.join(self.model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Model config not found at {config_file}.")
            
        self.device = 0 if torch.cuda.is_available() else -1

    def analyze(self, audio_path, threshold=0.15):
        """Chunks audio and identifies explicit sounds like moaning."""
        print(f"Loading Audio Events model to GPU ({'CUDA' if self.device == 0 else 'CPU'})...")
        
        processor = AutoFeatureExtractor.from_pretrained(self.model_path, local_files_only=True)
        model = AutoModelForAudioClassification.from_pretrained(self.model_path, local_files_only=True)
        
        classifier = pipeline("audio-classification", model=model, feature_extractor=processor, device=self.device)
        
        results = []
        
        # Read the 16kHz wav file we extracted earlier
        data, samplerate = sf.read(audio_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1) # Convert to mono if stereo
            
        # Break audio into 5-second overlapping chunks to ensure we don't miss sounds on boundaries
        chunk_duration = 5.0 
        step_duration = 4.0  
        
        chunk_samples = int(chunk_duration * samplerate)
        step_samples = int(step_duration * samplerate)
        total_samples = len(data)
        
        for start_sample in range(0, total_samples, step_samples):
            end_sample = min(start_sample + chunk_samples, total_samples)
            chunk = data[start_sample:end_sample].astype(np.float32)
            
            if len(chunk) < samplerate: # Skip tail ends less than 1 second
                continue
                
            start_sec = start_sample / samplerate
            end_sec = end_sample / samplerate
            
            # Predict the sound classes in this 5 second block
            preds = classifier(chunk)
            
            for pred in preds:
                # We use a lower internal threshold because AudioSet confidence spreads across 527 classes
                if pred['label'] in TARGET_SOUNDS and pred['score'] >= threshold:
                    results.append({
                        "start": start_sec,
                        "end": end_sec,
                        "label": "Explicit Sounds",
                        "confidence": float(pred['score'])
                    })
                    break # Mark the chunk once and move on
                    
        # --- STRICT 2GB VRAM FLUSH ---
        print("Unloading Audio Events model from VRAM...")
        del classifier
        del model
        del processor
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return results
