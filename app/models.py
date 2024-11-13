from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'Category'

    id = db.Column(db.String, primary_key=True)

class User(db.Model):
    __tablename__ = 'User'

    id = db.Column('userID', db.Integer, primary_key=True)
    username = db.Column('userName', db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    review_score = db.Column('reviewScore', db.Integer, default=0)
    created_at = db.Column('createdAt', db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', back_populates='buyer')
    listings = db.relationship('Listing', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'
    

class Listing(db.Model):
    __tablename__ = 'Listing'

    id = db.Column('listingID', db.Integer, primary_key=True)  
    listing_title = db.Column('listingTitle', db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    provider_id = db.Column('providerID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    description = db.Column(db.String, nullable=True)
    picture = db.Column(db.String, nullable=True)
    status = db.Column('status', db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    available_start = db.Column('availableStart', db.Date, nullable=False)
    available_end = db.Column('availableEnd', db.Date, nullable=False)
    created_at = db.Column('createdAt', db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='listings')

    def __repr__(self):
        return f'<Listing {self.listing_title}, ${self.price}>'




class Transaction(db.Model):
    __tablename__ = 'Transaction'

    id = db.Column('transactionID', db.Integer, primary_key=True) 
    status = db.Column('status', db.String, nullable=False)
    buyer_id = db.Column('buyerID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.listingID'), nullable=False)
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=datetime.utcnow)
    start_date = db.Column('startDate', db.Date, nullable=False)
    end_date = db.Column('endDate', db.Date, nullable=False)
    
    buyer = db.relationship('User', back_populates='transactions')
    listing = db.relationship('Listing', backref='transactions', lazy=True)



    def __repr__(self): 
        return f'<Transaction {self.listingID}, {self.status}, {self.listingID}'


class Notification(db.Model):
    __tablename__ = 'Notification'

    notification_id = db.Column('notificationID', db.Integer, primary_key=True)  
    receiver_id = db.Column('receiverID', db.Integer, db.ForeignKey('User.userID'), nullable=False)  
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=db.func.current_timestamp())  
    viewed = db.Column(db.Boolean, nullable=False, default=False)  
    type = db.Column(db.String, nullable=False)  

    def __repr__(self):
        return f"<Notification {self.notificationID}, Type: {self.type}, Viewed: {self.viewed}>" 


class Review(db.Model):
    __tablename__ = 'Review'

    review_id = db.Column('reviewID', db.Integer, primary_key=True)  
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=db.func.current_timestamp())  
    reviewed_id = db.Column('reviewedID', db.Integer, db.ForeignKey('User.userID'), nullable=False)  
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.listingID'), nullable=False)  
    rating = db.Column(db.Integer, nullable=False)  
    comment = db.Column(db.Text, nullable=True)  

    def __repr__(self):
        return f"<Review {self.reviewID}, Rating: {self.rating}>"