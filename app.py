import hmac
import re
import smtplib
import sqlite3
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message
import cloudinary
import cloudinary.uploader
import datetime


# Global functions
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def validate_string(*string):
    flag = False
    for x in string:
        if isinstance(x, str):
            flag = True
        else:
            flag = False
    return flag


def validate_integer(integer):
    if isinstance(integer, (int, float)):
        return True
    else:
        return False


def validate_email(email):
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

    if re.search(regex, email):
        return True
    else:
        return None


def upload_file():
    app.logger.info('upload in route')
    cloudinary.config(
        cloud_name='dnuer7lrl',
        api_key='938329564673713',
        api_secret='8yTINboBmMjlnbV54kt4ILtVdZM'
    )
    upload_results = None
    if request.method == 'POST' or request.method == 'PUT' or request.method == 'GET':
        image = request.json['content']
        app.logger.info('%s image_to_upload', image)
        if image:
            upload_results = cloudinary.uploader.upload(image)
            app.logger.info(upload_results)
            return upload_results['url']
        else:
            message = "This is not an image"
            return message
    else:
        message = "wrong method is being used"
        return message


# ---------------------------------------------Creating Tables---------------------------------------------------------
# Functions to create locations table
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


# creating users table
def init_users_table():
    with sqlite3.connect("SMP.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users("
                     "user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "surname TEXT NOT NULL,"
                     "password TEXT NOT NULL,"
                     "email TEXT NOT NULL,"
                     "location_id TEXT NOT NULL,"
                     "FOREIGN KEY (location_id) REFERENCES locations(location_id))")
        print("users table created successfully")


init_users_table()


def init_files_table():
    with sqlite3.connect("SMP.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS files("
                     "file_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "user_id TEXT NOT NULL,"
                     "title TEXT NOT NULL,"
                     "content,"
                     "description TEXT NOT NULL,"
                     "format TEXT NOT NULL,"
                     "date_published DATETIME NOT NULL,"
                     "FOREIGN KEY (user_id) REFERENCES users(user_id))")
        print("files table created successfully")


init_files_table()


def init_post_table():
    with sqlite3.connect("SMP.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS posts("
                     "post_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "user_id TEXT NOT NULL,"
                     "title TEXT NOT NULL,"
                     "content TEXT NOT NULL,"
                     "date_published DATETIME NOT NULL,"
                     "FOREIGN KEY(user_id) REFERENCES users(user_id))")
        print("post table created successfully")


init_post_table()

# def drop_table():
#     with sqlite3.connect("SMP.db") as conn:
#         conn.execute("DROP TABLE files")
#         conn.commit()
#         print("Table dropped")
# drop_table()

# -----------------------------------------JOINING TABLES-------------------------------------------------------------


class JoinedTables:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def location_join_users(self):
        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users INNER JOIN locations ON users.location_id = locations.location_id "
                           "WHERE email=?AND password=?", (self.email, self.password))
            user_data = cursor.fetchone()
            return user_data


# -------------------------------------------All Classes ------------------------------------------


class Users:
    def __init__(self, name, surname, email, password, location_id):
        self.name = name
        self.surname = surname
        self.email = email
        self.password = password
        self.location_id = location_id

    def register_user(self):
        with sqlite3.connect('SMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users("
                           "name,"
                           "surname,"
                           "password,"
                           "email,"
                           "location_id) VALUES(?, ?, ?, ?, ?)",
                           (self.name, self.surname, self.password, self.email, self.location_id))
            conn.commit()


class Locations:
    def __init__(self, address, suburb, city, postal_code, province):
        self.address = address
        self.suburb = suburb
        self.city = city
        self.postal_code = postal_code
        self.province = province

    def register_location(self):
        response = {}
        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO locations("
                               "address,"
                               "suburb,"
                               "postal_code,"
                               "city,"
                               "province) VALUES(?, ?, ?, ?, ?)", (self.address, self.suburb, self.postal_code,
                                                                   self.city, self.province))
                conn.commit()
                response['status_code'] = 201
                response['message'] = "successfully added"
                return response
            except:
                response['status_code'] = 401
                response['message'] = 'Database Failed'
                return response


class Files:
    def __init__(self, users_id, title, content, description, file_format, date_published):
        self.users_id = users_id
        self.title = title
        self.content = content
        self.description = description
        self.file_format = file_format
        self.date_published = date_published

    def register_file(self):
        with sqlite3.connect('SMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO files("
                           "user_id,"
                           "title,"
                           "content,"
                           "description,"
                           "format,"
                           "date_published"
                           ") VALUES(?, ?, ?, ?, ?, ?)",
                           (self.users_id, self.title, self.content, self.description, self.file_format,
                            self.date_published))
            conn.commit()


class Post:
    def __init__(self, user_id, title, content, date_published):
        self.user_id = user_id
        self.title = title
        self.content = content
        self.date_published = date_published

    def add_post(self):
        with sqlite3.connect('SMP.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts("
                           "user_id,"
                           "title,"
                           "content,"
                           "date_published) VALUES(?, ?, ?, ?)",
                           (self.user_id, self.title, self.content, self.date_published))
            conn.commit()


# ----------------------------------------------------- API SETUP------------------------------------------------------


app = Flask(__name__)
CORS(app)
app.debug = True


# -------------------------------------------------------ROUTES--------------------------------------------------------
@app.route('/', methods=["GET"])
# home screen
def welcome():
    response = {}
    if request.method == "GET":
        response["message"] = "Welcome"
        response["status_code"] = 201
        return response


# ---------------------------------------locations route---------------------------------------------------------
@app.route('/locations/', methods=["POST", "GET"])
def locations():
    response = {}
    # retrieves users locations data
    if request.method == "GET":
        try:
            with sqlite3.connect("SMP.db") as conn:
                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM locations")
                location = cursor.fetchall()
                response['status_code'] = 201
                response['data'] = location
            return response
        except:
            response['status_code'] = 401
            response['message'] = "Failed to retrieve data"
            return response
    # add users location data to locations table
    elif request.method == "POST":
        address = request.json['address']
        suburb = request.json['suburb']
        city = request.json['city']
        postal_code = request.json['postal_code']
        province = request.json['province']

        locations_obj = Locations(address, suburb, city, postal_code, province)
        response = locations_obj.register_location()
        return response

    else:
        response['status_code'] = 501
        response['message'] = "Invalid method selected"
        return response


@app.route("/location/<int:location_id>", methods=["GET", "PUT", "DELETE"])
def location(location_id):
    response = {}
    # retrieves users location data
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM locations WHERE location_id=" + str(location_id))
            location_ = cursor.fetchone()
            if location is not None:
                response['status_code'] = 201
                response['data'] = location_
                response['message'] = "Location retrieved successfully."
                return response
            else:
                response['status_code'] = 401
                response['message'] = "Location doesn't not exist"
                return response
    # updates users location
    elif request.method == "PUT":
        with sqlite3.connect('SMP.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("address") is not None:
                put_data["address"] = incoming_data.get("address")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE locations SET address=? WHERE location_id=?", (put_data["address"]
                                                                                          , location_id))
                    conn.commit()
                    response['address'] = "Address Updated successfully"
                    response['status_code'] = 201

            elif incoming_data.get("suburb") is not None:
                put_data["suburb"] = incoming_data.get("suburb")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE locations SET suburb=? WHERE location_id=?", (put_data["suburb"],
                                                                                         location_id))
                    conn.commit()
                    response['suburb'] = "suburb Updated successfully"
                    response['status_code'] = 201

            elif incoming_data.get("postal_code") is not None:
                put_data["postal_code"] = incoming_data.get("postal_code")
                if validate_integer(put_data["postal_code"] is True):
                    with sqlite3.connect('SMP.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE locations SET postal_code=? WHERE location_id=?",
                                       (put_data["postal_code"],
                                        location_id))
                        conn.commit()
                        response['postal_code'] = "Postal code Updated successfully"
                        response['status_code'] = 201

            elif incoming_data.get("city") is not None:
                put_data["city"] = incoming_data.get("city")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE locations SET city=? WHERE location_id=?", (put_data["city"],
                                                                                       location_id))
                    conn.commit()
                    response['city'] = "City Updated successfully"
                    response['status_code'] = 201

            elif incoming_data.get("province") is not None:
                put_data["province"] = incoming_data.get("province")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE locations SET province=? WHERE location_id=?", (put_data["province"],
                                                                                           location_id))
                    conn.commit()
                    response['province'] = "province Updated successfully"
                    response['status_code'] = 201

            else:
                response['message'] = "Updates were unsuccessful."
                response['status_code'] = 401
        return response

    else:
        response['status_code'] = 501
        response['message'] = "Method is not allowed"
        return response


# -------------------------------------------------Users route----------------------------------------------------
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
    elif request.method == "PATCH":
        email = request.json["email"]
        password = request.json["password"]

        if validate_email(email) is True and validate_string(email, password):
            table = JoinedTables(email, password)
            users_data = table.location_join_users()
            response['status_code'] = 201
            response['data'] = users_data
            response['message'] = 'Successfully logged In'
            return response
        elif validate_email(email) is None:
            response['status_code'] = 401
            response['message'] = "Enter valid email"
            return response

        elif not validate_string(email, password):
            response['status_code'] = 401
            response['message'] = "Please enter string values"
            return response

    # Register
    elif request.method == "POST":
        try:
            name = request.json['name']
            surname = request.json['surname']
            password = request.json['password']
            email = request.json['email']
            location_id = request.json['location_id']

            if validate_email(email) is True:
                if validate_string(name, surname, password, email, location_id):

                    user_obj = Users(name, surname, email, password, location_id)
                    user_obj.register_user()

                    response['message'] = "successfully added new user to database"
                    response['status_code'] = 201
                else:
                    response["validation"] = "String Validation failed please enter a string"
                return response
            elif validate_email(email) is None:
                response['status_code'] = 402
                response['message'] = "Please enter valid email"
                return response
        except ValueError:
            response['status_code'] = 401
            response['message'] = "Failed to load user into database"
            return response
    else:
        response['status_code'] = 501
        response['message'] = "Invalid method selected"
        return response


@app.route("/user/<int:user_id>", methods=["GET", "PUT", "DELETE"])
def user(user_id):
    response = {}
    # retrieves users details
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id=" + str(user_id))

            user = cursor.fetchone()

            if user is not None:
                response['status_code'] = 201
                response['data'] = user
                response['message'] = "User retrieved successfully."
                return response
            else:
                response['status_code'] = 209
                response['message'] = "User doesn't exist."
                return response
    # updates users details
    elif request.method == "PUT":
        with sqlite3.connect('SMP.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET name=? WHERE user_id=?", (put_data["name"], user_id))
                    conn.commit()
                    response['name'] = "Name Updated successfully"
                    response['status_code'] = 201

            elif incoming_data.get("surname") is not None:
                put_data["surname"] = incoming_data.get("surname")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET surname=? WHERE user_id=?", (put_data["surname"], user_id))
                    conn.commit()
                    response['surname'] = "Surname Updated successfully"
                    response['status_code'] = 201

            elif incoming_data.get("email") is not None:
                put_data["email"] = incoming_data.get("email")
                if bool(validate_email(put_data['email']) is True):
                    with sqlite3.connect('SMP.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET email=? WHERE user_id=?", (put_data["email"], user_id))
                        conn.commit()
                        response['email'] = "Email Updated successfully"
                        response['status_code'] = 201
                elif validate_email(str(put_data['email'])) is None:
                    response['email'] = "Invalid Email."
                    response['status_code'] = 401

            elif incoming_data.get("password") is not None:
                put_data["password"] = incoming_data.get("password")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password=? WHERE user_id=?", (put_data["password"], user_id))
                    conn.commit()
                    response['password'] = "Password Updated successfully"
                    response['status_code'] = 201
            else:
                response['message'] = "Updates were unsuccessful."
                response['status_code'] = 401
        return response
    # deletes user
    elif request.method == "DELETE":
        try:
            with sqlite3.connect('SMP.db') as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id =" + str(user_id))
                conn.commit()
                response['status_code'] = 201
                response['message'] = "User deleted successfully"
                return response
        except:
            response['status_code'] = 401
            response['message'] = "Failed to delete user"
            return response
    else:
        response['status_code'] = 501
        response['message'] = "Invalid method selected"
        return response


# ------------------------------------------Users Files---------------------------------------------------------
@app.route('/files/', methods=["GET", "POST"])
def files():
    response = {}
    # add information to files table
    if request.method == "POST":
        user_id = request.json['user_id']
        title = request.json['title']
        content = upload_file()
        description = request.json['description']
        file_format = request.json['format']
        date_published = datetime.datetime.now()

        obj_files = Files(user_id, title, content, description, file_format, date_published)
        obj_files.register_file()

        response['message'] = "File registered successfully"
        response['status_code'] = 201
    # retrieves all files from files table
    elif request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files")

            all_files = cursor.fetchall()

            response['message'] = "Files retrieved successfully"
            response['status_code'] = 201
            response['data'] = all_files
    else:
        response['message'] = "Invalid method selected"
        response['status_code'] = 401
    return response


@app.route("/file/<int:user_id>/<int:file_id>", methods=['GET', 'PUT', 'DELETE'])
def users_file(user_id, file_id):
    response = {}
    # retrieves users file
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE file_id=? AND user_id=?", (str(file_id), str(user_id)))

            user_file = cursor.fetchall()

            response['message'] = "Users File retrieved successfully"
            response['status_code'] = 201
            response['data'] = user_file
    # deletes users file
    elif request.method == "DELETE":
        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE * FROM files WHERE file_id=? AND user_id=?", (str(file_id), str(user_id)))
            conn.commit()

            response['message'] = "Users file deleted successfully"
            response['status_code'] = 201
    # updates users file
    elif request.method == "PUT":
        with sqlite3.connect("SMP.db") as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("title") is not None:
                put_data["title"] = incoming_data.get("title")
                with sqlite3.connect('SMP.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE files SET title=? WHERE user_id=? AND file_id=?", (put_data["title"]
                                                                                              , user_id, file_id))
                    conn.commit()
                    response['title'] = "Users title Updated successfully"
                    response['status_code'] = 201
    return response


# -------------------------------------------------USERS POSTS------------------------------------------
@app.route('/posts/', methods=["POST", "GET"])
def posts():
    response = {}
    # retrieves posts from table
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts")
            posts = cursor.fetchall()
            response["status_code"] = 201
            response['data'] = posts
    #  adds posts to table
    elif request.method == "POST":
        user_id = request.json['user_id']
        title = request.json['title']
        content = request.json['content']
        date_published = datetime.datetime.now()

        posts_obj = Post(user_id, title, content, date_published)
        posts_obj.add_post()

        response['message'] = "Post Added Successfully"
        response['status_code'] = 201

    else:
        response['message'] = "Invalid method selected"
        response['status_code'] = 401

    return response


@app.route("/post/<int:user_id>/<int:post_id>", methods=['GET', 'PUT', 'DELETE'])
def users_post(post_id, user_id):
    response = {}
    # retrieves post
    if request.method == "GET":
        with sqlite3.connect("SMP.db") as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE post_id = ? AND user_id=?", (str(post_id), str(user_id)))
            user_post = cursor.fetchall()
            conn.commit()

            response['message'] = "Users post retrieved successfully"
            response['status_code'] = 201
            response['data'] = user_post
    elif request.method == "DELETE":
        with sqlite3.connect("SMP.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE * FROM posts WHERE post_id = ? AND user_id=?", (str(post_id), str(user_id)))
    # updates post
    elif request.method == "PUT":
        with sqlite3.connect('SMP.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("title") is not None:
                put_data['title'] = incoming_data.get("title")
                with sqlite3.connect("SMP.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE posts set title=? WHERE post_id = ? AND user_id=?",
                                   (put_data["title"], str(post_id), str(user_id)))
                    conn.commit()
                    response['title'] = "Post title updated successfully"
                    response['status_code'] = 201
    else:
        response['message'] = "Invalid method"
        response["status_code"] = 201

    return response


if __name__ == "__main__":
    app.run()
    app.debug = True
