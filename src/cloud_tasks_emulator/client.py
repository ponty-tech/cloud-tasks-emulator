import json
import os
import time
from uuid import uuid4
from .config import QUEUE_NAME, SCHEDULER_NAME
from google.protobuf.timestamp_pb2 import Timestamp

from .redis_client import rc


class CloudTasksClient:
    def delete_task(self, name):
        name = name.split("/")[-1]

        try:
            rc.zrem(SCHEDULER_NAME, name)
            rc.hdel(QUEUE_NAME, name)
        except ConnectionError as e:
            raise Exception(message=f'Failed to delete task {name}. Error: {e}')

    def create_task(
        self,
        parent,
        task,
        response_view=None,
        retry=object,
        timeout=None,
        metadata=None
    ):
        if parent is None or task is None:
            raise ValueError("Must specify 'parent' and 'task'")

        if response_view is not None:
            raise NotImplementedError()

        if timeout is not None:
            raise NotImplementedError()

        if metadata is not None:
            raise NotImplementedError()

        task_id = str(uuid4())

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

        if os.getenv("PNTY_ENV"):
            if os.getenv("PNTY_ENV") == "dev":
                project_id = "scrubbed-one"
            else:
                project_id = "prs-stage" if os.getenv("PNTY_ENV") == "stage" else "prs-next"
        else:
            project_id = "prs-stage" if os.getenv("FLASK_ENV", "production") == "development" else "prs-next"

        schedule_time = task.get("schedule_time", None)
        if type(schedule_time) == Timestamp:
            schedule_time = schedule_time.to_seconds()
        elif type(schedule_time) == float:
            schedule_time = int(schedule_time)
        elif type(schedule_time) == int:
            pass
        elif schedule_time is None:
            schedule_time = int(time())
        else:
            raise ValueError("Invalid schedule_time. Key must be a Timestamp, float, int or None.")

        cte_task = dict(
            task_id=task_id,
            method=method,
            uri=uri,
            body=body,
            retries=0,
            headers=headers,
            schedule_time=schedule_time,
            name=CloudTasksClient.queue_path(project_id, "europe-west1", "cte-emulator") + "/tasks/" + task_id,
        )
        if body:
            cte_task["body"] = body.decode()

        rc.hset(QUEUE_NAME, task_id, json.dumps(cte_task))
        rc.zadd(SCHEDULER_NAME, {task_id: schedule_time})
        return cte_task

    @staticmethod
    def queue_path(
        project: str,
        location: str,
        queue: str,
    ) -> str:
        """Returns a fully-qualified queue string."""
        return "projects/{project}/locations/{location}/queues/{queue}".format(
            project=project,
            location=location,
            queue=queue,
        )


class NotImplementedError(Exception):
    def __init__(self):
        message = "This feature is not implemented."
        super().__init__(message)


