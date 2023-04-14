import logging
from cloud_task_emulator import watcher

if __name__ == "__main__":
    logging.basicConfig(format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
    log = logging.getLogger(__name__)

    watcher()
else:
    log = logging.getLogger(__name__)
