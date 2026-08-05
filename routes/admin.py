from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Course, Student, Payment, Placement, Company, Lead, User
from models import Batch, Course, Faculty,  StudyMaterial


from flask import send_from_directory
from database import db, bcrypt
from sqlalchemy import func
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Message
from mail_config import mail
import secrets




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
    total_leads = Lead.query.count()

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
        total_leads=total_leads,
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


    search = request.args.get("search")
    course_filter = request.args.get("course")
    batch_filter = request.args.get("batch")


    query = Student.query



    if search:

        query = query.filter(
            Student.name.like(f"%{search}%")
        )


    if course_filter:

        query = query.filter(
            Student.course == course_filter
        )


    if batch_filter:

        query = query.filter(
            Student.batch == batch_filter
        )


    students = query.all()



    total_students = Student.query.count()



    active_students = Student.query.filter(
        Student.status.in_([
            "Paid",
            "Partially Paid",
            "Unpaid",
            "Active"
        ])
    ).count()



    placed_students = Student.query.filter_by(
        status="Placed"
    ).count()



    pending_fees = db.session.query(
        func.sum(Student.balance_amount)
    ).scalar() or 0



    courses = Course.query.all()



    batches = db.session.query(
        Student.batch
    ).distinct().all()



    return render_template(
        "admin/students.html",

        students=students,

        total_students=total_students,

        active_students=active_students,

        placed_students=placed_students,

        pending_fees=pending_fees,

        courses=courses,

        batches=[b[0] for b in batches]
    )
# ==========================================================
# Add Student
# ==========================================================


@admin.route("/students/add", methods=["GET", "POST"])
def add_student():

    lead = None

    lead_id = request.args.get("lead_id")

    if lead_id:
        lead = Lead.query.get_or_404(lead_id)


    courses = Course.query.all()


    if request.method == "POST":


        # ==============================
        # Upload Photo
        # ==============================

        photo_name = None

        photo = request.files.get("student_photo")

        if photo and photo.filename != "":

            photo_name = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "photos",
                    photo_name
                )
            )



        # ==============================
        # Upload Aadhaar
        # ==============================

        aadhaar_name = None

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



        # ==============================
        # Upload Qualification
        # ==============================

        qualification_name = None

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



        # ==============================
        # Create Student
        # ==============================


        student = Student(

            name=request.form.get("name"),

            dob=request.form.get("dob") or None,

            gender=request.form.get("gender"),

            aadhaar=request.form.get("aadhaar"),

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

            status="Unpaid",

            admission_date=request.form.get(
                "admission_date"
            ) or None,


            course_fee=float(
                request.form.get("course_fee") or 0
            ),


            paid_amount=float(
                request.form.get("paid_amount") or 0
            ),


            balance_amount=float(
                request.form.get("balance_amount") or 0
            ),


            payment_mode=request.form.get(
                "payment_mode"
            ),


            photo=photo_name,

            aadhaar_file=aadhaar_name,

            qualification_file=qualification_name,

            remarks=request.form.get("remarks")
        )



        db.session.add(student)

        db.session.commit()



        # ==================================================
        # CREATE LOGIN + SEND EMAIL ALWAYS
        # ==================================================


        if student.email:


            plain_password = secrets.token_urlsafe(8)



            user = User.query.filter_by(
                email=student.email
            ).first()



            if user:


                # Existing user update

                user.name = student.name

                user.phone = student.mobile

                user.password = bcrypt.generate_password_hash(
                    plain_password
                ).decode("utf-8")
                user.portal_stage = "explorer"

                user.is_active = True


            else:


                # New user create

                user = User(

                    name=student.name,

                    email=student.email,

                    phone=student.mobile,

                    password=bcrypt.generate_password_hash(
                        plain_password
                    ).decode("utf-8"),

                    role="student",

                    is_active=True,

                    portal_stage="explorer"

                )


                db.session.add(user)


            
            db.session.commit()



            # Connect student with user

            student.user_id = user.id

            db.session.commit()



            # ==============================
            # SEND EMAIL
            # ==============================

            try:


                msg = Message(

                    subject="RR Origin Student Portal Login",

                    recipients=[
                        student.email
                    ]

                )


                msg.body = f"""

Hello {student.name},


Welcome to RR Origin.


Your Student Portal Login Details:


Email:
{student.email}


Password:
{plain_password}


Login URL:

http://127.0.0.1:5000/login



Please change your password after login.


Regards,

RR Origin Team

"""


                mail.send(msg)



                print("==============================")

                print("EMAIL SENT SUCCESSFULLY")

                print("TO:", student.email)

                print("==============================")



            except Exception as e:


                print("==============================")

                print("EMAIL ERROR:", e)

                print("==============================")




            print("==============================")

            print("STUDENT LOGIN CREATED")

            print("EMAIL:", student.email)

            print("PASSWORD:", plain_password)

            print("==============================")




        # ==================================================
        # INITIAL PAYMENT
        # ==================================================


        if student.paid_amount > 0:


            receipt_number = (
                "RR"
                +
                datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
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



            generate_receipt(
                student,
                payment
            )



        flash(
            "Student added successfully!",
            "success"
        )


        return redirect(
            url_for(
                "admin.students"
            )
        )



    return render_template(
        "admin/add_student.html",
        courses=courses,
        lead=lead
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
    
    
    
@admin.route("/batch/<int:id>/students")
def batch_students(id):

    batch = Batch.query.get_or_404(id)

    students = Student.query.filter_by(
        course=batch.course,
        batch=batch.batch_type
    ).all()

    return render_template(
        "admin/batch_students.html",
        batch=batch,
        students=students
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

        elif student.paid_amount > 0:

            student.status = "Partially Paid"

        else:

            student.status = "Unpaid"

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

    # Delete user account
    if student.user_id:
        user = User.query.get(student.user_id)
        if user:
            db.session.delete(user)

    # Delete student
    db.session.delete(student)

    db.session.commit()

    flash("Student and user account deleted successfully.", "success")

    return redirect(url_for("admin.students"))
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
    
@admin.route('/course/delete/<int:id>')
def delete_course(id):

    course = Course.query.get_or_404(id)

    db.session.delete(course)
    db.session.commit()

    flash("Course deleted successfully","success")

    return redirect(url_for('admin.courses'))
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

        company = request.form.get("company")
        designation = request.form.get("designation")


        # CHECK DUPLICATE

        existing = Placement.query.filter_by(
            student_id=student.id,
            company=company,
            designation=designation
        ).first()


        if existing:

            flash(
                "This student already has this company and designation!",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_placement",
                    student_id=student.id
                )
            )


        placement = Placement(

            student_id=student.id,

            company=company,

            designation=designation,

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
        student.status = "Placed"
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

    batches = Batch.query.order_by(
        Batch.created_at.desc()
    ).all()

    return render_template(
        "admin/batches.html",
        batches=batches
    )


@admin.route("/batches/add", methods=["GET", "POST"])
def add_batch():

    courses = Course.query.all()
    faculties = Faculty.query.all()

    if request.method == "POST":

        batch = Batch(

            batch_id="B" + datetime.now().strftime("%Y%m%d%H%M%S"),

            batch_name=request.form.get("batch_name"),

            course=request.form.get("course"),

            trainer=request.form.get("trainer"),

            batch_type=request.form.get("batch_type"),

            timing=request.form.get("timing"),

            start_date=request.form.get("start_date") or None,

            status=request.form.get("status")
        )

        db.session.add(batch)
        db.session.commit()

        # ---------------------------------------
        # Update Students of same course
        # ---------------------------------------

        students = Student.query.filter_by(
            course=batch.course
        ).all()

        for student in students:

            student.batch = batch.batch_name

            student.trainer = batch.trainer

        db.session.commit()

        flash(
            "Batch Added Successfully",
            "success"
        )

        return redirect(
            url_for("admin.batches")
        )

    return render_template(
        "admin/add_batch.html",
        courses=courses,
        faculties=faculties
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
# STUDY MATERIALS
# ==========================================================

@admin.route("/study-materials")
def study_materials():

    search = request.args.get("search")
    course = request.args.get("course")

    query = StudyMaterial.query

    if search:

        query = query.filter(
            StudyMaterial.title.like(f"%{search}%")
        )

    if course:

        query = query.filter(
            StudyMaterial.course == course
        )

   

    materials = query.order_by(
        StudyMaterial.created_at.desc()
    ).all()

    courses = Course.query.all()

   

    return render_template(

        "admin/study_materials.html",

        materials=materials,

        courses=courses,


    )
# ==========================================================
# Study Material Upload Folder
# ==========================================================

MATERIAL_UPLOAD_FOLDER = "static/study_materials"

os.makedirs(
    MATERIAL_UPLOAD_FOLDER,
    exist_ok=True
)
    
@admin.route("/study-materials/add", methods=["GET", "POST"])
def add_study_material():


    courses = Course.query.all()



    if request.method == "POST":

        file = request.files.get("material")

        filename = None

        if file and file.filename != "":

            filename = secure_filename(file.filename)

            file.save(

                os.path.join(

                    MATERIAL_UPLOAD_FOLDER,

                    filename

                )

            )

        material = StudyMaterial(

            title=request.form.get("title"),

            description=request.form.get("description"),

            course=request.form.get("course"),



            material_type=request.form.get("material_type"),

            file_name=filename,

            uploaded_by="Admin"

        )

        db.session.add(material)

        db.session.commit()

        flash(

            "Study Material Uploaded Successfully",

            "success"

        )

        return redirect(

            url_for("admin.study_materials")

        )

    return render_template(
    "admin/add_study_material.html",
    courses=courses,
)
    
@admin.route("/study-materials/delete/<int:id>", methods=["POST"])
def delete_study_material(id):

    material = StudyMaterial.query.get_or_404(id)

    path = os.path.join(

        MATERIAL_UPLOAD_FOLDER,

        material.file_name

    )

    if os.path.exists(path):

        os.remove(path)

    db.session.delete(material)

    db.session.commit()

    flash(

        "Material Deleted Successfully",

        "success"

    )

    return redirect(

        url_for("admin.study_materials")

    )
@admin.route("/study-materials/download/<filename>")
def download_material(filename):

    return send_from_directory(

        MATERIAL_UPLOAD_FOLDER,

        filename,

        as_attachment=True

    )

# ==========================================================
# Settings
# ==========================================================

@admin.route("/settings")
def settings():

    return render_template(
        "admin/settings.html"
    )

@admin.route("/leads")
def leads():

    leads = Lead.query.order_by(
        Lead.created_at.desc()
    ).all()

    return render_template(
        "admin/leads.html",
        leads=leads
    )
@admin.route("/lead/<int:lead_id>")
def lead_details(lead_id):

    lead = Lead.query.get_or_404(lead_id)

    return render_template(
        "admin/lead_details.html",
        lead=lead
    )
@admin.route("/lead/<int:lead_id>/approve")
def approve_lead(lead_id):

    lead = Lead.query.get_or_404(lead_id)

    # Update status
    lead.status = "Approved"
    db.session.commit()

    # Redirect to Add Student page with lead_id
    return redirect(
        url_for("admin.add_student", lead_id=lead.id)
    )
# ==========================================================
# Reject Lead
# ==========================================================

@admin.route("/lead/<int:lead_id>/reject")
def reject_lead(lead_id):

    lead = Lead.query.get_or_404(lead_id)

    lead.status = "Rejected"

    db.session.commit()

    flash("Lead Rejected Successfully", "warning")

    return redirect(url_for("admin.leads"))