import os
import requests
from flask import Flask, session,render_template,request,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL1"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/",methods=["POST","GET"])
def index():
    session["user_id"]=-1
    return render_template("index.html")

@app.route("/SearchReview")
def SearchReview():
    user=db.execute("SELECT * FROM users WHERE id=:id",{"id":session["user_id"]}).fetchone()
    return render_template("search_review.html",Name=user.name,message="")

@app.route("/books", methods=["POST"])
def books():
    user=db.execute("SELECT * FROM users WHERE id=:id",{"id":session["user_id"]}).fetchone()
    book_name=request.form.get("book_name")
    author=request.form.get("author")
    isbn=request.form.get("isbn")
    books=db.execute("SELECT * FROM books WHERE title LIKE :book OR author LIKE :author OR isbn LIKE :isbn ",
                    {"book":f"%{book_name}%","isbn":f"%{isbn}%","author":f"%{author}%"}).fetchall()
    
    if books is None:
        return render_template("search_review",Name=user.name,message="No book found")

    return render_template("books.html",Name=user.name,books=books)
    

@app.route("/Review/<int:book_id>")
def Review(book_id):
        user=db.execute("SELECT * FROM users WHERE id=:id",{"id":session["user_id"]}).fetchone()
        book=db.execute("SELECT * FROM books WHERE id=:id",{"id":book_id}).fetchone()
        res=requests.get(" https://www.goodreads.com/book/review_counts.json",
                        params={"key":"rqlAtLD19JVP0U82ahAKg","isbns":book.isbn})
        if res.status_code==400:
            return "<h1>Not Found<h1>"
        data=res.json()
        average_rating=data["books"][0]["average_rating"]
        work_ratings_count=data["books"][0]["work_ratings_count"]
        reviews=db.execute("SELECT * FROM reviews WHERE book_id=:id",{"id":book.id}).fetchall()
        return render_template("book.html",average_rating=average_rating,work_ratings_count=work_ratings_count,book=book,Name=user.name,reviews=reviews)

@app.route("/AddReview/<int:book_id>",methods=["POST"])
def AddReview(book_id):
    user=db.execute("SELECT * FROM users WHERE id=:id",{"id":session["user_id"]}).fetchone()
    if db.execute("SELECT * FROM reviews WHERE user_id=:id",{"id":session["user_id"]}).rowcount!=0:
        return render_template("AddFail.html",Name=user.name)

    try:

        rating=int(request.form.get("rating"))
    except ValueError:
        return "<h1> fail </h1>"

    review=request.form.get("review")
    db.execute("INSERT INTO reviews (rating,review,book_id,user_id) VALUES (:rating,:review,:book_id,:user_id)"
                ,{"rating":rating,"review":review,"book_id":book_id,"user_id":user.id})
    db.commit()
    return render_template("AddSuccess.html")



@app.route("/login",methods=["POST","GET"])
def login():
    if session["user_id"]==-1:
        #Get the username and check that it is avalable in database
        username=request.form.get("username")
        password=request.form.get("password")
        user=db.execute("SELECT * FROM users WHERE username=:username ",{"username":username}).fetchone()
        if user is None:
            return render_template("LogInFail.html",username=False,password=True)
        if user.password!=password:
            return render_template("LogInFail.html",username=True,password=False)
        session["user_id"]=user.id
        return render_template("Home.html",Name=user.name)
    else:
        user=db.execute("SELECT * FROM users WHERE id=:id",{"id":session["user_id"]}).fetchone()
        return render_template("Home.html",Name=user.name)


@app.route("/Register",methods=["POST"])
def Register():
    return render_template("register.html",message="")

@app.route("/AddUser",methods=["POST"])
def AddUser():

    #Get user name first and check it
    name=request.form.get("name")
    if name == "":
        return render_template("register.html",message="Empty space name")
    
    #Get username and check there it is unique
    username=request.form.get("username")
    if db.execute("SELECT * FROM users WHERE username=:username",{"username":username}).rowcount!=0:
        return render_template("register.html",message="Username already taken")

    #Check that both passwords equal each other
    password=request.form.get("password")
    re_password=request.form.get("re-password")
    if password=="" or password!=re_password:
        return render_template("register.html",message="Invalid Password retry again")
    
    db.execute("INSERT INTO users (username,password,name) VALUES(:username,:password,:name)",
    {"username":username,"name":name,"password":password})
    db.commit()
    return render_template("success.html")

@app.route("/api/<string:isbn>")
def bookapi(isbn):

    res=requests.get("https://www.goodreads.com/book/review_counts.json",
                    params={"key":"rqlAtLD19JVP0U82ahAKg","isbns":isbn})
    
    data=res.json()
    rating=data["books"][0]["average_rating"]
    review=data["books"][0]["reviews_count"]

    book=db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()

    return jsonify(
        {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": review,
            "average_score": rating
        }
    )