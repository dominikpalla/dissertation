from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("student", __name__, url_prefix="/student", template_folder="templates")

data = []  # in-memory storage

@bp.route("/")
def list_student():
    return render_template("student/list.html", items=data)

@bp.route("/new", methods=["GET","POST"])
def new_student():
    if request.method == "POST":
        item = {
            "ID": request.form.get("ID"),
            "Jméno": request.form.get("Jméno"),
            "Příjmení": request.form.get("Příjmení"),
            "Věk": request.form.get("Věk")
        }
        data.append(item)
        return redirect(url_for("student.list_student"))
    return render_template("student/form.html")

@bp.route("/edit/<int:idx>", methods=["GET","POST"])
def edit_student(idx):
    if idx < 0 or idx >= len(data):
        return redirect(url_for("student.list_student"))
    if request.method == "POST":
        data[idx]["ID"] = request.form.get("ID")
        data[idx]["Jméno"] = request.form.get("Jméno")
        data[idx]["Příjmení"] = request.form.get("Příjmení")
        data[idx]["Věk"] = request.form.get("Věk")
        return redirect(url_for("student.list_student"))
    return render_template("student/form.html", item=data[idx], idx=idx)

@bp.route("/delete/<int:idx>")
def delete_student(idx):
    if 0 <= idx < len(data):
        data.pop(idx)
    return redirect(url_for("student.list_student"))