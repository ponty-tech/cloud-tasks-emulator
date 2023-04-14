from redis import StrictRedis
import os
import logging

log = logging.getLogger(__name__)


class DecodedRedis(StrictRedis):
    @classmethod
    def from_url(cls, url, db=None, **kwargs):
        log.info("Connecting to Redis: %s", url)
        kwargs["decode_responses"] = True
        return StrictRedis.from_url(url, **kwargs)


rc = DecodedRedis().from_url(os.getenv("REDIS_URL", "redis://localhost:63792/0"))
