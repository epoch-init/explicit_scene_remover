from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app) # Allow React frontend to connect
    
    # Initialize SocketIO with Redis message queue so Celery can emit events
    socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'], cors_allowed_origins="*")

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    from tasks import analyze_video_mock
    @app.route('/api/analyze', methods=['POST'])
    def trigger_analysis():
        # Trigger the Celery task
        task = analyze_video_mock.delay()
        return jsonify({"task_id": task.id, "status": "Task Started"}), 202

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
