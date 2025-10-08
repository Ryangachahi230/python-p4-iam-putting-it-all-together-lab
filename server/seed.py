#!/usr/bin/env python3

from random import randint, choice as rc
from faker import Faker

from app import app
from models import db, Recipe, User

fake = Faker()

with app.app_context():

    print("Deleting all records...")
    # Always delete child tables first
    Recipe.query.delete()
    User.query.delete()

    print("Creating users...")

    users = []
    usernames = set()

    for _ in range(20):
        username = fake.unique.first_name()
        user = User(
            username=username,
            bio=fake.paragraph(nb_sentences=3),
            image_url=fake.image_url(),
        )
        user.password_hash = "password123"  # consistent, easy for testing
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    print("Creating recipes...")

    recipes = []
    for _ in range(100):
        # Ensure instructions are always > 50 chars
        instructions = fake.paragraph(nb_sentences=8)
        while len(instructions) < 50:
            instructions += " " + fake.sentence()

        recipe = Recipe(
            title=fake.sentence().rstrip('.'),
            instructions=instructions,
            minutes_to_complete=randint(15, 90),
            user=rc(users)
        )
        recipes.append(recipe)

    db.session.add_all(recipes)
    db.session.commit()

    print("Database seeded successfully!")
