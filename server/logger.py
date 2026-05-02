import sys
from datetime import datetime
from config import LOG_FILE

LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
CURRENT_LEVEL = "DEBUG"


def _write(level: str, message: str):
    if LEVELS[level] < LEVELS[CURRENT_LEVEL]:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {message}\n"

    sys.stdout.write(line)
    sys.stdout.flush()

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


class _Logger:
    def debug(self, msg: str):
        _write("DEBUG", msg)

    def info(self, msg: str):
        _write("INFO", msg)

    def warning(self, msg: str):
        _write("WARNING", msg)

    def error(self, msg: str, exc_info: bool = False):
        _write("ERROR", msg)
        if exc_info:
            import traceback
            tb = traceback.format_exc()
            if tb.strip() != "NoneType: None":
                _write("ERROR", tb)


logger = _Logger()