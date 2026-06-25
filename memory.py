"""
HERMES Persistent Memory System
Survives restarts, reboots, and redeploys.
Stores to /opt/hermes/memory/ on the VPS — permanent disk storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/opt/hermes/memory"))
MAX_HISTORY = 100  # messages per agent per user
MAX_CONTEXT = 20   # messages sent to AI per request


class Memory:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "facts").mkdir(exist_ok=True)

    def _path(self, user_id: int, agent_key: str) -> Path:
        return MEMORY_DIR / f"{user_id}_{agent_key}.json"

    def _facts_path(self, user_id: int) -> Path:
        return MEMORY_DIR / "facts" / f"{user_id}.json"

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

    def get_history(self, user_id: int, agent_key: str, limit: int = MAX_CONTEXT) -> list:
        messages = self._load(user_id, agent_key)
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]

    def save_fact(self, user_id: int, key: str, value: str):
        """Save a long-term fact about the user — persists forever"""
        path = self._facts_path(user_id)
        facts = {}
        if path.exists():
            try:
                facts = json.loads(path.read_text())
            except Exception:
                facts = {}
        facts[key] = {
            "value": value,
            "saved_at": datetime.now().isoformat()
        }
        path.write_text(json.dumps(facts, indent=2))

    def get_facts(self, user_id: int) -> dict:
        """Get all long-term facts about the user"""
        path = self._facts_path(user_id)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return {}
        return {}

    def get_facts_as_text(self, user_id: int) -> str:
        """Format facts as a system prompt injection"""
        facts = self.get_facts(user_id)
        if not facts:
            return ""
        lines = ["LONG-TERM MEMORY ABOUT THIS USER:"]
        for key, data in facts.items():
            lines.append(f"- {key}: {data['value']}")
        return "\n".join(lines)

    def clear_history(self, user_id: int, agent_key: str):
        path = self._path(user_id, agent_key)
        if path.exists():
            path.unlink()

    def clear_facts(self, user_id: int):
        path = self._facts_path(user_id)
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
