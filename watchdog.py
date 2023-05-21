import time
import threading
import subprocess

def start_ping_watchdog(host, ping_interval, watchdog_timeout):
    def ping_thread():
        while True:
            subprocess.run(["ping", "-c", "5", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(ping_interval)

    def watchdog_timer_expired():
        pass

    ping_thread = threading.Thread(target=ping_thread)
    watchdog_timer = threading.Timer(watchdog_timeout, watchdog_timer_expired)

    ping_thread.start()
    watchdog_timer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watchdog_timer.cancel()
        ping_thread.join()

if __name__ == "__main__":
    start_ping_watchdog("google.com", 5, 10)

