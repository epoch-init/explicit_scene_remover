import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    SOCKETIO_MESSAGE_QUEUE = 'redis://localhost:6379/0' # Allows Celery to broadcast WS
