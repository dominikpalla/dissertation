from pathlib import Path

BASE_DIR = Path(__file__).parent
MODULES_DIR = BASE_DIR / "modules"


def generate_module(spec: dict):
    """Generate Flask blueprints (CRUD) for each entity in spec."""
    if not spec or "entities" not in spec or not spec["entities"]:
        print("❌ No entities in spec, cannot generate module.")
        return

    MODULES_DIR.mkdir(exist_ok=True)

    for entity in spec["entities"]:
        name = entity["name"].lower()
        attrs = entity.get("attributes", [])
        entity_dir = MODULES_DIR / name
        templates_dir = entity_dir / "templates" / name

        entity_dir.mkdir(parents=True, exist_ok=True)
        templates_dir.mkdir(parents=True, exist_ok=True)

        # ---------- Blueprint (__init__.py) ----------
        # build POST dict and update lines
        post_lines = ",\n".join(
            [f'            "{a["name"]}": request.form.get("{a["name"]}")' for a in attrs]
        )
        update_lines = "\n".join(
            [f'        data[idx]["{a["name"]}"] = request.form.get("{a["name"]}")' for a in attrs]
        )

        bp_code = f"""
from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("{name}", __name__, url_prefix="/{name}", template_folder="templates")

data = []  # in-memory storage

@bp.route("/")
def list_{name}():
    return render_template("{name}/list.html", items=data)

@bp.route("/new", methods=["GET","POST"])
def new_{name}():
    if request.method == "POST":
        item = {{
{post_lines}
        }}
        data.append(item)
        return redirect(url_for("{name}.list_{name}"))
    return render_template("{name}/form.html")

@bp.route("/edit/<int:idx>", methods=["GET","POST"])
def edit_{name}(idx):
    if idx < 0 or idx >= len(data):
        return redirect(url_for("{name}.list_{name}"))
    if request.method == "POST":
{update_lines}
        return redirect(url_for("{name}.list_{name}"))
    return render_template("{name}/form.html", item=data[idx], idx=idx)

@bp.route("/delete/<int:idx>")
def delete_{name}(idx):
    if 0 <= idx < len(data):
        data.pop(idx)
    return redirect(url_for("{name}.list_{name}"))
"""
        (entity_dir / "__init__.py").write_text(bp_code.strip(), encoding="utf-8")

        # ---------- Templates (list.html, form.html) ----------
        th_headers = "\n".join([f"          <th>{a['name']}</th>" for a in attrs])
        td_cells = "\n".join([f"          <td>{{{{ item['{a['name']}'] }}}}</td>" for a in attrs])

        list_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{entity["name"]} list</title>
    <style>
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
      th {{ background: #f2f2f2; }}
      a.button {{ padding: 4px 8px; background: #111; color: #fff; text-decoration: none; border-radius: 6px; }}
      a.button:hover {{ background: #333; }}
    </style>
  </head>
  <body>
    <h2>{entity["name"]} list</h2>
    <p><a href="{{{{ url_for('{name}.new_{name}') }}}}" class="button">+ New {entity["name"]}</a></p>
    <table>
      <thead>
        <tr>
{th_headers}
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {{% for item in items %}}
        <tr>
{td_cells}
          <td>
            <a href="{{{{ url_for('{name}.edit_{name}', idx=loop.index0) }}}}" class="button">Edit</a>
            <a href="{{{{ url_for('{name}.delete_{name}', idx=loop.index0) }}}}" class="button">Delete</a>
          </td>
        </tr>
        {{% endfor %}}
      </tbody>
    </table>
  </body>
</html>
"""
        (templates_dir / "list.html").write_text(list_html.strip(), encoding="utf-8")

        form_fields = "\n".join(
            [
                (
                    f'      <label>{a["name"].capitalize()}: '
                    f'<input type="text" name="{a["name"]}" '
                    f'value="{{{{ item["{a["name"]}"] if item else "" }}}}"></label>'
                )
                for a in attrs
            ]
        )

        form_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{entity["name"]} form</title>
    <style>
      label {{ display: block; margin-top: 8px; }}
      input {{ padding: 6px; width: 260px; }}
      button {{ margin-top: 12px; padding: 8px 14px; background: #111; color: #fff; border: none; border-radius: 6px; cursor: pointer; }}
      button:hover {{ background: #333; }}
      a {{ text-decoration: none; }}
    </style>
  </head>
  <body>
    <h2>{entity["name"]} form</h2>
    <form method="post">
{form_fields}
      <button type="submit">Save</button>
    </form>
    <p><a href="{{{{ url_for('{name}.list_{name}') }}}}">Back to list</a></p>
  </body>
</html>
"""
        (templates_dir / "form.html").write_text(form_html.strip(), encoding="utf-8")

        print(f"✅ Generated module for {entity['name']} in {entity_dir}")