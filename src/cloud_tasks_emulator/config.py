import os


CTE_BASE_URL = os.getenv("CTE_BASE_URL", "https://utveckling.pontydev.se")
SCHEDULER_NAME = "cte:scheduler"
QUEUE_NAME = "cte:queue"

MAX_SCHEDULE_TIME = int(os.getenv("CTE_MAX_SCHEDULE_TIME", "2592000")) # 30 days
