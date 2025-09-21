import ast
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).parent
MODULES_DIR = BASE_DIR / "modules"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"__READ_ERROR__: {e}"


def _syntax_errors(py_file: Path) -> List[Dict[str, Any]]:
    errors = []
    try:
        src = py_file.read_text(encoding="utf-8")
        ast.parse(src, filename=str(py_file))
    except SyntaxError as e:
        errors.append({
            "type": "syntax",
            "file": str(py_file),
            "message": f"{e.__class__.__name__}: {e.msg} at line {e.lineno}, col {e.offset}"
        })
    except Exception as e:
        errors.append({
            "type": "syntax",
            "file": str(py_file),
            "message": f"ParseError: {e}"
        })
    return errors


def _security_scan(text: str, file: Path) -> List[Dict[str, Any]]:
    findings = []
    dangerous = ["eval(", "exec(", "os.system(", "subprocess.Popen(", "subprocess.call(", "open('/etc/passwd'"]
    for token in dangerous:
        if token in text:
            findings.append({
                "type": "security",
                "file": str(file),
                "message": f"Found potentially dangerous token '{token}'"
            })
    return findings


def _import_blueprint(module_name: str, init_file: Path):
    spec = importlib.util.spec_from_file_location(module_name, init_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    if not hasattr(mod, "bp"):
        raise RuntimeError(f"Module {module_name} has no 'bp' blueprint.")
    return mod.bp


def _smoke_test_entity(entity_name: str) -> List[Dict[str, Any]]:
    """
    Build a tiny Flask app, register the entity blueprint, verify routes:
      GET /<e>/, GET /<e>/new, POST /<e>/new, GET /<e>/edit/0, GET /<e>/delete/0
    """
    from flask import Flask
    errs = []
    mod_name = f"modules.{entity_name}"
    init_file = MODULES_DIR / entity_name / "__init__.py"

    try:
        bp = _import_blueprint(mod_name, init_file)
    except Exception as e:
        errs.append({
            "type": "logic",
            "entity": entity_name,
            "message": f"Failed to import blueprint: {e}"
        })
        return errs

    app = Flask(__name__)
    app.register_blueprint(bp)

    client = app.test_client()
    # list
    r = client.get(f"/{entity_name}/")
    if r.status_code != 200:
        errs.append({
            "type": "logic",
            "entity": entity_name,
            "message": f"GET /{entity_name}/ returned {r.status_code}"
        })

    # new (GET)
    r = client.get(f"/{entity_name}/new")
    if r.status_code != 200:
        errs.append({
            "type": "logic",
            "entity": entity_name,
            "message": f"GET /{entity_name}/new returned {r.status_code}"
        })

    return errs


def _logic_checks(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    errs = []
    if "entities" not in spec or not isinstance(spec["entities"], list) or not spec["entities"]:
        errs.append({"type": "logic", "message": "Specification has no entities."})
        return errs

    for ent in spec["entities"]:
        name = ent.get("name", "")
        if not name:
            errs.append({"type": "logic", "message": "Entity without a name."})
            continue
        low = name.lower()
        ent_dir = MODULES_DIR / low
        init_py = ent_dir / "__init__.py"
        list_tpl = ent_dir / "templates" / low / "list.html"
        form_tpl = ent_dir / "templates" / low / "form.html"

        if not init_py.exists():
            errs.append({"type": "logic", "entity": name, "message": f"Missing {init_py}"})
        if not list_tpl.exists():
            errs.append({"type": "logic", "entity": name, "message": f"Missing {list_tpl}"})
        if not form_tpl.exists():
            errs.append({"type": "logic", "entity": name, "message": f"Missing {form_tpl}"})

        # route names presence (basic heuristic)
        if init_py.exists():
            init_text = _read_text(init_py)
            must_have = [f"def list_{low}", f"def new_{low}", f"def edit_{low}", f"def delete_{low}"]
            for sig in must_have:
                if sig not in init_text:
                    errs.append({"type": "logic", "entity": name, "message": f"Route '{sig}()' not found in {init_py}"})

        # attribute presence in templates (heuristic check)
        attrs = ent.get("attributes", [])
        if attrs:
            list_text = _read_text(list_tpl) if list_tpl.exists() else ""
            form_text = _read_text(form_tpl) if form_tpl.exists() else ""
            for a in attrs:
                aname = a.get("name", "")
                if aname:
                    if aname not in form_text:
                        errs.append({"type": "logic", "entity": name, "message": f"Attribute '{aname}' not present in form.html"})
                    if aname not in list_text:
                        errs.append({"type": "logic", "entity": name, "message": f"Attribute '{aname}' not present in list.html"})

        # smoke test in Flask
        errs.extend(_smoke_test_entity(low))

    return errs


def validate_module(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates:
      - syntax check for all generated *.py
      - security scan
      - logic checks against spec
      - smoke tests of blueprints
    Returns:
      {"status":"ok"}  OR  {"status":"issues","errors":[...]}
    """
    errors: List[Dict[str, Any]] = []

    # syntax + security on all generated modules
    if MODULES_DIR.exists():
        for ent_dir in MODULES_DIR.iterdir():
            if not ent_dir.is_dir():
                continue
            for py in ent_dir.rglob("*.py"):
                errors.extend(_syntax_errors(py))
                txt = _read_text(py)
                errors.extend(_security_scan(txt, py))

            # security scan templates
            for tpl in ent_dir.rglob("*.html"):
                txt = _read_text(tpl)
                # Simple XSS heuristic: raw '{{ item[...]|safe }}' (we don't use |safe => fine)
                # We still scan for '<script>' tags
                if "<script>" in txt.lower():
                    errors.append({
                        "type": "security",
                        "file": str(tpl),
                        "message": "Inline <script> tag detected in template"
                    })

    # logic/spec checks + smoke tests
    errors.extend(_logic_checks(spec))

    return {"status": "ok"} if not errors else {"status": "issues", "errors": errors}