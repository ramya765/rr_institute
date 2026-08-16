from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session
)
from models import Course, Student, Payment, Placement, Company, Lead, User
from models import Course, Faculty,  StudyMaterial
from models import InstituteSettings,Notification
from sqlalchemy.exc import IntegrityError

from decimal import Decimal
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
def create_notification(
    notification_type,
    title,
    message,
    user_id=None
):
    

    settings = InstituteSettings.query.first()

    # ==========================================
    # ADMIN NOTIFICATIONS
    # ==========================================

    # user_id=None means this is an ADMIN notification

    if user_id is None:

        if not settings:
            return

        if notification_type == "lead":

            if not settings.new_lead_notification:
                return

        elif notification_type == "admission":

            if not settings.admission_notification:
                return

        elif notification_type == "payment":

            if not settings.payment_notification:
                return

        elif notification_type == "placement":

            if not settings.placement_notification:
                return

    # ==========================================
    # STUDENT NOTIFICATIONS
    # ==========================================

    # If user_id is provided, this notification
    # belongs to that particular student.
    #
    # Student notifications are NOT controlled
    # by the admin notification settings.

    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False
    )

    db.session.add(notification)

    db.session.commit()




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
@admin.context_processor
def inject_admin_notifications():

    unread_count = Notification.query.filter(
        Notification.user_id.is_(None),
        Notification.is_read == False
    ).count()

    return {
        "admin_unread_count": unread_count
    }



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
# ==========================================================
# PAGINATION
# ==========================================================

    page = request.args.get("page", 1, type=int)

    per_page = 10

    pagination = query.paginate(
    page=page,
    per_page=per_page,
    error_out=False
)

    students = pagination.items

    
    # ==========================================================
# PAYMENT STATUS FOR STUDENTS PAGE
# ==========================================================

    for student in students:

        course_fee = float(student.course_fee or 0)
        paid_amount = float(student.paid_amount or 0)
        balance_amount = float(student.balance_amount or 0)

        if course_fee > 0 and balance_amount <= 0:
            student.payment_status = "Paid"

        elif paid_amount > 0:
            student.payment_status = "Partially Paid"

        else:
            student.payment_status = "Unpaid"
        



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
        pagination=pagination,

        batches=[b[0] for b in batches]
    )
    
@admin.route("/check-student-mobile")
def check_student_mobile():

    mobile = request.args.get("mobile", "").strip()

    exists = Student.query.filter_by(
        mobile=mobile
    ).first() is not None

    return {
        "exists": exists
    }

@admin.route("/check-student-aadhaar")
def check_student_aadhaar():

    aadhaar = request.args.get("aadhaar", "").strip()

    exists = Student.query.filter_by(
        aadhaar=aadhaar
    ).first() is not None

    return {
        "exists": exists
    }


@admin.route("/check-student-email")
def check_student_email():

    email = request.args.get("email", "").strip()

    if not email:

        return {
            "exists": False
        }

    exists = Student.query.filter_by(
        email=email
    ).first() is not None

    return {
        "exists": exists
    }
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

    faculties = Faculty.query.all()

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        try:

            # ======================================================
            # GET FORM VALUES
            # ======================================================

            name = request.form.get("name", "").strip()

            email = request.form.get(
                "email", ""
            ).strip().lower()

            aadhaar_number = request.form.get(
                "aadhaar", ""
            ).strip()

            mobile_number = request.form.get(
                "mobile", ""
            ).strip()

            course = request.form.get(
                "course", ""
            ).strip()

            batch = request.form.get(
                "batch", ""
            ).strip()

            trainer = request.form.get(
                "trainer", ""
            ).strip()

            # ======================================================
            # BASIC VALIDATION
            # ======================================================

            if not name:
                flash(
                    "Student name is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            if not mobile_number:
                flash(
                    "Mobile number is required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            if not course:
                flash(
                    "Please select a course.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            if not batch:
                flash(
                    "Please select a batch.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            # ======================================================
            # DUPLICATE EMAIL
            # ======================================================

            if email:

                existing_student = Student.query.filter_by(
                    email=email
                ).first()

                if existing_student:

                    flash(
                        "Email already exists. This student is already registered.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin.add_student",
                            lead_id=lead_id
                        ) if lead_id else url_for(
                            "admin.add_student"
                        )
                    )

            # ======================================================
            # DUPLICATE AADHAAR
            # ======================================================

            if aadhaar_number:

                existing_aadhaar = Student.query.filter_by(
                    aadhaar=aadhaar_number
                ).first()

                if existing_aadhaar:

                    flash(
                        "Aadhaar number already exists.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin.add_student",
                            lead_id=lead_id
                        ) if lead_id else url_for(
                            "admin.add_student"
                        )
                    )

            # ======================================================
            # DUPLICATE MOBILE
            # ======================================================

            if mobile_number:

                existing_mobile = Student.query.filter_by(
                    mobile=mobile_number
                ).first()

                if existing_mobile:

                    flash(
                        "Mobile number already exists.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "admin.add_student",
                            lead_id=lead_id
                        ) if lead_id else url_for(
                            "admin.add_student"
                        )
                    )

            # ======================================================
            # FIND EXISTING USER
            # ======================================================

            user = None

            if email:

                user = User.query.filter_by(
                    email=email
                ).first()

                # --------------------------------------------------
                # USER ALREADY LINKED TO STUDENT
                # --------------------------------------------------

                if user:

                    existing_user_student = Student.query.filter_by(
                        user_id=user.id
                    ).first()

                    if existing_user_student:

                        flash(
                            "This user is already registered as a student.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "admin.edit_student",
                                id=existing_user_student.id
                            )
                        )

            # ======================================================
            # FILE UPLOAD - PHOTO
            # ======================================================

            photo_name = None

            photo = request.files.get(
                "student_photo"
            )

            if photo and photo.filename:

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

            # ======================================================
            # FILE UPLOAD - AADHAAR
            # ======================================================

            aadhaar_name = None

            aadhaar_file = request.files.get(
                "aadhaar_file"
            )

            if aadhaar_file and aadhaar_file.filename:

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

            # ======================================================
            # FILE UPLOAD - QUALIFICATION
            # ======================================================

            qualification_name = None

            qualification_file = request.files.get(
                "qualification_files"
            )

            if (
                qualification_file
                and qualification_file.filename
            ):

                qualification_name = secure_filename(
                    qualification_file.filename
                )

                qualification_file.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        "qualification",
                        qualification_name
                    )
                )

            # ======================================================
            # FEE DETAILS
            # ======================================================

            try:

                course_fee = float(
                    request.form.get(
                        "course_fee"
                    ) or 0
                )

                paid_amount = float(
                    request.form.get(
                        "paid_amount"
                    ) or 0
                )

            except ValueError:

                flash(
                    "Please enter valid fee amounts.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            # ------------------------------------------------------
            # Prevent negative values
            # ------------------------------------------------------

            if course_fee < 0:
                course_fee = 0

            if paid_amount < 0:
                paid_amount = 0

            # ------------------------------------------------------
            # Prevent overpayment
            # ------------------------------------------------------

            if paid_amount > course_fee:

                flash(
                    "Paid amount cannot be greater than course fee.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.add_student",
                        lead_id=lead_id
                    ) if lead_id else url_for(
                        "admin.add_student"
                    )
                )

            # ------------------------------------------------------
            # CALCULATE BALANCE
            # ------------------------------------------------------

            balance_amount = (
                course_fee - paid_amount
            )

            # ======================================================
            # STATUS
            # ======================================================

            if course_fee > 0 and balance_amount <= 0:

                student_status = "Paid"

            elif paid_amount > 0:

                student_status = "Partially Paid"

            else:

                student_status = "Unpaid"

            # ======================================================
            # CREATE STUDENT
            # ======================================================

            student = Student(

                name=name,

                dob=request.form.get(
                    "dob"
                ) or None,

                gender=request.form.get(
                    "gender"
                ),

                aadhaar=(
                    aadhaar_number
                    if aadhaar_number
                    else None
                ),

                qualification=request.form.get(
                    "qualification"
                ),

                occupation=request.form.get(
                    "occupation"
                ),

                father_name=request.form.get(
                    "father_name"
                ),

                mother_name=request.form.get(
                    "mother_name"
                ),

                parent_mobile=request.form.get(
                    "parent_mobile"
                ),

                mobile=mobile_number,

                alternate_mobile=request.form.get(
                    "alternate_mobile"
                ),

                email=(
                    email
                    if email
                    else None
                ),

                address=request.form.get(
                    "address"
                ),

                course=course,

                batch=batch,

                # TRAINER IS OPTIONAL
                trainer=(
                    trainer
                    if trainer
                    else None
                ),

                admission_date=request.form.get(
                    "admission_date"
                ) or None,

                course_fee=course_fee,

                paid_amount=paid_amount,

                balance_amount=balance_amount,

                payment_mode=request.form.get(
                    "payment_mode"
                ),

                status=student_status,

                photo=photo_name,

                aadhaar_file=aadhaar_name,

                qualification_file=qualification_name,

                remarks=request.form.get(
                    "remarks"
                )
            )

            # ======================================================
            # CONNECT EXISTING USER
            # ======================================================

            if user:

                student.user_id = user.id

            # ======================================================
            # SAVE STUDENT
            # ======================================================

            db.session.add(student)

            db.session.flush()

            print(
                "STUDENT CREATED:",
                student.id,
                student.name
            )

            # ======================================================
            # CREATE / UPDATE LOGIN ACCOUNT
            # ======================================================

            plain_password = None

            if email:

                plain_password = secrets.token_urlsafe(8)

                # --------------------------------------------------
                # EXISTING USER
                # --------------------------------------------------

                if user:

                    user.name = student.name

                    user.phone = student.mobile

                    user.password = (
                        bcrypt
                        .generate_password_hash(
                            plain_password
                        )
                        .decode("utf-8")
                    )

                    user.portal_stage = "explorer"

                    user.is_active = True

                # --------------------------------------------------
                # NEW USER
                # --------------------------------------------------

                else:

                    user = User(

                        name=student.name,

                        email=student.email,

                        phone=student.mobile,

                        password=(
                            bcrypt
                            .generate_password_hash(
                                plain_password
                            )
                            .decode("utf-8")
                        ),

                        role="student",

                        is_active=True,

                        portal_stage="explorer"
                    )

                    db.session.add(user)

                    db.session.flush()

                    print(
                        "USER CREATED:",
                        user.id
                    )

                # --------------------------------------------------
                # CONNECT STUDENT
                # --------------------------------------------------

                student.user_id = user.id

            # ======================================================
            # INITIAL PAYMENT
            # ======================================================

            payment = None

            if paid_amount > 0:

                receipt_number = (
                    "RR"
                    + datetime.now().strftime(
                        "%Y%m%d%H%M%S%f"
                    )
                )

                payment = Payment(

                    student_id=student.id,

                    amount=paid_amount,

                    payment_mode=(
                        request.form.get(
                            "payment_mode"
                        ) or "Cash"
                    ),

                    transaction_id="",

                    receipt_number=receipt_number,

                    received_by="Admin",

                    remarks="Admission Payment"
                )

                db.session.add(payment)

                db.session.flush()

            # ======================================================
            # FINAL COMMIT
            # ======================================================

            db.session.commit()

            print(
                "================================"
            )

            print(
                "STUDENT SAVED SUCCESSFULLY"
            )

            print(
                "ID:",
                student.id
            )

            print(
                "NAME:",
                student.name
            )

            print(
                "COURSE:",
                student.course
            )

            print(
                "FEE:",
                student.course_fee
            )

            print(
                "PAID:",
                student.paid_amount
            )

            print(
                "BALANCE:",
                student.balance_amount
            )

            print(
                "USER ID:",
                student.user_id
            )

            print(
                "================================"
            )

            # ======================================================
            # RECEIPT
            # ======================================================

            if payment:

                try:

                    generate_receipt(
                        student,
                        payment
                    )

                except Exception as e:

                    print(
                        "RECEIPT ERROR:",
                        e
                    )

                        # ======================================================
            # ADMISSION NOTIFICATIONS
            # ======================================================

            # ------------------------------------------------------
            # 1. STUDENT NOTIFICATION
            # ------------------------------------------------------

            if student.user_id:

                try:

                    create_notification(
                        "admission",
                        "Admission Confirmed 🎓",

                        f"Congratulations {student.name}! "
                        f"Your admission to {student.course} "
                        f"has been successfully confirmed.",

                        user_id=student.user_id
                    )

                    print(
                        "STUDENT ADMISSION NOTIFICATION CREATED:",
                        student.user_id
                    )

                except Exception as e:

                    print(
                        "STUDENT ADMISSION NOTIFICATION ERROR:",
                        repr(e)
                    )


            # ------------------------------------------------------
            # 2. ADMIN NOTIFICATION
            # ------------------------------------------------------

            try:

                create_notification(
                    "admission",
                    "New Student Admission 🎓",

                    f"New student {student.name} "
                    f"has been admitted to {student.course}.",

                    user_id=None
                )

                print(
                    "ADMIN ADMISSION NOTIFICATION CREATED"
                )

            except Exception as e:

                print(
                    "ADMIN ADMISSION NOTIFICATION ERROR:",
                    repr(e)
                )


            # ======================================================
            # PAYMENT NOTIFICATION
            # ======================================================

            # ======================================================
            # PAYMENT NOTIFICATION
            # ======================================================

            if (
                student.user_id
                and paid_amount > 0
            ):

                try:

                    create_notification(

                        "payment",

                        "Payment Received 💰",

                        f"₹{paid_amount:,.2f} payment received "
                        f"for {student.course}. "
                        f"Your remaining balance is "
                        f"₹{balance_amount:,.2f}.",

                        user_id=student.user_id
                    )

                except Exception as e:

                    print(
                        "PAYMENT NOTIFICATION ERROR:",
                        e
                    )

            # ======================================================
            # SEND LOGIN EMAIL
            # ======================================================

            if (
                student.email
                and plain_password
            ):

                try:

                    msg = Message(

                        subject=(
                            "RR Origin Student Portal Login"
                        ),

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

                    print(
                        "LOGIN EMAIL SENT:",
                        student.email
                    )

                except Exception as e:

                    print(
                        "EMAIL ERROR:",
                        e
                    )

            # ======================================================
            # SUCCESS
            # ======================================================

            flash(
                "Student added successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "admin.students"
                )
            )

        # ==========================================================
        # DATABASE ERROR
        # ==========================================================

        except IntegrityError as e:

            db.session.rollback()

            print(
                "DATABASE INTEGRITY ERROR:",
                e
            )

            error_message = str(
                e
            ).lower()

            if "email" in error_message:

                flash(
                    "Email already exists.",
                    "danger"
                )

            elif "aadhaar" in error_message:

                flash(
                    "Aadhaar number already exists.",
                    "danger"
                )

            elif "mobile" in error_message:

                flash(
                    "Mobile number already exists.",
                    "danger"
                )

            elif "user_id" in error_message:

                flash(
                    "This user is already registered as a student.",
                    "danger"
                )

            else:

                flash(
                    "Unable to add student. "
                    "Please check the entered details.",
                    "danger"
                )

            return redirect(
                url_for(
                    "admin.add_student",
                    lead_id=lead_id
                ) if lead_id else url_for(
                    "admin.add_student"
                )
            )

        # ==========================================================
        # ANY OTHER ERROR
        # ==========================================================

        except Exception as e:

            db.session.rollback()

            print(
                "================================"
            )

            print(
                "ADD STUDENT ERROR:"
            )

            print(
                repr(e)
            )

            print(
                "================================"
            )

            flash(
                f"Unable to add student: {str(e)}",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_student",
                    lead_id=lead_id
                ) if lead_id else url_for(
                    "admin.add_student"
                )
            )

    # ==========================================================
    # DISPLAY PAGE
    # ==========================================================

    return render_template(

        "admin/add_student.html",

        courses=courses,

        faculties=faculties,

        lead=lead
    )
## ==========================================================
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

    # ==================================================
    # POST - UPDATE STUDENT
    # ==================================================

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

        # ----------------------------------------------
        # Course & Batch
        # ----------------------------------------------

        student.course = request.form.get("course")
        student.batch = request.form.get("batch")

        # ----------------------------------------------
        # AUTOMATIC TRAINER ASSIGNMENT
        # ----------------------------------------------

        faculty = Faculty.query.filter_by(
            subject=student.course,
            batch=student.batch,
            status="Active"
        ).first()

        if faculty:
            student.trainer = faculty.name
        else:
            student.trainer = None

        student.admission_date = request.form.get(
            "admission_date"
        ) or None

        # ----------------------------------------------
        # Course Fee
        # ----------------------------------------------

        if request.form.get("course_fee"):

            student.course_fee = float(
                request.form.get("course_fee")
            )

        student.payment_mode = request.form.get(
            "payment_mode"
        )

        student.remarks = request.form.get(
            "remarks"
        )

        # ----------------------------------------------
        # Replace Student Photo
        # ----------------------------------------------

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

            student.photo = photo_name

        # ----------------------------------------------
        # Replace Aadhaar File
        # ----------------------------------------------

        aadhaar = request.files.get(
            "aadhaar_file"
        )

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

        # ----------------------------------------------
        # SAVE
        # ----------------------------------------------

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

    # ==================================================
    # GET - DISPLAY STUDENT
    # ==================================================

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

# ==============================
# ADD PAYMENT
# ==============================

# ==========================================================
# ADD PAYMENT
# ==========================================================

@admin.route("/students/<int:id>/payment", methods=["POST"])
def add_payment(id):

    student = Student.query.get_or_404(id)

    try:

        # ==================================================
        # GET COURSE FEE
        # ==================================================

        course_fee = Decimal(
            str(student.course_fee or 0)
        )

        # ==================================================
        # GET ALL PREVIOUS PAYMENTS
        # Payment table is the SOURCE OF TRUTH
        # ==================================================

        previous_payments = Payment.query.filter_by(
            student_id=student.id
        ).all()

        total_paid_before = sum(
            (
                Decimal(str(payment.amount or 0))
                for payment in previous_payments
            ),
            Decimal("0.00")
        )

        # ==================================================
        # REMAINING BALANCE BEFORE NEW PAYMENT
        # ==================================================

        remaining = (
            course_fee - total_paid_before
        )

        # Prevent negative balance

        if remaining < Decimal("0.00"):
            remaining = Decimal("0.00")

        # ==================================================
        # ALREADY FULLY PAID
        # ==================================================

        if remaining <= Decimal("0.00"):

            flash(
                "Course fee is already fully paid. "
                "No more payments are allowed.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        # ==================================================
        # GET NEW PAYMENT AMOUNT
        # ==================================================

        amount_string = request.form.get(
            "amount",
            "0"
        ).strip()

        try:

            amount = Decimal(
                amount_string
            ).quantize(
                Decimal("0.01")
            )

        except Exception:

            flash(
                "Please enter a valid payment amount.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        # ==================================================
        # INVALID PAYMENT
        # ==================================================

        if amount <= Decimal("0.00"):

            flash(
                "Enter a valid payment amount.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        # ==================================================
        # PREVENT OVER PAYMENT
        # ==================================================

        if amount > remaining:

            flash(
                f"Only ₹{remaining:,.2f} is remaining. "
                f"Please enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        # ==================================================
        # PAYMENT DETAILS
        # ==================================================

        payment_mode = request.form.get(
            "payment_mode"
        )

        transaction_id = request.form.get(
            "transaction_id"
        )

        remarks = request.form.get(
            "remarks"
        )

        # ==================================================
        # RECEIPT NUMBER
        # ==================================================

        receipt_number = (
            "RR"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        # ==================================================
        # CREATE PAYMENT
        # ==================================================

        payment = Payment(

            student_id=student.id,

            amount=float(amount),

            payment_mode=payment_mode,

            transaction_id=transaction_id,

            receipt_number=receipt_number,

            received_by="Admin",

            remarks=remarks
        )

        db.session.add(payment)

        # ==================================================
        # CALCULATE NEW TOTAL
        # ==================================================

        total_paid_after = (
            total_paid_before + amount
        )

        # ==================================================
        # CALCULATE NEW BALANCE
        # ==================================================

        new_balance = (
            course_fee - total_paid_after
        )

        # Prevent tiny negative values

        if new_balance < Decimal("0.00"):
            new_balance = Decimal("0.00")

        # ==================================================
        # UPDATE STUDENT FEE DETAILS
        # ==================================================

        student.paid_amount = float(
            total_paid_after
        )

        student.balance_amount = float(
            new_balance
        )

        # ==================================================
        # UPDATE PAYMENT STATUS
        # ==================================================

        if new_balance <= Decimal("0.00"):

            student.status = "Paid"

        elif total_paid_after > Decimal("0.00"):

            student.status = "Partially Paid"

        else:

            student.status = "Unpaid"

        # ==================================================
        # SAVE EVERYTHING
        # ==================================================

        db.session.commit()

        # ==================================================
        # ADMIN NOTIFICATION
        # ==================================================

        create_notification(

            "payment",

            "Payment Received 💰",

            f"₹{amount:,.2f} payment received from "
            f"{student.name} for {student.course}. "
            f"Total paid: ₹{total_paid_after:,.2f}. "
            f"Remaining balance: ₹{new_balance:,.2f}.",

            user_id=None
        )

        # ==================================================
        # STUDENT NOTIFICATION
        # ==================================================

        if student.user_id:

            create_notification(

                "payment",

                "Payment Received 💰",

                f"₹{amount:,.2f} payment received for "
                f"{student.course}. "
                f"Your total paid amount is "
                f"₹{total_paid_after:,.2f}. "
                f"Your remaining balance is "
                f"₹{new_balance:,.2f}.",

                user_id=student.user_id
            )

        # ==================================================
        # GENERATE RECEIPT
        # ==================================================

        generate_receipt(
            student,
            payment
        )

        # ==================================================
        # SUCCESS MESSAGE
        # ==================================================

        flash(
            "Payment Added Successfully",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print(
            "PAYMENT ERROR:",
            e
        )

        flash(
            f"Unable to add payment: {str(e)}",
            "danger"
        )

    # ==================================================
    # RETURN TO STUDENT
    # ==================================================

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

    # Get actual active trainers/faculty
    faculties = Faculty.query.filter_by(
        status="Active"
    ).all()

    return render_template(
        "admin/courses.html",
        courses=courses,
        faculties=faculties
    )


# ==========================================================
# Add Course
# ==========================================================
# ==========================================================
# Add Course
# ==========================================================

@admin.route("/courses/add", methods=["GET", "POST"])
def add_course():

    if request.method == "POST":

        # ==========================================
        # COURSE IMAGE
        # ==========================================

        image = request.files.get("image")

        image_name = None

        if image and image.filename != "":

            image_name = secure_filename(
                image.filename
            )

            # Create courses folder if it does not exist
            courses_folder = os.path.join(
                UPLOAD_FOLDER,
                "courses"
            )

            os.makedirs(
                courses_folder,
                exist_ok=True
            )

            # Save image
            image.save(
                os.path.join(
                    courses_folder,
                    image_name
                )
            )

        # ==========================================
        # CREATE COURSE
        # ==========================================

        course = Course(

            title=request.form.get("title"),

            description=request.form.get("description"),

            duration=request.form.get("duration"),

            mode=request.form.get("mode"),

            trainer=request.form.get("trainer"),

            price=request.form.get("price") or "0",

            featured=True
            if request.form.get("featured")
            else False,

            image=image_name

        )

        # ==========================================
        # SAVE DATABASE
        # ==========================================

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

@admin.route("/courses/edit/<int:id>", methods=["GET", "POST"])
def edit_course(id):

    course = Course.query.get_or_404(id)

    if request.method == "POST":

        course.title = request.form.get("title")

        course.duration = request.form.get("duration")

        course.trainer = request.form.get("trainer")

        course.mode = request.form.get("mode")

        course.description = request.form.get("description")

        course.featured = (
            "featured" in request.form
        )
        price = request.form.get("price")

        if price:
            course.price = Decimal(price)
        else:
            course.price = Decimal("0")

        # ==========================================
        # COURSE IMAGE
        # ==========================================

        image = request.files.get("image")

        if image and image.filename != "":

            image_name = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    "courses",
                    image_name
                )
            )

            course.image = image_name

        # ==========================================
        # SAVE
        # ==========================================

        try:

            db.session.commit()

            flash(
                "Course updated successfully!",
                "success"
            )

            return redirect(
                url_for("admin.courses")
            )

        except Exception as e:

            db.session.rollback()

            print("Edit Course Error:", e)

            flash(
                "Unable to update course.",
                "danger"
            )

    return render_template(
        "admin/edit_course.html",
        course=course
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
@admin.route("/faculty/status/<int:id>/<status>")
def change_faculty_status(id, status):

    faculty = Faculty.query.get_or_404(id)

    if status not in ["Active", "Inactive"]:

        flash(
            "Invalid faculty status.",
            "danger"
        )

        return redirect(
            url_for("admin.faculty")
        )

    faculty.status = status

    db.session.commit()

    if status == "Inactive":

        flash(
            f"{faculty.name} has been marked as inactive.",
            "warning"
        )

    else:

        flash(
            f"{faculty.name} has been activated successfully.",
            "success"
        )

    return redirect(
        url_for("admin.faculty")
    )


# ==========================================================
# Add Placement
# ==========================================================

# ================================
# ADD PLACEMENT
# ================================

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


        # ================================
        # PLACEMENT NOTIFICATIONS
        # ================================

        # ------------------------------------------------
        # 1. STUDENT PLACEMENT NOTIFICATION
        # ------------------------------------------------

        if student.user_id:

            try:

                create_notification(

                    "placement",

                    "Congratulations! 🎉",

                    f"Congratulations {student.name}! "
                    f"You have been placed at {company} "
                    f"as {designation} "
                    f"with a package of "
                    f"₹{placement.package:,.2f}.",

                    user_id=student.user_id
                )

                print(
                    "STUDENT PLACEMENT NOTIFICATION CREATED:",
                    student.user_id
                )

            except Exception as e:

                print(
                    "STUDENT PLACEMENT NOTIFICATION ERROR:",
                    repr(e)
                )


        # ------------------------------------------------
        # 2. ADMIN PLACEMENT NOTIFICATION
        # ------------------------------------------------

        try:

            create_notification(

                "placement",

                "New Student Placement 🎉",

                f"{student.name} has been placed at "
                f"{company} as {designation} "
                f"with a package of "
                f"₹{placement.package:,.2f}.",

                user_id=None
            )

            print(
                "ADMIN PLACEMENT NOTIFICATION CREATED"
            )

        except Exception as e:

            print(
                "ADMIN PLACEMENT NOTIFICATION ERROR:",
                repr(e)
            )


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

    faculties = Faculty.query.filter_by(
    status="Active"
).all()

    return render_template(
        "admin/faculty.html",
        faculties=faculties
    )

@admin.route("/faculty/add", methods=["GET", "POST"])
def add_faculty():

    if request.method == "POST":

        faculty = Faculty(
            faculty_id="F" + datetime.now().strftime("%Y%m%d%H%M%S"),
            name=request.form.get("name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            subject=request.form.get("subject"),
            qualification=request.form.get("qualification"),
            experience=request.form.get("experience"),
            batch=request.form.get("batch"),
            payment=float(request.form.get("payment") or 0),
            status=request.form.get("status"),
            address=request.form.get("address")
        )

        db.session.add(faculty)
        db.session.commit()

        flash("Faculty added successfully!", "success")

        return redirect(url_for("admin.faculty"))

    return render_template("admin/add_faculty.html")

# ==========================================================
# Batches
# ==========================================================

# @admin.route("/batches")
# def batches():

#     batches = Batch.query.order_by(
#         Batch.created_at.desc()
#     ).all()

#     return render_template(
#         "admin/batches.html",
#         batches=batches
#     )


# @admin.route("/batches/add", methods=["GET", "POST"])
# def add_batch():

#     courses = Course.query.all()
#     faculties = Faculty.query.all()

#     if request.method == "POST":

#         batch = Batch(

#             batch_id="B" + datetime.now().strftime("%Y%m%d%H%M%S"),

#             batch_name=request.form.get("batch_name"),

#             course=request.form.get("course"),

#             trainer=request.form.get("trainer"),

#             batch_type=request.form.get("batch_type"),

#             timing=request.form.get("timing"),

#             start_date=request.form.get("start_date") or None,

#             status=request.form.get("status")
#         )

#         db.session.add(batch)
#         db.session.commit()

#         # ---------------------------------------
#         # Update Students of same course
#         # ---------------------------------------

#         students = Student.query.filter_by(
#             course=batch.course
#         ).all()

#         for student in students:

#             student.batch = batch.batch_name

#             student.trainer = batch.trainer

#         db.session.commit()

#         flash(
#             "Batch Added Successfully",
#             "success"
#         )

#         return redirect(
#             url_for("admin.batches")
#         )

#     return render_template(
#         "admin/add_batch.html",
#         courses=courses,
#         faculties=faculties
#     )

# # ==========================================================
# # Enquiries
# # ==========================================================

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

# ==========================================================
# Notifications
# ==========================================================

@admin.route(
    "/notifications",
    methods=["GET", "POST"]
)
def notifications():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    settings = InstituteSettings.query.first()

    if not settings:

        settings = InstituteSettings(
            institute_name="RR IT Origin",
            new_lead_notification=True,
            admission_notification=True,
            payment_notification=True,
            placement_notification=True,
            student_registration=True,
            student_login=True,
            maintenance_mode=False
        )

        db.session.add(settings)
        db.session.commit()

    # ==========================================
    # SAVE NOTIFICATION SETTINGS
    # ==========================================

    if request.method == "POST":

        settings.new_lead_notification = (
            "new_lead_notification"
            in request.form
        )

        settings.admission_notification = (
            "admission_notification"
            in request.form
        )

        settings.payment_notification = (
            "payment_notification"
            in request.form
        )

        settings.placement_notification = (
            "placement_notification"
            in request.form
        )

        db.session.commit()

        flash(
            "Notification settings updated successfully!",
            "success"
        )

        return redirect(
            url_for("admin.notifications")
        )

    # ==========================================
    # GET NOTIFICATIONS
    # ==========================================

    notification_list = Notification.query.filter(
    Notification.user_id.is_(None)
    ).order_by(
    Notification.created_at.desc()
    ).all()

    unread_count = Notification.query.filter(
    Notification.user_id.is_(None),
    Notification.is_read == False
    ).count()

    return render_template(
        "admin/notifications.html",

        settings=settings,

        notifications=notification_list,

        unread_count=unread_count
    )
# ==========================================================
# Mark Notification as Read
# ==========================================================

@admin.route(
    "/notifications/read/<int:id>",
    methods=["POST"]
)
def mark_notification_read(id):

    notification = Notification.query.get_or_404(id)

    notification.is_read = True

    db.session.commit()

    return redirect(
        url_for("admin.notifications")
    )
# ==========================================================
# Mark All Notifications as Read
# ==========================================================

@admin.route(
    "/notifications/read-all",
    methods=["POST"]
)
def mark_all_notifications_read():

    Notification.query.filter_by(
        is_read=False
    ).update(
        {
            "is_read": True
        }
    )

    db.session.commit()

    flash(
        "All notifications marked as read.",
        "success"
    )

    return redirect(
        url_for("admin.notifications")
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
    
# ==========================================================
# ADD STUDY MATERIAL
# ==========================================================

@admin.route("/study-materials/add", methods=["GET", "POST"])
def add_study_material():

    courses = Course.query.all()

    if request.method == "POST":

        # --------------------------------------------------
        # Upload File
        # --------------------------------------------------

        file = request.files.get("material")

        filename = None

        if file and file.filename != "":

            filename = secure_filename(
                file.filename
            )

            file.save(
                os.path.join(
                    MATERIAL_UPLOAD_FOLDER,
                    filename
                )
            )

        # --------------------------------------------------
        # Create Study Material
        # --------------------------------------------------

        material = StudyMaterial(

            title=request.form.get("title"),

            description=request.form.get(
                "description"
            ),

            course=request.form.get(
                "course"
            ),

            material_type=request.form.get(
                "material_type"
            ),

            file_name=filename,

            uploaded_by="Admin"
        )

        db.session.add(material)

        db.session.commit()

        # --------------------------------------------------
        # Success Message
        # --------------------------------------------------

        flash(
            "Study Material Uploaded Successfully",
            "success"
        )

        return redirect(
            url_for(
                "admin.study_materials"
            )
        )

    # --------------------------------------------------
    # GET Request
    # --------------------------------------------------

    return render_template(
        "admin/add_study_material.html",
        courses=courses
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


# ==========================================
# Admin Settings
# ==========================================

@admin.route("/settings", methods=["GET", "POST"])
def settings():

    # Check admin login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get current settings
    settings = InstituteSettings.query.first()

    # If no settings record exists, create one
    if not settings:
        settings = InstituteSettings(
            institute_name="RR IT Origin",
            new_lead_notification=True,
            admission_notification=True,
            payment_notification=True,
            placement_notification=True,
            student_registration=True,
            student_login=True,
            maintenance_mode=False
        )

        db.session.add(settings)
        db.session.commit()

    # ==========================================
    # SAVE SETTINGS
    # ==========================================

    if request.method == "POST":

        # Institute Information
        settings.institute_name = request.form.get(
            "institute_name"
        )

        settings.email = request.form.get(
            "email"
        )

        settings.phone = request.form.get(
            "phone"
        )

        settings.whatsapp = request.form.get(
            "whatsapp"
        )

        settings.website = request.form.get(
            "website"
        )

        settings.address = request.form.get(
            "address"
        )

        settings.city = request.form.get(
            "city"
        )

        settings.state = request.form.get(
            "state"
        )

        settings.pincode = request.form.get(
            "pincode"
        )

        settings.logo = request.form.get(
            "logo"
        )

        # ==========================================
        # Communication
        # ==========================================

        settings.contact_email = request.form.get(
            "contact_email"
        )

        settings.support_email = request.form.get(
            "support_email"
        )

        settings.welcome_text = request.form.get(
            "welcome_text"
        )

        settings.footer_text = request.form.get(
            "footer_text"
        )

        # ==========================================
        # Social Media
        # ==========================================

        settings.facebook = request.form.get(
            "facebook"
        )

        settings.instagram = request.form.get(
            "instagram"
        )

        settings.linkedin = request.form.get(
            "linkedin"
        )

        settings.youtube = request.form.get(
            "youtube"
        )

        # ==========================================
        # Notifications
        # ==========================================

        settings.new_lead_notification = (
            "new_lead_notification" in request.form
        )

        settings.admission_notification = (
            "admission_notification" in request.form
        )

        settings.payment_notification = (
            "payment_notification" in request.form
        )

        settings.placement_notification = (
            "placement_notification" in request.form
        )

        # ==========================================
        # Student Portal
        # ==========================================

        settings.student_registration = (
            "student_registration" in request.form
        )

        settings.student_login = (
            "student_login" in request.form
        )

        settings.maintenance_mode = (
            "maintenance_mode" in request.form
        )

        # ==========================================
        # Save
        # ==========================================

        try:

            db.session.commit()

            flash(
                "Settings updated successfully!",
                "success"
            )

        except Exception as e:

            db.session.rollback()

            print("Settings Error:", e)

            flash(
                "Unable to save settings.",
                "danger"
            )

        return redirect(
            url_for("admin.settings")
        )

    # ==========================================
    # Display Settings Page
    # ==========================================

    return render_template(
        "admin/settings.html",
        settings=settings
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
# ==========================================================
# CREATE NOTIFICATION
# ==========================================================

