"""
Firestore Cache and Cloud Sync Engine for SoundWave
Provides high-speed dual-layer caching (in-memory 0ms + disk) and seamless
asynchronous Firestore REST API synchronization for zero-lag performance.
"""

import json
import os
import re
import sys
import time
import threading
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "firestore_cache"
CONFIG_FILE = DATA_DIR / "firebase_config.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Dual-layer in-memory cache: key -> (timestamp, ttl, value)
_MEM_CACHE: Dict[str, Tuple[float, float, Any]] = {}
_MEM_CACHE_LOCK = threading.Lock()

# Background async worker queue for Firestore cloud pushes
_SYNC_QUEUE = []
_SYNC_QUEUE_LOCK = threading.Lock()


def _sanitize_key(key: str) -> str:
    """Sanitize key for filesystem and Firestore document ID."""
    s = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', str(key))
    return s[:128] if len(s) > 128 else s


def to_firestore_value(val: Any) -> Dict[str, Any]:
    """Converts a standard Python object into a Firestore REST field structure."""
    if val is None:
        return {"nullValue": None}
    if isinstance(val, bool):
        return {"booleanValue": val}
    if isinstance(val, int):
        return {"integerValue": str(val)}
    if isinstance(val, float):
        return {"doubleValue": val}
    if isinstance(val, str):
        return {"stringValue": val}
    if isinstance(val, list):
        return {"arrayValue": {"values": [to_firestore_value(v) for v in val]}}
    if isinstance(val, dict):
        fields = {k: to_firestore_value(v) for k, v in val.items()}
        return {"mapValue": {"fields": fields}}
    return {"stringValue": str(val)}


def from_firestore_value(val_obj: Dict[str, Any]) -> Any:
    """Converts a Firestore REST field structure back into a standard Python object."""
    if not isinstance(val_obj, dict):
        return val_obj
    if "nullValue" in val_obj:
        return None
    if "booleanValue" in val_obj:
        return val_obj["booleanValue"]
    if "integerValue" in val_obj:
        try:
            return int(val_obj["integerValue"])
        except Exception:
            return val_obj["integerValue"]
    if "doubleValue" in val_obj:
        return float(val_obj["doubleValue"])
    if "stringValue" in val_obj:
        return val_obj["stringValue"]
    if "arrayValue" in val_obj:
        return [from_firestore_value(v) for v in val_obj["arrayValue"].get("values", [])]
    if "mapValue" in val_obj:
        fields = val_obj["mapValue"].get("fields", {})
        return {k: from_firestore_value(v) for k, v in fields.items()}
    return None


class FirestoreManager:
    """Zero-dependency Firestore REST Client with asynchronous sync."""

    def __init__(self):
        self.project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("FIRESTORE_PROJECT_ID", "")
        self.api_key = os.environ.get("FIREBASE_API_KEY", "")
        self.database = os.environ.get("FIREBASE_DATABASE", "(default)")
        self.load_config()

        # Start background async sync worker daemon
        self._worker_thread = threading.Thread(target=self._background_sync_loop, daemon=True)
        self._worker_thread.start()

    def load_config(self) -> None:
        """Loads configuration from firebase_config.json if available."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if not self.project_id and cfg.get("projectId"):
                        self.project_id = cfg.get("projectId")
                    if not self.api_key and cfg.get("apiKey"):
                        self.api_key = cfg.get("apiKey")
            except Exception as e:
                print(f"[FirestoreManager] Error reading config: {e}", file=sys.stderr)

    def save_config(self, project_id: str, api_key: str = "") -> None:
        """Updates and persists the Firestore configuration."""
        self.project_id = project_id.strip()
        if api_key:
            self.api_key = api_key.strip()
        data = {"projectId": self.project_id, "apiKey": self.api_key, "updated_at": time.time()}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[FirestoreManager] Error saving config: {e}", file=sys.stderr)

    def is_configured(self) -> bool:
        return bool(self.project_id)

    def get_status(self) -> Dict[str, Any]:
        with _MEM_CACHE_LOCK:
            mem_count = len(_MEM_CACHE)
        with _SYNC_QUEUE_LOCK:
            pending_count = len(_SYNC_QUEUE)

        return {
            "status": "connected" if self.is_configured() else "standby_local_cache",
            "project_id": self.project_id or "not_configured (using local 0ms high-speed engine)",
            "has_api_key": bool(self.api_key),
            "memory_cache_count": mem_count,
            "pending_sync_queue": pending_count,
            "backend_mode": "Firestore Dual-Layer Real-Time Cache"
        }

    def _build_doc_url(self, collection: str, doc_id: str) -> str:
        base = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database}/documents/{collection}/{doc_id}"
        if self.api_key:
            base += f"?key={urllib.parse.quote(self.api_key)}"
        return base

    def get_document(self, collection: str, doc_id: str, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        """Fetches a document directly from Firestore REST API with a strict low timeout."""
        if not self.is_configured():
            return None

        clean_doc_id = _sanitize_key(doc_id)
        url = self._build_doc_url(collection, clean_doc_id)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SoundWave/2026"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    fields = raw_data.get("fields", {})
                    return {k: from_firestore_value(v) for k, v in fields.items()}
        except Exception:
            # Degrade gracefully to local cache on any network/timeout issue
            return None
        return None

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any], timeout: float = 3.0) -> bool:
        """Pushes a document to Firestore REST API using PATCH (upsert)."""
        if not self.is_configured():
            return False

        clean_doc_id = _sanitize_key(doc_id)
        url = self._build_doc_url(collection, clean_doc_id)
        fs_fields = {k: to_firestore_value(v) for k, v in data.items()}
        payload = json.dumps({"fields": fs_fields}).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, method="PATCH", headers={
                "Content-Type": "application/json",
                "User-Agent": "SoundWave/2026"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            return False

    def queue_async_set(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        """Queues an update to Firestore in the background for zero lag on client requests."""
        if not self.is_configured():
            return
        with _SYNC_QUEUE_LOCK:
            _SYNC_QUEUE.append((collection, doc_id, data))

    def _background_sync_loop(self) -> None:
        """Daemon thread: flushes queue to Firestore periodically without affecting request latency."""
        while True:
            item = None
            with _SYNC_QUEUE_LOCK:
                if _SYNC_QUEUE:
                    item = _SYNC_QUEUE.pop(0)

            if item:
                col, doc_id, data = item
                try:
                    self.set_document(col, doc_id, data)
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                time.sleep(1.0)


# Global singleton instance
firestore_mgr = FirestoreManager()


class ZeroLagCache:
    """
    High-Performance Zero-Lag Cache.
    Retrieves from In-Memory Cache in <0.1ms.
    Backs up to Disk Cache and Firestore Cloud asynchronously.
    """

    @staticmethod
    def get(collection: str, key: str, default: Any = None) -> Any:
        full_key = f"{collection}::{key}"
        now = time.time()

        # 1. Check in-memory cache (0.01ms)
        with _MEM_CACHE_LOCK:
            if full_key in _MEM_CACHE:
                cached_time, ttl, val = _MEM_CACHE[full_key]
                if now - cached_time < ttl:
                    return val

        # 2. Check disk cache (~0.5ms)
        disk_path = CACHE_DIR / f"{_sanitize_key(full_key)}.json"
        if disk_path.exists():
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    cached_time = entry.get("_timestamp", 0)
                    ttl = entry.get("_ttl", 3600)
                    if now - cached_time < ttl:
                        data = entry.get("data")
                        with _MEM_CACHE_LOCK:
                            _MEM_CACHE[full_key] = (cached_time, ttl, data)
                        return data
            except Exception:
                pass

        # 3. Check Firestore (optional, fast timeout)
        if firestore_mgr.is_configured():
            doc = firestore_mgr.get_document(collection, _sanitize_key(key), timeout=0.8)
            if doc and "data" in doc:
                val = doc.get("data")
                ZeroLagCache.set(collection, key, val, ttl=3600, sync_firestore=False)
                return val

        return default

    @staticmethod
    def set(collection: str, key: str, value: Any, ttl: float = 3600, sync_firestore: bool = True) -> None:
        full_key = f"{collection}::{key}"
        now = time.time()

        # 1. Update in-memory cache immediately (0ms)
        with _MEM_CACHE_LOCK:
            _MEM_CACHE[full_key] = (now, ttl, value)

        # 2. Update disk cache asynchronously or synchronously
        try:
            disk_path = CACHE_DIR / f"{_sanitize_key(full_key)}.json"
            with open(disk_path, "w", encoding="utf-8") as f:
                json.dump({"_timestamp": now, "_ttl": ttl, "data": value}, f)
        except Exception:
            pass

        # 3. Queue to Firestore asynchronously (Never blocks caller!)
        if sync_firestore and firestore_mgr.is_configured():
            firestore_mgr.queue_async_set(collection, _sanitize_key(key), {
                "key": key,
                "timestamp": now,
                "ttl": ttl,
                "data": value
            })

    @staticmethod
    def clear() -> None:
        with _MEM_CACHE_LOCK:
            _MEM_CACHE.clear()
