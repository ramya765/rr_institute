from flask import Flask, render_template

from config import Config
from database import init_db, db

# Create Flask App
app = Flask(__name__)

# Load Config
app.config.from_object(Config)

# Initialize Database
init_db(app)

# Import Models (IMPORTANT: import after init_db)
import models

# Create Tables
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
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


# ======================================================
# Run Application
# ======================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )