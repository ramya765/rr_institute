from flask import Blueprint, render_template, redirect, url_for, session
from sqlalchemy import func

from database import db
from models import (
    Course,
    Enrollment,
    Student,
    Placement
)

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

    current_student = Student.query.filter_by(
        email=session.get("email")
    ).first()

    return render_template(
        "student/dashboard.html",
        student=current_student
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

    existing = Enrollment.query.filter_by(
        student_id=session["user_id"],
        course_id=course_id
    ).first()

    if not existing:

        enrollment = Enrollment(
            student_id=session["user_id"],
            course_id=course_id
        )

        db.session.add(enrollment)
        db.session.commit()

    course = Course.query.get_or_404(course_id)

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


# ==========================================
# STUDENT PROFILE
# ==========================================
@student.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_student = Student.query.filter_by(
        email=session.get("email")
    ).first()

    return render_template(
        "student/profile.html",
        student=current_student
    )


# ==========================================
# PAYMENT HISTORY
# ==========================================
@student.route("/payments")
def payments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_student = Student.query.filter_by(
        email=session.get("email")
    ).first()

    payments = current_student.payments

    return render_template(
        "student/payments.html",
        student=current_student,
        payments=payments
    )


# ==========================================
# PLACEMENT STATUS
# ==========================================
@student.route("/placement")
def placement():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_student = Student.query.filter_by(
        email=session.get("email")
    ).first()

    placement = Placement.query.filter_by(
        student_id=current_student.id
    ).first()

    return render_template(
        "student/placement.html",
        student=current_student,
        placement=placement
    )


# ==========================================
# PLACEMENT STATISTICS
# ==========================================
@student.route("/placement-stats")
def placement_stats():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    stats = db.session.query(
        Placement.company,
        func.count(Placement.id)
    ).group_by(
        Placement.company
    ).all()

    return render_template(
        "student/placement_stats.html",
        stats=stats
    )