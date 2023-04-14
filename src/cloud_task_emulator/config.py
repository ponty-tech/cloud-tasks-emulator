import os

CTE_PREFIX = os.getenv("CTE_PREFIX", "cte")
CTE_BASE_URL = os.getenv("CTE_BASE_URL", "http://localhost:6002")
QUEUE_NAME = "{0}:queue".format(CTE_PREFIX)
QUEUE_NAME_DEFERRED = "{0}:queue:deferred".format(CTE_PREFIX)
PNTY_ENV = os.getenv("PNTY_ENV", "prod")
