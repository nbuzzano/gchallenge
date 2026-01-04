"""Tests for metrics endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestHiredByQuarterMetrics:
    """Tests for /metrics/hired-by-quarter endpoint"""
    
    def test_hired_by_quarter_empty_database(self, client):
        """Test metric with no data"""
        response = client.get("/metrics/hired-by-quarter")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_hired_by_quarter_with_data(self, client, db_session):
        """Test metric with sample data"""
        from app.database import Department, Job, Employee
        
        # Create departments
        dept1 = Department(id=1, department="Engineering")
        dept2 = Department(id=2, department="Sales")
        db_session.add(dept1)
        db_session.add(dept2)
        
        # Create jobs
        job1 = Job(id=1, job="Developer")
        job2 = Job(id=2, job="Manager")
        db_session.add(job1)
        db_session.add(job2)
        
        # Create employees hired in different quarters of 2021
        employees = [
            Employee(id=1, name="John Q1", datetime="2021-01-15T10:00:00", department_id=1, job_id=1),
            Employee(id=2, name="Jane Q1", datetime="2021-02-20T10:00:00", department_id=1, job_id=1),
            Employee(id=3, name="Bob Q2", datetime="2021-04-15T10:00:00", department_id=1, job_id=1),
            Employee(id=4, name="Alice Q3", datetime="2021-07-10T10:00:00", department_id=2, job_id=2),
            Employee(id=5, name="Charlie Q4", datetime="2021-10-05T10:00:00", department_id=2, job_id=2),
            Employee(id=6, name="David Q4", datetime="2021-11-20T10:00:00", department_id=2, job_id=2),
        ]
        for emp in employees:
            db_session.add(emp)
        
        db_session.commit()
        
        response = client.get("/metrics/hired-by-quarter")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Check Engineering - Developer (Q1: 2, Q2: 1, Q3: 0, Q4: 0)
        eng_dev = next(r for r in data if r["department"] == "Engineering" and r["job"] == "Developer")
        assert eng_dev["Q1"] == 2
        assert eng_dev["Q2"] == 1
        assert eng_dev["Q3"] == 0
        assert eng_dev["Q4"] == 0
        
        # Check Sales - Manager (Q1: 0, Q2: 0, Q3: 1, Q4: 2)
        sales_mgr = next(r for r in data if r["department"] == "Sales" and r["job"] == "Manager")
        assert sales_mgr["Q1"] == 0
        assert sales_mgr["Q2"] == 0
        assert sales_mgr["Q3"] == 1
        assert sales_mgr["Q4"] == 2
    
    def test_hired_by_quarter_only_2021(self, client, db_session):
        """Test that only 2021 data is included"""
        from app.database import Department, Job, Employee
        
        dept = Department(id=1, department="IT")
        job = Job(id=1, job="Engineer")
        db_session.add(dept)
        db_session.add(job)
        
        # Add employees from different years
        employees = [
            Employee(id=1, name="2020 Hire", datetime="2020-06-15T10:00:00", department_id=1, job_id=1),
            Employee(id=2, name="2021 Hire", datetime="2021-06-15T10:00:00", department_id=1, job_id=1),
            Employee(id=3, name="2022 Hire", datetime="2022-06-15T10:00:00", department_id=1, job_id=1),
        ]
        for emp in employees:
            db_session.add(emp)
        
        db_session.commit()
        
        response = client.get("/metrics/hired-by-quarter")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        
        # Only 2021 hire should be counted
        result = data[0]
        assert result["department"] == "IT"
        assert result["job"] == "Engineer"
        assert result["Q2"] == 1  # June is Q2
        assert result["Q1"] == 0
        assert result["Q3"] == 0
        assert result["Q4"] == 0


class TestDepartmentsAboveAverageMetrics:
    """Tests for /metrics/departments-above-average endpoint"""
    
    def test_departments_above_average_empty_database(self, client):
        """Test metric with no data"""
        response = client.get("/metrics/departments-above-average")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_departments_above_average_with_data(self, client, db_session):
        """Test departments above average hiring"""
        from app.database import Department, Job, Employee
        
        # Create departments
        dept1 = Department(id=1, department="Engineering")
        dept2 = Department(id=2, department="Sales")
        dept3 = Department(id=3, department="Marketing")
        dept4 = Department(id=4, department="HR")
        db_session.add_all([dept1, dept2, dept3, dept4])
        
        # Create job
        job = Job(id=1, job="Employee")
        db_session.add(job)
        
        # Create employees in 2021
        # Engineering: 10 employees
        for i in range(10):
            db_session.add(Employee(
                id=i+1, 
                name=f"Eng {i}", 
                datetime="2021-06-15T10:00:00", 
                department_id=1, 
                job_id=1
            ))
        
        # Sales: 5 employees
        for i in range(5):
            db_session.add(Employee(
                id=i+11, 
                name=f"Sales {i}", 
                datetime="2021-06-15T10:00:00", 
                department_id=2, 
                job_id=1
            ))
        
        # Marketing: 2 employees
        for i in range(2):
            db_session.add(Employee(
                id=i+16, 
                name=f"Mkt {i}", 
                datetime="2021-06-15T10:00:00", 
                department_id=3, 
                job_id=1
            ))
        
        # HR: 1 employee
        db_session.add(Employee(
            id=18, 
            name="HR 1", 
            datetime="2021-06-15T10:00:00", 
            department_id=4, 
            job_id=1
        ))
        
        db_session.commit()
        
        # Mean = (10 + 5 + 2 + 1) / 4 = 4.5
        # Above average: Engineering (10), Sales (5)
        
        response = client.get("/metrics/departments-above-average")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Should be ordered by hired (descending)
        assert data[0]["department"] == "Engineering"
        assert data[0]["id"] == 1
        assert data[0]["hired"] == 10
        
        assert data[1]["department"] == "Sales"
        assert data[1]["id"] == 2
        assert data[1]["hired"] == 5
    
    def test_departments_above_average_ignores_other_years(self, client, db_session):
        """Test that only 2021 hires are counted"""
        from app.database import Department, Job, Employee
        
        dept = Department(id=1, department="IT")
        db_session.add(dept)
        
        job = Job(id=1, job="Engineer")
        db_session.add(job)
        
        # Add employees from 2021 and other years
        db_session.add(Employee(id=1, name="2020", datetime="2020-01-15T10:00:00", department_id=1, job_id=1))
        db_session.add(Employee(id=2, name="2021", datetime="2021-01-15T10:00:00", department_id=1, job_id=1))
        db_session.add(Employee(id=3, name="2022", datetime="2022-01-15T10:00:00", department_id=1, job_id=1))
        
        db_session.commit()
        
        response = client.get("/metrics/departments-above-average")
        assert response.status_code == 200
        
        data = response.json()
        # Only 1 employee in 2021, mean is 1, so none above average
        assert len(data) == 0
