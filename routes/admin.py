from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Course, User
from database import db

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/dashboard")
def dashboard():

    all_courses = Course.query.order_by(Course.created_at.desc()).all()

    total_courses = Course.query.count()

    total_students = User.query.filter_by(role="student").count()

    return render_template(
        "admin/dashboard.html",
        courses=all_courses,
        total_courses=total_courses,
        total_students=total_students
    )


@admin.route("/courses")
def courses():

    all_courses = Course.query.all()

    return render_template(
        "admin/courses.html",
        courses=all_courses
    )


@admin.route("/course/add", methods=["GET", "POST"])
def add_course():

    if request.method == "POST":

        course = Course(
            title=request.form["title"],
            description=request.form["description"],
            duration=request.form["duration"],
            mode=request.form["mode"],
            trainer=request.form["trainer"],
            price=request.form["price"]
        )

        db.session.add(course)
        db.session.commit()

        flash("Course Added Successfully", "success")

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_course.html")