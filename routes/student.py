from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash
)

from database import db
from models import Course, Lead, User, Student, Batch

student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)

# ==========================================
# Student Dashboard
# ==========================================

@student.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student_record = Student.query.filter_by(
        user_id=user.id
    ).first()

    return render_template(
        "student/dashboard.html",
        student=student_record,
        user=user
    )


# ==========================================
# Explorer Dashboard
# ==========================================
@student.route("/explorer")
def explorer_dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    if user.portal_stage != "explorer":
        flash("Access Denied", "danger")
        return redirect(
            url_for("student.dashboard")
        )

    student_record = Student.query.filter_by(
        email=user.email
    ).first()

    # ADD THIS
    batch = None

    if student_record:
        batch = Batch.query.filter_by(
            batch_type=student_record.batch,
            course=student_record.course
        ).first()

    return render_template(
        "student/explorer_dashboard.html",
        student=student_record,
        user=user,
        batch=batch
    )
# ==========================================
# Courses
# ==========================================

@student.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    courses = Course.query.order_by(
        Course.id.desc()
    ).all()

    return render_template(
        "student/courses.html",
        courses=courses
    )


# ==========================================
# Course Details
# ==========================================

@student.route("/course/<int:course_id>")
def course_details(course_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    course = Course.query.get_or_404(course_id)

    return render_template(
        "student/course_details.html",
        course=course
    )


# ==========================================
# Enroll Form
# ==========================================

@student.route("/enroll/<int:course_id>")
def enroll(course_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    course = Course.query.get_or_404(course_id)

    return render_template(
        "enroll.html",
        course=course
    )


# ==========================================
# Submit Enrollment
# ==========================================

@student.route("/submit-enrollment", methods=["POST"])
def submit_enrollment():

    course = Course.query.get_or_404(
        request.form.get("course_id")
    )

    lead = Lead(
        name=request.form.get("name"),
        mobile=request.form.get("mobile"),
        email=request.form.get("email"),
        course=course.title,
        message=request.form.get("message"),
        status="Pending"
    )

    db.session.add(lead)
    db.session.commit()

    return redirect(
        url_for("student.thank_you")
    )


# ==========================================
# Thank You
# ==========================================

@student.route("/thank-you")
def thank_you():

    return render_template(
        "thank_you.html"
    )