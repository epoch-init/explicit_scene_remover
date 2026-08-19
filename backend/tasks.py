import os
import uuid
from celery import Celery
from flask_socketio import SocketIO
from config import Config
from utils.extraction import extract_media
from ml.vision import VisionModelWrapper
from ml.audio import AudioModelWrapper
from utils.aggregator import process_cuts
from utils.export import export_clean_media
from ml.audio_events import AudioEventModelWrapper

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

@celery_app.task(bind=True)
def export_video_task(self, video_path, srt_path, cuts, mode):
    socketio.emit('task_progress', {'status': 'Starting Export...', 'progress': 10})
    
    # Save the output in a 'completed' folder in the project root
    output_dir = os.path.join(os.getcwd(), 'completed')
    
    try:
        socketio.emit('task_progress', {
            'status': 'Running FFmpeg (This may take a while for Frame-Accurate mode)...', 
            'progress': 50
        })
        
        result_paths = export_clean_media(video_path, srt_path, cuts, output_dir, mode)
        
        socketio.emit('task_progress', {'status': 'Export Complete!', 'progress': 100})
        socketio.emit('export_complete', {
            'video_path': result_paths['video'],
            'subtitle_path': result_paths['subtitle']
        })
        
        return {"status": "Success", "paths": result_paths}
    except Exception as e:
        socketio.emit('task_progress', {'status': f'Export Error: {str(e)}', 'progress': 0})
        return {"status": "Failed", "error": str(e)}

@celery_app.task(bind=True)
def analyze_video_task(self, video_path, fps, target_labels, threshold, padding):
    task_id = self.request.id or str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), 'temp', task_id)
    raw_cuts = []
    
    try:
        # 1. Extraction
        socketio.emit('task_progress', {'status': 'Extracting frames & audio...', 'progress': 10})
        media = extract_media(video_path, temp_dir, fps=fps)
        
        # 2. Vision AI (Nudity)
        if "Nudity/NSFW" in target_labels:
            socketio.emit('task_progress', {'status': 'Analyzing video frames...', 'progress': 30})
            vision = VisionModelWrapper()
            vision_cuts = vision.analyze(media['frames_dir'], fps=fps, threshold=0.0)
            raw_cuts.extend(vision_cuts)
        
        # 3. Audio Text AI (Profanity)
        if "Profanity" in target_labels:
            socketio.emit('task_progress', {'status': 'Transcribing audio for profanity...', 'progress': 55})
            audio = AudioModelWrapper()
            audio_cuts = audio.analyze(media['audio_path'])
            raw_cuts.extend(audio_cuts)

        # 4. Audio Events AI (Moaning/Explicit Sounds)
        if "Explicit Sounds" in target_labels:
            socketio.emit('task_progress', {'status': 'Scanning audio for explicit sounds...', 'progress': 80})
            audio_events = AudioEventModelWrapper()
            # We pass the user's selected threshold directly to the wrapper here
            event_cuts = audio_events.analyze(media['audio_path'], threshold=threshold)
            raw_cuts.extend(event_cuts)

        socketio.emit('task_progress', {'status': 'Filtering & Formatting cuts...', 'progress': 95})

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

