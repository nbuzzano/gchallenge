import pytest
from io import BytesIO
from app.database import Department, Job, Employee


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_read_root(self, client):
        """Test GET / returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "DB Migration REST API"
        assert "version" in data
        assert "endpoints" in data


class TestDepartmentUpload:
    """Tests for department CSV upload"""
    
    def test_upload_departments_success(self, client, sample_csv_departments):
        """Test successful department CSV upload"""
        response = client.post(
            "/upload/departments",
            files={"file": ("departments.csv", BytesIO(sample_csv_departments), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 3
        assert "Successfully uploaded" in data["message"]
    
    def test_upload_departments_empty_file(self, client):
        """Test uploading empty CSV file"""
        empty_csv = b""
        response = client.post(
            "/upload/departments",
            files={"file": ("departments.csv", BytesIO(empty_csv), "text/csv")}
        )
        assert response.status_code == 400
    
    def test_upload_departments_invalid_columns(self, client):
        """Test uploading CSV with wrong number of columns"""
        invalid_csv = b"1,Engineering,Extra"
        response = client.post(
            "/upload/departments",
            files={"file": ("departments.csv", BytesIO(invalid_csv), "text/csv")}
        )
        assert response.status_code == 400
        assert "2 columns" in response.json()["detail"]
    
    def test_upload_departments_too_many_rows(self, client):
        """Test uploading CSV with more than 1000 rows"""
        csv_data = "\n".join([f"{i},Department{i}" for i in range(1, 1002)])
        response = client.post(
            "/upload/departments",
            files={"file": ("departments.csv", BytesIO(csv_data.encode()), "text/csv")}
        )
        assert response.status_code == 400
        assert "between 1 and 1000" in response.json()["detail"]


class TestJobUpload:
    """Tests for job CSV upload"""
    
    def test_upload_jobs_success(self, client, sample_csv_jobs):
        """Test successful job CSV upload"""
        response = client.post(
            "/upload/jobs",
            files={"file": ("jobs.csv", BytesIO(sample_csv_jobs), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 3
        assert "Successfully uploaded" in data["message"]
    
    def test_upload_jobs_invalid_columns(self, client):
        """Test uploading CSV with wrong number of columns"""
        invalid_csv = b"1,Engineer,Extra"
        response = client.post(
            "/upload/jobs",
            files={"file": ("jobs.csv", BytesIO(invalid_csv), "text/csv")}
        )
        assert response.status_code == 400
        assert "2 columns" in response.json()["detail"]


class TestEmployeeUpload:
    """Tests for employee CSV upload"""
    
    def test_upload_employees_success(self, client, sample_csv_employees):
        """Test successful employee CSV upload"""
        response = client.post(
            "/upload/employees",
            files={"file": ("employees.csv", BytesIO(sample_csv_employees), "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 2
        assert "Successfully uploaded" in data["message"]
    
    def test_upload_employees_invalid_columns(self, client):
        """Test uploading CSV with wrong number of columns"""
        invalid_csv = b"1,John Doe,2021-01-15T09:00:00,1"
        response = client.post(
            "/upload/employees",
            files={"file": ("employees.csv", BytesIO(invalid_csv), "text/csv")}
        )
        assert response.status_code == 400
        assert "5 columns" in response.json()["detail"]


class TestDepartmentBatchInsert:
    """Tests for department batch insert"""
    
    def test_batch_insert_departments_success(self, client):
        """Test successful batch department insert"""
        payload = {
            "departments": [
                {"id": 1, "department": "Engineering"},
                {"id": 2, "department": "Sales"}
            ]
        }
        response = client.post("/batch/departments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 2
    
    def test_batch_insert_departments_empty(self, client):
        """Test batch insert with empty list"""
        payload = {"departments": []}
        response = client.post("/batch/departments", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_batch_insert_departments_too_many(self, client):
        """Test batch insert with more than 1000 rows"""
        departments = [
            {"id": i, "department": f"Department{i}"}
            for i in range(1, 1002)
        ]
        payload = {"departments": departments}
        response = client.post("/batch/departments", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_batch_insert_departments_max_allowed(self, client):
        """Test batch insert with exactly 1000 rows"""
        departments = [
            {"id": i, "department": f"Department{i}"}
            for i in range(1, 1001)
        ]
        payload = {"departments": departments}
        response = client.post("/batch/departments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 1000


class TestJobBatchInsert:
    """Tests for job batch insert"""
    
    def test_batch_insert_jobs_success(self, client):
        """Test successful batch job insert"""
        payload = {
            "jobs": [
                {"id": 1, "job": "Software Engineer"},
                {"id": 2, "job": "Data Analyst"}
            ]
        }
        response = client.post("/batch/jobs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 2
    
    def test_batch_insert_jobs_single_row(self, client):
        """Test batch insert with single row (minimum allowed)"""
        payload = {
            "jobs": [
                {"id": 1, "job": "Product Manager"}
            ]
        }
        response = client.post("/batch/jobs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 1


class TestEmployeeBatchInsert:
    """Tests for employee batch insert"""
    
    def test_batch_insert_employees_success(self, client):
        """Test successful batch employee insert"""
        payload = {
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
        response = client.post("/batch/employees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 1
    
    def test_batch_insert_employees_multiple(self, client):
        """Test batch insert multiple employees"""
        payload = {
            "employees": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "datetime": "2021-01-15T09:00:00",
                    "department_id": 1,
                    "job_id": 1
                },
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "datetime": "2021-02-20T10:30:00",
                    "department_id": 2,
                    "job_id": 2
                }
            ]
        }
        response = client.post("/batch/employees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_inserted"] == 2
