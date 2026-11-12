import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:  # pragma: no cover - optional dependency
    WebClient = None
    SlackApiError = RuntimeError

STATE_PATH = Path(__file__).parent / "state.json"
PROBLEMS_PATH = Path(__file__).parent / "problems.yaml"
BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")


def load_problems() -> List[Dict]:
    if PROBLEMS_PATH.exists():
        if yaml is None:
            raise RuntimeError("Instala pyyaml o elimina problems.yaml")
        with PROBLEMS_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        if not isinstance(data, list):
            raise ValueError("El archivo problems.yaml debe contener una lista de problemas.")
        return data
    return DEFAULT_PROBLEMS


def init_state(n: int) -> Dict:
    order = list(range(n))
    random.shuffle(order)
    return {"order": order, "pos": 0, "last_post": None}


def load_state(n: int) -> Dict:
    state: Dict = {}
    if STATE_PATH.exists():
        try:
            with STATE_PATH.open("r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            state = {}

    if not isinstance(state, dict):
        state = {}
    if "order" not in state or not isinstance(state["order"], list) or len(state["order"]) != n:
        state = init_state(n)
    return state


def save_state(state: Dict):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def today_iso():
    return datetime.now().date().isoformat()


def select_today(problems: List[Dict], state: Dict) -> Dict:
    if not problems:
        raise ValueError("No hay problemas cargados.")

    pos = state.get("pos", 0)
    if state.get("last_post") == today_iso():
        idx = state["order"][pos % len(state["order"])]
        return problems[idx]

    idx = state["order"][pos % len(state["order"])]
    problem = problems[idx]
    state["pos"] = (pos + 1) % len(problems)
    state["last_post"] = today_iso()
    return problem


def build_message(problem: Dict) -> Dict:
    title = problem.get("title", "Reto Python")
    prompt = problem.get("prompt", "Sin enunciado.")
    hints = problem.get("hints", [])
    tags = problem.get("tags", [])

    hints_md = "\n".join([f"• {h}" for h in hints]) if hints else "—"
    tags_md = ", ".join(tags) if tags else "principiante"
    header = f":snake: *Reto Python del día:* *{title}*"
    body = f"{prompt}\n\n*Pistas:*\n{hints_md}\n\n*Etiquetas:* `{tags_md}`"

    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": header}},
            {"type": "section", "text": {"type": "mrkdwn", "text": body}},
            {"type": "divider"},
        ]
    }


def post_to_slack(payload: Dict):
    if WebClient is None:
        raise RuntimeError("La librería slack_sdk no está instalada.")
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError("Faltan variables de entorno: SLACK_BOT_TOKEN y SLACK_CHANNEL_ID.")

    client = WebClient(token=BOT_TOKEN)
    try:
        client.chat_postMessage(channel=CHANNEL_ID, **payload)
    except SlackApiError as e:
        detail = e.response.data if hasattr(e, "response") else e
        raise RuntimeError(f"Error Slack: {detail}") from e


def main():
    problems = load_problems()
    state = load_state(len(problems))
    prob = select_today(problems, state)
    payload = build_message(prob)

    try:
        post_to_slack(payload)
    except RuntimeError as exc:
        print(f"No se pudo publicar en Slack: {exc}")
        print("Problema elegido:", prob.get("title"))
        return

    save_state(state)
    print("Publicado:", prob["title"])


if __name__ == "__main__":
    main()

