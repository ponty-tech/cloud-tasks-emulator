import json
import logging
import math
import sys
import threading
from time import sleep, time

import requests
from redis.exceptions import ConnectionError

from .decoded_redis import rc
from .config import QUEUE_NAME_DEFERRED, QUEUE_NAME, CTE_BASE_URL

log = logging.getLogger(__name__)


class DeferredTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        log.info("init defer")
        self.quit = threading.Event()

    def run(self):
        log.info("running defer")
        # log.info(self.quit.is_set())
        while not self.quit.is_set():
            try:
                items = rc.zrange(QUEUE_NAME_DEFERRED, 0, 0, withscores=True)
            except ConnectionError:
                sleep(5)
                continue
            if not items or items[0][1] > time():
                sleep(0.2)
                continue
            log.info(json.dumps(items))
            queue_task = json.loads(items[0][0])
            log.info(json.dumps(queue_task))
            make_request(**queue_task)
            rc.zrem(QUEUE_NAME_DEFERRED, items[0][0])
        log.info("stopping defer")


# def drain():
#     log.info("Draining queues %s, %s", QUEUE_NAME, QUEUE_NAME_DEFERRED)
#     try:
#         rc.delete(QUEUE_NAME)
#         rc.delete(QUEUE_NAME_DEFERRED)
#     except ConnectionError:
#         log.warning("Redis not alive. Queue not drained.")


def make_request(task_id, method, uri, body, retries, headers=None):
    if "http" not in uri:
        url = "{0}{1}".format(CTE_BASE_URL, uri)
    else:
        url = uri

    kwargs = dict()
    if body is not None:
        kwargs["data"] = body

    log.info("Making request for task %s", task_id)
    if headers:
        headers.update(
            {
                "X-AppEngine-QueueName": "cte-emulator",
                "X-Cloudtasks-Taskname": task_id,
                "Content-Type": "application/json",
            }
        )
    else:
        headers = {
            "X-AppEngine-QueueName": "cte-emulator",
            "X-Cloudtasks-Taskname": task_id,
            "Content-Type": "application/json",
        }

    r = requests.request(method, url, headers=headers, allow_redirects=False, **kwargs)
    if r.status_code >= 200 and r.status_code <= 299:
        log.info("Request for task %s successful", task_id)
        return True

    # we have failed...
    retries += 1
    if retries > 3:
        log.error("Permanently failed task %s", task_id)
        return False

    cte_task = dict(task_id=task_id, method=method, uri=uri, body=body, retries=retries)
    cte_task_encoded = json.dumps(cte_task)

    execution_ts = math.ceil(time() + retries**3)
    rc.zadd(QUEUE_NAME_DEFERRED, {cte_task_encoded: execution_ts})

    return False


# def make_test_task():
#     ctc = CloudTasksClient()

#     test_task = {"app_engine_http_request": {"http_method": "GET", "relative_uri": "/api/v2/user"}}

#     parent = ctc.queue_path("prs-next", "europe-west1", "default")
#     ctc.create_task(parent, test_task)


# def make_test_task_deferred():
#     from google.protobuf import timestamp_pb2  # noqa

#     ctc = CloudTasksClient()

#     test_task = {"app_engine_http_request": {"http_method": "GET", "relative_uri": "/api/v2/user"}}
#     d = datetime.utcnow() + timedelta(seconds=5)
#     timestamp = timestamp_pb2.Timestamp()
#     timestamp.FromDatetime(d)
#     test_task["schedule_time"] = timestamp
#     parent = ctc.queue_path("prs-next", "eu-west1", "default")
#     ctc.create_task(request={"parent": parent, "task": test_task})


def watcher():
    log.info("Starting CTE")
    log.info("Using Queuename: %s", QUEUE_NAME)
    log.info("Using Queuename: %s", QUEUE_NAME_DEFERRED)
    try:
        t1 = DeferredTask()
        t1.start()
        while True:
            try:
                item = rc.blpop(QUEUE_NAME)
            except ConnectionError as e:
                log.error(e)
                sleep(5)
                continue
            queue_task = json.loads(item[1])
            try:
                make_request(**queue_task)
            except TypeError as e:
                log.error(e)
    except KeyboardInterrupt:
        # todo handling shutdown gracefully
        log.info("")
        t1.quit.set()
        t1.join()
        # drain()
        log.info("CTE closed")
        sys.exit(0)
