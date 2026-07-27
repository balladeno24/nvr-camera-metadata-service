# NVR and Camera Metadata Service

A REST API for storing and retrieving metadata for Network Video Recorders
and their connected cameras.

## Features

The service supports:

- Creating NVR metadata.
- Listing all NVR metadata.
- Deleting NVR metadata.
- Creating camera metadata.
- Deleting camera metadata.
- Retrieving all cameras connected to a specific NVR.
- Filtering cameras by location.
- Filtering cameras by kind.
- Filtering cameras by both location and kind.
- Enforcing each NVR's maximum input-channel capacity.
- Persisting data between application restarts.

Deleting an NVR also deletes its associated cameras.

## Technology

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Pytest

## Requirements

Python 3.10 or later is recommended.

## Installation

Clone the repository and open a terminal in the project root.

### Windows PowerShell

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

### macOS or Linux

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Load the sample data

Run:

```bash
python seed.py
```

The seed script loads the data from `sample_nvr_camera_data.json`.

Existing records with matching serial numbers are skipped.

## Run the service

Run:

```bash
python -m uvicorn app.main:app --reload
```

The service will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The health endpoint is available at:

```text
http://127.0.0.1:8000/health
```

## Run the automated tests

Run:

```bash
python -m pytest -v
```

The test suite validates:

- NVR and camera creation.
- Duplicate NVR rejection.
- Duplicate camera rejection.
- Missing NVR rejection.
- Invalid UUID rejection.
- Camera filtering.
- Maximum channel capacity.
- Missing-resource deletion responses.
- Cascade deletion of cameras when an NVR is deleted.

## API endpoints

### Health check

```text
GET /health
```

### NVR endpoints

```text
GET /nvrs
POST /nvrs
DELETE /nvrs/{nvr_uuid}
```

### Camera endpoints

```text
POST /cameras
GET /cameras
DELETE /cameras/{camera_uuid}
GET /nvrs/{nvr_uuid}/cameras
```

The `GET /cameras` endpoint accepts these optional query parameters:

```text
location
kind
```

Example:

```text
GET /cameras?location=Building%20A&kind=electro-optical
```

## Persistence

The application uses a local SQLite database by default:

```text
nvr_camera.db
```

The database remains available after the application is stopped and restarted.

A different SQLAlchemy database URL can be supplied through the
`DATABASE_URL` environment variable.

Example in PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./another_database.db"
python -m uvicorn app.main:app --reload
```

## Camera kinds

The accepted camera kinds are:

```text
electro-optical
thermal
infrared
```