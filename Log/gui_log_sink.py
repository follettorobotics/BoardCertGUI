

class GuiLogSink:
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def write(self, message):
        self.log_queue.put(message)


class StdoutRedirector:
    def __init__(self, queue_value):
        self.queue = queue_value

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass
