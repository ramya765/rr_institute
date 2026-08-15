from flask import Blueprint, render_template

from models import InstituteSettings, Company


# ==========================================================
# CREATE BLUEPRINT
# ==========================================================

main = Blueprint(
    "main",
    __name__
)


# ==========================================================
# HOME
# ==========================================================

@main.route("/")
def home():

    settings = InstituteSettings.query.first()

    # Get registered companies for Home page
    companies = Company.query.all()

    return render_template(
        "home.html",
        settings=settings,
        companies=companies
    )


# ==========================================================
# ABOUT
# ==========================================================

@main.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ==========================================================
# COURSES
# ==========================================================

@main.route("/courses")
def courses():

    return render_template(
        "courses.html"
    )


# ==========================================================
# COURSE DETAILS
# ==========================================================

@main.route("/course/<int:id>")
def course_details(id):

    return render_template(
        "course_details.html",
        course_id=id
    )


# ==========================================================
# PLACEMENTS
# ==========================================================

@main.route("/placements")
def placements():

    return render_template(
        "placements.html"
    )


# ==========================================================
# GALLERY
# ==========================================================

@main.route("/gallery")
def gallery():

    return render_template(
        "gallery.html"
    )


# ==========================================================
# TESTIMONIALS
# ==========================================================

@main.route("/testimonials")
def testimonials():

    return render_template(
        "testimonials.html"
    )


# ==========================================================
# CONTACT
# ==========================================================

@main.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ==========================================================
# FAQ
# ==========================================================

@main.route("/faq")
def faq():

    return render_template(
        "faq.html"
    )


# ==========================================================
# PRIVACY POLICY
# ==========================================================

@main.route("/privacy-policy")
def privacy_policy():

    return render_template(
        "privacy_policy.html"
    )


# ==========================================================
# TERMS & CONDITIONS
# ==========================================================

@main.route("/terms")
def terms():

    return render_template(
        "terms.html"
    )


# ==========================================================
# ENROLL
# ==========================================================

