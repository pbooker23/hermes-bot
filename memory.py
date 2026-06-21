"""
HERMES Memory System
Uses JSON file storage — no Redis, no extra cost.
Railway persists the /app directory between deploys.
"""

import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/tmp/hermes_memory"))
MAX_HISTORY = 50  # messages per agent per user


class Memory:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: int, agent_key: str) -> Path:
        return MEMORY_DIR / f"{user_id}_{agent_key}.json"

    def _stats_path(self, user_id: int) -> Path:
        return MEMORY_DIR / f"{user_id}_stats.json"

    def _load(self, user_id: int, agent_key: str) -> list:
        path = self._path(user_id, agent_key)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return []
        return []

    def _save(self, user_id: int, agent_key: str, messages: list):
        path = self._path(user_id, agent_key)
        # Keep only last MAX_HISTORY messages
        if len(messages) > MAX_HISTORY:
            messages = messages[-MAX_HISTORY:]
        path.write_text(json.dumps(messages, indent=2))

    def save_message(self, user_id: int, agent_key: str, role: str, content: str):
        messages = self._load(user_id, agent_key)
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save(user_id, agent_key, messages)
        self._increment_stat(user_id, agent_key)

    def get_history(self, user_id: int, agent_key: str, limit: int = 10) -> list:
        messages = self._load(user_id, agent_key)
        # Return only role/content for the API (strip timestamp)
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]

    def clear_history(self, user_id: int, agent_key: str):
        path = self._path(user_id, agent_key)
        if path.exists():
            path.unlink()

    def _increment_stat(self, user_id: int, agent_key: str):
        path = self._stats_path(user_id)
        stats = {}
        if path.exists():
            try:
                stats = json.loads(path.read_text())
            except Exception:
                stats = {}
        stats[agent_key] = stats.get(agent_key, 0) + 1
        stats["total"] = stats.get("total", 0) + 1
        path.write_text(json.dumps(stats))

    def get_stats(self, user_id: int) -> dict:
        path = self._stats_path(user_id)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return {}
        return {}
