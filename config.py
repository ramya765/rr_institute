class Config:

    SECRET_KEY = "academy_website_2025_secret_key"

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:Parislove%40143@localhost/academy_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False