from flask import Flask, render_template

from config import Config
from database import init_db, db
from mail_config import mail

from flask import Flask, render_template
from flask_bcrypt import Bcrypt
 


# ======================================================
# Create Flask App
# ======================================================

app = Flask(__name__)


# ======================================================
# Load Configuration
# ======================================================

app.config.from_object(Config)


# ======================================================
# Mail Configuration
# ======================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "nalluridivya3133@gmail.com"
app.config["MAIL_PASSWORD"] = "xkyu agpo fmtr fxim"
app.config["MAIL_DEFAULT_SENDER"] = "nalluridivya3133@gmail.com"


mail.init_app(app)


# ======================================================
# Initialize Database
# ======================================================

init_db(app)


# ======================================================
# Import Models
# ======================================================

import models


# ======================================================
# Create Database Tables
# ======================================================

with app.app_context():

    try:

        db.create_all()

        print("=" * 50)
        print("Database Connected Successfully")
        print("Tables Created Successfully")
        print("=" * 50)

    except Exception as e:

        print("=" * 50)
        print("Database Connection Failed")
        print(e)
        print("=" * 50)



# ======================================================
# Register Blueprints
# ======================================================

from routes.main import main
from routes.auth import auth
from routes.admin import admin
from routes.student import student


app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(student)



# ======================================================
# Error Pages
# ======================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404



@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500



# ======================================================
# Run Application
# ======================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )