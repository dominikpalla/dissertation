from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('auto', __name__, url_prefix='/auto', template_folder='templates')

# in-memory store
items = []

@bp.route("/")
def list_auto():
    return render_template("auto/list.html", items=items)

@bp.route("/new", methods=["GET", "POST"])
def new_auto():
    if request.method == "POST":
        data = {}
        data['spz'] = request.form.get('spz')
        data['barva'] = request.form.get('barva')
        data['objem_motoru'] = request.form.get('objem_motoru')
        items.append(data)
        return redirect(url_for('auto.list_auto'))
    return render_template("auto/new.html")