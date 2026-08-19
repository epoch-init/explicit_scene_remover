import os
from transformers import CLIPProcessor, CLIPModel
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

def download_and_bundle():
    models_dir = os.path.join(os.getcwd(), 'models')
    os.makedirs(models_dir, exist_ok=True)

    print("Downloading Vision Model (OpenAI CLIP Zero-Shot)...")
    clip_path = os.path.join(models_dir, 'vision_clip')
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_processor.save_pretrained(clip_path)
    clip_model.save_pretrained(clip_path)

    print("Downloading Audio Speech Model (openai/whisper-tiny)...")
    audio_path = os.path.join(models_dir, 'audio_whisper')
    audio_processor = AutoProcessor.from_pretrained("openai/whisper-tiny")
    audio_model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny")
    audio_processor.save_pretrained(audio_path)
    audio_model.save_pretrained(audio_path)

    print("Downloading Audio Events Model (MIT/ast-finetuned-audioset)...")
    event_path = os.path.join(models_dir, 'audio_events_ast')
    event_processor = AutoFeatureExtractor.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
    event_model = AutoModelForAudioClassification.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
    event_processor.save_pretrained(event_path)
    event_model.save_pretrained(event_path)

    print(f"✅ All 3 Models successfully bundled for offline use!")

if __name__ == "__main__":
    download_and_bundle()
