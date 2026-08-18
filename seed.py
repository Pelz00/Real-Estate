"""
Populate the database with demo data so you can see every feature working
right away.

Run with:
    python seed.py

Demo agent login:  agent@haven.com   / password123
Demo buyer login:  buyer@haven.com   / password123
Demo admin login:  admin@haven.com   / password123
"""
from app import create_app, db
from app.models import User, Property, PropertyImage, Inquiry

app = create_app()

DEMO_PROPERTIES = [
    dict(title="Sunlit Bungalow on Palm Avenue", price=185000, listing_type="sale",
         property_type="house", bedrooms=3, bathrooms=2, area_sqft=1450,
         address="14 Palm Avenue", city="Lekki", state="Lagos",
         description="A bright, airy bungalow with a private garden, updated kitchen, "
                      "and two minutes' walk from the beach road. Freshly painted throughout."),
    dict(title="Modern Two-Bed Apartment, Downtown", price=1200, listing_type="rent",
         property_type="apartment", bedrooms=2, bathrooms=2, area_sqft=980,
         address="221B Marina Street", city="Victoria Island", state="Lagos",
         description="Fully serviced apartment with 24/7 power, gym access, and secure "
                      "parking. Walking distance to the business district."),
    dict(title="Riverside Family Home", price=340000, listing_type="sale",
         property_type="house", bedrooms=5, bathrooms=4, area_sqft=3200,
         address="9 Riverside Close", city="Abuja", state="FCT",
         description="Spacious family home with a large backyard, home office, and "
                      "attached two-car garage. Quiet cul-de-sac location."),
    dict(title="Studio Loft near the Arts District", price=650, listing_type="rent",
         property_type="apartment", bedrooms=1, bathrooms=1, area_sqft=520,
         address="55 Gallery Row", city="Ikeja", state="Lagos",
         description="Compact, stylish studio with high ceilings and large windows. "
                      "Perfect for a single professional or student."),
    dict(title="Commercial Corner Lot", price=95000, listing_type="sale",
         property_type="land", bedrooms=0, bathrooms=0, area_sqft=6000,
         address="Plot 12, Freedom Way", city="Port Harcourt", state="Rivers",
         description="Prime corner plot zoned for commercial use, on a busy road with "
                      "excellent visibility and existing utility connections."),
    dict(title="Gated Estate Condo with Pool Access", price=210000, listing_type="sale",
         property_type="condo", bedrooms=3, bathrooms=3, area_sqft=1600,
         address="7 Serenity Gardens", city="Lekki", state="Lagos",
         description="Contemporary condo inside a gated estate with shared pool, gym, "
                      "and 24-hour security. Balcony overlooks a landscaped courtyard."),
]


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()

        agent = User(name="Amara Okafor", email="agent@haven.com", role="agent", email_verified=True)
        agent.set_password("password123")

        buyer = User(name="Daniel Brooks", email="buyer@haven.com", role="buyer", email_verified=True)
        buyer.set_password("password123")

        admin = User(name="Site Admin", email="admin@haven.com", role="admin", email_verified=True)
        admin.set_password("password123")

        db.session.add_all([agent, buyer, admin])
        db.session.commit()

        for data in DEMO_PROPERTIES:
            prop = Property(owner_id=agent.id, **data)
            db.session.add(prop)
        db.session.commit()

        image_paths = [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1400&q=80",
        ]
        for property_index, prop in enumerate(Property.query.order_by(Property.id).all()):
            for position, image_path in enumerate(image_paths[:2 + property_index % 2]):
                db.session.add(PropertyImage(property_id=prop.id, image_path=image_path, position=position))
        db.session.commit()

        first_property = Property.query.first()
        inquiry = Inquiry(
            name=buyer.name, email=buyer.email,
            message="Hi, is this still available? I'd love to schedule a viewing this week.",
            property_id=first_property.id, sender_id=buyer.id,
        )
        db.session.add(inquiry)
        db.session.commit()

        print("Seeded database with 3 users and %d listings." % len(DEMO_PROPERTIES))
        print("Agent login: agent@haven.com / password123")
        print("Buyer login: buyer@haven.com / password123")
        print("Admin login: admin@haven.com / password123")


if __name__ == "__main__":
    run()
