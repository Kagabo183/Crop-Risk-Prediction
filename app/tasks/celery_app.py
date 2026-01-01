from celery import Celery
import os

# Broker/res backend configuration - prefer explicit env vars set by the environment
BROKER = os.environ.get('CELERY_BROKER_URL') or (f"redis://{os.environ.get('REDIS_URL') or os.environ.get('REDIS_HOST','redis')}:6379/0")
RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or os.environ.get('CELERY_RESULT_BACKEND')

celery_app = Celery('crop_risk')
celery_app.conf.broker_url = BROKER
if RESULT_BACKEND:
    celery_app.conf.result_backend = RESULT_BACKEND
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']

# Run periodic scanner every 10 minutes to auto-enqueue processing of new TIFFs
celery_app.conf.timezone = 'UTC'
celery_app.conf.beat_schedule = {
    'scan-sentinel2-every-10-mins': {
        'task': 'app.tasks.process_tasks.scan_and_enqueue',
        'schedule': 600.0,
        'args': (),
    }
}


@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
