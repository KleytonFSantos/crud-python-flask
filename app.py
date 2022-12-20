from flask import Flask, jsonify, request, make_response
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow import fields


app = Flask(__name__)

load_dotenv()

user = os.getenv("DATABASE_USER")
host = os.getenv("DATABASE_HOST")
port = os.getenv("DATABASE_PORT")
database_name = os.getenv("DATABASE_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{user}@{host}:{port}/{database_name}"

db = SQLAlchemy(app)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def __init__(self, title, author):
        self.title = title
        self.author = author

    def __repr__(self):
        return '' % self.id


with app.app_context():
    db.create_all()


class BookSchema(SQLAlchemySchema):
    class Meta(SQLAlchemySchema.Meta):
        model = Book
        sqla_session = db.session
    id = fields.Number(dump_only=True)
    title = fields.String(required=True)
    author = fields.String(required=True)


@app.route('/')
def home():
    return jsonify('Hello World')


@app.route('/books', methods=['GET'])
def get_books():
    allBooks = Book.query.all()
    bookSchema = BookSchema(many=True)
    books = bookSchema.dump(allBooks)
    return make_response(books)


@app.route('/books/<int:id>', methods=['GET'])
def get_books_by_id(id):
    query = db.session.execute(db.select(Book).filter_by(id=id)).one()
    oneBook = BookSchema(many=True)
    book = oneBook.dump(query)
    return make_response(book)


@app.route('/books/filtered/<string:search>', methods=['GET'])
def filtered_books(search):
    query = Book.query.filter(Book.title.like(search + "%")).all()
    if query == []:
        query = Book.query.filter(Book.author.like(search + "%")).all()
    books = BookSchema(many=True)
    response = books.dump(query)
    if response == []:
        return make_response(jsonify(message="This book don't exist"), 404)
    return make_response(response)


@app.route('/books/create', methods=['POST'])
def create_book():
    data = request.get_json()
    bookSchema = BookSchema(load_instance=True)
    book = bookSchema.load(data)
    result = bookSchema.dump(book.create())
    return make_response(jsonify({"books": result}), 200)


@app.route('/books/<int:id>', methods=['PUT'])
def edit_book(id):

    data = request.get_json()

    getBooks = Book.query.get(id)

    if data.get('title'):
        getBooks.title = data.get('title')
    if data.get('author'):
        getBooks.author = data.get('author')

    db.session.add(getBooks)
    db.session.commit()

    bookSchema = BookSchema(only=['id', 'title', 'author'])
    book = bookSchema.dump(getBooks)

    return make_response(jsonify({'book': book}, 200))


@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    getBook = Book.query.get(id)
    db.session.delete(getBook)
    db.session.commit()

    return make_response("", 204)


app.run(port=8000, host='localhost', debug=True)
