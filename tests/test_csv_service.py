import pytest
import pandas as pd
from io import StringIO
from sqlalchemy.orm import Session

from app.csv_service import CSVService


class TestCSVParsing:
    """Tests for CSV parsing functionality"""
    
    def test_parse_csv_valid(self):
        """Test parsing valid CSV content"""
        csv_content = b"1,Engineering\n2,Sales"
        df = CSVService.parse_csv(csv_content)
        assert len(df) == 2
        assert df.shape[1] == 2
    
    def test_parse_csv_invalid_encoding(self):
        """Test parsing CSV with invalid encoding"""
        invalid_bytes = b"\x80\x81\x82"
        with pytest.raises(ValueError, match="Error parsing CSV"):
            CSVService.parse_csv(invalid_bytes)
    
    def test_parse_csv_single_row(self):
        """Test parsing CSV with single row"""
        csv_content = b"1,Engineering"
        df = CSVService.parse_csv(csv_content)
        assert len(df) == 1


class TestBatchSizeValidation:
    """Tests for batch size validation"""
    
    def test_validate_batch_size_valid(self):
        """Test validation with valid batch size"""
        df = pd.DataFrame({"col1": range(100)})
        # Should not raise any exception
        CSVService.validate_batch_size(df)
    
    def test_validate_batch_size_minimum(self):
        """Test validation with minimum valid batch size"""
        df = pd.DataFrame({"col1": [1]})
        CSVService.validate_batch_size(df)
    
    def test_validate_batch_size_maximum(self):
        """Test validation with maximum valid batch size"""
        df = pd.DataFrame({"col1": range(1000)})
        CSVService.validate_batch_size(df)
    
    def test_validate_batch_size_empty(self):
        """Test validation with empty dataframe"""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="between 1 and 1000"):
            CSVService.validate_batch_size(df)
    
    def test_validate_batch_size_too_large(self):
        """Test validation with too large batch"""
        df = pd.DataFrame({"col1": range(1001)})
        with pytest.raises(ValueError, match="between 1 and 1000"):
            CSVService.validate_batch_size(df)


class TestDepartmentUploadService:
    """Tests for department upload service"""
    
    def test_upload_departments_csv(self, db_session):
        """Test uploading departments CSV"""
        csv_content = b"1,Engineering\n2,Sales\n3,Marketing"
        rows = CSVService.upload_departments_csv(csv_content, db_session)
        assert rows == 3
    
    def test_upload_departments_csv_invalid_columns(self, db_session):
        """Test uploading departments CSV with invalid columns"""
        csv_content = b"1,Engineering,Extra"
        with pytest.raises(ValueError, match="2 columns"):
            CSVService.upload_departments_csv(csv_content, db_session)
    
    def test_upload_departments_csv_too_large(self, db_session):
        """Test uploading departments CSV with too many rows"""
        csv_data = "\n".join([f"{i},Department{i}" for i in range(1, 1002)])
        with pytest.raises(ValueError, match="between 1 and 1000"):
            CSVService.upload_departments_csv(csv_data.encode(), db_session)


class TestJobUploadService:
    """Tests for job upload service"""
    
    def test_upload_jobs_csv(self, db_session):
        """Test uploading jobs CSV"""
        csv_content = b"1,Software Engineer\n2,Data Analyst\n3,Product Manager"
        rows = CSVService.upload_jobs_csv(csv_content, db_session)
        assert rows == 3
    
    def test_upload_jobs_csv_invalid_columns(self, db_session):
        """Test uploading jobs CSV with invalid columns"""
        csv_content = b"1,Engineer,Extra"
        with pytest.raises(ValueError, match="2 columns"):
            CSVService.upload_jobs_csv(csv_content, db_session)


class TestEmployeeUploadService:
    """Tests for employee upload service"""
    
    def test_upload_employees_csv(self, db_session):
        """Test uploading employees CSV"""
        csv_content = b"1,John Doe,2021-01-15T09:00:00,1,1\n2,Jane Smith,2021-02-20T10:30:00,2,2"
        rows = CSVService.upload_employees_csv(csv_content, db_session)
        assert rows == 2
    
    def test_upload_employees_csv_invalid_columns(self, db_session):
        """Test uploading employees CSV with invalid columns"""
        csv_content = b"1,John Doe,2021-01-15T09:00:00,1"
        with pytest.raises(ValueError, match="5 columns"):
            CSVService.upload_employees_csv(csv_content, db_session)


class TestBatchInsertService:
    """Tests for batch insert service"""
    
    def test_batch_insert_departments(self, db_session):
        """Test batch inserting departments"""
        departments = [
            {"id": 1, "department": "Engineering"},
            {"id": 2, "department": "Sales"}
        ]
        rows = CSVService.batch_insert_departments(departments, db_session)
        assert rows == 2
    
    def test_batch_insert_departments_invalid_size(self, db_session):
        """Test batch insert with invalid size"""
        departments = []
        with pytest.raises(ValueError, match="between 1 and 1000"):
            CSVService.batch_insert_departments(departments, db_session)
    
    def test_batch_insert_jobs(self, db_session):
        """Test batch inserting jobs"""
        jobs = [
            {"id": 1, "job": "Software Engineer"},
            {"id": 2, "job": "Data Analyst"}
        ]
        rows = CSVService.batch_insert_jobs(jobs, db_session)
        assert rows == 2
    
    def test_batch_insert_employees(self, db_session):
        """Test batch inserting employees"""
        employees = [
            {
                "id": 1,
                "name": "John Doe",
                "datetime": "2021-01-15T09:00:00",
                "department_id": 1,
                "job_id": 1
            }
        ]
        rows = CSVService.batch_insert_employees(employees, db_session)
        assert rows == 1
    
    def test_batch_insert_employees_multiple(self, db_session):
        """Test batch inserting multiple employees"""
        employees = [
            {
                "id": i,
                "name": f"Employee{i}",
                "datetime": "2021-01-15T09:00:00",
                "department_id": 1,
                "job_id": 1
            }
            for i in range(1, 11)
        ]
        rows = CSVService.batch_insert_employees(employees, db_session)
        assert rows == 10
