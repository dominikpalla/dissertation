from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("computer", __name__, url_prefix="/computer", template_folder="templates")

data = []  # in-memory storage

@bp.route("/")
def list_computer():
    return render_template("computer/list.html", items=data)

@bp.route("/new", methods=["GET","POST"])
def new_computer():
    if request.method == "POST":
        item = {
            "id": request.form.get("id"),
            "RAM": request.form.get("RAM"),
            "CPU": request.form.get("CPU"),
            "SSD": request.form.get("SSD")
        }
        data.append(item)
        return redirect(url_for("computer.list_computer"))
    return render_template("computer/form.html")

@bp.route("/edit/<int:idx>", methods=["GET","POST"])
def edit_computer(idx):
    if idx < 0 or idx >= len(data):
        return redirect(url_for("computer.list_computer"))
    if request.method == "POST":
        data[idx]["id"] = request.form.get("id")
        data[idx]["RAM"] = request.form.get("RAM")
        data[idx]["CPU"] = request.form.get("CPU")
        data[idx]["SSD"] = request.form.get("SSD")
        return redirect(url_for("computer.list_computer"))
    return render_template("computer/form.html", item=data[idx], idx=idx)

@bp.route("/delete/<int:idx>")
def delete_computer(idx):
    if 0 <= idx < len(data):
        data.pop(idx)
    return redirect(url_for("computer.list_computer"))