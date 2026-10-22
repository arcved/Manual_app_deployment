"""Task Manager - a small Flask + MongoDB app for learning manual deployment."""

import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Read variables from a local ".env" file (if it exists) into the environment.
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "task_manager")

MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
DB_ERROR_MESSAGE = "Cannot reach the database. Please check that MongoDB is running."

app = Flask(__name__)

# MongoClient connects lazily, so the app can start even if MongoDB is down.
# Fail after 3 seconds (instead of the default 30) so error pages appear quickly.
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
tasks = client[MONGO_DB_NAME]["tasks"]


def render_home(error=None, form=None, status=200):
    """Show the homepage. Loads tasks from MongoDB unless the database is down."""
    all_tasks = []
    try:
        all_tasks = list(tasks.find().sort("created_at", -1))
    except PyMongoError:
        # Show a friendly message only - never the raw error (it may contain the URI).
        error = error or DB_ERROR_MESSAGE
        status = 503

    # Counts for the summary cards, and the optional ?filter= tab on the page.
    counts = {
        "total": len(all_tasks),
        "done": sum(1 for t in all_tasks if t.get("completed")),
    }
    counts["open"] = counts["total"] - counts["done"]

    current_filter = request.args.get("filter", "all")
    if current_filter == "open":
        task_list = [t for t in all_tasks if not t.get("completed")]
    elif current_filter == "done":
        task_list = [t for t in all_tasks if t.get("completed")]
    else:
        current_filter = "all"
        task_list = all_tasks

    return render_template(
        "index.html",
        tasks=task_list,
        counts=counts,
        current_filter=current_filter,
        error=error,
        form=form or {},
    ), status


@app.get("/")
def index():
    return render_home()


@app.post("/tasks")
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    # Validate the input before touching the database.
    error = None
    if not title:
        error = "Please enter a task title."
    elif len(title) > MAX_TITLE_LENGTH:
        error = f"Title must be {MAX_TITLE_LENGTH} characters or fewer."
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        error = f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
    if error:
        return render_home(error=error, form=request.form, status=400)

    try:
        tasks.insert_one(
            {
                "title": title,
                "description": description,
                "completed": False,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except PyMongoError:
        return render_home(error=DB_ERROR_MESSAGE, form=request.form, status=503)
    return redirect(url_for("index"))


def to_object_id(task_id):
    """Convert the id from the URL into a MongoDB ObjectId (or None if invalid)."""
    try:
        return ObjectId(task_id)
    except (InvalidId, TypeError):
        return None


@app.post("/tasks/<task_id>/complete")
def complete_task(task_id):
    oid = to_object_id(task_id)
    if oid is None:
        return render_home(error="Invalid task id.", status=400)
    try:
        tasks.update_one({"_id": oid}, {"$set": {"completed": True}})
    except PyMongoError:
        return render_home(error=DB_ERROR_MESSAGE, status=503)
    return redirect(url_for("index"))


@app.post("/tasks/<task_id>/delete")
def delete_task(task_id):
    oid = to_object_id(task_id)
    if oid is None:
        return render_home(error="Invalid task id.", status=400)
    try:
        tasks.delete_one({"_id": oid})
    except PyMongoError:
        return render_home(error=DB_ERROR_MESSAGE, status=503)
    return redirect(url_for("index"))


@app.get("/health")
def health():
    """Report whether the app can talk to MongoDB (HTTP 200 = yes, 503 = no)."""
    try:
        client.admin.command("ping")
    except PyMongoError:
        return jsonify(status="error", database="unreachable"), 503
    return jsonify(status="ok", database="connected"), 200


if __name__ == "__main__":
    # Development server only. Binds to localhost unless FLASK_HOST says otherwise.
    app.run(
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
