# utils/config.py
"""
Robust .env loader + getter.
Searches for a .env file in several candidate locations (cwd, script dir, parents, home),
loads it (using python-dotenv if available), and also parses manually if needed.
Provides get_api_key(name) to return the value (or None) and reports where it was found.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv, dotenv_values
    DOTENV_AVAILABLE = True
except Exception:
    DOTENV_AVAILABLE = False

SEARCH_STEPS = 6  # number of parent levels to search

def find_dotenv_candidates():
    """Yield candidate .env paths to check (strings)."""
    # 1) Current working directory
    cwd = Path.cwd()
    yield cwd / ".env"
    # 2) Script directory (where this file is)
    yield Path(__file__).resolve().parent.parent / ".env"
    # 3) Walk up parents from cwd
    p = cwd
    for _ in range(SEARCH_STEPS):
        p = p.parent
        yield p / ".env"
    # 4) Home directory
    yield Path.home() / ".env"
    # 5) Windows OneDrive Desktop/Project heuristics (common on Windows)
    onedrive = os.environ.get("ONEDRIVE")
    if onedrive:
        yield Path(onedrive) / ".env"
    # final: no .env found
    return

def load_dotenv_best_effort():
    """
    Try to locate a .env file and load it. Returns the path loaded, or None.
    Also sets os.environ entries for parsed values if python-dotenv isn't available.
    """
    # 1) Try load_dotenv() default first (handles env already loaded)
    if DOTENV_AVAILABLE:
        try:
            load_dotenv(override=False)
        except Exception:
            pass

    for p in find_dotenv_candidates():
        try:
            if not p:
                continue
            if p.exists():
                # load with python-dotenv if available (preferred)
                if DOTENV_AVAILABLE:
                    load_dotenv(dotenv_path=str(p), override=False)
                else:
                    # manual parse
                    for line in p.read_text(encoding="utf8").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k,v = line.split("=",1)
                        k = k.strip()
                        v = v.strip().strip('\'"')
                        # only set if not present in environment
                        if k not in os.environ:
                            os.environ[k] = v
                return str(p)
        except Exception:
            continue
    return None

# call it once on import to try to populate env vars
_LOADED_PATH = load_dotenv_best_effort()

def get_dotenv_path():
    return _LOADED_PATH

def get_api_key(name, required=False):
    """
    Return API key value for environment variable `name`.
    Search order:
      1) os.environ
      2) (already loaded) .env file parsed into env
    The loader above already attempted to load .env from several locations.
    Returns the value (string) or None.
    If required=True and not found, raises RuntimeError.
    """
    val = os.environ.get(name)
    if val:
        # small check: strip spaces
        val = val.strip()
        if val:
            return val
    # No key in env; attempt to parse .env file directly (again) and check there
    # (handles unusual file encodings)
    dotenv_path = get_dotenv_path()
    if dotenv_path:
        try:
            # try python-dotenv value reading if available
            if DOTENV_AVAILABLE:
                d = dotenv_values(dotenv_path)
                if d and name in d and d[name]:
                    return str(d[name]).strip()
            else:
                # fallback manual read
                p = Path(dotenv_path)
                for line in p.read_text(encoding="utf8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k,v = line.split("=",1)
                    if k.strip() == name:
                        return v.strip().strip('"').strip("'")
        except Exception:
            pass
    if required:
        raise RuntimeError(f"Required API key '{name}' not found in environment or .env (searched {dotenv_path}).")
    return None

def where_key_came_from(name):
    """Return a short string describing where the key was found (env/.env path/none)."""
    if os.environ.get(name):
        return "os.environ"
    p = get_dotenv_path()
    if p:
        try:
            if DOTENV_AVAILABLE:
                val = dotenv_values(p).get(name)
                if val:
                    return f".env ({p})"
            else:
                # manual
                for line in Path(p).read_text(encoding="utf8").splitlines():
                    if line.strip().startswith(f"{name}="):
                        return f".env ({p})"
        except Exception:
            pass
    return "not found"