import time
from threading import Lock

current_user_id = None
current_role = None


class GlobalState:
    def __init__(self):
        self.active_drivers = {}
        self.lock = Lock()

    def driver_login(self, driver_id, name):
        with self.lock:
            self.active_drivers[driver_id] = {
                "name": name,
                "last_seen": time.time()
            }

    def get_driver_status(self, timeout=300):
        """
        timeout: seconds a driver is considered online after login
        """
        now = time.time()
        status = {}

        with self.lock:
            for did, info in self.active_drivers.items():
                online = (now - info["last_seen"]) < timeout
                status[did] = {
                    "name": info["name"],
                    "online": online,
                    "last_seen": info["last_seen"]
                }
        return status


GLOBAL_STATE = GlobalState()
