from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Course, Student, Payment, Placement, Company
from database import db
from sqlalchemy import func
from werkzeug.utils import secure_filename
from datetime import datetime

import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor


# ==========================================================
# Blueprint
# ==========================================================

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================================
# Upload Folders
# ==========================================================

UPLOAD_FOLDER = "static/uploads"

os.makedirs(
    os.path.join(UPLOAD_FOLDER, "photos"),
    exist_ok=True
)

os.makedirs(
    os.path.join(UPLOAD_FOLDER, "aadhaar"),
    exist_ok=True
)

os.makedirs(
    os.path.join(UPLOAD_FOLDER, "qualification"),
    exist_ok=True
)

os.makedirs(
    os.path.join(UPLOAD_FOLDER, "companies"),
    exist_ok=True
)


# ==========================================================
# Generate Receipt
# ==========================================================

def generate_receipt(student, payment):

    receipt_folder = "static/receipts"
    os.makedirs(receipt_folder, exist_ok=True)

    pdf_path = os.path.join(
        receipt_folder,
        f"{payment.receipt_number}.pdf"
    )

    c = canvas.Canvas(pdf_path, pagesize=A4)

    width, height = A4

    # ------------------------------------------------------
    # Logo
    # ------------------------------------------------------

    logo_path = "static/logo.jpeg"

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(
            logo,
            40,
            height - 110,
            width=70,
            height=70,
            preserveAspectRatio=True
        )

    # ------------------------------------------------------
    # Header
    # ------------------------------------------------------

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(HexColor("#C59D2A"))
    c.drawString(130, height - 60, "RR ORIGIN")

    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawString(130, height - 80, "WHERE CAREERS BEGIN")

    c.line(40, height - 120, 560, height - 120)

    # ------------------------------------------------------
    # Receipt Title
    # ------------------------------------------------------

    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, height - 150, "PAYMENT RECEIPT")

    y = height - 190

    c.setFont("Helvetica", 12)

    c.drawString(
        50,
        y,
        f"Receipt No : {payment.receipt_number}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Student Name : {student.name}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Course : {student.course}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Batch : {student.batch}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Amount Paid : Rs. {payment.amount:,.2f}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Remaining Balance : Rs. {student.balance_amount:,.2f}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Payment Mode : {payment.payment_mode}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Transaction ID : {payment.transaction_id or '-'}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Date : {payment.payment_date.strftime('%d-%m-%Y')}"
    )

    y -= 60

    c.line(40, y, 560, y)

    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(
        50,
        y,
        "Thank you for choosing RR ORIGIN!"
    )

    y -= 40

    c.drawRightString(
        540,
        y,
        "Authorized Signature"
    )

    c.save()

    return pdf_path


# ==========================================================
# Dashboard
# ==========================================================
# ==========================================================
# Dashboard
# ==========================================================

@admin.route("/dashboard")
def dashboard():

    total_students = Student.query.count()

    total_courses = Course.query.count()

    total_placements = Placement.query.count()

    # Company Count
    total_companies = Company.query.count()

    # Highest Package
    highest_package = db.session.query(
        func.max(Placement.package)
    ).scalar()

    if highest_package is None:
        highest_package = 0

    # Average Package
    average_package = db.session.query(
        func.avg(Placement.package)
    ).scalar()

    if average_package is None:
        average_package = 0
    else:
        average_package = round(average_package, 2)

    # Placement Percentage
    if total_students > 0:
        placement_percentage = round(
            (total_placements / total_students) * 100,
            2
        )
    else:
        placement_percentage = 0

    # Recent Students
    recent_students = Student.query.order_by(
        Student.created_at.desc()
    ).limit(5).all()

    # Recent Placements
    recent_placements = Placement.query.order_by(
        Placement.created_at.desc()
    ).limit(5).all()

    # Companies
    companies = Company.query.all()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_courses=total_courses,
        total_companies=total_companies,
        total_placements=total_placements,
        highest_package=highest_package,
        average_package=average_package,
        placement_percentage=placement_percentage,
        recent_students=recent_students,
        recent_placements=recent_placements,
        companies=companies,
        admin_name="Admin",
        current_date=datetime.now().strftime("%d-%m-%Y"),
        current_year=datetime.now().year
    )


# ==========================================================
# Students
# ==========================================================
# ==========================================================
# Students
# ==========================================================

@admin.route("/students")
def students():

    students = Student.query.all()

    return render_template(
        "admin/students.html",
        students=students
    )


# ==========================================================
# Add Student
# ==========================================================

@admin.route("/students/add", methods=["GET", "POST"])
def add_student():

    courses = Course.query.all()

    if request.method == "POST":

        # ==================================================
        # Aadhaar Validation
        # ==================================================

        aadhaar = request.form.get("aadhaar")

        if not aadhaar:
            flash(
                "Aadhaar number is mandatory!",
                "danger"
            )
            return redirect(url_for("admin.add_student"))

        if len(aadhaar) != 12 or not aadhaar.isdigit():
            flash(
                "Enter valid 12 digit Aadhaar number!",
                "danger"
            )
            return redirect(url_for("admin.add_student"))

        # Duplicate Aadhaar Check
        existing_student = Student.query.filter_by(
            aadhaar=aadhaar
        ).first()

        if existing_student:
            flash(
                "Aadhaar number already registered!",
                "danger"
            )
            return redirect(url_for("admin.add_student"))

        # ==================================================
        # Student Photo Upload
        # ==================================================

        photo_name = None

        photo = request.files.get("student_photo")

        if photo and photo.filename:

            photo_name = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "photos",
                    photo_name
                )
            )

        # ==================================================
        # Aadhaar File Upload
        # ==================================================

        aadhaar_name = None

        aadhaar_file = request.files.get("aadhaar_file")

        if not aadhaar_file or aadhaar_file.filename == "":
            flash(
                "Please upload Aadhaar card!",
                "danger"
            )
            return redirect(url_for("admin.add_student"))

        aadhaar_name = secure_filename(
            aadhaar_file.filename
        )

        aadhaar_file.save(
            os.path.join(
                UPLOAD_FOLDER,
                "aadhaar",
                aadhaar_name
            )
        )

        # ==================================================
        # Qualification File Upload
        # ==================================================

        qualification_name = None

        qualification = request.files.get(
            "qualification_files"
        )

        if qualification and qualification.filename:

            qualification_name = secure_filename(
                qualification.filename
            )

            qualification.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "qualification",
                    qualification_name
                )
            )

        # ==================================================
        # Create Student Object
        # (Continue in Part 3B)
        # ==================================================
        student = Student(

            name=request.form.get("name"),

            dob=request.form.get("dob") or None,

            gender=request.form.get("gender"),

            aadhaar=aadhaar,

            qualification=request.form.get("qualification"),

            occupation=request.form.get("occupation"),

            father_name=request.form.get("father_name"),

            mother_name=request.form.get("mother_name"),

            parent_mobile=request.form.get("parent_mobile"),

            mobile=request.form.get("mobile"),

            alternate_mobile=request.form.get("alternate_mobile"),

            email=request.form.get("email"),

            address=request.form.get("address"),

            course=request.form.get("course"),

            batch=request.form.get("batch"),

            trainer=request.form.get("trainer"),

            admission_date=request.form.get("admission_date") or None,

            course_fee=float(request.form.get("course_fee") or 0),

            paid_amount=float(request.form.get("paid_amount") or 0),

            balance_amount=float(request.form.get("balance_amount") or 0),

            payment_mode=request.form.get("payment_mode"),

            photo=photo_name,

            aadhaar_file=aadhaar_name,

            qualification_file=qualification_name,

            status="Active",

            remarks=request.form.get("remarks")
        )

        try:

            db.session.add(student)
            db.session.commit()

            # ==========================================
            # Initial Payment Entry
            # ==========================================

            if student.paid_amount > 0:

                receipt_number = (
                    "RR" +
                    datetime.now().strftime("%Y%m%d%H%M%S")
                )

                payment = Payment(

                    student_id=student.id,

                    amount=student.paid_amount,

                    payment_mode=student.payment_mode,

                    transaction_id="",

                    receipt_number=receipt_number,

                    received_by="Admin",

                    remarks="Admission Payment"
                )

                db.session.add(payment)
                db.session.commit()

                # Generate Receipt AFTER payment is saved
                generate_receipt(student, payment)

            flash(
                "Student added successfully!",
                "success"
            )

            return redirect(
                url_for("admin.students")
            )

        except Exception as e:

            db.session.rollback()

            print(e)

            flash(
                "Error while adding student!",
                "danger"
            )

            return redirect(
                url_for("admin.add_student")
            )

    return render_template(
        "admin/add_student.html",
        courses=courses
    )
# ==========================================================
# Edit Student
# ==========================================================

@admin.route("/students/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    student = Student.query.get_or_404(id)

    payments = Payment.query.filter_by(
        student_id=student.id
    ).order_by(
        Payment.payment_date.desc()
    ).all()

    # --------------------------------------------------
    # Fee Summary
    # --------------------------------------------------

    total_paid = sum(payment.amount for payment in payments)

    balance = (student.course_fee or 0) - total_paid

    if total_paid == 0:
        status = "Pending"
    elif balance == 0:
        status = "Paid"
    else:
        status = "Partially Paid"

    courses = Course.query.all()

    batches = [
        "Morning",
        "Afternoon",
        "Evening",
        "Weekend"
    ]

    if request.method == "POST":

        # ----------------------------------------------
        # Basic Details
        # ----------------------------------------------

        student.name = request.form.get("name")
        student.dob = request.form.get("dob") or None
        student.gender = request.form.get("gender")
        student.aadhaar = request.form.get("aadhaar")
        student.qualification = request.form.get("qualification")
        student.occupation = request.form.get("occupation")
        student.father_name = request.form.get("father_name")
        student.mother_name = request.form.get("mother_name")
        student.parent_mobile = request.form.get("parent_mobile")
        student.mobile = request.form.get("mobile")
        student.alternate_mobile = request.form.get("alternate_mobile")
        student.email = request.form.get("email")
        student.address = request.form.get("address")
        student.course = request.form.get("course")
        student.batch = request.form.get("batch")
        student.trainer = request.form.get("trainer")
        student.admission_date = request.form.get("admission_date") or None

        if request.form.get("course_fee"):
            student.course_fee = float(
                request.form.get("course_fee")
            )

        student.payment_mode = request.form.get("payment_mode")
        student.remarks = request.form.get("remarks")

        # ----------------------------------------------
        # Replace Student Photo
        # ----------------------------------------------

        photo = request.files.get("student_photo")

        if photo and photo.filename != "":

            photo_name = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "photos",
                    photo_name
                )
            )

            student.photo = photo_name

        # ----------------------------------------------
        # Replace Aadhaar File
        # ----------------------------------------------

        aadhaar = request.files.get("aadhaar_file")

        if aadhaar and aadhaar.filename != "":

            aadhaar_name = secure_filename(
                aadhaar.filename
            )

            aadhaar.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "aadhaar",
                    aadhaar_name
                )
            )

            student.aadhaar_file = aadhaar_name

        # ----------------------------------------------
        # Replace Qualification File
        # ----------------------------------------------

        qualification = request.files.get(
            "qualification_files"
        )

        if qualification and qualification.filename != "":

            qualification_name = secure_filename(
                qualification.filename
            )

            qualification.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "qualification",
                    qualification_name
                )
            )

            student.qualification_file = qualification_name

        db.session.commit()

        flash(
            "Student updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "admin.edit_student",
                id=student.id
            )
        )

    return render_template(
        "admin/edit_student.html",
        student=student,
        courses=courses,
        batches=batches,
        payments=payments,
        total_paid=total_paid,
        balance=balance,
        status=status
    )
# ==========================================================
# Add Payment
# ==========================================================

@admin.route("/students/<int:id>/payment", methods=["POST"])
def add_payment(id):

    student = Student.query.get_or_404(id)

    try:

        # --------------------------------------------------
        # Remaining Balance Check
        # --------------------------------------------------

        remaining = (
            (student.course_fee or 0)
            - (student.paid_amount or 0)
        )

        # Already Fully Paid
        if remaining <= 0:
            flash(
                "Course fee is already fully paid. No more payments are allowed.",
                "warning"
            )
            return redirect(
                url_for("admin.edit_student", id=id)
            )

        amount = float(
            request.form.get("amount") or 0
        )

        # Invalid Amount
        if amount <= 0:
            flash(
                "Enter a valid payment amount.",
                "danger"
            )
            return redirect(
                url_for("admin.edit_student", id=id)
            )

        # Prevent Over Payment
        if amount > remaining:
            flash(
                f"Only Rs. {remaining:,.2f} is remaining. Please enter a valid amount.",
                "danger"
            )
            return redirect(
                url_for("admin.edit_student", id=id)
            )

        payment_mode = request.form.get("payment_mode")
        transaction_id = request.form.get("transaction_id")
        remarks = request.form.get("remarks")

        receipt_number = (
            "RR"
            + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        payment = Payment(

            student_id=student.id,

            amount=amount,

            payment_mode=payment_mode,

            transaction_id=transaction_id,

            receipt_number=receipt_number,

            received_by="Admin",

            remarks=remarks
        )

        db.session.add(payment)

        # --------------------------------------------------
        # Update Student Fee Details
        # --------------------------------------------------

        student.paid_amount += amount

        student.balance_amount = (
            student.course_fee - student.paid_amount
        )

        if student.balance_amount <= 0:

            student.balance_amount = 0
            student.status = "Paid"

        elif student.paid_amount == 0:

            student.status = "Pending"

        else:

            student.status = "Partially Paid"

        db.session.commit()

        # --------------------------------------------------
        # Generate Receipt
        # --------------------------------------------------

        generate_receipt(student, payment)

        flash(
            "Payment Added Successfully",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print("ERROR:", e)

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for(
            "admin.edit_student",
            id=id
        )
    )
# ==========================================================
# Delete Student
# ==========================================================

@admin.route("/students/delete/<int:id>", methods=["POST"])
def delete_student(id):

    student = Student.query.get_or_404(id)

    db.session.delete(student)
    db.session.commit()

    flash(
        "Student deleted successfully!",
        "success"
    )

    return redirect(
        url_for("admin.students")
    )


# ==========================================================
# Courses
# ==========================================================

@admin.route("/courses")
def courses():

    courses = Course.query.all()

    print("COURSE PAGE")
    print(courses)
    print(len(courses))

    return render_template(
        "admin/courses.html",
        courses=courses
    )


# ==========================================================
# Add Course
# ==========================================================

@admin.route("/courses/add", methods=["GET", "POST"])
def add_course():

    if request.method == "POST":

        course = Course(

            title=request.form.get("title"),

            description=request.form.get("description"),

            duration=request.form.get("duration"),

            mode=request.form.get("mode"),

            trainer=request.form.get("trainer"),

            price=float(
                request.form.get("price") or 0
            ),

            featured=True if request.form.get("featured") else False
        )

        db.session.add(course)
        db.session.commit()

        flash(
            "Course added successfully!",
            "success"
        )

        return redirect(
            url_for("admin.courses")
        )

    return render_template(
        "admin/add_course.html"
    )


# ==========================================================
# Edit Course
# ==========================================================

@admin.route("/courses/edit/<int:id>")
def edit_course(id):

    return render_template(
        "admin/edit_course.html"
    )
# ==========================================================
# Companies
# ==========================================================

@admin.route("/companies")
def companies():

    companies = Company.query.all()

    return render_template(
        "admin/companies.html",
        companies=companies
    )


# ==========================================================
# Add Company
# ==========================================================

@admin.route("/companies/add", methods=["GET", "POST"])
def add_company():

    if request.method == "POST":

        company_name = request.form.get("company")

        # ==================================================
        # Company Logo Upload
        # ==================================================

        photo_name = None

        photo = request.files.get("photo")

        if photo and photo.filename:

            photo_name = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "companies",
                    photo_name
                )
            )

        company = Company(

            company=company_name,

            photo=photo_name
        )

        db.session.add(company)
        db.session.commit()

        flash(
            "Company added successfully!",
            "success"
        )

        return redirect(
            url_for("admin.companies")
        )

    return render_template(
        "admin/add_company.html"
    )


# ==========================================================
# Placements
# ==========================================================
# ==========================================================
# Placements
# ==========================================================

@admin.route("/placements")
def placements():

    course = request.args.get("course")

    courses = db.session.query(
        Student.course
    ).distinct().all()

    if course:
        students = Student.query.filter_by(
            course=course
        ).all()
    else:
        students = Student.query.all()

    return render_template(
        "admin/placements.html",
        students=students,
        courses=[c[0] for c in courses]
    )


# ==========================================================
# Add Placement
# ==========================================================

@admin.route("/add-placement/<int:student_id>", methods=["GET", "POST"])
def add_placement(student_id):

    student = Student.query.get_or_404(student_id)

    companies = Company.query.all()

    if request.method == "POST":

        placement = Placement(

            student_id=student.id,

            company=request.form.get("company"),

            designation=request.form.get("designation"),

            package=float(
                request.form.get("package")
            ),

            placement_date=datetime.strptime(
                request.form.get("placement_date"),
                "%Y-%m-%d"
            ).date(),

            status="Placed"
        )

        db.session.add(placement)
        db.session.commit()

        flash(
            "Placement Added Successfully",
            "success"
        )

        return redirect(
            url_for("admin.placements")
        )

    return render_template(
        "admin/add_placement.html",
        student=student,
        companies=companies
    )


# ==========================================================
# Faculty
# ==========================================================
# ==========================================================
# Faculty
# ==========================================================

@admin.route("/faculty")
def faculty():

    return render_template(
        "admin/faculty.html"
    )


@admin.route("/faculty/add")
def add_faculty():

    return render_template(
        "admin/add_faculty.html"
    )


# ==========================================================
# Batches
# ==========================================================

@admin.route("/batches")
def batches():

    return render_template(
        "admin/batches.html"
    )


@admin.route("/batches/add")
def add_batch():

    return render_template(
        "admin/add_batch.html"
    )


# ==========================================================
# Enquiries
# ==========================================================

@admin.route("/enquiries")
def enquiries():

    return render_template(
        "admin/enquiries.html"
    )


# ==========================================================
# Gallery
# ==========================================================

@admin.route("/gallery")
def gallery():

    return render_template(
        "admin/gallery.html"
    )


# ==========================================================
# Testimonials
# ==========================================================

@admin.route("/testimonials")
def testimonials():

    return render_template(
        "admin/testimonials.html"
    )


# ==========================================================
# Notifications
# ==========================================================

@admin.route("/notifications")
def notifications():

    return render_template(
        "admin/notifications.html"
    )


# ==========================================================
# Settings
# ==========================================================

@admin.route("/settings")
def settings():

    return render_template(
        "admin/settings.html"
    )
