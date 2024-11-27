from flask import Blueprint, session, request, redirect, url_for, render_template, flash
from .models import db, User, Listing, Notification, Category, Transaction, UserReview, CategoryListing, Vehicle
from datetime import datetime
from app.utils import allowed_file
import os
from werkzeug.utils import secure_filename
from flask import current_app  
from flask import send_from_directory

main = Blueprint('main', __name__)



@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(upload_folder, filename)
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
            flash(f"Je bent ingelogd! Welkom, {user.username}.", "success")
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
    flash("Je bent uitgelogd!", "success")
    return redirect(url_for('main.index'))


# User profile route
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.phone_number = request.form['phone number']
        user.address = request.form['address']
        db.session.commit()
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user)


# 2. Listing Management Routes


# Add listing route
@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login', next=request.url))

    if request.method == 'POST':
        try:

            file = request.files.get('listing_images')
            picture_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                # Upload-folder ophalen uit de config
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                # Bestandslocatie bepalen
                file_path = os.path.join(upload_folder, filename)

                # Bestand opslaan
                file.save(file_path)

                # Relatief pad opslaan voor de database
                picture_path = os.path.join('uploads', filename)
                print(f"File uploaded successfully: {picture_path}")
            else:
                print("No valid file uploaded or file type is not allowed.")


            # Nieuwe listing toevoegen
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
            db.session.flush() 

            # Add Categories
            selected_categories = request.form.getlist('categories') or []
            for category_name in selected_categories:
                category = Category.query.filter_by(name=category_name).first()
                if category:
                    category_listing = CategoryListing(categoryName=category.name, listingID=new_listing.id)
                    db.session.add(category_listing)

            # Add Vehicle
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

            # Commit All Changes
            db.session.commit()

            # Categorize Vehicles (if necessary logic exists)
            categorized_vehicles = categorize_vehicle_prices(db.session)  # Assuming this function exists
            for vehicle_data in categorized_vehicles:
                print(f"Vehicle {vehicle_data['vehicle_id']} categorized as {vehicle_data['category']}")

            print("Listing, categories, and vehicle committed to the database.")

            flash("Listing added successfully!", "success")
            return redirect(url_for('main.index'))

        except Exception as e:
            # Rollback in case of errors
            db.session.rollback()
            print(f"Error during listing creation: {str(e)}")
            flash(f"An error occurred while adding the listing: {str(e)}", "danger")
            return redirect(url_for('main.add_listing'))

    # Render the add listing page with necessary data
    categories = Category.query.all()  # Fetch categories for dropdown  
    return render_template('add_listing.html', categories=categories, categorized_vehicles=[])

    # Functie voertuigen categoriseren (algoritme 1)
def categorize_vehicle_prices(session):
    vehicles = session.query(Vehicle, Listing.price_per_day, Listing.location, Vehicle.vehicle_type).join(Listing).all()

    grouped_vehicles = {}
    for vehicle, price_per_day, location, vehicle_type in vehicles:
        key = (vehicle_type, location)
        if key not in grouped_vehicles:
            grouped_vehicles[key] = []
        grouped_vehicles[key].append((vehicle, price_per_day))

    categorized_vehicles = []
    for group_key, group_vehicles in grouped_vehicles.items():
        prices = [price for _, price in group_vehicles]

        if len(prices) < 3:
            continue

        low_threshold = np.percentile(prices, 33)
        high_threshold = np.percentile(prices, 66)

        for vehicle, price in group_vehicles:
            if price <= low_threshold:
                category = "Laag"
            elif price <= high_threshold:
                category = "Gemiddeld"
            else:
                category = "Hoog"

            categorized_vehicles.append({
                "vehicle_id": vehicle.vehicle_id,
                "price_per_day": price,
                "category": category,
                "vehicle_type": group_key[0],
                "location": group_key[1]
            })

    return categorized_vehicles

    # Fetch Categories for Form
    categories = Category.query.all()
    return render_template('add_listing.html', categories=categories)


# Edit listing route
@main.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash("Je moet ingelogd zijn om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    # Zoek de listing
    listing = Listing.query.get_or_404(listing_id)

    # Controleer of de gebruiker de eigenaar is
    if listing.provider_id != user_id:
        flash("Je hebt geen toestemming om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Update de gegevens van de listing
        listing.listing_title = request.form.get('listing_title')
        listing.description = request.form.get('description')
        listing.price_per_day = float(request.form.get('price_per_day'))
        db.session.commit()
        flash(f"Zoekertje '{listing.listing_title}' is succesvol bijgewerkt.", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('edit_listing.html', listing=listing)


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
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash("Je moet ingelogd zijn om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    # Zoek de listing
    listing = Listing.query.get_or_404(listing_id)

    # Controleer of de gebruiker de eigenaar is
    if listing.provider_id != user_id:
        flash("Je hebt geen toestemming om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.dashboard'))

    # Controleer de status
    if listing.status != "available":
        flash("Deze zoekertje is al gedeactiveerd of heeft een andere status.", "warning")
        return redirect(url_for('main.dashboard'))

    # Update de status naar "deactivated"
    listing.status = "deactivated"
    db.session.commit()
    flash(f"Zoekertje '{listing.listing_title}' is gedeactiveerd.", "success")

    return redirect(url_for('main.dashboard'))


# Activate listing route
@main.route('/activate_listing/<int:listing_id>', methods=['POST'])
def activate_listing(listing_id):
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash("Je moet ingelogd zijn om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    # Zoek de listing op basis van listing_id
    listing = Listing.query.get_or_404(listing_id)

    # Controleer of de ingelogde gebruiker de eigenaar is van de listing
    if listing.provider_id != user_id:
        flash("Je hebt geen toestemming om deze actie uit te voeren.", "danger")
        return redirect(url_for('main.dashboard'))

    # Controleer of de listing al "deactivated" is
    if listing.status != "deactivated":
        flash("Deze zoekertje is al beschikbaar of heeft een andere status.", "warning")
        return redirect(url_for('main.dashboard'))

    # Update de status naar "available"
    listing.status = "available"
    db.session.commit()
    flash(f"Zoekertje '{listing.listing_title}' is nu weer beschikbaar.", "success")

    return redirect(url_for('main.dashboard'))


# View listing route
@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)  # Haal de listing op
    vehicle = Vehicle.query.filter_by(listing_id=listing.id).first()  # Haal de bijbehorende vehicle info op
    provider = User.query.get(listing.provider_id)  # Haal de verhuurder op

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

    # Haal de gemiddelde score direct uit de provider (User)
    average_review_score = provider.review_score if provider else None

    return render_template('view_listing.html',
                           listing=listing,
                           vehicle=vehicle,
                           provider=provider,
                           average_review_score=average_review_score)


# 3. Search & Dashboard Routes

# Index route
@main.route('/')
def index():
    all_listings = Listing.query.filter_by(status='available').all()
    categories = Category.query.all()
    notifications_unread_count = 0  # Default value if not logged in or no notifications
    total_users = User.query.count()  
    total_listings = Listing.query.count()  
    rented_listings = Listing.query.filter_by(status='rented').count()  
    total_transactions = Transaction.query.count() 

    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        notifications = Notification.query.filter_by(receiver_id=user.id, viewed=False).all()
        notifications_unread_count = len(notifications)

        return render_template(
            'index.html',
            username=user.username,
            all_listings=all_listings,
            categories=categories,
            notifications_unread_count=notifications_unread_count,
            total_users=total_users,
            total_listings=total_listings,
            rented_listings=rented_listings,
            total_transactions=total_transactions

        )
    
 


    return render_template(
        'index.html',
        username=None,
        all_listings=all_listings,
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

    return render_template('index.html', all_listings=listings, categories=categories)


@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash("Gebruiker niet gevonden.", "danger")
        return redirect(url_for('main.logout'))

    # Wijzig profielgegevens
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_phone_number = request.form.get('phone_number')
        new_address = request.form.get('address')

        # Controleer en update username
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash("Deze gebruikersnaam is al in gebruik.", "danger")
            else:
                user.username = new_username

        # Controleer en update e-mail
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                flash("Dit e-mailadres is al in gebruik.", "danger")
            else:
                user.email = new_email

        # Update telefoonnummer
        if new_phone_number and new_phone_number != user.phone_number:
            user.phone_number = new_phone_number

        # Update adres
        if new_address and new_address != user.address:
            user.address = new_address

        # Print de wijzigingen voor debuggen
        print(f"Updated user: {user.username}, {user.email}, {user.phone_number}, {user.address}")
        
        try:
            # Opslaan in de database
            db.session.commit()
            flash("Profiel succesvol bijgewerkt!", "success")
        except Exception as e:
            flash(f"Er is een fout opgetreden: {e}", "danger")
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

    return render_template(
        'dashboard.html',
        user=user,
        written_reviews=written_reviews,
        received_reviews=received_reviews,
        own_listings=own_listings,
        rented_listings=rented_listings,
        transactions=transactions,
        notifications=notifications,
        notifications_unread_count=notifications_unread_count  
    )


# 4. Transaction Routes

# Transaction details route
@main.route('/transaction/<int:transaction_id>', methods=['GET'])
def transaction_details(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    transaction = Transaction.query.get(transaction_id)
    if transaction and transaction.renter_id == session['user_id']:
        return render_template('transaction_details.html', transaction=transaction)

    return 'Transaction not found', 404


# 5. Review Routes

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


# 6. Notification Routes

# View notifications route
def get_notifications_for_user(username):
    # Dit zou je moeten aanpassen aan de logica van je app, bijvoorbeeld een database-query
    return [
        {"id": 1, "message": "Nieuwe auto toegevoegd!", "read": False},
        {"id": 2, "message": "Je reservering is bevestigd.", "read": True},
    ]

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