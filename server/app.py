#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

from config import app, db, api
from models import User, Recipe


# -----------------------------
# SIGNUP
# -----------------------------
class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio')
        image_url = data.get('image_url')

        # basic validation
        if not username or not password:
            return {'error': 'Username and password required'}, 422

        try:
            user = User(username=username, bio=bio, image_url=image_url)
            user.password_hash = password  # invokes setter

            db.session.add(user)
            db.session.commit()

            # auto-login
            session['user_id'] = user.id
            return user.to_dict(), 201

        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422


# -----------------------------
# CHECK SESSION
# -----------------------------
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401

        user = User.query.get(user_id)
        if not user:
            return {}, 401

        return user.to_dict(), 200


# -----------------------------
# LOGIN
# -----------------------------
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise Unauthorized("Missing username or password")

        user = User.query.filter_by(username=username).first()

        if not user or not user.authenticate(password):
            raise Unauthorized("Invalid username or password")

        session['user_id'] = user.id
        return user.to_dict(), 200


# -----------------------------
# LOGOUT
# -----------------------------
class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        session.pop('user_id', None)
        return {}, 204

# -----------------------------
# RECIPES INDEX
# -----------------------------
class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        # Only return recipes for logged-in user
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return [r.to_dict() for r in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        if not title or not instructions:
            return {'error': 'Missing required fields'}, 422

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()

            return recipe.to_dict(), 201

        except ValueError as e:
            db.session.rollback()
            return {'error': str(e)}, 422


# -----------------------------
# REGISTER RESOURCES
# -----------------------------
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


# -----------------------------
# MODEL SERIALIZATION SUPPORT
# -----------------------------
def add_to_dict_methods():
    """Attach to_dict() methods dynamically for testing."""
    def to_dict_user(self):
        return {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "image_url": self.image_url
        }

    def to_dict_recipe(self):
        return {
            "id": self.id,
            "title": self.title,
            "instructions": self.instructions,
            "minutes_to_complete": self.minutes_to_complete,
            "user_id": self.user_id
        }

    if not hasattr(User, "to_dict"):
        User.to_dict = to_dict_user
    if not hasattr(Recipe, "to_dict"):
        Recipe.to_dict = to_dict_recipe

add_to_dict_methods()


# -----------------------------
# MAIN ENTRY POINT
# -----------------------------
if __name__ == '__main__':
    app.run(port=5555, debug=True)
