from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("lamp", __name__, url_prefix="/lamp", template_folder="templates")

data = []  # in-memory storage

@bp.route("/")
def list_lamp():
    return render_template("lamp/list.html", items=data)

@bp.route("/new", methods=["GET","POST"])
def new_lamp():
    if request.method == "POST":
        item = {
            "ID": request.form.get("ID"),
            "Color": request.form.get("Color"),
            "Price": request.form.get("Price")
        }
        data.append(item)
        return redirect(url_for("lamp.list_lamp"))
    return render_template("lamp/form.html")

@bp.route("/edit/<int:idx>", methods=["GET","POST"])
def edit_lamp(idx):
    if idx < 0 or idx >= len(data):
        return redirect(url_for("lamp.list_lamp"))
    if request.method == "POST":
        data[idx]["ID"] = request.form.get("ID")
        data[idx]["Color"] = request.form.get("Color")
        data[idx]["Price"] = request.form.get("Price")
        return redirect(url_for("lamp.list_lamp"))
    return render_template("lamp/form.html", item=data[idx], idx=idx)

@bp.route("/delete/<int:idx>")
def delete_lamp(idx):
    if 0 <= idx < len(data):
        data.pop(idx)
    return redirect(url_for("lamp.list_lamp"))