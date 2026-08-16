from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from database import db, bcrypt
from models import User, Student, InstituteSettings,PasswordResetToken
import hashlib
from datetime import datetime



auth = Blueprint("auth", __name__)



# ==========================
# Register
# ==========================
# ==========================
# Register
# ==========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    # ==========================================
    # CHECK STUDENT REGISTRATION SETTING
    # ==========================================

    settings = InstituteSettings.query.first()

    if settings and not settings.student_registration:

        flash(
            "Student registration is currently disabled.",
            "warning"
        )

        return redirect(
            url_for("main.home")
        )


    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )


        # ==========================================
        # VALIDATION
        # ==========================================

        if not name or not email or not phone or not password:

            flash(
                "Please fill all fields.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        # ==========================================
        # CHECK DUPLICATE EMAIL
        # ==========================================

        existing_user = User.query.filter_by(
            email=email
        ).first()


        if existing_user:

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        # ==========================================
        # PASSWORD
        # ==========================================

        hashed_password = (
            bcrypt
            .generate_password_hash(password)
            .decode("utf-8")
        )


        # ==========================================
        # FIRST USER = ADMIN
        # OTHER USERS = STUDENT
        # ==========================================

        user_count = User.query.count()


        if user_count == 0:

            user_role = "admin"

        else:

            user_role = "student"


        # ==========================================
        # CREATE USER
        # ==========================================

        new_user = User(

            name=name,

            email=email,

            phone=phone,

            password=hashed_password,

            role=user_role,

            portal_stage="normal"

        )


        db.session.add(new_user)

        db.session.commit()


        flash(
            "Registration Successful. Please Login.",
             "register_success"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "register.html"
    )
# ==========================
# Login
# ==========================
# ==========================
# Login
# ==========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password"
        )


        # ==========================================
        # FIND USER
        # ==========================================

        user = User.query.filter_by(
            email=email
        ).first()


        if user is None:

            flash(
                "Invalid Email.",
                 "login_error"
            )

            return redirect(
                url_for("auth.login")
            )


        # ==========================================
        # CHECK PASSWORD
        # ==========================================

        if not bcrypt.check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid Password.",
                "login_error"
            )

            return redirect(
                url_for("auth.login")
            )


        # ==========================================
        # GET SETTINGS
        # ==========================================

        settings = InstituteSettings.query.first()


        # ==========================================
        # STUDENT LOGIN CHECK
        # ==========================================

        if (
            user.role == "student"
            and settings
            and not settings.student_login
        ):

            flash(
                "Student login is currently disabled.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )


        # ==========================================
        # MAINTENANCE MODE
        # ==========================================

        if (
            user.role == "student"
            and settings
            and settings.maintenance_mode
        ):

            flash(
                "The student portal is currently under maintenance. Please try again later.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )


        # ==========================================
        # CREATE SESSION
        # ==========================================

        session["user_id"] = user.id

        session["username"] = user.name

        session["role"] = user.role

        session["email"] = user.email


        flash(
            "Login Successful.",
             "login_success"
        )


        # ==========================================
        # ADMIN
        # ==========================================

        if user.role == "admin":

            return redirect(
                url_for("admin.dashboard")
            )


        print(
            "LOGIN EMAIL:",
            user.email
        )

        print(
            "LOGIN ROLE:",
            user.role
        )

        print(
            "LOGIN PORTAL:",
            user.portal_stage
        )


        # ==========================================
        # STUDENT EXPLORER
        # ==========================================

        if user.portal_stage == "explorer":

            return redirect(
                url_for(
                    "student.explorer_dashboard"
                )
            )


        # ==========================================
        # NORMAL STUDENT
        # ==========================================

        return redirect(
            url_for(
                "student.dashboard"
            )
        )


    return render_template(
        "login.html"
    )
# ==========================
# Logout
# ==========================
@auth.route("/logout")
def logout():

    session.clear()

    flash(
    "Logged out successfully.",
    "logout_success"
)

    return redirect(url_for("main.home"))
@auth.route("/forgot-password", methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "Email not found",
                 "forgot_error"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        return redirect(
            url_for(
                "auth.reset_password",
                email=email
            )
        )

    return render_template(
        "forgot_password.html"
    )

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    token = request.args.get("token") \
        if request.method == "GET" \
        else request.form.get("token")

    if not token:
        flash(
            "Invalid password reset link.",
            "reset_error"
        )
        return redirect(url_for("auth.login"))

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    reset_record = PasswordResetToken.query.filter_by(
        token_hash=token_hash,
        used=False
    ).first()

    if not reset_record:

        flash(
            "This password reset link is invalid or has already been used.",
             "reset_error"
        )

        return redirect(
            url_for("auth.login")
        )

    if reset_record.expires_at < datetime.utcnow():

        flash(
            "This password reset link has expired. Please request a new one.",
              
    "reset_error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "GET":

        return render_template(
            "reset_password.html",
            token=token
        )

    password = request.form.get("password")
    confirm_password = request.form.get(
        "confirm_password"
    )

    if password != confirm_password:

        flash(
            "Passwords do not match.",
             "reset_error"
        )

        return render_template(
            "auth/reset_password.html",
            token=token
        )

    if len(password) < 8:

        flash(
            "Password must contain at least 8 characters.",
            "reset_error"
        )

        return render_template(
            "auth/reset_password.html",
            token=token
        )

    user = User.query.get(
        reset_record.user_id
    )

    user.password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Make token unusable
    reset_record.used = True

    db.session.commit()

    flash(
        "Your password has been updated successfully.",
           "password_reset_success"
    )

    return redirect(
        url_for("auth.login")
    )