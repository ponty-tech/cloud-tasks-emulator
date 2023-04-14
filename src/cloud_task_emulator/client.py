import json
from uuid import uuid4
from time import sleep
from datetime import datetime, timedelta
from .config import QUEUE_NAME_DEFERRED, QUEUE_NAME, PNTY_ENV
from .decoded_redis import rc


class CloudTasksClient:
    def delete_task(self, name):
        name = name.split("/")[-1]
        try:
            items = rc.zrange(QUEUE_NAME_DEFERRED, 0, 0, withscores=True)
            for item in items:
                ij = json.loads(item[0])
                if ij.get("task_id") == name:
                    rc.zrem(QUEUE_NAME_DEFERRED, item[0])
        except ConnectionError:
            sleep(5)

    def create_task(self, parent, task, response_view=None, retry=object, timeout=None, metadata=None):
        if response_view is not None:
            raise NotImplementedError()

        if timeout is not None:
            raise NotImplementedError()

        if metadata is not None:
            raise NotImplementedError()

        # retry https://googleapis.github.io/google-cloud-python/latest/core/retry.html#google.api_core.retry.Retry  # noqa
        # task['schedule_time'] = None
        try:
            if "app_engine_http_request" in task:
                method = task["app_engine_http_request"]["http_method"]
                uri = task["app_engine_http_request"]["relative_uri"]
                body = task["app_engine_http_request"].get("body", None)
                headers = task["app_engine_http_request"].get("headers", {})
            else:
                method = task["http_request"]["http_method"]
                uri = task["http_request"]["url"]
                body = task["http_request"].get("body", None)
                headers = task["http_request"].get("headers", {})

        except KeyError:
            raise KeyError("Missing required key")

        cte_task = dict(task_id=str(uuid4()), method=method, uri=uri, body=body, retries=0, headers=headers)
        if body:
            cte_task["body"] = body.decode()
        cte_task_encoded = json.dumps(cte_task)

        try:
            if task.get("schedule_time"):
                delay_until = task["schedule_time"]
                # set a faux max queue time for task, in gcloud its 30 days.
                dt_object = datetime.fromtimestamp(delay_until.ToSeconds())
                if dt_object > datetime.now() + timedelta(minutes=5):
                    dt_object = datetime.now() + timedelta(minutes=5)
                    # delay_until = timestamp_pb2.Timestamp()
                    # delay_until.FromDatetime(dt_object)
                execution_ts = (dt_object - datetime(1970, 1, 1)).total_seconds()
                # execution_ts = delay_until.ToSeconds()
                rc.zadd(QUEUE_NAME_DEFERRED, {cte_task_encoded: execution_ts})
            else:
                # none deferred task
                rc.rpush(QUEUE_NAME, cte_task_encoded)
        except ConnectionError:
            raise RuntimeError("Could not connect to Redis.")
        project_id = "prs-stage" if PNTY_ENV == "dev" else "prs-next"

        cte_task["name"] = self.queue_path(project_id, "europe-west1", "cte-emulator") + "/tasks/" + cte_task["task_id"]
        return cte_task

    def queue_path(self, project, location, queue):
        return "projects/{project_id}/locations/{location_id}/queues/{queue_id}".format(
            project_id=project, location_id=location, queue_id=queue
        )


class NotImplementedError(Exception):
    def __init__(self):
        message = "This feature is not implemented."
        super().__init__(message)
