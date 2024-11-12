from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.String, primary_key=True)

class User(db.Model):
    __tablename__ ='user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    listings = db.relationship('Listing', backref='user', lazy=True)
    email = db.Column(db.String, nullable=False)
    reviewScore = db.Column(db.Integer, nullable=True)
    createdAt = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
class Listing(db.Model):
    __tablename__ = 'listing'

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
        return f'<Listing {self.listingTitle}, ${self.price}>'



class Transaction(db.Model):
    __tablename__ = 'transaction'

    id = db.Column(db.Integer(8), primary_key=True)
    status = db.Column(db.Boolean, nullable=False)
    buyerID = db.Column(db.Integer(8), db.ForeignKey('user.id'), nullable=False)
    listingID = db.Column(db.Integer(8), db.ForeignKey('listing.id'), nullable=False)
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    
    buyer = db.relationship('User', backref='transactions', lazy=True)
    listing = db.relationship('Listing', backref='transactions', lazy=True)


    def __repr__(self):
        return f'<Transaction {self.listingID}, {self.status}, {self.listingID}'


class Notification(db.Model):
    __tablename__ = 'notification'

    notificationID = db.Column(db.Integer(8), primary_key=True)  
    receiverID = db.Column(db.Integer(8), nullable=False)  
    createdAt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  
    viewed = db.Column(db.Boolean, nullable=False, default=False)  
    type = db.Column(db.String, nullable=False)  

    def __repr__(self):
        return f"<Notification {self.notificationID}, Type: {self.type}, Viewed: {self.viewed}>" 


class Review(db.Model):
    __tablename__ = 'review'

    reviewID = db.Column(db.Integer(8), primary_key=True)  
    createdAt = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  
    reviewedID = db.Column(db.Integer(8), db.ForeignKey('user.userID'), nullable=False)  
    listingID = db.Column(db.Integer, db.ForeignKey('listing.listingID'), nullable=False)  
    rating = db.Column(db.Integer, nullable=False)  
    comment = db.Column(db.Text, nullable=True)  

    def __repr__(self):
        return f"<Review {self.reviewID}, Rating: {self.rating}>"