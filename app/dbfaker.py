from faker import Faker
from datetime import datetime
from models import db, User  # Zorg ervoor dat je de models goed hebt geïmporteerd
from app import main

fake = Faker()


# Functie om gebruikersdata te genereren en toe te voegen
def create_fake_users(num_users):
    for _ in range(num_users):
        # Genereer fake data
        username = fake.user_name()
        email = fake.email()
        address = fake.address()
        phone_number = fake.phone_number()
        created_at = fake.date_this_decade()  # Huidige of eerdere datum

        # Maak een nieuwe gebruiker
        user = User(
            username=username,
            email=email,
            address=address,
            phone_number=phone_number,
            created_at=created_at
        )

        # Voeg de gebruiker toe aan de sessie en commit
        db.session.add(user)

    # Sla de wijzigingen op in de database
    db.session.commit()


# Aantal gebruikers dat je wilt genereren
create_fake_users(10)

print("Fake gebruikers toegevoegd!")
