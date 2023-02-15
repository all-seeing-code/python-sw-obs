import requests
import dill
import time
class ComputeThisResult:
    def __init__(self, url, func, args):
        self.url = url
        self.func = func
        self.args = args

    def run(self):
        start_time = time.time()
        payload = {
            'function': dill.dumps(self.func),
            'args': self.args
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url, headers=headers, data=dill.dumps(payload))
        response.raise_for_status()
        return {"Result: " : response.json()['result'], "Time taken: " : time.time() - start_time}

def compute_this(url="http://localhost:5000/submit"):
    def decorator(func):
        def wrapper(*args):
            return ComputeThisResult(url, func, *args).run()
        return wrapper
    return decorator
