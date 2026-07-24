from datetime import datetime
from database import db


# ==========================================
# USERS TABLE
# ==========================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    phone = db.Column(db.String(15), nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum("admin", "student"),
        nullable=False,
        default="student"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User {self.name}>"


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


# ==========================================
# PLACEMENTS TABLE
# ==========================================
class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)

    student_name = db.Column(db.String(100))

    company = db.Column(db.String(100))

    package = db.Column(db.String(50))

    photo = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


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
class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id")
    )

    enrolled_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )