import uvicorn
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from models import Author, Book

from fastapi_sqlalchemy import DBSessionMiddleware, db
from schemas import Book as SchemaBook
from schemas import Author as SchemaAuthor

load_dotenv(".env")

app = FastAPI()

app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])

@app.get("/")
async def root():
    return {"message": "hello world"}


@app.post("/add-book/", response_model=SchemaBook)
async def add_book(book: SchemaBook):
    book_dict = book.model_dump()
    db_book = Book(**book_dict)
    db.session.add(db_book)
    db.session.commit()
    return db_book

@app.post("/add-author/", response_model=SchemaAuthor)
async def add_author(author: SchemaAuthor):
    author_dict = author.model_dump()
    db_author = Author(**author_dict)
    db.session.add(db_author)
    db.session.commit()
    return db_author

@app.get("/books/")
def get_books():
    books = db.session.query(Book).all()

    return books



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
