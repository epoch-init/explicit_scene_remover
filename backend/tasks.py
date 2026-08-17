import os
import uuid
from celery import Celery
from flask_socketio import SocketIO
from config import Config
from utils.extraction import extract_media
from ml.vision import VisionModelWrapper
from ml.audio import AudioModelWrapper

celery_app = Celery('autocleanse_tasks', broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
socketio = SocketIO(message_queue=Config.SOCKETIO_MESSAGE_QUEUE)

@celery_app.task(bind=True)
def analyze_video_task(self, video_path, fps):
    task_id = self.request.id or str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), 'temp', task_id)
    all_cuts = []
    
    try:
        # 1. Extraction
        socketio.emit('task_progress', {'status': 'Extracting frames & audio...', 'progress': 10})
        media = extract_media(video_path, temp_dir, fps=fps)
        
        # 2. Vision AI (Load -> Process -> Unload)
        socketio.emit('task_progress', {'status': 'Loading Vision AI...', 'progress': 30})
        vision = VisionModelWrapper()
        
        socketio.emit('task_progress', {'status': 'Analyzing video frames...', 'progress': 45})
        vision_cuts = vision.analyze(media['frames_dir'], fps=fps, threshold=0.7)
        all_cuts.extend(vision_cuts)
        
        # 3. Audio AI (Load -> Process -> Unload)
        socketio.emit('task_progress', {'status': 'Loading Audio AI...', 'progress': 65})
        audio = AudioModelWrapper()
        
        socketio.emit('task_progress', {'status': 'Analyzing audio track...', 'progress': 80})
        audio_cuts = audio.analyze(media['audio_path'])
        all_cuts.extend(audio_cuts)

        # Merge results & cleanup message
        socketio.emit('task_progress', {'status': 'Finalizing cuts...', 'progress': 95})

        # Sort cuts chronologically
        all_cuts = sorted(all_cuts, key=lambda x: x['start'])

        socketio.emit('task_complete', {
            'status': 'Complete!',
            'progress': 100,
            'cuts': all_cuts
        })
        
        return {"status": "Success", "cuts_found": len(all_cuts), "temp_dir": temp_dir}
        
    except Exception as e:
        socketio.emit('task_progress', {'status': f'Error: {str(e)}', 'progress': 0})
        return {"status": "Failed", "error": str(e)}
