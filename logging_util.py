# vusbpb/logging_util.py
import sys


def _log(level: str, msg: str) -> None:
    """Log single line to stderr; systemd/journald zbierze to automatycznie."""
    sys.stderr.write(f"[{level}] vusbpb: {msg}\n")
    sys.stderr.flush()


def log_info(msg: str) -> None:
    _log("INFO", msg)


def log_warning(msg: str) -> None:
    _log("WARNING", msg)


def log_error(msg: str) -> None:
    _log("ERROR", msg)
