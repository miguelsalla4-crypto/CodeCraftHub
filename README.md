# CodeCraftHub

CodeCraftHub is a beginner-friendly REST API for tracking courses that developers want to learn. It uses Python and Flask, with course data stored in a local JSON file. No database or authentication is required.

## Features

- Add, list, retrieve, update, and delete courses.
- Generate integer course IDs and creation timestamps automatically.
- Save course data in courses.json.
- Create courses.json automatically if it does not exist.
- Validate required fields, course statuses, and dates.
- Return error responses for missing courses, malformed JSON, and file read/write problems.

## Requirements

- Python 3.9 or newer
- Windows PowerShell for the commands below
- curl.exe
- Python packages listed in requirements.txt

## Project Structure

    CodeCraftHub/
    ├── app.py
    ├── courses.json
    ├── requirements.txt
    └── README.md

- app.py: Flask application, API routes, validation, and file handling.
- courses.json: Saved course records. An empty course list is represented by [].
- requirements.txt: Python package versions needed to run the project.
- README.md: Installation, usage, and testing instructions.

The .venv folder is a local Python environment. It should not be uploaded to GitHub.

## Installation

Open PowerShell and navigate to the project folder:

```powershell
Set-Location "$HOME\CodeCraftHub"
```

If you saved the project somewhere else, use that folder's path instead.

Create a virtual environment:

```powershell
py -m venv .venv
```

Install the required packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

These commands use the virtual environment directly, so activating it is not necessary.

## Running the Application

From the project folder, run:

```powershell
.\.venv\Scripts\python.exe app.py
```

The application should start at:

    http://127.0.0.1:5000

Keep this PowerShell window open while using the API. Open a second PowerShell window to run test commands.

To stop the application, press Ctrl + C in the server window.

The app runs in debug mode for local development.

## Course Fields

| Field | Description |
| --- | --- |
| id | Automatically generated integer, starting from 1 for an empty course list |
| name | Required non-empty string |
| description | Required non-empty string |
| target_date | Required date using YYYY-MM-DD |
| status | Not Started, In Progress, or Completed |
| created_at | Automatically generated UTC timestamp |

IDs are generated from the highest existing course ID plus one. IDs can be reused after records are deleted.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | /api/courses | Create a course |
| GET | /api/courses | List all courses |
| GET | /api/courses/<course_id> | Retrieve one course |
| PUT | /api/courses/<course_id> | Update a course |
| DELETE | /api/courses/<course_id> | Delete a course |

POST and PUT requests require name, description, target_date, and status.

PUT requires all four editable fields, even when changing only the status. The existing id and created_at values are preserved.

## Testing Instructions

Start the application first. Run the following commands in a second PowerShell window.

These are expected results, not an automatically generated test report. The -i option displays HTTP status codes.

### 1. Create a Course

Save a JSON request to a temporary file:

```powershell
@'
{
  "name": "Python Basics",
  "description": "Learn Python fundamentals.",
  "target_date": "2026-12-31",
  "status": "Not Started"
}
'@ | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-create.json"
```

Send the request:

```powershell
curl.exe -i -X POST "http://127.0.0.1:5000/api/courses" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-create.json"
```

Expected status: 201 Created.

Example response:

```json
{
  "id": 1,
  "name": "Python Basics",
  "description": "Learn Python fundamentals.",
  "target_date": "2026-12-31",
  "status": "Not Started",
  "created_at": "2026-11-17T04:33:13.739476+00:00"
}
```

The timestamp will vary. Use the returned ID in subsequent commands if it is not 1.

### 2. List All Courses

```powershell
curl.exe -i "http://127.0.0.1:5000/api/courses"
```

Expected status: 200 OK.

The response is a JSON array containing the saved courses.

### 3. Retrieve One Course

```powershell
curl.exe -i "http://127.0.0.1:5000/api/courses/1"
```

Expected status: 200 OK, with the selected course's details.

### 4. Update the Course

Create the update payload:

```powershell
@'
{
  "name": "Python Basics",
  "description": "Learn Python fundamentals.",
  "target_date": "2026-12-31",
  "status": "In Progress"
}
'@ | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-update.json"
```

Send the update:

```powershell
curl.exe -i -X PUT "http://127.0.0.1:5000/api/courses/1" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-update.json"
```

Expected status: 200 OK. The returned status should be In Progress.

### 5. Check Saved Data

```powershell
Get-Content "$HOME\CodeCraftHub\courses.json"
```

The file should contain the updated course.

To check persistence across restarts, stop the server with Ctrl + C, start it again, and repeat the GET request. The saved course should still be available.

### 6. Delete the Course

```powershell
curl.exe -i -X DELETE "http://127.0.0.1:5000/api/courses/1"
```

Expected status: 200 OK.

```json
{
  "message": "Course deleted successfully"
}
```

### 7. Test a Missing Course

After deleting the course, run:

```powershell
curl.exe -i "http://127.0.0.1:5000/api/courses/1"
```

Expected status: 404 Not Found.

```json
{
  "error": "Course not found"
}
```

### 8. Test Missing Required Fields

```powershell
'{"name":"Incomplete Course"}' | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-missing.json"

curl.exe -i -X POST "http://127.0.0.1:5000/api/courses" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-missing.json"
```

Expected status: 400 Bad Request, with messages identifying missing fields.

### 9. Test an Invalid Status

```powershell
'{"name":"Test Course","description":"Testing validation.","target_date":"2026-12-31","status":"Invalid"}' | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-invalid.json"

curl.exe -i -X POST "http://127.0.0.1:5000/api/courses" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-invalid.json"
```

Expected status: 400 Bad Request, with a message listing the allowed statuses.

### 10. Test an Invalid Date

```powershell
'{"name":"Test Course","description":"Testing dates.","target_date":"2026-02-30","status":"Not Started"}' | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-date.json"

curl.exe -i -X POST "http://127.0.0.1:5000/api/courses" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-date.json"
```

Expected status: 400 Bad Request because February 30 is not a valid date.

### 11. Test Malformed JSON

```powershell
'{"name":}' | Set-Content -Encoding ascii "$env:TEMP\codecrafthub-malformed.json"

curl.exe -i -X POST "http://127.0.0.1:5000/api/courses" -H "Content-Type: application/json" --data-binary "@$env:TEMP/codecrafthub-malformed.json"
```

Expected status: 400 Bad Request.

```json
{
  "error": "Malformed JSON request"
}
```

## Troubleshooting

### Python is not recognized

Close and reopen PowerShell after installing Python. Check the installation with:

```powershell
py --version
```

### Flask is not installed

Run the dependency installation command from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### app.py cannot be found

Make sure PowerShell is in the correct folder:

```powershell
Set-Location "$HOME\CodeCraftHub"
Get-ChildItem
```

Check that the filename is app.py, not app.py.txt.

### Connection refused

Make sure the server is still running in the original PowerShell window and the URL uses port 5000.

### The browser shows Not Found at the home address

This project provides an API, not a homepage. Open:

    http://127.0.0.1:5000/api/courses

### Port 5000 is already in use

Stop another copy of the application if one is running. Alternatively, change the final line in app.py to:

```python
app.run(debug=True, port=5001)
```

Then use port 5001 in all test URLs.

### PUT reports missing fields

Include name, description, target_date, and status in the update request.

### JSON requests fail in PowerShell

Use the JSON-file examples above with curl.exe and --data-binary. They avoid problems with passing JSON quotation marks directly through PowerShell.

### File read/write errors

Check that the project folder is writable and courses.json contains valid JSON. Back up existing course data before repairing the file.

An empty course file should contain:

```json
[]
```

## Limitations

This is a local learning project. It does not include authentication, a graphical interface, or a database.

JSON file storage does not safely coordinate simultaneous writes from multiple users. The application is intended for practicing REST APIs, not production deployment.

## Use of Generative AI

Generative AI was used to help develop the application, propose test cases, and prepare documentation. Generated code and expected responses should be checked by running the application and comparing actual results.