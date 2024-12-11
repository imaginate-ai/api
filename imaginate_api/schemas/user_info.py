from bson.objectid import ObjectId
from flask_login import UserMixin
from imaginate_api.extensions import login_manager
from imaginate_api.extensions import db

# Specification: https://flask-login.readthedocs.io/en/latest/#
COLLECTION_NAME = "users"
COLLECTION = db[COLLECTION_NAME]


class User(UserMixin):
  def __init__(self, user_data=None):
    self.user_data = user_data or {}

  @property
  def is_authenticated(self):
    return self.user_data.get("authenticated", False)

  @property
  def is_active(self):
    return self.user_data.get("active", False)

  @property
  def is_anonymous(self):
    return False  # Always return False based on specification

  def get_id(self):
    return str(self.user_data["_id"])

  def get_clientside_data(self):
    return {
      "email": self.user_data.get("email"),
    }

  def authenticate_user(self):
    COLLECTION.update_one(
      {"_id": self.user_data["_id"]}, {"$set": {"authenticated": True}}
    )
    self.user_data["authenticated"] = True

  def deactivate_user(self):
    COLLECTION.update_one({"_id": self.user_data["_id"]}, {"$set": {"active": False}})
    self.user_data["active"] = False

  @classmethod
  def find_or_create_user(cls, data, provider=None):
    # Primary identifier: Try to find the existing user by using the unique ID from the provider
    if provider:
      existing_user = COLLECTION.find_one({f"{provider}_id": data["id"]})
      if existing_user:
        return User(user_data=existing_user)

    # Secondary identifier: Try to find the existing user by using the email from the provider
    existing_user = COLLECTION.find_one({"email": data["email"]})
    if existing_user:
      if provider:
        COLLECTION.update_one(
          {"_id": existing_user["_id"]}, {"$set": {f"{provider}_id": data["id"]}}
        )
      return User(user_data=existing_user)

    # If no user is found, create a new one
    data["authenticated"] = False
    data["active"] = True
    data[f"{provider}_id"] = data.pop("id")
    new_user = COLLECTION.insert_one(data)
    return User.get(new_user.inserted_id)

  # Get user by ID
  @classmethod
  def get(cls, user_id):
    user = COLLECTION.find_one({"_id": ObjectId(user_id)})
    if not user:
      return None
    return cls(user_data=user)


# Callback function for Flask login library to load user from session user_id
@login_manager.user_loader
def load_user(user_id):
  return User.get(user_id)
