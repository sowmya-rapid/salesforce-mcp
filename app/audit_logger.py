import logging
import json
from datetime import datetime

logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("logs/audit.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(message)s"))

if not logger.handlers:
    logger.addHandler(handler)


def audit_log(
    tool: str,
    inputs: dict,
    result,
    status: str,
    correlation_id: str,
):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool,
        "inputs": inputs,
        "result": result,
        "status": status,
        "correlation_id": correlation_id,
    }
    logger.info(json.dumps(log_entry))
