from flask import Flask, json, render_template
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from imaginate_api.date.routes import bp as date_routes
from imaginate_api.image.routes import bp as image_routes
from imaginate_api.user.routes import bp as user_routes
from imaginate_api.config import Config
from imaginate_api.extensions import login_manager
import os


def create_app():
  app = Flask(__name__)
  CORS(app)
  app.config.from_object(Config)
  login_manager.init_app(app)
  app.secret_key = os.getenv("FLASK_SECRET_KEY")
  app.register_blueprint(date_routes, url_prefix="/date")
  app.register_blueprint(image_routes, url_prefix="/image")
  app.register_blueprint(user_routes, url_prefix="/user")
  return app


# Create app
app = create_app()


# This endpoint is simply for testing purposes
@app.route("/")
def index():
  return render_template("index.html")


# Generic error handler in JSON rather than HTML
@app.errorhandler(HTTPException)
def handle_exception(exc: HTTPException):
  response = exc.get_response()
  response.data = json.dumps(
    {
      "code": exc.code,
      "name": exc.name,
      "description": exc.description,
    }
  )
  response.content_type = "application/json"
  return response


# Run app on invocation
if __name__ == "__main__":
  if app.config["DB_ENV"] == "prod":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
  else:
    app.run()
