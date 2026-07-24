from flask import Blueprint, render_template, request, redirect, url_for, flash


from models import Course
from database import db
from models import Student

admin = Blueprint("admin", __name__, url_prefix="/admin")


# Dashboard
@admin.route("/dashboard")
def dashboard():
    return render_template("admin/dashboard.html")


# =========================
# Students
# =========================

@admin.route("/students")
def students():

    students = Student.query.all()

    return render_template(
        "admin/students.html",
        students=students
    )

@admin.route("/students/add", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        student = Student(
            name=request.form.get("name"),
            email=request.form.get("email"),
            mobile=request.form.get("mobile"),
            course=request.form.get("course"),
            batch=request.form.get("batch")
        )

        db.session.add(student)
        db.session.commit()

        flash("Student added successfully!", "success")

        return redirect(url_for("admin.students"))

    return render_template("admin/add_student.html")


@admin.route("/students/edit/<int:id>")
def edit_student(id):
    return render_template("admin/edit_student.html")


# =========================
# Courses
# =========================

@admin.route("/courses")
def courses():
    courses = Course.query.all()
    return render_template("admin/courses.html", courses=courses)


@admin.route("/courses/add", methods=["GET", "POST"])
def add_course():

    if request.method == "POST":

        course = Course(
            title=request.form.get("title"),
            description=request.form.get("description"),
            duration=request.form.get("duration"),
            mode=request.form.get("mode"),
            trainer=request.form.get("trainer"),
            price=float(request.form.get("price") or 0),
            featured=True if request.form.get("featured") else False
        )

        db.session.add(course)
        db.session.commit()

        flash("Course added successfully!", "success")

        return redirect(url_for("admin.courses"))

    return render_template("admin/add_course.html")


@admin.route("/courses/edit/<int:id>")
def edit_course(id):
    return render_template("admin/edit_course.html")


# =========================
# Companies
# =========================

@admin.route("/companies")
def companies():
    return render_template("admin/companies.html")


@admin.route("/companies/add")
def add_company():
    return render_template("admin/add_company.html")


# =========================
# Placements
# =========================

@admin.route("/placements")
def placements():
    return render_template("admin/placements.html")


@admin.route("/placements/add")
def add_placement():
    return render_template("admin/add_placement.html")


# =========================
# Faculty
# =========================

@admin.route("/faculty")
def faculty():
    return render_template("admin/faculty.html")


@admin.route("/faculty/add")
def add_faculty():
    return render_template("admin/add_faculty.html")


# =========================
# Batches
# =========================

@admin.route("/batches")
def batches():
    return render_template("admin/batches.html")


@admin.route("/batches/add")
def add_batch():
    return render_template("admin/add_batch.html")


# =========================
# Enquiries
# =========================

@admin.route("/enquiries")
def enquiries():
    return render_template("admin/enquiries.html")


# =========================
# Gallery
# =========================

@admin.route("/gallery")
def gallery():
    return render_template("admin/gallery.html")


# =========================
# Testimonials
# =========================

@admin.route("/testimonials")
def testimonials():
    return render_template("admin/testimonials.html")


# =========================
# Notifications
# =========================

@admin.route("/notifications")
def notifications():
    return render_template("admin/notifications.html")


# =========================
# Settings
# =========================

@admin.route("/settings")
def settings():
    return render_template("admin/settings.html")