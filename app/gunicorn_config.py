from app import config as conf

bind = conf.GUNICORN_BIND
workers = conf.GUNICORN_WORKERS
timeout = conf.GUNICORN_TIMEOUT

loglevel = "info"