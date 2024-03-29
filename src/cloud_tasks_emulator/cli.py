import logging
import sys
from .scheduler import Scheduler

def main():
    logging.basicConfig(format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
    log = logging.getLogger(__name__)
    print(__name__)
    log.info("Starting CTE")
    sched = Scheduler()
    try:
        sched.start()
        sched.join()
    except KeyboardInterrupt:
        log.info("Terminating CTE")
        sched.quit.set()
        sched.join()
        sched.drain()
        log.info("Closed CTE")
        sys.exit(0)

