from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash,
    send_from_directory
)
from datetime import datetime

from database import db
from models import Course, Lead, User, Student, StudyMaterial
from models import Payment,Placement

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
@student.route("/my-course")
def my_course():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student_record = Student.query.filter_by(
        user_id=user.id
    ).first_or_404()

    return render_template(
        "student/my_course.html",
        student=student_record
    )


@student.route("/fee-details")
def fee_details():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student_record = Student.query.filter_by(
        user_id=user.id
    ).first_or_404()

    payments = Payment.query.filter_by(
        student_id=student_record.id
    ).order_by(
        Payment.payment_date.desc()
    ).all()

    return render_template(
        "student/fee_details.html",
        student=student_record,
        payments=payments
    )


@student.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student = Student.query.filter_by(
        user_id=user.id
    ).first_or_404()

    return render_template(
        "student/profile.html",
        student=student
    )
# ==========================================
# Placement
# ==========================================

@student.route("/placement")
def placement():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student = Student.query.filter_by(
        user_id=user.id
    ).first_or_404()

    placement = Placement.query.filter_by(
        student_id=student.id
    ).first()

    return render_template(
        "student/placement.html",
        student=student,
        placement=placement
    )


# ==========================================
# Placement Statistics
# ==========================================

@student.route("/placement-statistics")
def placement_statistics():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student_record = Student.query.filter_by(
        user_id=user.id
    ).first_or_404()

    return render_template(
        "student/placement_statistics.html",
        student=student_record,
        user=user,
        current_year=datetime.now().year
    )


# ==========================================
# Explorer Dashboard
# ==========================================
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

    
    return render_template(
        "student/explorer_dashboard.html",
        student=student_record,
        user=user,
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
@student.route("/study-materials")
def study_materials():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    student = Student.query.filter_by(
        email=user.email
    ).first()

    if not student:
        flash(
            "Student record not found",
            "danger"
        )
        return redirect(
            url_for("student.explorer_dashboard")
        )

    materials = StudyMaterial.query.filter_by(
        course=student.course
    ).all()

    return render_template(
        "student/study_materials.html",
        student=student,
        materials=materials
    )
@student.route("/study-materials/download/<filename>")
def download_material(filename):

    return send_from_directory(
        "static/study_materials",
        filename,
        as_attachment=True
    )
@student.route("/study-materials/view/<filename>")
def view_material(filename):

    return send_from_directory(
        "static/study_materials",
        filename
    )