from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
# from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
import random
import json
import config
import requests
import uuid
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rybka1'
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_PATH

db = SQLAlchemy(app)
# migrate = Migrate(app, db)

# manager = Manager(app)
# manager.add_command('db', MigrateCommand)


from models import *

db.create_all()


@app.route('/')
def start():
    return render_template('login_user.html')


@app.route('/start', methods=['POST', 'GET'])
def login():
    # print(request.form.get('user'))
    # session['user'] = request.form.get('user')
    # name = session.get('user')
    # print(name)
    return render_template('room.html')


@app.route("/json", methods=['POST'])
def book_json():
    """
    method to add the book to db
    method gets json,
    """
    print("added new book")
    data = json.loads(request.get_json())
    genre = Genre.query.filter_by(name=data["genre"]).first()
    if genre is None:
        genre = Genre(name=data["genre"])
    print("genre: ", data["genre"])
    author = Author.query.filter_by(name=data["author"]).first()
    if author is None:
        author = Author(name=data["author"])
    room = Room.query.filter_by(name=data['room']).first()
    if room is None:
        room = Room(name=data['room'])
    db.session.add(genre)
    db.session.add(author)
    db.session.commit()
    book = Books(title=data["name"], photo=data["picture"],
                 description=data["description"],
                 genre_id=genre.id, author_id=author.id,
                 rating_from_bookstore=data['rating'])
    db.session.add(book)
    db.session.commit()
    db.session.add(room)
    room.rooms_books.append(book)
    db.session.commit()
    return '<p>Book added</p>'


@app.route("/facebook")
def main_page():
    return render_template('facebook.html')


@app.route('/rating', methods=['GET'])
def rating_page():
    books = Books.query.all()
    upd = []
    print(len(books))
    for i in range(len(books)):
        book = books[i]
        upd.append(dict(title=book.title,
                        photo=book.photo,
                        description=book.description,
                        likes=book.likes, dislikes=book.dislikes))
    upd = sorted(upd, key=lambda x: x['likes'] if x['likes'] else 0, reverse=True)
    return render_template("rating.html", items=upd, )


@app.route('/bookpage1', methods=['POST', 'GET'])
def book_page1():
    name = session['room_id']
    book = Books.query.filter(Books.rooms_with_books.any(name=name)).first()
    book_id = book.id
    if request.method == 'POST':
        # room = Room.query.filter(Room.rooms_books.any(name=book_id)).first()
        book = Books.query.get(int(request.form['book_id']))
        if request.form['action'] == 'like':
            if book.get_like() == None:
                book.set_like(0)
            book.set_like(int(book.get_like()) + 1)
        else:
            if book.get_dislike() == None:
                book.set_dislike(0)
            book.set_dislike(int(book.dislikes) + 1)
        db.session.commit()
    return render_template("random_book.html", title=book.title,
                           photo=book.photo,
                           description=book.description,
                           book_id=book_id)
    # return render_template("book.html", books=books)


# @app.route("/bookpage", methods=['POST', 'GET'])
# def book_page():
#     books = Books.query.all()
#     num_of_book = random.randint(0, len(books))
#     book = books[num_of_book]
#     print('lol')
#     if request.method == 'POST':
#         print(int(request.form['book_id']))
#         book = books[int(request.form['book_id'])]
#         print(book)
#         if 'like' in request.form:
#             if book.get_like() == None:
#                 book.set_like(0)
#             book.set_like(int(book.get_like()) + 1)
#         else:
#             if book.get_dislike() == None:
#                 book.set_dislike(0)
#             book.set_dislike(int(book.get_dislike()) + 1)
#         db.session.commit()
#     return render_template("book.html", title=book.get_title(),
#                            photo=book.get_photo(),
#                            description=book.get_description(),
#                            book_id=num_of_book)


@app.route("/add_book", methods=['POST'])
def add_book():
    room = request.form['book_id']

    title = request.form.get('book_title')
    photo = request.form.get('photo')
    author = request.form.get('author')
    description = request.form.get('description')
    book_dict = {'name': title, 'picture': photo, 'author': author,
                 'description': description, 'genre': None,
                 'rating': None, 'room': room}
    json_book = json.dumps(book_dict)
    requests.post("http://127.0.0.1:5000/json", json=json_book)
    if request.form['action'] == "add":
        return render_template('adding.html', room_id=room)
    else:
        return render_template('end.html', room_id=room)


@app.route('/adding')
def adding():
    room_id = secrets.token_hex(4)
    return render_template('adding.html', room_id=room_id)


@app.route('/room', methods=['POST'])
def room():
    print('lol')
    if 'create' in request.form:
        room_id = uuid.uuid4()
        print('lol')
        return render_template('adding.html', room_id=room_id)
    if 'submit' in request.form:
        room_id = request.form.get('room_id')
        session['room_id'] = room_id
        return redirect(url_for('.book_page1'))


@app.route("/action")
def action():
    return render_template('choose_option.html')


# twitter_blueprint = make_twitter_blueprint(
# api_key='f7dUFCVeAspsUmXBZXGLrNF8e',
#
# api_secret='yAjRQ7CXzoOmPjfoVO2QLOnz40sqhIyU3a43WC4NdZXbLXwJMI')
#
# app.register_blueprint(twitter_blueprint, url_prefix="/twitter_login")


# @app.route("/twitter")
# def twitter_login():
#     if not twitter.authorized:
#         return redirect(url_for("twitter.login"))
#     account_info = twitter.get("account/settings.json")
#
#     if account_info.ok:
#         account_info_json = account_info.json()
#         return "<h1> Your twitter name is @{}".format(
#             account_info_json['screen_name'])
#     return '<h1>Request failed!</h1>'


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
    # manager.run()
    # app.run(debug=True)
