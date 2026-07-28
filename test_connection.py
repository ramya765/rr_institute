import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="Parislove@143",
        database="academy_db"
    )

    print("Connected Successfully!")

    conn.close()

except Exception as e:
    print(e)