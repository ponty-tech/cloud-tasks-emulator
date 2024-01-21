import json
import os
from uuid import uuid4
from typing import (
    Optional,
    Sequence,
    Tuple,
    Union,
)
from google.cloud.tasks_v2.types import cloudtasks
from google.cloud.tasks_v2.types import task as gct_task
from time import time
from .config import QUEUE_NAME, SCHEDULER_NAME

from .redis_client import rc


class CloudTasksClient:
    def _get_task_from_request(self, request):
        if "parent" not in request:
            raise ValueError("request must contain 'parent'.")
        parent = request["parent"]
        if "task" not in request:
            raise ValueError("request must contain 'task'.")
        task = request["task"]
        return parent, task

    def delete_task(
        self,
        request: Optional[Union[cloudtasks.DeleteTaskRequest, dict]] = None,
        *,
        name: Optional[str] = None,
        retry: Optional[object] = None,
        timeout: Union[float, object] = None,
        metadata: Sequence[Tuple[str, str]] = None,
    ) -> None:
        _, task = self._get_task_from_request(request)

        try:
            rc.zrem(SCHEDULER_NAME, task["task_id"])
            rc.hdel(QUEUE_NAME, task["task_id"])
        except ConnectionError as e:
            raise Exception(message=f'Failed to delete task {task["task_id"]}. Error: {e}')

    def create_task(
        self,
        request: Optional[Union[cloudtasks.CreateTaskRequest, dict]] = None,
        *,
        parent: Optional[str] = None,
        task: Optional[gct_task.Task] = None,
        retry: Optional[object] = None,
        timeout: Union[float, object] = None,
        metadata: Sequence[Tuple[str, str]] = None,
    ) -> gct_task.Task:
        if parent is None and task is None and request is None:
            raise ValueError("Must specify 'parent' or 'task' or 'request'.")

        if request is not None:
            parent, task = self._get_task_from_request(request)
        else:
            if parent is None:
                raise ValueError("parent must not be None.")
            if task is None:
                raise ValueError("task must not be None.")

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

        cte_task = dict(
            task_id=task_id,
            method=method,
            uri=uri,
            body=body,
            retries=0,
            headers=headers,
            schedule_time=task.get("schedule_time", int(time())),
            name=CloudTasksClient.queue_path(project_id, "europe-west1", "cte-emulator") + "/tasks/" + task_id,
        )
        if body:
            cte_task["body"] = body.decode()

        rc.hset(QUEUE_NAME, task_id, json.dumps(cte_task))
        rc.zadd(SCHEDULER_NAME, {task_id: cte_task.get("schedule_time")})
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


