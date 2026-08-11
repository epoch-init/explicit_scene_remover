import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from utils.file_browser import get_directory_contents

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app) 
    
    socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'], cors_allowed_origins="*")

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route('/api/files/browse', methods=['GET'])
    def browse_files():
        # Default to root on Ubuntu ('/') or C:/ on Windows if no path provided
        target_path = request.args.get('path', '/') 
        result = get_directory_contents(target_path)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result), 200

    from tasks import analyze_video_task
    @app.route('/api/analyze', methods=['POST'])
    def trigger_analysis():
        data = request.json or {}
        video_path = data.get('video_path')
        fps = data.get('fps', 1.0)
        
        if not video_path:
            return jsonify({"error": "video_path is required"}), 400
            
        task = analyze_video_task.delay(video_path, fps)
        return jsonify({"task_id": task.id, "status": "Task Started"}), 202

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
