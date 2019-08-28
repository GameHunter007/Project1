import csv 
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session

#Link to database
engine=create_engine(os.getenv("DATABASE_URL1"))
db=scoped_session(sessionmaker(bind=engine))


def main():
    file=open("books.csv")
    reader=csv.reader(file)
    for isbn,title,author,year in reader:
        db.execute("INSERT INTO books (isbn,title,author,year) VALUES(:isbn,:title,:author,:year)",
        {"isbn":isbn ,"title":title , "author":author , "year":year })
        print(f"added {title}")
    db.commit()




if __name__=="__main__":
    main()