from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name, broker='redis://localhost:6379/0')  # Adjust the Redis URL if needed
    celery.conf.update(app.config)
    return celery
