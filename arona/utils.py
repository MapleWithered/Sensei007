import time


def try_until_succ(func, max_retries=5, sleep_time=1):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise e
            time.sleep(sleep_time)
