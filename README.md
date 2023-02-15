# Set up instructions


## Client

Decorate any function that you wish to run remotely with `@compute_this()`. The client will capture the function and wrap it to be pickled and send over the wire.

Note that the libraries you need to run your function should already be imported in the server's environment. There's no run-time check.

Configure number of parrallel threads by changing `max_workers` in:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            frs = []
            start_time = time.time()
            for x in range(10):
                frs.append(executor.submit(func, x))

            for r in frs:
                print(r.result())

            print("Total time: ", time.time() - start_time)
        time.sleep(15)
```
Since each thread waits for its job to be returned, this is required to concurrently send requests to the server.

Update number of worker processes using:
```bash
curl -H "Content-Type: application/json" -d '{"count":15}' -X POST localhost:5000/update_worker
```


## Server

### Backend
To start backend:
```bash
cd backend
docker-compose up
```

This should build server's docker image and pull prometheus & grafanas image from docker-hub. It will also ensure that all ports are correctly configured.

Server works on a worker queue principle. Each client thread's job gets added to a work queue and the server's processors pick jobs from work queue and add results back on the result queue.

### Grafana
Once the grafana is running, you can login to `localhost:3000` using default username and password `(admin,admin)`. 

Update the datasource with: `http://prometheus:9090`

You can also import a dashboard with relevant metrics by importing [`grafana.json`]()

When successfully import the final dashboard should look like:





