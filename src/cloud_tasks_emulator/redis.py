from redis import StrictRedis
import os
import logging

log = logging.getLogger(__name__)

if not os.getenv("REDIS_URL"):
    log.warning("REDIS_URL not set. Using redis://redis:6379/0")

rc = StrictRedis().from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
