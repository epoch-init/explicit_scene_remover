import os
from transformers import AutoImageProcessor, AutoModelForImageClassification
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

def download_and_bundle():
    models_dir = os.path.join(os.getcwd(), 'models')
    os.makedirs(models_dir, exist_ok=True)

    print("Downloading Vision Model (Falconsai/nsfw_image_detection)...")
    vision_path = os.path.join(models_dir, 'vision_nsfw')
    vision_processor = AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
    vision_model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
    vision_processor.save_pretrained(vision_path)
    vision_model.save_pretrained(vision_path)

    print("Downloading Audio Model (openai/whisper-tiny)...")
    audio_path = os.path.join(models_dir, 'audio_whisper')
    audio_processor = AutoProcessor.from_pretrained("openai/whisper-tiny")
    audio_model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-tiny")
    audio_processor.save_pretrained(audio_path)
    audio_model.save_pretrained(audio_path)

    print(f"✅ Models successfully bundled in {models_dir} for offline use!")

if __name__ == "__main__":
    download_and_bundle()
