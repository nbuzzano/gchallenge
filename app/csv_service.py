import pandas as pd
import io
from typing import List, Dict
from sqlalchemy.orm import Session
from app.database import Department, Job, Employee


class CSVService:
    @staticmethod
    def parse_csv(file_content: bytes) -> pd.DataFrame:
        """Parse CSV file content into a pandas DataFrame"""
        try:
            csv_string = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_string), header=None)
            return df
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")

    @staticmethod
    def validate_batch_size(data: pd.DataFrame) -> None:
        """Validate that batch size is between 1 and 1000 rows"""
        if len(data) < 1 or len(data) > 1000:
            raise ValueError(f"Batch size must be between 1 and 1000 rows. Received: {len(data)}")

    @staticmethod
    def upload_departments_csv(file_content: bytes, db: Session) -> int:
        """Upload departments from CSV file"""
        df = CSVService.parse_csv(file_content)
        CSVService.validate_batch_size(df)
        
        # Expected columns: id, department
        if df.shape[1] != 2:
            raise ValueError("Departments CSV must have 2 columns: id, department")
        
        df.columns = ['id', 'department']
        
        rows_inserted = 0
        for _, row in df.iterrows():
            department = Department(
                id=int(row['id']),
                department=str(row['department'])
            )
            db.add(department)
            rows_inserted += 1
        
        db.commit()
        return rows_inserted

    @staticmethod
    def upload_jobs_csv(file_content: bytes, db: Session) -> int:
        """Upload jobs from CSV file"""
        df = CSVService.parse_csv(file_content)
        CSVService.validate_batch_size(df)
        
        # Expected columns: id, job
        if df.shape[1] != 2:
            raise ValueError("Jobs CSV must have 2 columns: id, job")
        
        df.columns = ['id', 'job']
        
        rows_inserted = 0
        for _, row in df.iterrows():
            job = Job(
                id=int(row['id']),
                job=str(row['job'])
            )
            db.add(job)
            rows_inserted += 1
        
        db.commit()
        return rows_inserted

    @staticmethod
    def upload_employees_csv(file_content: bytes, db: Session) -> int:
        """Upload employees from CSV file"""
        df = CSVService.parse_csv(file_content)
        CSVService.validate_batch_size(df)
        
        # Expected columns: id, name, datetime, department_id, job_id
        if df.shape[1] != 5:
            raise ValueError("Employees CSV must have 5 columns: id, name, datetime, department_id, job_id")
        
        df.columns = ['id', 'name', 'datetime', 'department_id', 'job_id']
        
        rows_inserted = 0
        for _, row in df.iterrows():
            employee = Employee(
                id=int(row['id']),
                name=str(row['name']),
                datetime=str(row['datetime']),
                department_id=int(row['department_id']),
                job_id=int(row['job_id'])
            )
            db.add(employee)
            rows_inserted += 1
        
        db.commit()
        return rows_inserted

    @staticmethod
    def batch_insert_departments(departments: List[Dict], db: Session) -> int:
        """Batch insert departments"""
        if not (1 <= len(departments) <= 1000):
            raise ValueError(f"Batch size must be between 1 and 1000 rows. Received: {len(departments)}")
        
        for dept in departments:
            department = Department(**dept)
            db.add(department)
        
        db.commit()
        return len(departments)

    @staticmethod
    def batch_insert_jobs(jobs: List[Dict], db: Session) -> int:
        """Batch insert jobs"""
        if not (1 <= len(jobs) <= 1000):
            raise ValueError(f"Batch size must be between 1 and 1000 rows. Received: {len(jobs)}")
        
        for job_data in jobs:
            job = Job(**job_data)
            db.add(job)
        
        db.commit()
        return len(jobs)

    @staticmethod
    def batch_insert_employees(employees: List[Dict], db: Session) -> int:
        """Batch insert employees"""
        if not (1 <= len(employees) <= 1000):
            raise ValueError(f"Batch size must be between 1 and 1000 rows. Received: {len(employees)}")
        
        for emp in employees:
            employee = Employee(**emp)
            db.add(employee)
        
        db.commit()
        return len(employees)
