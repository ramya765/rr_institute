from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from database import db, bcrypt
from models import User, Student

auth = Blueprint("auth", __name__)


# ==========================
# Register
# ==========================
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")


        if not name or not email or not phone or not password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for("auth.register"))


        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))


        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register"))


        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")


        # First registered user becomes admin
        user_count = User.query.count()

        if user_count == 0:
            user_role = "admin"
        else:
            user_role = "student"


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


        flash("Registration Successful. Please Login.", "success")

        return redirect(url_for("auth.login"))


    return render_template("register.html")



# ==========================
# Login
# ==========================
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")


        user = User.query.filter_by(email=email).first()


        if user is None:
            flash("Invalid Email.", "danger")
            return redirect(url_for("auth.login"))


        if not bcrypt.check_password_hash(user.password, password):
            flash("Invalid Password.", "danger")
            return redirect(url_for("auth.login"))



        session["user_id"] = user.id
        session["username"] = user.name
        session["role"] = user.role
        session["email"] = user.email


        flash("Login Successful.", "success")


        # Redirect based on database role
        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        print("LOGIN EMAIL:", user.email)
        print("LOGIN ROLE:", user.role)
        print("LOGIN PORTAL:", user.portal_stage)

# Student created by Admin
       # Check whether this user is linked to Student table
       # Student Dashboard Decision

        if user.portal_stage == "explorer":
            return redirect(
                    url_for("student.explorer_dashboard")
            )

        return redirect(
            url_for("student.dashboard")
        )


    return render_template("login.html")



# ==========================
# Logout
# ==========================
@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("main.home"))