"""
Simple file-based request history tracking.
Phase 3 will replace this with PostgreSQL.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Store history in app's data directory
HISTORY_DIR = Path("/tmp/dns_requests") if os.path.exists("/tmp") else Path("./data/requests")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_request(
    zone: str,
    action: str,
    records: list[dict[str, Any]],
    justification: str,
    results: list[dict[str, Any]],
    user_ip: str | None = None,
) -> str:
    """
    Save a DNS request to history.
    Returns the request ID.
    """
    request_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    
    request_data = {
        "id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "zone": zone,
        "action": action,
        "records": records,
        "justification": justification,
        "results": results,
        "user_ip": user_ip,
        "success_count": sum(1 for r in results if r.get("status") == "success"),
        "error_count": sum(1 for r in results if r.get("status") == "error"),
    }
    
    # Save to file
    file_path = HISTORY_DIR / f"{request_id}.json"
    with open(file_path, "w") as f:
        json.dump(request_data, f, indent=2)
    
    return request_id


def get_request_history(limit: int = 50) -> list[dict[str, Any]]:
    """
    Get recent request history.
    Returns list of requests, newest first.
    """
    if not HISTORY_DIR.exists():
        return []
    
    # Get all request files
    request_files = sorted(
        HISTORY_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:limit]
    
    requests = []
    for file_path in request_files:
        try:
            with open(file_path) as f:
                requests.append(json.load(f))
        except Exception:
            continue
    
    return requests


def get_request_by_id(request_id: str) -> dict[str, Any] | None:
    """
    Get a specific request by ID.
    """
    file_path = HISTORY_DIR / f"{request_id}.json"
    if not file_path.exists():
        return None
    
    try:
        with open(file_path) as f:
            return json.load(f)
    except Exception:
        return None


def cleanup_old_requests(days: int = 90) -> int:
    """
    Delete requests older than specified days.
    Returns number of requests deleted.
    """
    if not HISTORY_DIR.exists():
        return 0
    
    import time
    cutoff_time = time.time() - (days * 86400)
    deleted = 0
    
    for file_path in HISTORY_DIR.glob("*.json"):
        if file_path.stat().st_mtime < cutoff_time:
            file_path.unlink()
            deleted += 1
    
    return deleted
