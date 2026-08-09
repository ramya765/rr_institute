from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from database import db, bcrypt
from models import User, Student, InstituteSettings


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
            "success"
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
                "danger"
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
                "danger"
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
            "success"
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

    flash("Logged out successfully.", "success")

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
                "danger"
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
@auth.route("/reset-password", methods=["GET","POST"])
def reset_password():

    email = request.args.get("email")

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        user.password = bcrypt.generate_password_hash(password).decode("utf-8")

        db.session.commit()

        flash(
            "Password Updated Successfully",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "reset_password.html",
        email=email
    )