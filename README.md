# DB Migration REST API

A REST API for migrating historical data from CSV files to a SQL database with batch transaction support.

## 📋 Overview

This project provides a local REST API that:
- ✅ Receives historical data from CSV files
- ✅ Uploads CSV files to a SQL database (SQLite)
- ✅ Supports batch transactions (1 to 1000 rows per request)
- ✅ Handles 3 tables: `departments`, `jobs`, and `employees`

## 🗂️ Database Schema

### Departments Table
| Column     | Type    | Description           |
|------------|---------|----------------------|
| id         | Integer | Primary key          |
| department | String  | Department name      |

### Jobs Table
| Column | Type    | Description    |
|--------|---------|---------------|
| id     | Integer | Primary key   |
| job    | String  | Job title     |

### Employees Table
| Column        | Type    | Description                    |
|--------------|---------|--------------------------------|
| id           | Integer | Primary key                    |
| name         | String  | Employee name                  |
| datetime     | String  | Hire datetime (ISO format)     |
| department_id| Integer | Foreign key to departments     |
| job_id       | Integer | Foreign key to jobs            |

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Poetry 1.6+ (https://python-poetry.org/docs/#installation)

### Setup

1. Clone the repository:
```bash
git clone <github-repo-url>
cd gchallenge
```

2. Install dependencies with Poetry (creates a virtualenv automatically):
```bash
poetry install
```

3. (Optional) Spawn a shell inside the Poetry environment:
```bash
poetry shell
```

If you need a `requirements.txt` (e.g., for CI), export it from Poetry:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## 🏃 Running the API

Start the server (without activating a shell):
```bash
poetry run uvicorn app.main:app --reload
```

Or, if you ran `poetry shell`, simply:
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## 🧪 Running Tests

The project uses **pytest** (the standard Python testing framework) for automated testing.

Install dev dependencies (if not already installed):
```bash
poetry install
```

Run all tests:
```bash
poetry run pytest
```

Run tests with verbose output:
```bash
poetry run pytest -v
```

Run specific test file:
```bash
poetry run pytest tests/test_main.py
```

Run specific test class:
```bash
poetry run pytest tests/test_main.py::TestDepartmentUpload
```

Run specific test function:
```bash
poetry run pytest tests/test_main.py::TestDepartmentUpload::test_upload_departments_success
```

Run tests with coverage report:
```bash
poetry run pytest --cov=app --cov-report=html
```

### Test Structure

The tests are organized into two main files:

- **`tests/test_main.py`**: Tests for API endpoints
  - Root endpoint (`/`)
  - CSV upload endpoints (`/upload/*`)
  - Batch insert endpoints (`/batch/*`)
  - Validation of batch sizes (1-1000 rows)
  - Error handling for invalid data

- **`tests/test_csv_service.py`**: Tests for CSV processing logic
  - CSV parsing and encoding handling
  - Batch size validation
  - Department, job, and employee CSV uploads
  - Batch insert operations

### Test Coverage

- 40+ automated tests covering:
  - Successful uploads and inserts
  - Edge cases (empty files, min/max batch sizes)
  - Error conditions (invalid columns, oversized batches)
  - Data validation

## 📡 API Endpoints

### Root Endpoint
- **GET** `/` - API information and available endpoints

### CSV Upload Endpoints

#### Upload Departments
- **POST** `/upload/departments`
- Upload a CSV file with departments data
- CSV Format: `id,department`
- Example: `1,Engineering`

#### Upload Jobs
- **POST** `/upload/jobs`
- Upload a CSV file with jobs data
- CSV Format: `id,job`
- Example: `1,Software Engineer`

#### Upload Employees
- **POST** `/upload/employees`
- Upload a CSV file with employees data
- CSV Format: `id,name,datetime,department_id,job_id`
- Example: `1,John Doe,2021-01-15T09:00:00,1,1`

### Batch Insert Endpoints

#### Batch Insert Departments
- **POST** `/batch/departments`
- Insert 1-1000 departments in a single request
- Request body:
```json
{
  "departments": [
    {"id": 1, "department": "Engineering"},
    {"id": 2, "department": "Sales"}
  ]
}
```

#### Batch Insert Jobs
- **POST** `/batch/jobs`
- Insert 1-1000 jobs in a single request
- Request body:
```json
{
  "jobs": [
    {"id": 1, "job": "Software Engineer"},
    {"id": 2, "job": "Data Analyst"}
  ]
}
```

#### Batch Insert Employees
- **POST** `/batch/employees`
- Insert 1-1000 employees in a single request
- Request body:
```json
{
  "employees": [
    {
      "id": 1,
      "name": "John Doe",
      "datetime": "2021-01-15T09:00:00",
      "department_id": 1,
      "job_id": 1
    }
  ]
}
```

## 📂 Project Structure

```
gchallenge/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and endpoints
│   ├── database.py       # Database models and connection
│   ├── schemas.py        # Pydantic schemas for validation
│   └── csv_service.py    # CSV processing logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures and configuration
│   ├── test_main.py      # API endpoint tests
│   └── test_csv_service.py # CSV service unit tests
├── data/
│   ├── departments.csv   # Sample departments data
│   ├── jobs.csv          # Sample jobs data
│   └── employees.csv     # Sample employees data
├── pyproject.toml       # Poetry project and dependency config
├── requirements.txt     # (Optional) export via `poetry export`
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 💡 Usage Examples

### Using cURL

**Upload departments CSV:**
```bash
curl -X POST "http://localhost:8000/upload/departments" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/departments.csv"
```

**Upload jobs CSV:**
```bash
curl -X POST "http://localhost:8000/upload/jobs" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/jobs.csv"
```

**Upload employees CSV:**
```bash
curl -X POST "http://localhost:8000/upload/employees" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/employees.csv"
```

**Batch insert departments:**
```bash
curl -X POST "http://localhost:8000/batch/departments" \
  -H "Content-Type: application/json" \
  -d '{
    "departments": [
      {"id": 100, "department": "Research"},
      {"id": 101, "department": "Innovation"}
    ]
  }'
```

### Using Python requests

```python
import requests

# Upload CSV file
with open('data/departments.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload/departments',
        files={'file': f}
    )
    print(response.json())

# Batch insert
data = {
    "departments": [
        {"id": 100, "department": "Research"},
        {"id": 101, "department": "Innovation"}
    ]
}
response = requests.post(
    'http://localhost:8000/batch/departments',
    json=data
)
print(response.json())
```

## ✅ Features

- **FastAPI Framework**: Modern, fast, with automatic API documentation
- **SQLite Database**: Lightweight SQL database, no external dependencies
- **Data Validation**: Automatic validation using Pydantic schemas
- **Batch Size Validation**: Ensures 1-1000 rows per request
- **Error Handling**: Comprehensive error messages
- **CSV Support**: Comma-separated file parsing with pandas
- **Interactive Documentation**: Swagger UI at `/docs`

## 🧪 Testing with Sample Data

The project includes sample CSV files in the `data/` directory:

1. Start the server: `uvicorn app.main:app --reload`
2. Open your browser at `http://localhost:8000/docs`
3. Use the interactive Swagger UI to test endpoints
4. Or use the curl commands from the examples above

## 🔧 Technologies Used

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Pandas**: Data manipulation and CSV processing
- **Uvicorn**: ASGI server for running the application
- **SQLite**: SQL database engine

## 📝 CSV File Format

All CSV files must be comma-separated and follow these formats:

**departments.csv** (no header):
```
1,Engineering
2,Sales
3,Marketing
```

**jobs.csv** (no header):
```
1,Software Engineer
2,Data Analyst
3,Product Manager
```

**employees.csv** (no header):
```
1,John Doe,2021-01-15T09:00:00,1,1
2,Jane Smith,2021-02-20T10:30:00,2,4
```

## ⚠️ Important Notes

- Batch size must be between 1 and 1000 rows per request
- CSV files should not include headers
- All datetime values should be in ISO 8601 format
- The database file (`migration.db`) is created automatically on first run
- Foreign key constraints are not enforced in SQLite by default

## 🤝 Contributing

This project was developed as part of a database migration challenge. Feel free to fork and improve!

## 📄 License

MIT License - Feel free to use this project for your own purposes.
