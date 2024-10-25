from flask import Flask, json, render_template
from imaginate_api.config import Config
from imaginate_api.date.routes import bp as date_routes
from imaginate_api.extensions import cache
from imaginate_api.image.routes import bp as image_routes
from werkzeug.exceptions import HTTPException

def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)
  app.register_blueprint(date_routes, url_prefix="/date")
  app.register_blueprint(image_routes, url_prefix="/image")
  return app
   

# Create app
app = create_app()

# Initialize Redis cache
cache.init_app(app)


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
  if Config.DB_ENV == 'prod':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
  else:
    app.run()
