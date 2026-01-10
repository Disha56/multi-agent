# agents/base_agent.py
from abc import ABC, abstractmethod
from utils.helpers import now_iso

class BaseAgent(ABC):
    def __init__(self, name):
        self.name = name
        self.started_at = None
        self.ended_at = None
        self.log = []

    def _log(self, msg):
        ts = now_iso()
        entry = {"ts": ts, "agent": self.name, "msg": msg}
        self.log.append(entry)
        print(f"[{ts}] [{self.name}] {msg}")

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
