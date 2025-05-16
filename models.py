# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CrawledData(db.Model):
    __tablename__ = "crawled_data"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<CrawledData {self.url}>"
