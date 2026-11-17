from datetime import date, datetime, timezone
import json
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType


# Create the Flask application
app = Flask(__name__)

# Store courses.json in the same folder as this app.py file
DATA_FILE = Path(__file__).parent / "courses.json"

# These are the only valid course statuses
VALID_STATUSES = {
    "Not Started",
    "In Progress",
    "Completed",
}


class DataFileError(Exception):
    """
    Custom error used when courses.json cannot be read or written.
    """
    pass


def load_courses():
    """
    Read courses from courses.json.

    If courses.json does not exist, create it with an empty list.
    """
    try:
        if not DATA_FILE.exists():
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump([], file, indent=2)

            return []

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            courses = json.load(file)

        # The JSON file should contain a list of courses
        if not isinstance(courses, list):
            raise DataFileError(
                "courses.json must contain a JSON list."
            )

        return courses

    except json.JSONDecodeError as error:
        raise DataFileError(
            f"courses.json contains invalid JSON: {error}"
        ) from error

    except OSError as error:
        raise DataFileError(
            f"Could not read courses.json: {error}"
        ) from error


def save_courses(courses):
    """
    Save the complete list of courses to courses.json.
    """
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(courses, file, indent=2)

    except OSError as error:
        raise DataFileError(
            f"Could not write to courses.json: {error}"
        ) from error


def get_json_body():
    """
    Read and return JSON from the request body.

    The request must contain a JSON object, such as:

    {
        "name": "Python Basics",
        "description": "Learn Python fundamentals.",
        "target_date": "2026-12-31",
        "status": "Not Started"
    }
    """
    # Check that the client sent a JSON request
    if not request.is_json:
        return None, (
            jsonify({
                "error": "Request must have Content-Type: application/json"
            }),
            400,
        )

    # Flask raises an error automatically if the JSON is malformed
    data = request.get_json()

    if not isinstance(data, dict):
        return None, (
            jsonify({
                "error": "JSON request body must be an object"
            }),
            400,
        )

    return data, None


def validate_course_data(data):
    """
    Validate the fields required for a course.

    Returns a list of validation error messages.
    An empty list means the data is valid.
    """
    errors = []

    required_fields = [
        "name",
        "description",
        "target_date",
        "status",
    ]

    # Check that all required fields exist
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    # Stop here if required fields are missing
    if errors:
        return errors

    # Validate the course name
    if not isinstance(data["name"], str) or not data["name"].strip():
        errors.append("'name' must be a non-empty string")

    # Validate the description
    if (
        not isinstance(data["description"], str)
        or not data["description"].strip()
    ):
        errors.append("'description' must be a non-empty string")

    # Validate the target date
    if not isinstance(data["target_date"], str):
        errors.append("'target_date' must be a string in YYYY-MM-DD format")
    else:
        try:
            # fromisoformat validates dates such as 2026-12-31
            date.fromisoformat(data["target_date"])
        except ValueError:
            errors.append(
                "'target_date' must be a valid date in YYYY-MM-DD format"
            )

    # Validate the status
    if data["status"] not in VALID_STATUSES:
        errors.append(
            "'status' must be one of: "
            + ", ".join(sorted(VALID_STATUSES))
        )

    return errors


def find_course(courses, course_id):
    """
    Find one course in a list by its integer ID.
    """
    for course in courses:
        if course.get("id") == course_id:
            return course

    return None


def get_next_course_id(courses):
    """
    Generate the next integer ID.

    The first course receives ID 1. After that, the next ID is one
    greater than the highest existing ID.
    """
    if not courses:
        return 1

    existing_ids = [
        course["id"]
        for course in courses
        if isinstance(course.get("id"), int)
    ]

    if not existing_ids:
        return 1

    return max(existing_ids) + 1


@app.errorhandler(BadRequest)
def handle_bad_request(error):
    """
    Handle malformed JSON requests.
    """
    return jsonify({
        "error": "Malformed JSON request"
    }), 400


@app.errorhandler(UnsupportedMediaType)
def handle_unsupported_media_type(error):
    """
    Handle requests that do not contain JSON when JSON is required.
    """
    return jsonify({
        "error": "Request must contain JSON data"
    }), 415


@app.route("/api/courses", methods=["POST"])
def create_course():
    """
    Add a new course.

    Required JSON fields:
    - name
    - description
    - target_date
    - status
    """
    data, error_response = get_json_body()

    if error_response:
        return error_response

    validation_errors = validate_course_data(data)

    if validation_errors:
        return jsonify({
            "errors": validation_errors
        }), 400

    try:
        courses = load_courses()

        new_course = {
            "id": get_next_course_id(courses),
            "name": data["name"].strip(),
            "description": data["description"].strip(),
            "target_date": data["target_date"],
            "status": data["status"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        courses.append(new_course)
        save_courses(courses)

        return jsonify(new_course), 201

    except DataFileError as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/courses", methods=["GET"])
def get_courses():
    """
    Return all courses.
    """
    try:
        courses = load_courses()

        return jsonify(courses), 200

    except DataFileError as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """
    Return one course by its integer ID.
    """
    try:
        courses = load_courses()
        course = find_course(courses, course_id)

        if course is None:
            return jsonify({
                "error": "Course not found"
            }), 404

        return jsonify(course), 200

    except DataFileError as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    """
    Update an existing course.

    PUT requires all editable course fields:
    - name
    - description
    - target_date
    - status

    The ID and created_at values cannot be changed by the client.
    """
    data, error_response = get_json_body()

    if error_response:
        return error_response

    validation_errors = validate_course_data(data)

    if validation_errors:
        return jsonify({
            "errors": validation_errors
        }), 400

    try:
        courses = load_courses()
        course = find_course(courses, course_id)

        if course is None:
            return jsonify({
                "error": "Course not found"
            }), 404

        # Update only the editable fields.
        # The original ID and created_at timestamp are preserved.
        course["name"] = data["name"].strip()
        course["description"] = data["description"].strip()
        course["target_date"] = data["target_date"]
        course["status"] = data["status"]

        save_courses(courses)

        return jsonify(course), 200

    except DataFileError as error:
        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    """
    Delete a course by its integer ID.
    """
    try:
        courses = load_courses()
        course = find_course(courses, course_id)

        if course is None:
            return jsonify({
                "error": "Course not found"
            }), 404

        courses.remove(course)
        save_courses(courses)

        return jsonify({
            "message": "Course deleted successfully"
        }), 200

    except DataFileError as error:
        return jsonify({
            "error": str(error)
        }), 500


# Automatically create courses.json when the application starts
# if the file does not already exist.
try:
    if not DATA_FILE.exists():
        save_courses([])
except DataFileError:
    # The API endpoints will return a useful error response if the file
    # cannot be created or accessed.
    pass


if __name__ == "__main__":
    # debug=True is useful while learning and developing locally.
    app.run(debug=True)