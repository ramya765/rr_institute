from datetime import datetime
from database import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_mode = db.Column(
        db.String(50),
        nullable=False
    )

    transaction_id = db.Column(
        db.String(100)
    )

    receipt_number = db.Column(
        db.String(50),
        unique=True
    )

    received_by = db.Column(
        db.String(100)
    )

    remarks = db.Column(
        db.Text
    )

    payment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================
# USERS TABLE
# ==========================================
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(15),
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.Enum("admin", "student"),
        default="student",
        nullable=False
    )

    # NEW
    is_active = db.Column(
        db.Boolean,
        default=False
    )

    # NEW
    portal_stage = db.Column(
        db.String(30),
        default="explorer"
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# ==========================================
# COURSES TABLE
# ==========================================
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    duration = db.Column(db.String(100))

    mode = db.Column(db.String(100))

    trainer = db.Column(db.String(100))

    price = db.Column(db.Float)

    image = db.Column(db.String(255))

    featured = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Course {self.title}>"


# ==========================================
# GALLERY TABLE
# ==========================================
class Gallery(db.Model):
    __tablename__ = "gallery"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    image = db.Column(db.String(255), nullable=False)

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================
# TESTIMONIALS TABLE
# ==========================================
class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)

    student_name = db.Column(db.String(100))

    company = db.Column(db.String(100))

    review = db.Column(db.Text)

    photo = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(db.String(20), unique=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True)

    phone = db.Column(db.String(15))

    subject = db.Column(db.String(100))

    qualification = db.Column(db.String(100))

    experience = db.Column(db.String(50))

    batch = db.Column(db.String(50))
    # Morning / Afternoon / Evening / Night

    joining_date = db.Column(db.Date)

    payment = db.Column(db.Float)

    status = db.Column(db.String(20), default="Active")

    address = db.Column(db.Text)

    photo = db.Column(db.String(255))



class Batch(db.Model):
    __tablename__ = "batches"

    id = db.Column(db.Integer, primary_key=True)

    batch_id = db.Column(
        db.String(20),
        unique=True
    )

    batch_name = db.Column(
        db.String(100),
        nullable=False
    )

    course = db.Column(
        db.String(100),
        nullable=False
    )

    trainer = db.Column(
        db.String(100),
        nullable=False
    )

    batch_type = db.Column(
        db.String(30),
        nullable=False
    )

    timing = db.Column(
        db.String(50)
    )

    start_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )# ==========================================
# PLACEMENTS TABLE
# ==========================================
# ==========================================
# PLACEMENTS TABLE
# ==========================================

from datetime import datetime
from database import db

class Enquiry(db.Model):

    __tablename__ = "enquiries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    course = db.Column(
        db.String(100)
    )

    qualification = db.Column(
        db.String(100)
    )

    message = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(20),
        default="New"
    )
    # New / Contacted / Interested / Converted

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    
class Placement(db.Model):

    __tablename__ = "placements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    company = db.Column(
        db.String(100),
        nullable=False
    )

    designation = db.Column(
        db.String(100)
    )

    package = db.Column(
        db.Float
    )

    placement_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="Placed"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    student = db.relationship(
        "Student",
        backref=db.backref(
            "placements",
            lazy=True
        )
    )


    # PREVENT DUPLICATES
    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "company",
            "designation",
            name="unique_student_company_designation"
        ),
    )
# ==========================================
# COMPANIES TABLE
# ==========================================

class Company(db.Model):

    __tablename__ = "companies"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    company = db.Column(
        db.String(100),
        nullable=False
    )


    photo = db.Column(
        db.String(255)
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    def __repr__(self):

        return f"<Company {self.company}>"

# ==========================================
# CONTACT TABLE
# ==========================================
class Contact(db.Model):
    __tablename__ = "contact"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), nullable=False)

    phone = db.Column(db.String(20))

    subject = db.Column(db.String(200))

    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================
# WEBSITE SETTINGS TABLE
# ==========================================
class WebsiteSetting(db.Model):
    __tablename__ = "website_settings"

    id = db.Column(db.Integer, primary_key=True)

    banner_title = db.Column(db.String(255))

    banner_description = db.Column(db.Text)

    whatsapp_number = db.Column(db.String(20))

    phone = db.Column(db.String(20))

    email = db.Column(db.String(120))

    address = db.Column(db.Text)

    facebook = db.Column(db.String(255))

    instagram = db.Column(db.String(255))

    youtube = db.Column(db.String(255))

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    
    
# ==========================================
# ENROLLMENTS TABLE
# ==========================================
# ==========================================
# ENROLLMENTS TABLE
# ==========================================
class Enrollment(db.Model):

    __tablename__ = "enrollments"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )


    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )


    enrolled_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
class Lead(db.Model):
    __tablename__ = "lead"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(120))
    course = db.Column(db.String(100))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="Pending")



    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ==========================================
# STUDENTS TABLE
# ==========================================
# ==========================================
# STUDENTS TABLE
# ==========================================
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.id"),
    unique=True,
    nullable=True
)

    # --------------------------
    # Personal Details
    # --------------------------
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    aadhaar = db.Column(
    db.String(20),
    unique=True,
    nullable=True
)
    qualification = db.Column(db.String(100))
    occupation = db.Column(db.String(100))

    # --------------------------
    # Parent Details
    # --------------------------
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    parent_mobile = db.Column(db.String(20))

    # --------------------------
    # Contact Details
    # --------------------------
    mobile = db.Column(db.String(20), nullable=False)
    alternate_mobile = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)

    # --------------------------
    # Course Details
    # --------------------------
    course = db.Column(db.String(100), nullable=False)

    # Morning / Afternoon / Evening / Weekend
    batch = db.Column(db.String(30), nullable=False)

    trainer = db.Column(db.String(100))
    admission_date = db.Column(db.Date)

    # --------------------------
    # Fee Details
    # --------------------------
    course_fee = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    balance_amount = db.Column(db.Float, default=0)
    payment_mode = db.Column(db.String(50))

    # --------------------------
    # Documents
    # --------------------------
    photo = db.Column(db.String(255))
    aadhaar_file = db.Column(db.String(255))
    qualification_file = db.Column(db.String(255))

    # --------------------------
    # Student Status
    # --------------------------
    status = db.Column(
        db.String(30),
        default="Active"
    )
    payments = db.relationship(
    "Payment",
    backref="student",
    lazy=True,
    cascade="all, delete-orphan"
)

    remarks = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    

    def __repr__(self):
        return f"<Student {self.name}>"
    