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

    faculties = Faculty.query.all()

    if request.method == "POST":

        # ==========================================================
        # GET FORM VALUES
        # ==========================================================

        email = request.form.get("email")
        aadhaar_number = request.form.get("aadhaar")
        mobile_number = request.form.get("mobile")

        # ==========================================================
        # DUPLICATE EMAIL CHECK
        # ==========================================================

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

        # ==========================================================
        # DUPLICATE AADHAAR CHECK
        # ==========================================================

        if aadhaar_number:

            existing_aadhaar = Student.query.filter_by(
                aadhaar=aadhaar_number
            ).first()

            if existing_aadhaar:

                flash(
                    "Aadhaar number already exists. Please check the Aadhaar number.",
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
        # DUPLICATE MOBILE CHECK
        # ==========================================================

        if mobile_number:

            existing_mobile = Student.query.filter_by(
                mobile=mobile_number
            ).first()

            if existing_mobile:

                flash(
                    "Mobile number already exists. Please use a different mobile number.",
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
        # FIND EXISTING USER
        # ==========================================================

        user = None

        if email:

            user = User.query.filter_by(
                email=email
            ).first()

        # ==========================================================
        # CHECK IF USER ALREADY HAS A STUDENT
        # ==========================================================

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

        # ==========================================================
        # UPLOAD PHOTO
        # ==========================================================

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

        # ==========================================================
        # UPLOAD AADHAAR
        # ==========================================================

        aadhaar_name = None

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

        # ==========================================================
        # UPLOAD QUALIFICATION
        # ==========================================================

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

        # ==========================================================
        # CREATE STUDENT
        # ==========================================================

        try:

            student = Student(

                name=request.form.get("name"),

                dob=request.form.get("dob") or None,

                gender=request.form.get("gender"),

                aadhaar=request.form.get("aadhaar"),

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

                mobile=request.form.get(
                    "mobile"
                ),

                alternate_mobile=request.form.get(
                    "alternate_mobile"
                ),

                email=request.form.get(
                    "email"
                ),

                address=request.form.get(
                    "address"
                ),

                course=request.form.get(
                    "course"
                ),

                batch=request.form.get(
                    "batch"
                ),

                trainer=request.form.get(
                    "trainer"
                ),

                status="Unpaid",

                admission_date=request.form.get(
                    "admission_date"
                ) or None,

                course_fee=float(
                    request.form.get(
                        "course_fee"
                    ) or 0
                ),

                paid_amount=float(
                    request.form.get(
                        "paid_amount"
                    ) or 0
                ),

                balance_amount=float(
                    request.form.get(
                        "balance_amount"
                    ) or 0
                ),

                payment_mode=request.form.get(
                    "payment_mode"
                ),

                photo=photo_name,

                aadhaar_file=aadhaar_name,

                qualification_file=qualification_name,

                remarks=request.form.get(
                    "remarks"
                )
            )

            # ======================================================
            # CONNECT WITH EXISTING USER
            # ======================================================

            if user:

                student.user_id = user.id

            # ======================================================
            # SAVE STUDENT
            # ======================================================

            db.session.add(student)

            db.session.commit()

        except IntegrityError as e:

            db.session.rollback()

            error_message = str(e).lower()

            if "email" in error_message:

                flash(
                    "Email already exists. Please use a different email.",
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
                    "Unable to add student. Please check the entered details.",
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
        # CREATE LOGIN ACCOUNT
        # ==========================================================

        if student.email:

            plain_password = secrets.token_urlsafe(8)

            user = User.query.filter_by(
                email=student.email
            ).first()

            if user:

                # ==================================================
                # EXISTING USER
                # ==================================================

                user.name = student.name

                user.phone = student.mobile

                user.password = (
                    bcrypt.generate_password_hash(
                        plain_password
                    ).decode("utf-8")
                )

                user.portal_stage = "explorer"

                user.is_active = True

            else:

                # ==================================================
                # NEW USER
                # ==================================================

                user = User(

                    name=student.name,

                    email=student.email,

                    phone=student.mobile,

                    password=(
                        bcrypt.generate_password_hash(
                            plain_password
                        ).decode("utf-8")
                    ),

                    role="student",

                    is_active=True,

                    portal_stage="explorer"
                )

                db.session.add(user)

            db.session.commit()

            # ======================================================
            # CONNECT STUDENT WITH USER
            # ======================================================

            student.user_id = user.id

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "This user is already registered as a student.",
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
            # ADMISSION NOTIFICATION
            # ======================================================

            create_notification(

                "admission",

                "Admission Confirmed 🎓",

                f"Congratulations {student.name}! "
                f"Your admission to {student.course} "
                f"has been successfully confirmed.",

                user_id=user.id
            )

            # ======================================================
            # SEND LOGIN EMAIL
            # ======================================================

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

                print(
                    "=============================="
                )

                print(
                    "EMAIL SENT SUCCESSFULLY"
                )

                print(
                    "TO:",
                    student.email
                )

                print(
                    "=============================="
                )

            except Exception as e:

                print(
                    "=============================="
                )

                print(
                    "EMAIL ERROR:",
                    e
                )

                print(
                    "=============================="
                )

            print(
                "=============================="
            )

            print(
                "STUDENT LOGIN CREATED"
            )

            print(
                "EMAIL:",
                student.email
            )

            print(
                "PASSWORD:",
                plain_password
            )

            print(
                "=============================="
            )

        # ==========================================================
        # INITIAL PAYMENT
        # ==========================================================

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

            # ======================================================
            # INITIAL PAYMENT NOTIFICATION
            # ======================================================

            if student.user_id:

                create_notification(

                    "payment",

                    "Payment Received 💰",

                    f"₹{student.paid_amount:,.2f} "
                    f"payment received for "
                    f"{student.course}. "
                    f"Your remaining balance is "
                    f"₹{student.balance_amount:,.2f}.",

                    user_id=student.user_id
                )

        # ==========================================================
        # SUCCESS MESSAGE
        # ==========================================================

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
    # DISPLAY ADD STUDENT PAGE
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
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        amount = float(
            request.form.get("amount") or 0
        )

        # --------------------------------------------------
        # Invalid Amount
        # --------------------------------------------------

        if amount <= 0:

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

        # --------------------------------------------------
        # Prevent Over Payment
        # --------------------------------------------------

        if amount > remaining:

            flash(
                f"Only Rs. {remaining:,.2f} is remaining. "
                f"Please enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_student",
                    id=id
                )
            )

        payment_mode = request.form.get("payment_mode")

        transaction_id = request.form.get(
            "transaction_id"
        )

        remarks = request.form.get(
            "remarks"
        )

        # --------------------------------------------------
        # Receipt Number
        # --------------------------------------------------

        receipt_number = (
            "RR"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
        )

        # --------------------------------------------------
        # Create Payment
        # --------------------------------------------------

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
            student.course_fee
            - student.paid_amount
        )

        if student.balance_amount <= 0:

            student.balance_amount = 0

            student.status = "Paid"

        elif student.paid_amount > 0:

            student.status = "Partially Paid"

        else:

            student.status = "Unpaid"

        # --------------------------------------------------
        # Save Payment
        # --------------------------------------------------

        db.session.commit()

        # ==================================================
        # PAYMENT NOTIFICATION
        # ==================================================

        if student.user_id:

            create_notification(

                "payment",

                "Payment Received 💰",

                f"₹{amount:,.2f} payment received for "
                f"{student.course}. "
                f"Your remaining balance is "
                f"₹{student.balance_amount:,.2f}.",

                user_id=student.user_id
            )

        # --------------------------------------------------
        # Generate Receipt
        # --------------------------------------------------

        generate_receipt(
            student,
            payment
        )

        # --------------------------------------------------
        # Success Message
        # --------------------------------------------------

        flash(
            "Payment Added Successfully",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print(
            "ERROR:",
            e
        )

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
            course.price = float(price)
        else:
            course.price = 0

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
        # STUDENT PLACEMENT NOTIFICATION
        # ================================

        if student.user_id:

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

