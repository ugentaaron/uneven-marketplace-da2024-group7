from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Category Model
class Category(db.Model):
    __tablename__ = 'Category'

    id = db.Column(db.String, primary_key=True)

    listings = db.relationship('CategoryListing', back_populates='category')


# CategoryListing Model (Many-to-Many)
class CategoryListing(db.Model):
    __tablename__ = 'CategoryListing'

    category_id = db.Column('categoryID', db.String, db.ForeignKey('Category.id'), primary_key=True)
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.id'), primary_key=True)

    category = db.relationship('Category', back_populates='listings')
    listing = db.relationship('Listing', back_populates='categories')


# User Model
class User(db.Model):
    __tablename__ = 'User'

    id = db.Column('userID', db.Integer, primary_key=True)
    username = db.Column('userName', db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    review_score = db.Column('reviewScore', db.Float, default=0.0)
    created_at = db.Column('createdAt', db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', back_populates='renter')
    listings = db.relationship('Listing', back_populates='provider')
    notifications = db.relationship('Notification', back_populates='receiver')
    given_feedback = db.relationship('UserReview', back_populates='reviewer', foreign_keys='UserReview.reviewer_id')
    received_feedback = db.relationship('UserReview', back_populates='reviewed', foreign_keys='UserReview.reviewed_id')

    def __repr__(self):
        return f'<User {self.username}>'


# Listing Model
class Listing(db.Model):
    __tablename__ = 'Listing'

    id = db.Column('listingID', db.Integer, primary_key=True)
    listing_title = db.Column('listingTitle', db.String(100), nullable=False)
    provider_id = db.Column('providerID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    picture = db.Column(db.String, nullable=True)
    status = db.Column('status', db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    available_start = db.Column('availableStart', db.Date, nullable=False)
    available_end = db.Column('availableEnd', db.Date, nullable=False)
    price_per_day = db.Column('pricePerDay', db.Float, nullable=True)
    created_at = db.Column('createdAt', db.DateTime, default=datetime.utcnow, nullable=False)

    provider = db.relationship('User', back_populates='listings')
    transactions = db.relationship('Transaction', back_populates='listing')
    reviews = db.relationship('UserReview', back_populates='listing')
    categories = db.relationship('CategoryListing', back_populates='listing')
    vehicle = db.relationship('Vehicle', backref='listing', uselist=False)

    def __repr__(self):
        return f'<Listing {self.listing_title}, ${self.price_per_day}>'


# Vehicle Model (One-to-One with Listing)
class Vehicle(db.Model):
    __tablename__ = 'Vehicle'

    vehicle_id = db.Column('vehicleID', db.Integer, primary_key=True)
    created_at = db.Column('createdAt', db.DateTime, default=datetime.utcnow, nullable=False)
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.id'), nullable=False)
    make = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column('vehicleType', db.String, nullable=False)
    fuel_type = db.Column('fuelType', db.String, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    extra_features = db.Column('extraFeatures', db.Text, nullable=True)

    def __repr__(self):
        return f'<Vehicle {self.make}, {self.year}>'


# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'Transaction'

    id = db.Column('transactionID', db.Integer, primary_key=True)
    status = db.Column('status', db.String, nullable=False)
    renter_id = db.Column('renterID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.id'), nullable=False)
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=datetime.utcnow)
    start_date = db.Column('startDate', db.Date, nullable=False)
    end_date = db.Column('endDate', db.Date, nullable=False)
    total_price = db.Column('totalPrice', db.Float, nullable=True)

    renter = db.relationship('User', back_populates='transactions')
    listing = db.relationship('Listing', back_populates='transactions')

    def __repr__(self):
        return f'<Transaction {self.id}, Status: {self.status}>'


# Notification Model
class Notification(db.Model):
    __tablename__ = 'Notification'

    notification_id = db.Column('notificationID', db.Integer, primary_key=True)
    receiver_id = db.Column('receiverID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, nullable=False, default=False)
    message = db.Column(db.Text, nullable=False)

    receiver = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification {self.notification_id}, Message: {self.message}, Viewed: {self.viewed}>"


# UserReview Model
class UserReview(db.Model):
    __tablename__ = 'UserReview'

    review_id = db.Column('reviewID', db.Integer, primary_key=True)
    created_at = db.Column('createdAt', db.DateTime, nullable=False, default=datetime.utcnow)
    reviewer_id = db.Column('reviewerID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    reviewed_id = db.Column('reviewedID', db.Integer, db.ForeignKey('User.userID'), nullable=False)
    listing_id = db.Column('listingID', db.Integer, db.ForeignKey('Listing.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    reviewer = db.relationship('User', back_populates='given_feedback', foreign_keys=[reviewer_id])
    reviewed = db.relationship('User', back_populates='received_feedback', foreign_keys=[reviewed_id])
    listing = db.relationship('Listing', back_populates='reviews')

    def __repr__(self):
        return f"<Review {self.review_id}, Rating: {self.rating}>"
