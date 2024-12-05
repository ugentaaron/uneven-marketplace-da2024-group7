from flask import Blueprint, session, request, redirect, url_for, render_template, flash, current_app, send_from_directory
from .models import db, User, Listing, Notification, Category, Transaction, UserReview, CategoryListing, Vehicle, Booking
from datetime import datetime, timedelta
from app.utils import allowed_file
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.orm import aliased
import mimetypes
from supabase import create_client, Client

main = Blueprint('main', __name__)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(upload_folder, filename)
@main.route('/register', methods=['GET', 'POST'])

# register route
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form['address']

        # Controleren of de gebruiker al bestaat
        if User.query.filter_by(username=username).first() is None:
            new_user = User(username=username, email=email, phone_number=phone_number, address=address)
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
            session['username'] = user.username
            flash(f"You are logged in! Welcome, {user.username}.", "success")
            # Als er een 'next' parameter in de URL zit, ga dan naar die URL
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # Anders stuur naar de homepage
            return redirect(url_for('main.index'))
        else:
            flash("User not found. Please try again.", "danger")
    return render_template('login.html')


# Logout route
@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    flash("You are logged out!", "success")
    return redirect(url_for('main.index'))


# user profile route
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Als de gebruiker het profiel bijwerkt
        user.username = request.form['username']
        user.email = request.form['email']
        user.phone_number = request.form['phone_number']
        user.address = request.form['address']
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user)



# 2. Listing Management Routes
@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login', next=request.url))

    if request.method == 'POST':
        try:
            # Validatie van datums
            available_start = datetime.strptime(request.form['available_start'], '%Y-%m-%d')
            available_end = datetime.strptime(request.form['available_end'], '%Y-%m-%d')
            if available_end < available_start:
                flash("The end date cannot be earlier than the start date.", "danger")
                return redirect(request.url)

            # Bestand uploaden (optioneel)
            file = request.files.get('listing_images')
            picture_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                picture_path = os.path.join('uploads', filename)
                print(f"File uploaded successfully: {picture_path}")
            else:
                print("No valid file uploaded or file type is not allowed.")

            # Nieuwe listing aanmaken
            new_listing = Listing(
                listing_title=request.form['listing_name'],
                price_per_day=float(request.form['price']),
                location=request.form['location'],
                available_start=request.form['available_start'],
                available_end=request.form['available_end'],
                description=request.form['description'],
                status=request.form.get('status', 'available'),
                picture=picture_path,
                provider_id=session['user_id'],
                created_at=datetime.utcnow()
            )
            db.session.add(new_listing)
            db.session.flush()  # Zorg ervoor dat de listing_id beschikbaar is

            # Voeg CategoryListing toe
            category_listing = CategoryListing(
                listing_id=new_listing.id,
                category_name=request.form['vehicle_type']
            )
            db.session.add(category_listing)

            # Voeg voertuigdetails toe
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

            # Commit alle wijzigingen
            db.session.commit()

            flash("Listing added successfully!", "success")
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            print(f"Error adding listing: {e}")
            flash("An error occurred while adding the listing. Please try again.", "danger")
            return redirect(request.url)

    # GET: Toon de formulierpagina
    categories = Category.query.all()  # Zorg ervoor dat 'categories' is gedefinieerd
    return render_template('add_listing.html', categories=categories)

'''
SUPABASE_URL = current_app.config['SUPABASE_URL']
SUPABASE_KEY = current_app.config['SUPABASE_KEY']
SUPABASE_BUCKET = current_app.config['SUPABASE_BUCKET']
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Add listing route
@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login', next=request.url))

    if request.method == 'POST':
        try:
            # Validatie van datums
            available_start = datetime.strptime(request.form['available_start'], '%Y-%m-%d')
            available_end = datetime.strptime(request.form['available_end'], '%Y-%m-%d')
            if available_end < available_start:
                flash("The end date cannot be earlier than the start date.", "danger")
                return redirect(request.url)

            # Bestand uploaden naar Supabase
            file = request.files.get('listing_images')
            picture_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                mimetype = mimetypes.guess_type(filename)[0]  # Haal de MIME type op
                file_data = file.read()

                # Upload naar Supabase
                response = supabase.storage.from_(SUPABASE_BUCKET).upload(f"listings/{filename}", file_data, {"content-type": mimetype})
                if response.get("error"):
                    raise Exception(response["error"]["message"])

                # Verkrijg de publieke URL van de afbeelding
                picture_path = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/listings/{filename}"
                print(f"File uploaded to Supabase: {picture_path}")
            else:
                print("No valid file uploaded or file type is not allowed.")

            # Nieuwe listing aanmaken
            new_listing = Listing(
                listing_title=request.form['listing_name'],
                price_per_day=float(request.form['price']),
                location=request.form['location'],
                available_start=request.form['available_start'],
                available_end=request.form['available_end'],
                description=request.form['description'],
                status=request.form.get('status', 'available'),
                picture=picture_path,  # Gebruik de URL van Supabase
                provider_id=session['user_id'],
                created_at=datetime.utcnow()
            )
            db.session.add(new_listing)
            db.session.flush()  # Zorg ervoor dat de listing_id beschikbaar is

            # Voeg CategoryListing toe
            category_listing = CategoryListing(
                listing_id=new_listing.id,
                category_name=request.form['vehicle_type']
            )
            db.session.add(category_listing)

            # Voeg voertuigdetails toe
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

            # Commit alle wijzigingen
            db.session.commit()

            flash("Listing added successfully!", "success")
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            print(f"Error adding listing: {e}")
            flash("An error occurred while adding the listing. Please try again.", "danger")
            return redirect(request.url)

    # GET: Toon de formulierpagina
    categories = Category.query.all()  # Zorg ervoor dat 'categories' is gedefinieerd
    return render_template('add_listing.html', categories=categories)
'''

# Edit listing route
@main.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    vehicle = Vehicle.query.filter_by(listing_id=listing.id).first()

    if request.method == 'POST':
        listing.listing_title = request.form['listing_name']
        listing.price_per_day = request.form['price']
        listing.location = request.form['location']
        listing.available_start = request.form['available_start']
        listing.available_end = request.form['available_end']
        listing.description = request.form['description']
        listing.status = request.form['status']

        vehicle.make = request.form['make']
        vehicle.year = request.form['year']
        vehicle.vehicle_type = request.form['vehicle_type']
        vehicle.fuel_type = request.form['fuel_type']
        vehicle.seats = request.form['seats']
        vehicle.extra_features = request.form['extra_features']

        # Update images if any are uploaded
        if 'listing_images' in request.files:
            try:
                # Validatie van datums
                available_start = datetime.strptime(request.form['available_start'], '%Y-%m-%d')
                available_end = datetime.strptime(request.form['available_end'], '%Y-%m-%d')
                if available_end < available_start:
                    flash("The end date cannot be earlier than the start date.", "danger")
                    return redirect(request.url)

                # Bestand uploaden (optioneel)
                file = request.files.get('listing_images')
                picture_path = None
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    picture_path = os.path.join('uploads', filename)
                    print(f"File uploaded successfully: {picture_path}")
                else:
                    print("No valid file uploaded or file type is not allowed.")

            except Exception as e:
                db.session.rollback()
                print(f"Error adding listing: {e}")
                flash("An error occurred while adding the listing. Please try again.", "danger")
                return redirect(request.url)

        db.session.commit()
        return redirect(url_for('main.edit_listing', listing_id=listing.id))

    categories = Category.query.all()
    return render_template('edit_listing.html', listing=listing, vehicle=vehicle, categories=categories)


# Delete listing route
@main.route('/delete-listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    listing = Listing.query.get_or_404(listing_id)
    if listing.provider_id != session['user_id']:
        flash("You are not authorized to delete this listing.", "danger")
        return redirect(url_for('main.my_listings'))

    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted successfully.", "success")
    return redirect(url_for('main.my_listings'))


# Deactivate listing route
@main.route('/deactivate_listing/<int:listing_id>', methods=['POST'])
def deactivate_listing(listing_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You must be logged in to perform this action.", "danger")
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    # Find the listing
    listing = Listing.query.get_or_404(listing_id)

    # Check if the user is the owner
    if listing.provider_id != user_id:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))

    # Check the status
    if listing.status != "available":
        flash("This listing is already deactivated or has a different status.", "warning")
        return redirect(url_for('main.dashboard'))

    # Update the status to "deactivated"
    listing.status = "deactivated"
    db.session.commit()

    # Add a notification for the owner
    add_notification(
        receiver_id=user_id,
        message=f"Your listing '{listing.listing_title}' has been successfully deactivated."
    )

    # Add a notification for renters with pending transactions
    pending_transactions = Transaction.query.filter_by(
        listing_id=listing_id,
        status="pending"
    ).all()

    for transaction in pending_transactions:
        add_notification(
            receiver_id=transaction.renter_id,
            message=f"The listing '{listing.listing_title}' that you wanted to rent has been deactivated by the owner. "
                    "Check your transactions for more information."
        )

    flash(f"Listing '{listing.listing_title}' has been deactivated.", "success")
    return redirect(url_for('main.dashboard'))


# Activate listing route
@main.route('/activate_listing/<int:listing_id>', methods=['POST'])
def activate_listing(listing_id):
    if 'user_id' not in session:
        flash("You must be logged in to perform this action.", "danger")
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    listing = Listing.query.get_or_404(listing_id)

    if listing.provider_id != user_id:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('main.dashboard'))

    # Check if the listing is already "deactivated"
    if listing.status != "deactivated":
        flash("This listing is already available or has a different status.", "warning")
        return redirect(url_for('main.dashboard'))

    # Update the status to "available"
    listing.status = "available"
    db.session.commit()

    # Add a notification for the owner
    add_notification(
        receiver_id=user_id,
        message=f"Your listing '{listing.listing_title}' has been successfully reactivated and made available."
    )

    flash(f"Listing '{listing.listing_title}' is now available again.", "success")
    return redirect(url_for('main.dashboard'))



@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    vehicle = Vehicle.query.filter_by(listing_id=listing.id).first()
    provider = User.query.get(listing.provider_id)
    bookings = Booking.query.filter_by(listing_id=listing.id).all()

    is_owner = 'user_id' in session and session['user_id'] == listing.provider_id

    unavailable_dates = []
    for booking in bookings:
        current_date = booking.start_date
        while current_date <= booking.end_date:
            unavailable_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)

    listing_start = listing.available_start.isoformat()
    listing_end = listing.available_end.isoformat()

    average_review_score = None
    if provider:
        reviews = UserReview.query.filter_by(reviewed_id=provider.id).all()
        if reviews:
            average_review_score = sum(review.rating for review in reviews) / len(reviews)

    if request.method == 'POST':
        if 'user_id' not in session:
            flash("Please log in to make a purchase.", "danger")
            return redirect(url_for('main.login'))

        action = request.form.get('action', '').strip()

        print("Form data received:", request.form)

        date_range = request.form.get('date_range', '').strip()
        if not date_range:
            flash("No date range selected. Please select a valid date range.", "danger")
            return redirect(url_for('main.view_listing', listing_id=listing.id))

        try:
            start_date_str, end_date_str = date_range.split(" to ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"Date parsing error: {e}")
            flash("Invalid date range selected. Please use the format YYYY-MM-DD to YYYY-MM-DD.", "danger")
            return redirect(url_for('main.view_listing', listing_id=listing.id))

        rental_days = (end_date - start_date).days
        if rental_days < 1:
            flash("The rental period must be at least one day.", "danger")
            return redirect(url_for('main.view_listing', listing_id=listing.id))

        for date in (start_date + timedelta(days=i) for i in range(rental_days)):
            if date.isoformat() in unavailable_dates:
                flash("The selected dates include unavailable bookings.", "danger")
                return redirect(url_for('main.view_listing', listing_id=listing.id))

        total_price = rental_days * listing.price_per_day

        # Create the transaction
        new_transaction = Transaction(
            listing_id=listing.id,
            renter_id=session['user_id'],
            status="pending",
            total_price=total_price,
            created_at=datetime.utcnow()
        )
        db.session.add(new_transaction)
        db.session.commit()

        # Create the booking immediately after the transaction
        new_booking = Booking(
            listing_id=listing.id,
            renter_id=session['user_id'],
            transaction_id=new_transaction.id,
            start_date=start_date,
            end_date=end_date,
            status="pending",  # Booking status can initially be 'pending'
            created_at=datetime.utcnow()
        )
        db.session.add(new_booking)
        db.session.commit()

        # Add notification for provider
        add_notification(
            receiver_id=listing.provider_id,
            message=f"New rental request received from {User.username} for '{listing.listing_title}' "
                    f"from {start_date} to {end_date}. Total amount: €{total_price:.2f}."
        )

        # Add notification for renter
        add_notification(
            receiver_id=session['user_id'],
            message=f"Your rental request for '{listing.listing_title}' has been submitted. "
                    f"View your transaction <a href='{url_for('main.transaction_details', transaction_id=new_transaction.id)}'>here</a>."
        )

        flash("Transaction created and booking initiated successfully!", "success")
        return redirect(url_for('main.transaction_details', transaction_id=new_transaction.id))

    return render_template(
        'view_listing.html',
        listing=listing,
        vehicle=vehicle,
        is_owner=is_owner,
        provider=provider,
        listing_start=listing_start,
        listing_end=listing_end,
        average_review_score=average_review_score,
        unavailable_dates=unavailable_dates
    )



# 3. Search & Dashboard Routes

# Index route
@main.route('/')
def index():
    deactivate_expired_listings()
    # Query parameters voor paginering
    page = int(request.args.get('page', 1))
    per_page = 6
    start = (page - 1) * per_page
    end = start + per_page

    # Filters voor zoekcriteria (optioneel)
    search_title = request.args.get('search_title', '')
    search_location = request.args.get('location', '')
    search_price_min = request.args.get('price_min', None, type=float)
    search_price_max = request.args.get('price_max', None, type=float)
    search_start_date = request.args.get('start_date', None)
    search_end_date = request.args.get('end_date', None)
    search_vehicle_type = request.args.get('vehicle_type', '')
    sort_order = request.args.get('sort_order', '')

    # Basisquery
    category_alias = aliased(CategoryListing)
    query = Listing.query.filter_by(status='available')

    # Zoekfilter toepassen
    if search_title:
        query = query.filter(Listing.listing_title.ilike(f"%{search_title}%"))
    if search_location:
        query = query.filter(Listing.location.ilike(f"%{search_location}%"))
    if search_price_min:
        query = query.filter(Listing.price_per_day >= search_price_min)
    if search_price_max:
        query = query.filter(Listing.price_per_day <= search_price_max)
    if search_start_date:
        query = query.filter(Listing.start_date >= search_start_date)
    if search_end_date:
        query = query.filter(Listing.end_date <= search_end_date)
    if search_vehicle_type:
        query = query.join(category_alias, category_alias.listing_id == Listing.id) \
            .filter(category_alias.category_name == search_vehicle_type)

    # Sortering toepassen
    if sort_order == 'price_asc':
        query = query.order_by(Listing.price_per_day.asc())
    elif sort_order == 'price_desc':
        query = query.order_by(Listing.price_per_day.desc())

    # Resultaten ophalen met paginering
    all_listings = query.all()
    paginated_listings = all_listings[start:end]
    has_more = end < len(all_listings)

    # Andere data voor de pagina
    categories = Category.query.all()
    total_users = User.query.count()
    total_listings = Listing.query.count()
    rented_listings = Listing.query.filter_by(status='rented').count()
    total_transactions = Transaction.query.count()
    notifications_unread_count = 0

    # Controleer op ingelogde gebruiker
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        notifications = Notification.query.filter_by(receiver_id=user.id, viewed=False).all()
        notifications_unread_count = len(notifications)

    # Template renderen
    return render_template(
        'index.html',
        username=username,
        all_listings=paginated_listings,
        has_more=has_more,
        page=page,
        search_title=search_title,
        search_location=search_location,
        search_price_min=search_price_min,
        search_price_max=search_price_max,
        search_start_date=search_start_date,
        search_end_date=search_end_date,
        search_vehicle_type=search_vehicle_type,
        sort_order=sort_order,
        categories=categories,
        notifications_unread_count=notifications_unread_count,
        total_users=total_users,
        total_listings=total_listings,
        rented_listings=rented_listings,
        total_transactions=total_transactions
    )



@main.route('/search', methods=['GET'])
def search():
    # Verkrijg de zoekparameters van de request
    vehicle_type = request.args.get('vehicle_type')
    location = request.args.get('location')
    price_max = request.args.get('price_max')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_order = request.args.get('sort_order')  # Nieuw: sorteerparameter

    # Start de query voor listings
    query = Listing.query.filter_by(status='available')

    # Voeg filters toe aan de query op basis van de zoekparameters
    if vehicle_type:
        query = query.join(CategoryListing).join(Category).filter(Category.name == vehicle_type)
    if location:
        query = query.filter(Listing.location.ilike(f'%{location}%'))
    if price_max:
        query = query.filter(Listing.price_per_day <= float(price_max))
    if start_date:
        query = query.filter(Listing.available_start <= start_date)
    if end_date:
        query = query.filter(Listing.available_end >= end_date)

    # Sorteer de query op prijs
    if sort_order == 'price_asc':
        query = query.order_by(Listing.price_per_day.asc())
    elif sort_order == 'price_desc':
        query = query.order_by(Listing.price_per_day.desc())

    # Verkrijg de gefilterde listings
    listings = query.all()

    # Verkrijg de lijst van categorieën voor de dropdown
    categories = Category.query.all()

    total_users = User.query.count()  
    total_listings = Listing.query.count()  
    rented_listings = Listing.query.filter_by(status='rented').count()  
    total_transactions = Transaction.query.count() 

    return render_template('index.html', 
        all_listings=listings, 
        categories=categories,
        total_users=total_users,
        total_listings=total_listings,
        rented_listings=rented_listings,
        total_transactions=total_transactions
)


import pandas as pd
from flask import jsonify
@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('main.logout'))

    # Wijzig profielgegevens
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_phone_number = request.form.get('phone_number')
        new_address = request.form.get('address')

        # Check and update username
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash("This username is already taken.", "danger")
            else:
                user.username = new_username

        # Check and update email
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                flash("This email address is already in use.", "danger")
            else:
                user.email = new_email

        # Update phone number
        if new_phone_number and new_phone_number != user.phone_number:
            user.phone_number = new_phone_number

        # Update address
        if new_address and new_address != user.address:
            user.address = new_address

        # Print changes for debugging
        print(f"Updated user: {user.username}, {user.email}, {user.phone_number}, {user.address}")

        try:
            # Save to database
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            db.session.rollback()

        return redirect(url_for('main.dashboard'))

    # Reviews
    written_reviews = UserReview.query.filter_by(reviewer_id=user_id).all()
    received_reviews = UserReview.query.filter_by(reviewed_id=user_id).all()

    # Eigen zoekertjes
    own_listings = Listing.query.filter_by(provider_id=user_id).all()

    # Gehuurde zoekertjes
    rented_transactions = Transaction.query.filter_by(renter_id=user_id).all()
    rented_listings = [trans.listing for trans in rented_transactions]

    # Transactiegeschiedenis
    transactions = Transaction.query.filter((Transaction.renter_id == user_id) |
                                            (Transaction.listing.has(provider_id=user_id))).all()

    # Ongelezen notificaties
    notifications = Notification.query.filter_by(receiver_id=user_id, viewed=False).all()
    notifications_unread_count = Notification.query.filter_by(receiver_id=user_id, viewed=False).count()

    bookings = Booking.query.filter(
        (Booking.renter_id == user_id) | (Booking.listing.has(provider_id=user_id))  
    ).all()

    # API-achtige logica om omzetgegevens te berekenen
    if request.args.get('data') == 'revenue':
        try:
            transactions = Transaction.query.join(Listing).filter(Listing.provider_id == user_id).all()
            data = [{'date': t.created_at, 'revenue': t.total_price} for t in transactions]

            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')

            monthly_revenue = df.groupby('month')['revenue'].sum().reset_index()
            monthly_revenue['month'] = monthly_revenue['month'].apply(lambda x: x.strftime('%m-%Y'))


            return jsonify(monthly_revenue.to_dict(orient="records"))
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    # Normale HTML-rendering
    return render_template(
        'dashboard.html',
        user=user,
        written_reviews=written_reviews,
        received_reviews=received_reviews,
        own_listings=own_listings,
        rented_listings=rented_listings,
        transactions=transactions,
        notifications=notifications,
        notifications_unread_count=notifications_unread_count,
        bookings=bookings
    )


@main.route('/booking/<int:booking_id>', methods=['GET', 'POST'])
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    listing = booking.listing
    provider = User.query.get(listing.provider_id)
    current_user_id = session.get('user_id')

    is_renter = booking.renter_id == current_user_id
    is_provider = listing.provider_id == current_user_id

    # Check if a review can be made
    existing_review = UserReview.query.filter_by(
        reviewer_id=current_user_id,
        listing_id=listing.id
    ).first() if is_renter else None

    can_review = (
        is_renter
        and booking.status == "confirmed"
        and datetime.utcnow().date() > booking.end_date
        and not existing_review
    )

    if request.method == 'POST':
        action = request.form.get('action')

        if action == "submit_review" and can_review:
            rating = int(request.form.get('rating'))
            comment = request.form.get('comment', '').strip()

            # Create and save the new review
            new_review = UserReview(
                reviewer_id=current_user_id,
                reviewed_id=listing.provider_id,
                listing_id=listing.id,
                rating=rating,
                comment=comment,
                created_at=datetime.utcnow()
            )
            db.session.add(new_review)
            db.session.commit()
            flash("Review submitted successfully!", "success")
            return redirect(url_for('main.booking_details', booking_id=booking_id))

    average_review_score = None
    if provider.received_feedback:
        reviews = [review.rating for review in provider.received_feedback]
        average_review_score = sum(reviews) / len(reviews)

    return render_template(
        'booking_details.html',
        booking=booking,
        listing=listing,
        provider=provider,
        is_renter=is_renter,
        is_provider=is_provider,
        can_review=can_review,
        existing_review=existing_review,
        average_review_score=average_review_score
    )

# 4. Transaction Routes

def is_vehicle_available(listing_id, start_date, end_date):
    overlapping_bookings = Booking.query.filter(
        Booking.listing_id == listing_id,
        Booking.status == 'confirmed',
        db.or_(
            db.and_(Booking.start_date <= start_date, Booking.end_date >= start_date),
            db.and_(Booking.start_date <= end_date, Booking.end_date >= end_date),
            db.and_(Booking.start_date >= start_date, Booking.end_date <= end_date)
        )
    ).all()

    return len(overlapping_bookings) == 0

# Transaction details route
@main.route('/transaction/<int:transaction_id>', methods=['GET', 'POST'])
def transaction_details(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    listing = transaction.listing
    provider = User.query.get(listing.provider_id)
    current_user_id = session.get('user_id')

    # Check if current user is renter or provider
    is_renter = transaction.renter_id == current_user_id
    is_provider = listing.provider_id == current_user_id

    # Get the booking related to the transaction (since start_date and end_date are now in Booking)
    booking = Booking.query.filter_by(transaction_id=transaction.id).first()

    # If booking does not exist, handle it gracefully (e.g., display an error or redirect)
    if not booking:
        flash("Booking not found for this transaction.", "danger")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle transaction status change to "processed"
        if action == "process_transaction" and is_renter and transaction.status == "pending":
            # Update transaction status
            transaction.status = "processed"
            db.session.commit()

            if transaction.renter_id != session['user_id']:
                flash("You are not authorized to process this payment.", "danger")
                return redirect(url_for('main.transaction_details', transaction_id=transaction_id))

            # Add notification for the renter
            add_notification(
                receiver_id=transaction.renter_id,
                message=f"Your payment for '{transaction.listing.listing_title}' from {booking.start_date} to {booking.end_date} "
                        f"has been successfully processed. The total amount is €{transaction.total_price:.2f}. View your booking "
                        f"<a href='{url_for('main.booking_details', booking_id=booking.booking_id)}'>here</a>."
            )

            # Add notification for the provider
            add_notification(
                receiver_id=transaction.listing.provider_id,
                message=f"The payment for the rental request of '{transaction.listing.listing_title}' from {booking.start_date} "
                        f"to {booking.end_date} has been completed. The total amount is €{transaction.total_price:.2f}. Check the booking "
                        f"<a href='{url_for('main.booking_details', booking_id=booking.booking_id)}'>here</a>."
            )

            flash("Payment processed successfully! The transaction is now marked as processed.", "success")
            return redirect(url_for('main.transaction_details', transaction_id=transaction_id))

    return render_template(
        'transaction_details.html',
        transaction=transaction,
        listing=listing,
        provider=provider,
        is_renter=is_renter,
        is_provider=is_provider,
        booking=booking  # Pass booking object to template
    )




# 5. Review Routes

# User reviews route
@main.route('/provider/<int:provider_id>', methods=['GET'])
def view_provider(provider_id):
    provider = User.query.get_or_404(provider_id)
    listings = Listing.query.filter_by(provider_id=provider_id).all()
    reviews = UserReview.query.filter_by(reviewed_id=provider_id).all()
    return render_template('provider.html', provider=provider, listings=listings, reviews=reviews)



# Add user review route
@main.route('/user/<int:user_id>/review/add', methods=['GET', 'POST'])
def add_review(user_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    current_user_id = session['user_id']
    reviewed_user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        # Retrieve the necessary data from the form
        rating = int(request.form['rating'])
        comment = request.form.get('comment', '').strip()
        listing_id = request.form.get('listing_id')

        # Check if the listing exists and is associated with the reviewed user
        listing = Listing.query.get_or_404(listing_id)
        if listing.provider_id != user_id:
            flash("The specified listing does not belong to the review recipient.", "danger")
            return redirect(url_for('main.add_review', user_id=user_id))

        # Create and save the review
        new_review = UserReview(
            reviewer_id=current_user_id,
            reviewed_id=user_id,
            listing_id=listing_id,
            rating=rating,
            comment=comment,
            created_at=datetime.utcnow()
        )
        db.session.add(new_review)
        db.session.commit()

        # Add notification for the recipient of the review
        add_notification(
            receiver_id=user_id,
            message=f"You have received a new review from {session.get('username', 'someone')}: "
                    f"{rating} stars. Comment: '{comment}' for the listing '{listing.listing_title}'."
        )

        # Add notification for the reviewer
        add_notification(
            receiver_id=current_user_id,
            message=f"You have successfully left a review for {reviewed_user.username}: "
                    f"{rating} stars. Comment: '{comment}' for the listing '{listing.listing_title}'."
        )

        flash("You have successfully left a review!", "success")
        return redirect(url_for('main.user_reviews', user_id=user_id))

    return render_template('add_review.html', user_id=user_id, reviewed_user=reviewed_user)

# 6. Notification Routes


def add_notification(receiver_id, message):
    """
    Voegt een nieuwe notificatie toe aan de database.
    """
    new_notification = Notification(
        receiver_id=receiver_id,
        message=message,
        created_at=datetime.utcnow(),
        viewed=False
    )
    db.session.add(new_notification)
    db.session.commit()


# View notifications route
@main.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))  # Gebruiker moet ingelogd zijn

    user_id = session['user_id']  # Verkrijg de gebruiker ID uit de session
    notifications = Notification.query.filter_by(receiver_id=user_id).all()

    unread_count = sum(1 for notification in notifications if not notification.viewed)
    return render_template('notifications.html', notifications=notifications, unread_count=unread_count)


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


@main.route('/all_listings')
def all_listings():
    # Parameters ophalen van de zoekbalk
    search_title = request.args.get('search_title', '')
    search_location = request.args.get('location', '')
    search_price_min = request.args.get('price_min', None, type=float)
    search_price_max = request.args.get('price_max', None, type=float)
    search_start_date = request.args.get('start_date', '')
    search_end_date = request.args.get('end_date', '')
    search_vehicle_type = request.args.get('vehicle_type', '')
    sort_order = request.args.get('sort_order', '')

    # Basisquery
    category_alias = aliased(CategoryListing)
    query = Listing.query.filter_by(status='available')

    # Zoekfilters toepassen
    if search_title:
        query = query.filter(Listing.listing_title.ilike(f"%{search_title}%"))
    if search_location:
        query = query.filter(Listing.location.ilike(f"%{search_location}%"))
    if search_price_min:
        query = query.filter(Listing.price_per_day >= search_price_min)
    if search_price_max:
        query = query.filter(Listing.price_per_day <= search_price_max)
    if search_vehicle_type:
        query = query.join(category_alias, category_alias.listing_id == Listing.id) \
            .filter(category_alias.category_name == search_vehicle_type)

    # Sortering
    if sort_order == "price_asc":
        query = query.order_by(Listing.price_per_day.asc())
    elif sort_order == "price_desc":
        query = query.order_by(Listing.price_per_day.desc())

    # Alle listings ophalen
    all_listings = query.all()

    # Weergeven van de pagina
    return render_template(
        'all_listings.html',
        all_listings=all_listings,
        search_title=search_title,
        search_location=search_location,
        search_price_min=search_price_min,
        search_price_max=search_price_max,
        search_start_date=search_start_date,
        search_end_date=search_end_date,
        search_vehicle_type=search_vehicle_type,
        sort_order=sort_order,
        categories=Category.query.all()
    )


def deactivate_expired_listings():
    listings = Listing.query.filter(Listing.available_end < datetime.utcnow().date(), Listing.status != 'deactivated').all()
    for listing in listings:
        listing.deactivate_if_expired()

    # Commit the changes
    db.session.commit()



@main.route('/performance', methods=['GET'])
def performance():
    if 'user_id' not in session:
        flash("Log in to access your performance page.", "danger")
        return redirect(url_for('main.login'))

    provider_id = session['user_id']
    listing_id = request.args.get('listing_id', type=int)

    selected_listing = Listing.query.get_or_404(listing_id)

    # Bereken de prestaties van de geselecteerde listing
    listing_performance = db.session.query(
        Listing.listing_title,
        Listing.location,
        Vehicle.vehicle_type,
        func.count(Booking.booking_id).label('total_bookings'),
        func.sum(Transaction.total_price).label('total_revenue'),
        
        func.coalesce(func.avg(UserReview.rating), 0.0).label('average_rating') 
    ).join(Vehicle, Vehicle.listing_id == Listing.id, isouter=True) \
     .join(Booking, Booking.listing_id == Listing.id, isouter=True) \
     .join(Transaction, Transaction.id == Booking.transaction_id, isouter=True) \
     .join(UserReview, UserReview.listing_id == Listing.id, isouter=True) \
     .filter(Listing.id == listing_id) \
     .group_by(Listing.id, Listing.location, Vehicle.vehicle_type) \
     .first()
    
    # Omzetgegevens per datum (voor grafiek)
    revenue_by_date = db.session.query(
        Booking.start_date.label('date'),
        func.sum(Transaction.total_price).label('revenue')
    ).join(Transaction, Transaction.id == Booking.transaction_id) \
     .filter(Booking.listing_id == listing_id, Transaction.status == "processed") \
     .group_by(Booking.start_date) \
     .order_by(Booking.start_date) \
     .all()

    # Formatteer omzetgegevens voor Chart.js
    listing_revenue_data = [
        {"date": row.date.strftime('%Y-%m-%d'), "revenue": float(row.revenue or 0)}
        for row in revenue_by_date
    ]

    # Vergelijk met andere listings in dezelfde stad en van hetzelfde voertuigtype
    city_comparison = db.session.query(
        Listing.listing_title,
        Vehicle.vehicle_type,
        func.count(Booking.booking_id).label('total_bookings'),
        func.coalesce(func.sum(Transaction.total_price), 0.0).label('total_revenue'),
        func.coalesce(func.avg(UserReview.rating), 0.0).label('average_rating')
    ).join(Vehicle, Vehicle.listing_id == Listing.id, isouter=True) \
     .join(Booking, Booking.listing_id == Listing.id, isouter=True) \
     .join(Transaction, Transaction.id == Booking.transaction_id, isouter=True) \
     .join(UserReview, UserReview.listing_id == Listing.id, isouter=True) \
     .filter(
         Listing.location == selected_listing.location,
         Listing.id != listing_id,
         Vehicle.vehicle_type == selected_listing.vehicle.vehicle_type
     ).group_by(Listing.id, Vehicle.vehicle_type) \
     .all()

    # Bereken rangschikking op basis van omzet
    city_rankings = db.session.query(
        Listing.id,
        func.coalesce(func.sum(Transaction.total_price), 0.0).label('total_revenue')
    ).join(Vehicle, Vehicle.listing_id == Listing.id, isouter=True) \
     .join(Booking, Booking.listing_id == Listing.id, isouter=True) \
     .join(Transaction, Transaction.id == Booking.transaction_id, isouter=True) \
     .filter(
         Listing.location == selected_listing.location,
         Vehicle.vehicle_type == selected_listing.vehicle.vehicle_type
     ).group_by(Listing.id) \
     .order_by(func.coalesce(func.sum(Transaction.total_price), 0.0).desc()) \
     .all()
    
    # Bepaal rang van de geselecteerde listing
    rank = next((index + 1 for index, row in enumerate(city_rankings) if row.id == listing_id), None)
    total_listings = len(city_rankings)

    rank_display = f"{rank} out of {total_listings}"
    if rank == 1:
        rank_display = f"#1 (Top Performer) out of {total_listings}"

    performance_analysis = {
        "outperforming": False,
        "suggest_price_increase": False,
        "recommendation": "Your listing is performing as expected.",
        "rank_display": rank_display,
        "rank": rank,
        "total_listings": total_listings
    }

    if listing_performance:
        avg_revenue = sum(row.total_revenue or 0 for row in city_rankings) / max(total_listings, 1)
        if (listing_performance.total_revenue or 0) > avg_revenue:  # Presteert boven het gemiddelde
            performance_analysis["outperforming"] = True
            if listing_performance.total_revenue > 1.2 * avg_revenue:  # 20% beter dan gemiddelde
                performance_analysis["suggest_price_increase"] = True
                performance_analysis["recommendation"] = (
                    "Your listing is outperforming similar listings. Consider increasing the price!"
                )
        else:
            performance_analysis["recommendation"] = (
                "Your listing is underperforming compared to similar listings. "
                "Consider improving your description, lowering the price, or adding promotions."
            )

    return render_template(
        'performance.html',
        listing_performance=listing_performance,
        listing_revenue_data=listing_revenue_data,
        city_comparison=city_comparison,
        performance_analysis=performance_analysis
    )