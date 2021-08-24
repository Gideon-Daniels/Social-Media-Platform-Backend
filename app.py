import hmac
import smtplib
import sqlite3
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message
import pymysql


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row [idx]
    return d


# Function to create locations table
def init_locations_table():
    conn = sqlite3.connect('SMP.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS locations("
                 "location_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "address TEXT NOT NULL,"
                 "suburb TEXT NOT NULL,"
                 "postal_code INTEGER NOT NULL,"
                 "city TEXT NOT NULL,"
                 "province TEXT NOT NULL"
                 ")")
    print("locations table created successfully")
    conn.close()


init_locations_table()

app = Flask(__name__)
CORS(app)
app.debug = True


@app.route('/', methods=["GET"])
def welcome():
    response = {}
    if request.method == "GET":
        response["message"] = "Welcome"
        response["status_code"] = 201
        return response


# inserting information into table locations
@app.route('/locations/', methods=["POST", "GET"])
def locations():
    response = {}

    if request.method == "GET":
        try:
            with sqlite3.connect("SMP.db") as conn:
                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM locations")
                locations = cursor.fetchall()

                response['status_code'] = 201
                response['data'] = locations
        except:
            response['status_code'] = 401
            response['message'] = "Failed to retrieve data"

    if request.method == "POST":
        address = request.json['address']
        suburb = request.json['suburb']
        city = request.json['city']
        postal_code = request.json['postal_code']
        province = request.json['province']

        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO locations("
                               "address,"
                               "suburb,"
                               "postal_code,"
                               "city,"
                               "province) VALUES(?, ?, ?, ?, ?)", (address, suburb, postal_code, city, province))
                response['status_code'] = 201
                response['message'] = "successfully added"
            except:
                response['status_code'] = 401
                response['message'] = 'Database Failed'
    return response


# creating users table
def init_users_table():
    with sqlite3.connect("SMP.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users("
                     "user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name,"
                     "surname,"
                     "password,"
                     "email,"
                     "location_id,"
                     "FOREIGN KEY (location_id) REFERENCES locations(location_id))")
        print("users table created successfully")


init_users_table()
# inserting information into users table


@app.route("/users/", methods=["GET", "POST", "PATCH"])
def user_registration():
    response = {}
    # fetches all users
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

        response['status_code'] = 201
        response['data'] = users
        return response

    # login
    if request.method == "PATCH":
        email = request.json["email"]
        password = request.json["password"]

        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?AND password=?", (email, password))
            user = cursor.fetchone()

        response['status_code'] = 201
        response['data'] = user
        response['message'] = 'Successfully logged In'
        return response

    # Register
    if request.method == "POST":
        try:
            name = request.json['name']
            surname = request.json['surname']
            password = request.json['password']
            email = request.json['email']
            location_id = request.json['location_id']

            with sqlite3.connect('SMP.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users("
                               "name,"
                               "surname,"
                               "password,"
                               "email,"
                               "location_id) VALUES(?, ?, ?, ?, ?)", (name, surname, password, email, location_id))
                conn.commit()
                response['message'] = "successfully added new user to database"
                response['status_code'] = 201
            return response
        except ValueError:
            response['status_code'] = 401
            response['message'] = "Failed to load user into database"



if __name__ == "__main__":
    app.run()
    app.debug = True
