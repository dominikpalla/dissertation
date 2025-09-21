from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('car', __name__, url_prefix='/car', template_folder='templates')

items = []  # simple in-memory store

@bp.route("/")
def list_car():
    return render_template("car/list.html", items=items)

@bp.route("/new", methods=["GET", "POST"])
def new_car():
    if request.method == "POST":
        data = {}
        data['license_plate'] = request.form.get('license_plate')
        data['color'] = request.form.get('color')
        data['engine_volume'] = request.form.get('engine_volume')
        items.append(data)
        return redirect(url_for('car.list_car'))
    return render_template("car/new.html")