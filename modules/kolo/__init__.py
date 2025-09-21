from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('kolo', __name__, url_prefix='/kolo', template_folder='templates')

items = []  # simple in-memory store

@bp.route("/")
def list_kolo():
    return render_template("kolo/list.html", items=items)

@bp.route("/new", methods=["GET", "POST"])
def new_kolo():
    if request.method == "POST":
        data = {}
        data['barva'] = request.form.get('barva')
        data['znacka'] = request.form.get('znacka')
        items.append(data)
        return redirect(url_for('kolo.list_kolo'))
    return render_template("kolo/new.html")