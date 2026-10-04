"""Cookie loader: file path wins, inline JSON env is the fallback."""
import json
import os


def load_cookies(path_env: str, json_env: str):
    path = os.environ.get(path_env, "")
    if path and os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("cookies", data)
    inline = os.environ.get(json_env, "")
    if inline:
        data = json.loads(inline)
        return data if isinstance(data, list) else data.get("cookies", data)
    raise SystemExit(f"no cookies: set {path_env} to a file or {json_env} inline")
