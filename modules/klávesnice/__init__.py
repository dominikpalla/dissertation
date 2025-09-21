from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("klávesnice", __name__, url_prefix="/klávesnice", template_folder="templates")

data = []  # in-memory storage

@bp.route("/")
def list_klávesnice():
    return render_template("klávesnice/list.html", items=data)

@bp.route("/new", methods=["GET","POST"])
def new_klávesnice():
    if request.method == "POST":
        item = {
            "id": request.form.get("id"),
            "barva": request.form.get("barva"),
            "cena": request.form.get("cena")
        }
        data.append(item)
        return redirect(url_for("klávesnice.list_klávesnice"))
    return render_template("klávesnice/form.html")

@bp.route("/edit/<int:idx>", methods=["GET","POST"])
def edit_klávesnice(idx):
    if idx < 0 or idx >= len(data):
        return redirect(url_for("klávesnice.list_klávesnice"))
    if request.method == "POST":
        data[idx]["id"] = request.form.get("id")
        data[idx]["barva"] = request.form.get("barva")
        data[idx]["cena"] = request.form.get("cena")
        return redirect(url_for("klávesnice.list_klávesnice"))
    return render_template("klávesnice/form.html", item=data[idx], idx=idx)

@bp.route("/delete/<int:idx>")
def delete_klávesnice(idx):
    if 0 <= idx < len(data):
        data.pop(idx)
    return redirect(url_for("klávesnice.list_klávesnice"))