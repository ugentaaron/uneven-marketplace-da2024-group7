from flask import Blueprint, session, request, redirect, url_for, render_template, flash
from .models import db, User, Listing, Notification, Category, Transaction, UserReview, CategoryListing, Vehicle
from datetime import datetime

main = Blueprint('main', __name__)


# Index route
@main.route('/')
def index():
    all_listings = Listing.query.all()
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        listings = Listing.query.filter_by(provider_id=user.id).all()
        return render_template('index.html', username=user.username, listings=listings, all_listings=all_listings)
    return render_template('index.html', username=None, all_listings=all_listings)


# Register route
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first() is None:
            new_user = User(username=username)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            flash("Registration successful!", "success")
            return redirect(url_for('main.index'))
        flash("Username already registered", "danger")
    return render_template('register.html')


# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        else:
            flash("User not found. Please try again.", "danger")
    return render_template('login.html')


# Logout route
@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.index'))


# Add listing route
@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        new_listing = Listing(
            listing_title=request.form['listing_name'],
            price_per_day=float(request.form['price']),
            location=request.form['location'],
            available_start=request.form['available_start'],
            available_end=request.form['available_end'],
            description=request.form['description'],
            status=request.form['status'],
            provider_id=session['user_id'],
            created_at=datetime.utcnow()
        )
        db.session.add(new_listing)
        db.session.commit()

        # Handle categories (many-to-many)
        selected_categories = request.form.getlist('categories')
        for category_name in selected_categories:
            category_listing = CategoryListing(category_name=category_name, listing_id=new_listing.id)
            db.session.add(category_listing)
        db.session.commit()

        # Handle vehicle (one-to-one)
        vehicle = Vehicle(
            listing_id=new_listing.id,
            make=request.form['make'],
            year=int(request.form['year']),
            vehicle_type=request.form['vehicle_type'],
            fuel_type=request.form['fuel_type'],
            seats=int(request.form['seats']),
            extra_features=request.form.get('extra_features', '')
        )
        db.session.add(vehicle)
        db.session.commit()

        return redirect(url_for('main.index'))

    categories = Category.query.all()  # For category selection in the form
    return render_template('add_listing.html', categories=categories)

@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    return render_template('listings.html', listings=all_listings)


@main.route('/my-listings')
def my_listings():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    listings = Listing.query.filter_by(provider_id=session['user_id']).all()
    return render_template('my_listings.html', listings=listings)



# Listing view route
@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if request.method == 'POST':
        if 'user_id' not in session:
            flash("Please log in to make a purchase.", "danger")
            return redirect(url_for('main.login'))

        start_date = request.form.get('start_date') or listing.available_start
        end_date = request.form.get('end_date') or listing.available_end

        new_transaction = Transaction(
            listing_id=listing.id,
            renter_id=session['user_id'],
            status="pending",
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.utcnow()
        )
        db.session.add(new_transaction)
        db.session.commit()

        flash("Transaction created successfully!", "success")
        return redirect(url_for('main.transaction_details', transaction_id=new_transaction.id))

    return render_template('view_listing.html', listing=listing)



# Transaction details route
@main.route('/transaction/<int:transaction_id>', methods=['GET'])
def transaction_details(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    transaction = Transaction.query.get(transaction_id)
    if transaction and transaction.renter_id == session['user_id']:
        return render_template('transaction_details.html', transaction=transaction)

    return 'Transaction not found', 404


# Search route
@main.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        location = request.form.get('location')
        max_price = request.form.get('max_price')
        category_name = request.form.get('category_name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        query = Listing.query

        if location:
            query = query.filter(Listing.location.ilike(f"%{location}%"))
        if max_price:
            query = query.filter(Listing.price_per_day <= float(max_price))
        if category_name:
            query = query.join(CategoryListing).filter(CategoryListing.category_name == category_name)
        if start_date and end_date:
            query = query.filter(Listing.available_start >= start_date, Listing.available_end <= end_date)

        listings = query.all()
        return render_template('search_results.html', listings=listings)

    categories = Category.query.all()
    return render_template('search.html', categories=categories)


# User profile route
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        db.session.commit()
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user)


# User reviews route
@main.route('/user/<int:user_id>/reviews', methods=['GET'])
def user_reviews(user_id):
    user = User.query.get(user_id)
    if not user:
        return 'User not found', 404

    reviews = UserReview.query.filter_by(reviewed_id=user.id).all()
    return render_template('user_reviews.html', user=user, reviews=reviews)


# Add user review route
@main.route('/user/<int:user_id>/review/add', methods=['GET', 'POST'])
def add_review(user_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form.get('comment', '')

        new_review = UserReview(
            reviewed_id=user_id,
            listing_id=request.form['listing_id'],
            rating=rating,
            comment=comment,
            created_at=datetime.utcnow()
        )
        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('main.user_reviews', user_id=user_id))

    return render_template('add_review.html', user_id=user_id)


# Dashboard route
@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    active_listings = Listing.query.filter_by(provider_id=user.id, status='active').all()
    transactions = Transaction.query.filter_by(renter_id=user.id).all()
    reviews = UserReview.query.filter_by(reviewer_id=user.id).all()
    notifications = Notification.query.filter_by(receiver_id=user.id, viewed=False).all()

    return render_template('dashboard.html', user=user, listings=active_listings,
                           transactions=transactions, reviews=reviews, notifications=notifications)



# Edit listing route
@main.route('/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    listing = Listing.query.get(listing_id)
    if listing.provider_id != session['user_id']:
        return 'Not authorized', 403

    if request.method == 'POST':
        listing.listing_title = request.form['listingTitle']
        listing.price_per_day = float(request.form['price'])
        listing.description = request.form['description']
        listing.status = 'status' in request.form
        listing.location = request.form['location']
        listing.available_start = request.form['available_start']
        listing.available_end = request.form['available_end']
        db.session.commit()
        return redirect(url_for('main.my_listings'))

    return render_template('edit_listing.html', listing=listing)


# View notifications route
@main.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    notifications = Notification.query.filter_by(receiver_id=user.id).all()
    return render_template('notifications.html', notifications=notifications)

# Mark notification as viewed route
@main.route('/notifications/mark-as-viewed/<int:notification_id>', methods=['POST'])
def mark_notification_as_viewed(notification_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    notification = Notification.query.get(notification_id)
    if notification and notification.receiver_id == session['user_id']:
        notification.viewed = True
        db.session.commit()
        flash("Notification marked as viewed.", "success")
    else:
        flash("Notification not found or you don't have permission to view it.", "danger")

    return redirect(url_for('main.notifications'))

# Delete notification route
@main.route('/notifications/delete/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    notification = Notification.query.get(notification_id)
    if notification and notification.receiver_id == session['user_id']:
        db.session.delete(notification)
        db.session.commit()
        flash("Notification deleted.", "success")
    else:
        flash("Notification not found or you don't have permission to delete it.", "danger")

    return redirect(url_for('main.notifications'))
