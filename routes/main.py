from flask import Blueprint, render_template

# Create Blueprint
main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("home.html")


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/courses")
def courses():
    return render_template("courses.html")


@main.route("/course/<int:id>")
def course_details(id):
    return render_template("course_details.html", course_id=id)


@main.route("/placements")
def placements():
    return render_template("placements.html")


@main.route("/gallery")
def gallery():
    return render_template("gallery.html")


@main.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")


@main.route("/contact")
def contact():
    return render_template("contact.html")


@main.route("/faq")
def faq():
    return render_template("faq.html")


@main.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@main.route("/terms")
def terms():
    return render_template("terms.html")