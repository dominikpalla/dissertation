import os, json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path(__file__).parent / "data"
last_valid_spec = {"entities": []}  # držíme draft


def interpret_step(history):
    global last_valid_spec

    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant helping a non-technical user design simple CRUD models.\n"
                "Always maintain an internal JSON draft of entities and attributes, but DO NOT show the JSON to the user.\n"
                "Instead, talk naturally: ask short clarification questions, propose summaries, and at the end ask the user to confirm.\n"
                "If the user confirms that summarization in any form or language, then output ONLY the JSON spec inside a ```json ... ``` block.\n"
            ),
        }
    ] + history

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        max_tokens=800,
    )
    text = response.choices[0].message.content.strip()

    spec = None
    msg = text
    done = False

    try:
        if "```json" in text:
            # finální JSON, který uživatel nepotřebuje vidět
            parts = text.split("```")
            json_part = [p for p in parts if p.strip().startswith("json")]
            if json_part:
                jtxt = json_part[0].replace("json", "", 1).strip()
                spec = json.loads(jtxt)
                last_valid_spec = spec
                done = True
                msg = "✅ Specification confirmed. Generating module..."
        else:
            # čistě textová odpověď (otázka / shrnutí)
            msg = text
            if last_valid_spec.get("entities"):
                spec = last_valid_spec

    except Exception as e:
        print("⚠️ Error parsing JSON:", e)
        if last_valid_spec.get("entities"):
            spec = last_valid_spec
        msg = "Using last saved draft."

    return spec, msg, done


def save_spec(spec, name):
    """Uloží specifikaci do data/ adresáře"""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(spec, f, indent=2)
    return path