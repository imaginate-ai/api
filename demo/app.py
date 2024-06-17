from flask import Flask, render_template, redirect, make_response, request
from dotenv import load_dotenv
from pymongo import MongoClient
import gridfs
import os

# Initialize clients
app = Flask(__name__)
load_dotenv()
db = MongoClient(os.getenv("MONGO_TOKEN"))["imaginate"]
fs = gridfs.GridFS(db)

# C - Implemented on /create endpoint
# R - Implemented on /read endpoint
# U - TODO
# D - TODO
# TODO: Limit upload to specific file types

# Allows testing of creation
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def upload():
    file = request.files["file"]
    if file.filename:
        if not next(fs.find({"filename": file.filename}), None):
            print("File not found: adding...")
            fs.put(file.stream.read(), filename=file.filename, type=file.content_type)
        else:
            print("File found: skipping...")
    return redirect("/read/" + file.filename)

@app.route("/read")
def read_all():
    content = ""
    for res in fs.find():
        content += f'<li><a href="/read/{res.filename}">{res.filename}</a></li>\n'
    return f"<ul>\n{content}</ul>"

@app.route("/read/<filename>")
def read(filename):
    res = next(fs.find({"filename": filename}), None)
    if res:
        response = make_response(res.read())
        response.headers.set("Content-Type", res.type)
        response.headers.set("Content-Length", f"{res.length}")
        return response
    return "Not found"

if __name__ == "__main__":
    app.run()