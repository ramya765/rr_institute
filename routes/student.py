from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)
from models import Course

student = Blueprint("student", __name__, url_prefix="/student")

@student.route("/dashboard")
def dashboard():
    return render_template("student/dashboard.html")
@student.route("/explorer")
def explorer_dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template("student/explorer_dashboard.html")
@student.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    courses = Course.query.order_by(Course.id.desc()).all()

    return render_template(
        "student/courses.html",
        courses=courses
    )


@student.route("/course/<int:id>")
def course_details(id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    course = Course.query.get_or_404(id)

    return render_template(
        "student/course_details.html",
        course=course
    )