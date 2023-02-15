import json
import multiprocessing
import os

from flask import Flask, Response, jsonify, request
import prometheus_client, time
import dill

from prometheus_client import Counter, Gauge, generate_latest
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# create a counter metric to track the number of requests
request_received = Counter('request_received', 'Number of requests processed')
pending_queries = Gauge("pending_queries", "The number of queries pending in queue")
jobs_processed = Gauge("jobs_processed", "The number of jobs processed")
worker_count = Gauge("worker_count", "Number of worker processes in worker pool")

metrics = PrometheusMetrics(app)
metrics.info("app_info", "App Info, this can be anything you want", version="1.0.0")

class DistributedWorkerPool:
    def __init__(self, num_workers):
        self.work_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.num_workers = num_workers
        self.workers = [
            multiprocessing.Process(target=self.worker, args=(self.work_queue, self.result_queue))
            for _ in range(num_workers)
        ]
        for worker in self.workers:
            worker.start()

    def update_worker_count(self, new_worker_count):
        if new_worker_count < self.num_workers:
            # Stop the extra workers
            for i in range(self.num_workers - new_worker_count):
                self.work_queue.put((None, None))
            self.workers = self.workers[:new_worker_count]
        else:
            # Start new workers
            for i in range(new_worker_count - self.num_workers):
                new_worker = multiprocessing.Process(target=self.worker, args=(self.work_queue, self.result_queue))
                self.workers.append(new_worker)
                new_worker.start()
        self.num_workers = new_worker_count

    def worker(self, work_queue, result_queue):
        while True:
            func, args = work_queue.get() # Blocking untill the item is not available
            if func is None:
                break
            function = dill.loads(func)
            result = function(args)
            result_queue.put(result)

    def submit_work(self, func, *args):
        pending_queries.inc()
        self.work_queue.put((func, *args))

    def get_result(self):
        res = self.result_queue.get()
        pending_queries.dec()
        jobs_processed.inc()
        return res

    def stop(self):
        for _ in self.workers:
            self.work_queue.put((None, None, None))
        for worker in self.workers:
            worker.join()


worker_pool = DistributedWorkerPool(4)
worker_count.set(4)
if os.environ.get("WORKERS") is not None:
    count = int(os.getenv("WORKERS"))
    worker_pool.update_worker_count(count)
    worker_count.set(count)

# @app.route('/metrics')
# def metrics():
#     return generate_latest()

@app.route("/update_worker", methods=["POST"])
def handle_update_worker():
    count = request.json['count']
    worker_pool.update_worker_count(count)
    worker_count.set(count)
    return Response(json.dumps({"worker_count": count}), content_type='text/plain')

@app.route("/submit", methods=["POST"])
def handle_request():
    # increment the request counter
    request_received.inc()
    data = request.data
    data = dill.loads(data)
    args = data['args']
    worker_pool.submit_work(data['function'], args)
    result = worker_pool.get_result()
    return json.dumps({"result": result})

if __name__ == "__main__":
    app.run(host='0.0.0.0')
