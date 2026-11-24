app = Flask(__name__), create website, the @app.
@app.route("/home"), when the browser opens /home, runs the function below it.
def and return, def makes a function (a named block of code). return is what it sends back.
methods=[], "GET" for viewing page and "POST" sending data (forms, login, register, buy).
request.form["email"], reads what the user typed in an HTML form field named email. .strip() removes extra spaces and .lower() makes the typed lowercase.
session, memory per user, kept in a cookie, works like dictionary, for each user to have their own cart saved data.
render_template("home.html", products2=get_all_products()), opens an HTML file and passes data into it (products2=get_all_products()).
redirect(url_for("login")), sends the browser to another page, url_for("login") finds the URL of the function named login.
Database
database stores data permanently (users, order, products), SQLite locally (store.db) and PostgreSQL server (Render)
conn = get_db(), opens a connection to the database.
cursor = conn.cursor(), the tool that carries the data between python and database.
execute_query(cursor, ...), sends one command.
cursor.fetchone(), get 1 row or None and cursor.fetchall(), get all row.
conn.commit(), saves changes, need when INSERT, UPDATE, and DELETE.
conn.close(), closes the connection.
conn.rollback(), cancels unsaved changes when something fails. 
4 main SQL commands
SELECT * FROM products2           -- read
INSERT INTO products2 (...) VALUES (...)   -- add
UPDATE products2 SET stock = 5 WHERE id = 1  -- change
DELETE FROM products2 WHERE id = 1  -- remove
generate_password_hash(password), turns to long scrambled text and save it, prevent others from seeing the typed password.
check_password_hash(hash, password), checks if the typed password matches the stored scrambled saved one, returns True/False.
.env and load_dotenv(), a file that holds the secrets(SECRET_KEY, DATABASE_URL), load_dotenv() loads it, os.getenv("SECRET_KEY") reads one value. in separated file for it hide/never upload.
CSRFProtect(app), blocks fake forms from other websites, every POST form needds a hidden token in the HTML file.
secure_filename(file.filename),  cleans an uploaded file name so it can't trick the server into saving the file in the wrong place.
SESSION_COOKIE_HTTPONLY = True,  the session can only be read by server, prevent hacker injects bad JavaScript.
uuid.uuid4().hex[:8], makes a random 8-character ID. add in image name prevent the two uploads to have same name.
MAX_CONTENT_LENGTH, biggest upload limit.
cursor.rowcount, how many rows the last command changed.
RETURNING id, save the id, then gives back the new row's id in the same INSERT command, so you don't need a second query.
UNIQUE (user_id, product_id), the database refuses a duplicate pair, one product inside the cart, user can't have the same product twice. 
IntegrityError, raise when a rules breaks like registering an email that already registered. catch with except.
DictCursor and row_factory, let you read by column name like user["email"] instead of user[2].
SESSION_COOKIE_SECURE, cookie only travels over HTTPS and SAMESITE = "Lax", other website can't send your cookie.
request.referrer, sends the user back to the page where he came from.
if __name__ == "__main__":, runs app.run() when this file start directly, noy when other file imports it.
SERIAL the id number goes up bt itself, SERIAL is PostgreSQL and AUTOINCREMENT is SQLite.
COALESCE(MAX(id), -1) + 1, Finds the biggest id and adds 1, if the table is empty COALESCE use -1 for the first id to start 0 (-1 + 1 = 0).
