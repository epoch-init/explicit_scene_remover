import os
import uuid
from celery import Celery
from flask_socketio import SocketIO
from config import Config
from utils.extraction import extract_media
from ml.vision import VisionModelWrapper
from ml.audio import AudioModelWrapper
from utils.aggregator import process_cuts # NEW

celery_app = Celery('autocleanse_tasks', broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
socketio = SocketIO(message_queue=Config.SOCKETIO_MESSAGE_QUEUE)

@celery_app.task(bind=True)
def analyze_video_task(self, video_path, fps, target_labels, threshold, padding):
    task_id = self.request.id or str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), 'temp', task_id)
    raw_cuts = []
    
    try:
        # 1. Extraction
        socketio.emit('task_progress', {'status': 'Extracting frames & audio...', 'progress': 10})
        media = extract_media(video_path, temp_dir, fps=fps)
        
        # 2. Vision AI
        if "Nudity/NSFW" in target_labels:
            socketio.emit('task_progress', {'status': 'Analyzing video frames...', 'progress': 30})
            vision = VisionModelWrapper()
            # Pass 0.0 threshold to wrapper so Aggregator can handle the real threshold later
            vision_cuts = vision.analyze(media['frames_dir'], fps=fps, threshold=0.0)
            raw_cuts.extend(vision_cuts)
        
        # 3. Audio AI
        if "Profanity" in target_labels:
            socketio.emit('task_progress', {'status': 'Analyzing audio track...', 'progress': 65})
            audio = AudioModelWrapper()
            audio_cuts = audio.analyze(media['audio_path'])
            raw_cuts.extend(audio_cuts)

        socketio.emit('task_progress', {'status': 'Filtering & Formatting cuts...', 'progress': 95})

        # NEW: Process cuts based on user preferences
        final_cuts = process_cuts(raw_cuts, target_labels, threshold, padding)

        socketio.emit('task_complete', {
            'status': 'Complete!',
            'progress': 100,
            'cuts': final_cuts
        })
        
        return {"status": "Success", "cuts_found": len(final_cuts), "temp_dir": temp_dir}
        
    except Exception as e:
        socketio.emit('task_progress', {'status': f'Error: {str(e)}', 'progress': 0})
        return {"status": "Failed", "error": str(e)}
