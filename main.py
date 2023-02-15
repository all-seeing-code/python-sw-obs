import time
import concurrent.futures

from distribute_challenge import compute_this

@compute_this()
def func(x):
    time.sleep(x)
    return x*x

@compute_this()
def func2(x):
    return 2*x

if __name__ == "__main__":
    
    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            frs = []
            start_time = time.time()
            for x in range(10):
                frs.append(executor.submit(func, x))

            for r in frs:
                print(r.result())

            print("Total time: ", time.time() - start_time)
        time.sleep(15)