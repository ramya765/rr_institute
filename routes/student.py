from flask import Blueprint, render_template, redirect, url_for, session

from database import db
from models import Course, Enrollment

student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


# ==========================================
# STUDENT DASHBOARD
# ==========================================
@student.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "student/dashboard.html"
    )


# ==========================================
# VIEW ALL COURSES
# ==========================================
@student.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    all_courses = Course.query.order_by(
        Course.created_at.desc()
    ).all()

    return render_template(
        "student/courses.html",
        courses=all_courses
    )


# ==========================================
# ENROLL COURSE
# ==========================================
@student.route("/enroll/<int:course_id>")
def enroll(course_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    existing_enrollment = Enrollment.query.filter_by(
        student_id=session["user_id"],
        course_id=course_id
    ).first()

    if not existing_enrollment:

        enrollment = Enrollment(
            student_id=session["user_id"],
            course_id=course_id
        )

        db.session.add(enrollment)
        db.session.commit()

    course = Course.query.get(course_id)

    whatsapp_url = (
        f"https://wa.me/919676250930"
        f"?text=Hi RR Institute, I want to enroll for {course.title}"
    )

    return redirect(whatsapp_url)


# ==========================================
# MY COURSES
# ==========================================
@student.route("/my-courses")
def my_courses():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    enrollments = Enrollment.query.filter_by(
        student_id=session["user_id"]
    ).all()

    enrolled_courses = []

    for enrollment in enrollments:

        course = Course.query.get(
            enrollment.course_id
        )

        if course:
            enrolled_courses.append(course)

    return render_template(
        "student/my_courses.html",
        courses=enrolled_courses
    )