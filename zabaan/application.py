from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, translate_lyrics, get_language_codes, get_language_list

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///zabaan.db")

# Global variable to keep track of whether user is logged in
no_login = False

@app.route("/", methods=["GET", "POST"])
def index():
    '''Main landing page where user can translate and save songs'''
    global no_login

    if request.method == "GET":
        # Check if user is logged in as someone
        if 'user_id' not in session.keys():
            no_login = True
        else:
            no_login = False
        # get_language_list() returns list of all supported langs to use in jinja template
        return render_template("index.html", langs=get_language_list(), source_empty=True, no_login=no_login)

    # POST REQUEST:
    # Getting song user wants to translate
    user_input = request.form.get("input")

    # Checking whether user is logged in with an acco'unt
    if 'user_id' not in session.keys():
        no_login = True
    else:
        no_login = False

    # This is to ensure the tongue button is disabled on load
    if not user_input:
        source_empty = True
        return render_template("index.html", source_empty=source_empty, langs=get_language_list(), no_login=no_login)

    # Gets the selected languages of source and destination
    src_lang = request.values.get("src-lang")
    dest_lang = request.values.get("dest-lang")

    # Helper function that returns a dictionary where each key is language that maps to its language code
    codes = get_language_codes()

    # (TEMPORARY) Reloads page if user has not selected a source or destination language
    if src_lang == "from..." or dest_lang == "to...":
        return render_template("index.html", source=user_input, langs=get_language_list(), no_login=no_login)

    # Translating using helper function, passing in mapped values of the user's selected languages
    translation = translate_lyrics(user_input, codes[src_lang], codes[dest_lang])

    # Gets whether user wants to save or translate
    choice = request.form['btn-choice']
    # Gets inputted song name
    song = request.form.get("song-name")
    # Gets the outputted (translated) text
    output = request.form.get("output")

    if choice == 'Save':
        # Returns error message if user did not enter a song name
        if not song:
            return render_template("index.html", source=user_input, langs=get_language_list(), no_songname=True, src_lang=src_lang, dest_lang=dest_lang)
        db.execute("INSERT INTO saved VALUES(:id, :song, :source, :dest, :srclyrics, :destlyrics);",id=session['user_id'], song=song, source=src_lang, dest=dest_lang, srclyrics=user_input, destlyrics=output)
        rows = db.execute("SELECT song,source,dest,sourcelyrics,destlyrics FROM saved WHERE user_id = :id;", id=session['user_id'])
        return render_template("saved.html", rows=rows)


    # Reload page with translation (and source in the input box)
    return render_template("index.html", source=user_input, translation=translation, langs=get_language_list(), no_login=no_login, src_lang=src_lang, dest_lang=dest_lang)

@app.route("/saved")
@login_required
def saved():
    '''Displays all current saved translations by querying database'''
    rows = db.execute("SELECT song,source,dest,sourcelyrics,destlyrics FROM saved WHERE user_id = :id;", id=session['user_id'])
    return render_template("saved.html",rows=rows)

@app.route("/edit/<src_lyrics>/<dest_lyrics>/<src_lang>/<dest_lang>", methods=["GET", "POST"])
@login_required
def edit(src_lyrics, dest_lyrics, src_lang, dest_lang):
    '''Displays lyrics of selected song from user's saved collection and allows them to edit the lyrics'''
    if request.method == "GET":
        # Gets corresponding row from database
        row = db.execute("SELECT * FROM saved WHERE user_id= :id AND sourcelyrics= :src_lyrics AND destlyrics= :dest_lyrics AND source= :src_lang AND dest= :dest_lang",
                          id=session['user_id'], src_lyrics=src_lyrics, dest_lyrics=dest_lyrics, src_lang=src_lang, dest_lang=dest_lang)[0]

        song = row['song']

        return render_template("edit.html", source=src_lyrics, translation=dest_lyrics, song=song, row=row)

    # Getting all the fields of the form
    user_input = request.form.get("editInput")
    output = request.form.get("editOutput")
    song_name = request.form.get("song-name-edit")

    # Updating corresponding columns in database
    db.execute("UPDATE saved SET song= :new_song, sourcelyrics= :new_source, destlyrics= :new_dest WHERE user_id=:id AND sourcelyrics= :src_lyrics AND destlyrics= :dest_lyrics AND source= :src_lang AND dest= :dest_lang",
                new_song=song_name, new_source=user_input, new_dest=output, id=session['user_id'], src_lyrics=src_lyrics, dest_lyrics=dest_lyrics, src_lang=src_lang, dest_lang=dest_lang)

    return redirect("/saved")


@app.route("/about")
def about():
    """Display info about project"""
    return render_template("about.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    uname = request.form.get("username")
    pw = request.form.get("password")
    # Ensure username was submitted
    if not uname:
        return render_template('register.html', invalid_un=True, error_msg="Must provide username")

    elif len(uname) < 4:
        return render_template('register.html', invalid_un=True, error_msg="Username too short")

    # Ensure password was submitted
    if not pw:
        return render_template('register.html', invalid_pw=True, error_msg="Must provide password")

    elif len(pw) < 6:
        return render_template('register.html', invalid_pw=True, error_msg="Password too short")

    elif pw != request.form.get("password-confirm"):
        return render_template('register.html', invalid_pw=True, error_msg="Passwords do not match")

    # Query database for username (if exists)
    rows = db.execute("SELECT * FROM users WHERE name = :username",
                        username=uname)

    # Ensure username does not already exist
    if len(rows) == 1:
        return render_template('register.html', invalid_un=True, error_msg="Username already exists")

    # Inserting new username and hashed password into database if they are valid
    db.execute("INSERT INTO users(name,hash) VALUES(:uname,:pw)", uname=uname.rstrip(), pw=generate_password_hash(pw))

    # Re-initialize rows to include newly added account
    rows = db.execute("SELECT * FROM users WHERE name = :username",
                      username=uname)

    # Remember which user has logged in
    session["user_id"] = rows[0]["id"]

    # Redirect user to home page
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        uname = request.form.get("username")
        pw = request.form.get("password")

        # Ensure username is valid
        if not uname:
            return render_template("login.html", invalid_un=True, error_msg="Must provide username")

        # Ensure password is valid
        if not pw:
            return render_template("login.html", invalid_pw=True, error_msg="Must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = :username", username=uname.rstrip())

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return render_template("login.html", invalid_un=True, error_msg="Username does not exist")

        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", invalid_pw=True, error_msg="Incorrect password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/passwordchange", methods=["GET", "POST"])
@login_required
def password_change():
    if request.method == "GET":
        return render_template("change.html")
    pw = request.form.get("password").strip()
    pw_confirm = request.form.get("password-confirm").strip()

    if len(pw) < 6:
        return render_template("change.html", invalid_pw=True, error_msg="Password too short")

    elif pw != pw_confirm:
        return render_template("change.html", invalid_pw=True, error_msg="Passwords do not match")

    # Update password in database for current user
    db.execute("UPDATE users SET hash = :pw WHERE id = :id ", pw=generate_password_hash(pw), id=session["user_id"])

    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
