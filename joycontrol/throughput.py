# throughput monitor

from datetime import datetime, timedelta


class ThroughputMonitor:

    INTERVAL = timedelta(seconds=3)

    def __init__(self, interval=INTERVAL):
        self.start_time = datetime.now()
        self.current_count = 0
        self.last_time = self.start_time
        self.last_count = 0
        self.counts_sec = 0
        self.interval = interval

    def increment(self):
        self.current_count += 1

    def update(self):
        now = datetime.now()
        count = self.current_count
        if (now - self.start_time) >= self.interval:
            self.counts_sec = count / self.interval.seconds()
            self.start_time = now
            self.current_count = 0
        self.last_time = now
        self.last_count = count
