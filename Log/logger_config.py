# logger_config.py
from loguru import logger

from Log.gui_log_sink import GuiLogSink


def setup_logger(log_queue):
    logger.remove()  # Remove existing handlers
    logger.add(GuiLogSink(log_queue), format="{time} {level} {message}")

    # You can add other configurations here if needed
    # For example, adding a file sink:
    # logger.add("file_{time}.log", rotation="1 day")

    return logger
