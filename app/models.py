from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    listings = db.relationship('Listing', backref='user', lazy=True)
    email = db.Column(db.String, nullable=False)
    reviewScore = db.Column(db.Integer, nullable=True)
    createdAt = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
class Listing(db.Model):
    id = db.Column(db.Integer(8), primary_key=True)
    listingTitle = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    providerID = db.Column(db.Integer(8), db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    picture = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    location = db.Column(db.String, nullable=False)
    available_start = db.Column(db.Date, nullable=False)
    available_end = db.Column(db.Date, nullable=False)
    createdAt = db.Column(db.DateTime, nullable=False)


    def __repr__(self):
        return f'<Listing {self.listing_name}, ${self.price}>'

class Transaction(db.Model):
    id = db.Column(db.Integer(8), primary_key=True)
    status = db.Column(db.Boolean, nullable=False)
    buyerID = db.Column(db.Integer(8), db.ForeignKey('user.id'), nullable=False)
    listingID = db.Column(db.Integer(8), db.ForeignKey('listing.id'), nullable=False)
    createdAt = db.Column(db.DateTime, nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)