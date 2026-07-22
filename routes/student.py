from flask import Blueprint, render_template

student = Blueprint("student", __name__, url_prefix="/student")

@student.route("/dashboard")
def dashboard():
    return render_template("student/dashboard.html")