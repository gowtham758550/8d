from flask import Flask, render_template, send_file, redirect, request, make_response
from os import urandom, path, getcwd
from pymongo import MongoClient
from config import password
from bcrypt import checkpw, hashpw, gensalt
from converter import converter
from gridfs import GridFS
from flask_pymongo import PyMongo

CURRENT_DIR = getcwd()
DOWNLOAD_FOLDER = path.join(CURRENT_DIR, 'downloads')
DB_DOWNLOAD_FOLDER = path.join(CURRENT_DIR, 'download_from_db')
UPLOAD_FOLDER = path.join(CURRENT_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = urandom(24)
app.config["MONGO_URI"] = f"mongodb+srv://flaskAdmin:{password}@cluster0.8ejth.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
mongo = PyMongo(app)


client = MongoClient(f"mongodb+srv://flaskAdmin:{password}@cluster0.8ejth.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.get_database('8d-audio-converter')
records = db.registeration


def authorization():
    email = request.cookies.get('email')
    # token = request.cookies.get('token')
    name = request.cookies.get('name')
    # print(name, mail)
    cookie_list = [email, name]
    if None in cookie_list:
        return False
    return True


def allowed_files(file):
    return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['get', 'post'])
def home():
    # print(authorization())
    if authorization():
        return redirect('/convert')
    return redirect('/login')


@app.route('/login', methods=['post', 'get'])
def login():
    if authorization():
        return redirect('/convert')
    message = "Login to your account"
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        email_found = records.find_one({"email": email})
        if email_found:
            real_password = email_found['password']
            if checkpw(password.encode('utf-8'), real_password):
                name = email_found['name']
                email = email_found['email']
                resp = make_response(redirect('/convert'))
                resp.set_cookie('name', name)
                resp.set_cookie('email', email)
                return resp
            message = "Incorrect password"
            return render_template('login.html', message = message)
        else:
            message = "Invalid mail id"
            return render_template('login.html', message = message)

    return render_template('login.html', message = message)


@app.route('/register', methods=['post', 'get'])
def register():
    if authorization():
        return redirect('/convert')
    message = 'Register your account'
    if request.method == 'POST':
        name = request.form.get('fullname')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user_found = records.find_one({"name": name})
        email_found = records.find_one({"email": email})
        if user_found:
            message = 'Username not available'
            return render_template('register.html', message = message)
        elif email_found:
            message = 'Mail id already exist'
            return render_template('register.html', message = message)
        else:
            hashed = hashpw(password2.encode('utf-8'), gensalt())
            user_details = {"name": name, "email": email, "password": hashed}
            records.insert_one(user_details)
            return redirect('/login')

    return render_template('register.html', message = message)


@app.route('/convert')
def convert():
    if authorization():
        return render_template('convert.html', name = request.cookies.get("name"))
    return redirect('/login')


@app.route('/download', methods=['post'])
def download():
    if request.method == 'POST':
        song = request.files['song']
        song_path = path.join(UPLOAD_FOLDER, song.filename)
        # print(song.filename)
        output_song_name = song.filename.rstrip(".mp3") + " 8D" + ".mp3"
        output_song = path.join(DOWNLOAD_FOLDER, output_song_name)
        song.save(song_path)
        converter(song_path, output_song, 200)
        # print(song)
        file_data = open(output_song, "rb").read()
        fs = GridFS(db, collection=request.cookies.get("name"))
        fs.put(file_data, filename = output_song_name)
        name = request.cookies.get("name")
        print(type(name))
        user_collection = db[name]
        user_collection.insert_one({
            "name": output_song_name
        })
        return send_file(output_song, as_attachment=True)

@app.route("/download/<song>")
def download_song(song):
    if authorization():
        name = request.cookies.get("name")
        collection = db[name]
        document = collection.find_one({
            "name": song
        })
        print(document)
        return mongo.send_file(song)
        # fs = GridFS(db, collection=request.cookies.get("name"))
        # client_temp = client.grid_file
        # data = client_temp.fs.files.find_one({
        #     "filename": song
        # })
        # print(data)
        # id = data["_id"]
        # print(id)
        # output_data = fs.get(id)
        # requested_song = path.join(DB_DOWNLOAD_FOLDER, song)
        # output = open(requested_song, "wb")
        # output.write(output_data)
        # output.close()
        # return send_file(requested_song, as_attachment=True)


@app.route('/user/<name>')
def user(name):
    if authorization():
        if request.cookies.get("name") == name:
            # name = request.cookies.get("name")
            user_collection = db[name]
            documents = []
            for document in user_collection.find():
                # print(document)
                documents.append(document)
            return render_template("user.html", name = request.cookies.get("name"), email = request.cookies.get("email"), recent_conversions = documents)
    return redirect('/login')

@app.route('/logout')
def logout():
    if authorization():
        resp = make_response(redirect('/login'))
        resp.set_cookie('name', max_age=0)
        resp.set_cookie('email', max_age=0)
        return resp
    return redirect('/login')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


if __name__ == '__main__':
    app.run(debug=True)
