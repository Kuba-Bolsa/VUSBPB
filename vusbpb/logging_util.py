import sys


def logInfo(msg: str) -> None:
    saveLog("INFO", msg)


def logWarning(msg: str) -> None:
    saveLog("WARNING", msg)


def logError(msg: str) -> None:
    saveLog("ERROR", msg)


def saveLog(level: str, msg: str) -> None:
    sys.stderr.write(f"[{level}] vusbpb: {msg}\n")
    sys.stderr.flush()