import logging
import sys
from cloud_tasks_emulator import Scheduler

if __name__ == "__main__":
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
else:
    log = logging.getLogger(__name__)
