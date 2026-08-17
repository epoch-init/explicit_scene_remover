import os
import gc
import torch
from transformers import pipeline

# Hardcoded profanity list for MVP (Can be moved to user settings later)
PROFANITY_LIST = ["fuck", "shit", "bitch", "asshole", "cunt", "damn"]

class AudioModelWrapper:
    def __init__(self, model_path="models/audio_whisper"):
        self.model_path = os.path.join(os.getcwd(), model_path)
        self.device = 0 if torch.cuda.is_available() else -1

    def analyze(self, audio_path):
        """Transcribes audio, extracts word timestamps, and flags profanity."""
        print(f"Loading Audio model to GPU ({'CUDA' if self.device == 0 else 'CPU'})...")
        
        # return_timestamps=True is crucial for mapping text back to video time
        transcriber = pipeline(
            "automatic-speech-recognition", 
            model=self.model_path, 
            device=self.device,
            chunk_length_s=30,
        )
        
        output = transcriber(audio_path, return_timestamps=True)
        
        results = []
        chunks = output.get('chunks', [])
        
        for chunk in chunks:
            text = chunk.get('text', '').lower()
            timestamp = chunk.get('timestamp', (0, 0))
            
            # Check for bad words in this audio chunk
            for word in PROFANITY_LIST:
                if word in text:
                    results.append({
                        "start": timestamp[0],
                        "end": timestamp[1],
                        "label": "Profanity",
                        "confidence": 1.0, # Whisper doesn't easily expose word-level confidence
                        "word": word
                    })
                    break # Tag the chunk once
                    
        # --- STRICT 2GB VRAM FLUSH ---
        print("Unloading Audio model from VRAM...")
        del transcriber
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return results
