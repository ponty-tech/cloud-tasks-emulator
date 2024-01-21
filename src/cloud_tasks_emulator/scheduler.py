from .redis_client import rc
from time import time, sleep
from datetime import datetime
import threading
import logging
import requests
import json
from redis.exceptions import ConnectionError
from .config import QUEUE_NAME, SCHEDULER_NAME, CTE_BASE_URL

class SchedulerException(Exception):
    def __init__(self, message=None, permanent=False):
        self.message = message
        self.permanent = permanent
        super().__init__(message)


class Scheduler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.quit = threading.Event()

    def run(self):
        logging.info("Running Scheduler")
        while not self.quit.is_set():
            try:
                items = rc.zrange(SCHEDULER_NAME, 0, int(time()), byscore=True, withscores=True)
            except ConnectionError as e:
                logging.warning(f"Redis not alive. Retrying in 5 seconds. {e}")
                sleep(5)
                continue
            if not items:
                sleep(0.2)
                continue
            for item in items:
                task = json.loads(rc.hget(QUEUE_NAME, item[0]))
                logging.info(
                    f'Task {task["task_id"]} for URI {task["uri"]} scheduled to be executed at {datetime.fromtimestamp(item[1])}'
                )

                logging.debug(json.dumps(task))
                remove_from_queue = False
                try:
                    self.make_request(**task)
                    remove_from_queue = True
                    logging.info(f'Request for task {task["task_id"]} successful')
                except SchedulerException as e:
                    if e.permanent:
                        remove_from_queue = True
                        logging.error(f'Request for task {task["task_id"]} permanently failed')
                    else:
                        retries = task.get("retries", 0)
                        retries += 1
                        if retries > 3:
                            logging.error(f'Request for task {task["task_id"]} permanently failed')
                            remove_from_queue = True
                        else:
                            logging.info(
                                f'Request for task {task["task_id"]} Failed. Retry {retries} of 3. Retrying in {retries ** 3} seconds.'
                            )
                            task["retries"] = retries
                            rc.hset(QUEUE_NAME, item[0], json.dumps(task))
                            rc.zincrby(SCHEDULER_NAME, retries**3, item[0])

                if remove_from_queue:
                    rc.zrem(SCHEDULER_NAME, item[0])
                    rc.delete(item[0])

    def make_request(self, task_id, method, uri, body, retries, name, schedule_time=None, headers=None):
        if "http" not in uri:
            url = "{0}{1}".format(CTE_BASE_URL, uri)
        else:
            url = uri

        kwargs = dict()
        if body is not None:
            kwargs["data"] = body

        logging.info(f"Making request for task {task_id} scheduled at {datetime.fromtimestamp(schedule_time)}")
        if headers:
            headers.update(
                {
                    "X-AppEngine-QueueName": "cte-emulator",
                    "X-Cloudtasks-Taskname": task_id,
                }
            )
        else:
            headers = {
                "X-AppEngine-QueueName": "cte-emulator",
                "X-Cloudtasks-Taskname": task_id,
            }

        try:
            r = requests.request(method, url, headers=headers, allow_redirects=False, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise SchedulerException(message=f"Permanently failed task {task_id}. Error: {e}", permanent=True)
        if r.status_code < 200 or r.status_code > 299:
            raise SchedulerException(message=f"Failed task {task_id} with status code {r.status_code}")
        return True

    def drain(self):
        logging.info("Draining queues")
        try:
            rc.delete(QUEUE_NAME)
            rc.delete(SCHEDULER_NAME)
        except ConnectionError:
            logging.warning("Redis not alive. Queue not drained.")

