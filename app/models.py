from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    listings = db.relationship('Listing', backref='user', lazy=True)
    email = db.Column(db.String, nullable = False)



    def __repr__(self):
        return f'<User {self.username}>'
    
class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Listing {self.listing_name}, ${self.price}>'



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

