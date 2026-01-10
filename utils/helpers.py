# utils/helpers.py
import time, random
from datetime import datetime

def retry_on_exception(func, attempts=3, delay=2, backoff=2, exceptions=(Exception,), *fargs, **kwargs):
    for i in range(attempts):
        try:
            return func(*fargs, **kwargs)
        except exceptions as e:
            if i == attempts - 1:
                raise
            time.sleep(delay * (backoff ** i))

def now_iso():
    return datetime.utcnow().isoformat() + "Z"
