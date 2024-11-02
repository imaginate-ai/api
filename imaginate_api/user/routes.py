from flask import Blueprint, abort, request, redirect, url_for, session, current_app
from flask_login import current_user, login_user
from imaginate_api.schemas.user_info import User
from http import HTTPStatus
from urllib.parse import urlencode
import secrets
import requests

bp = Blueprint("user", __name__)
reroute_url = "index"  # Currently set to index, but will be changed to imaginate home page in the future


# Initiates the authorization process with the specified provider
@bp.route("/authorize/<provider>")
def user_authorize(provider):
  if not current_user.is_anonymous:
    return redirect(url_for("index"))

  provider_data = current_app.config["AUTH_PROVIDERS"].get(provider)
  if not provider_data:
    abort(
      HTTPStatus.NOT_FOUND,
      description=f"Invalid provider, supports: {list(current_app.config["AUTH_PROVIDERS"].keys())}",
    )

  session["oauth_state"] = secrets.token_urlsafe(32)
  print(url_for("user.user_callback", provider=provider, _external=True))
  query = urlencode(
    {
      "client_id": provider_data["client_id"],
      "redirect_uri": url_for("user.user_callback", provider=provider, _external=True),
      "response_type": "code",  # This tells the OAuth provider that we expect an authorization code to be returned
      "scope": " ".join(provider_data["scopes"]),
      "state": session["oauth_state"],
    }
  )

  return redirect(f"{provider_data["authorize_url"]}?{query}")


# Handles the callback (i.e. redirection response) process with the specified provider
@bp.route("/callback/<provider>")
def user_callback(provider):
  if not current_user.is_anonymous:
    return redirect(url_for("index"))

  provider_data = current_app.config["AUTH_PROVIDERS"].get(provider)
  if not provider_data:
    abort(
      HTTPStatus.NOT_FOUND,
      description=f"Invalid provider, supports: {list(current_app.config["AUTH_PROVIDERS"].keys())}",
    )

  # Unable to authenticate with the specified provider
  if "error" in request.args:
    for k, v in request.args.items():
      if k.startswith("error"):
        print(f"{k}: {v}")  # Debug any errors by printing them
    abort(HTTPStatus.BAD_REQUEST, description="Authentication error")

  # Authorization does not match the specification we have set
  if request.args["state"] != session.get("oauth_state") or "code" not in request.args:
    abort(HTTPStatus.BAD_REQUEST, description="Authorization error")

  # Get an access token from the authorization code
  response = requests.post(
    provider_data["token_url"],
    data={
      "client_id": provider_data["client_id"],
      "client_secret": provider_data["client_secret"],
      "code": request.args["code"],
      "grant_type": "authorization_code",
      "redirect_uri": url_for("user.user_callback", provider=provider, _external=True),
    },
    headers={"Accept": "application/json"},
  )
  if not response.ok:
    abort(response.status_code, description="Authorization error")
  response_data = response.json()
  token = response_data.get("access_token")
  if not token:
    abort(HTTPStatus.UNAUTHORIZED, description="Authorization error")

  # Get the requested data
  response = requests.get(
    provider_data["user_info"]["url"],
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
  )
  if not response.ok:
    abort(response.status_code, description="Authorization error")

  # Login user and map requested data
  user_data = provider_data["user_info"]["data"](response.json())
  user = User.find_or_create_user(user_data)
  success = login_user(user)
  if success:
    user.authenticate_user()

  return redirect(url_for("index"))
