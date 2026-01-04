from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, and_
from typing import List
from app.database import get_db, create_tables, Department, Job, Employee
from app.csv_service import CSVService
from app.schemas import (
    DepartmentBatch, JobBatch, EmployeeBatch, 
    UploadResponse, HiredByQuarterSchema, DepartmentHiringMetricSchema
)

app = FastAPI(
    title="DB Migration REST API",
    description="REST API for uploading CSV data to SQL database with batch transaction support",
    version="1.0.0"
)


@app.on_event("startup")
def startup_event():
    """Create database tables on startup"""
    create_tables()


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "DB Migration REST API",
        "version": "1.0.0",
        "endpoints": {
            "upload_departments_csv": "/upload/departments",
            "upload_jobs_csv": "/upload/jobs",
            "upload_employees_csv": "/upload/employees",
            "batch_insert_departments": "/batch/departments",
            "batch_insert_jobs": "/batch/jobs",
            "batch_insert_employees": "/batch/employees",
            "metrics_hired_by_quarter": "/metrics/hired-by-quarter",
            "metrics_departments_above_average": "/metrics/departments-above-average"
        }
    }


# CSV Upload Endpoints
@app.post("/upload/departments", response_model=UploadResponse)
async def upload_departments_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload departments from CSV file.
    
    CSV Format: id,department
    Batch size: 1-1000 rows
    """
    try:
        content = await file.read()
        rows_inserted = CSVService.upload_departments_csv(content, db)
        return UploadResponse(
            message=f"Successfully uploaded {rows_inserted} departments",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/upload/jobs", response_model=UploadResponse)
async def upload_jobs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload jobs from CSV file.
    
    CSV Format: id,job
    Batch size: 1-1000 rows
    """
    try:
        content = await file.read()
        rows_inserted = CSVService.upload_jobs_csv(content, db)
        return UploadResponse(
            message=f"Successfully uploaded {rows_inserted} jobs",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/upload/employees", response_model=UploadResponse)
async def upload_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload employees from CSV file.
    
    CSV Format: id,name,datetime,department_id,job_id
    Batch size: 1-1000 rows
    """
    try:
        content = await file.read()
        rows_inserted = CSVService.upload_employees_csv(content, db)
        return UploadResponse(
            message=f"Successfully uploaded {rows_inserted} employees",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Batch Insert Endpoints
@app.post("/batch/departments", response_model=UploadResponse)
def batch_insert_departments(
    batch: DepartmentBatch,
    db: Session = Depends(get_db)
):
    """
    Batch insert departments (1-1000 rows per request).
    
    Request body example:
    {
        "departments": [
            {"id": 1, "department": "Engineering"},
            {"id": 2, "department": "Sales"}
        ]
    }
    """
    try:
        departments_data = [dept.model_dump() for dept in batch.departments]
        rows_inserted = CSVService.batch_insert_departments(departments_data, db)
        return UploadResponse(
            message=f"Successfully inserted {rows_inserted} departments",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/batch/jobs", response_model=UploadResponse)
def batch_insert_jobs(
    batch: JobBatch,
    db: Session = Depends(get_db)
):
    """
    Batch insert jobs (1-1000 rows per request).
    
    Request body example:
    {
        "jobs": [
            {"id": 1, "job": "Software Engineer"},
            {"id": 2, "job": "Data Analyst"}
        ]
    }
    """
    try:
        jobs_data = [job.model_dump() for job in batch.jobs]
        rows_inserted = CSVService.batch_insert_jobs(jobs_data, db)
        return UploadResponse(
            message=f"Successfully inserted {rows_inserted} jobs",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/batch/employees", response_model=UploadResponse)
def batch_insert_employees(
    batch: EmployeeBatch,
    db: Session = Depends(get_db)
):
    """
    Batch insert employees (1-1000 rows per request).
    
    Request body example:
    {
        "employees": [
            {
                "id": 1,
                "name": "John Doe",
                "datetime": "2021-01-01T10:00:00",
                "department_id": 1,
                "job_id": 1
            }
        ]
    }
    """
    try:
        employees_data = [emp.model_dump() for emp in batch.employees]
        rows_inserted = CSVService.batch_insert_employees(employees_data, db)
        return UploadResponse(
            message=f"Successfully inserted {rows_inserted} employees",
            rows_inserted=rows_inserted
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Metrics Endpoints
@app.get("/metrics/hired-by-quarter", response_model=List[HiredByQuarterSchema])
def get_hired_by_quarter(db: Session = Depends(get_db)):
    """
    Number of employees hired for each job and department in 2021 divided by quarter.
    Ordered alphabetically by department and job.
    
    Returns a list with the following structure:
    - department: Department name
    - job: Job title
    - Q1, Q2, Q3, Q4: Number of employees hired in each quarter
    """
    # Query using SQLAlchemy ORM for database compatibility
    results = db.query(
        Department.department,
        Job.job,
        func.sum(case((func.substr(Employee.datetime, 6, 2).in_(['01', '02', '03']), 1), else_=0)).label('Q1'),
        func.sum(case((func.substr(Employee.datetime, 6, 2).in_(['04', '05', '06']), 1), else_=0)).label('Q2'),
        func.sum(case((func.substr(Employee.datetime, 6, 2).in_(['07', '08', '09']), 1), else_=0)).label('Q3'),
        func.sum(case((func.substr(Employee.datetime, 6, 2).in_(['10', '11', '12']), 1), else_=0)).label('Q4')
    ).join(
        Department, Employee.department_id == Department.id
    ).join(
        Job, Employee.job_id == Job.id
    ).filter(
        func.substr(Employee.datetime, 1, 4) == '2021'
    ).group_by(
        Department.department, Job.job
    ).order_by(
        Department.department.asc(), Job.job.asc()
    ).all()
    
    return [
        HiredByQuarterSchema(
            department=row[0],
            job=row[1],
            Q1=row[2],
            Q2=row[3],
            Q3=row[4],
            Q4=row[5]
        )
        for row in results
    ]


@app.get("/metrics/departments-above-average", response_model=List[DepartmentHiringMetricSchema])
def get_departments_above_average(db: Session = Depends(get_db)):
    """
    List of departments that hired more employees than the mean in 2021.
    Ordered by number of employees hired (descending).
    
    Returns a list with:
    - id: Department ID
    - department: Department name
    - hired: Number of employees hired in 2021
    """
    # Subquery to count hires per department in 2021
    dept_hires = db.query(
        Department.id,
        Department.department,
        func.count(Employee.id).label('hired')
    ).outerjoin(
        Employee, 
        and_(
            Department.id == Employee.department_id,
            func.substr(Employee.datetime, 1, 4) == '2021'
        )
    ).group_by(
        Department.id, Department.department
    ).subquery()
    
    # Calculate average
    avg_hired = db.query(func.avg(dept_hires.c.hired)).scalar() or 0
    
    # Get departments above average
    results = db.query(
        dept_hires.c.id,
        dept_hires.c.department,
        dept_hires.c.hired
    ).filter(
        dept_hires.c.hired > avg_hired
    ).order_by(
        dept_hires.c.hired.desc()
    ).all()
    
    return [
        DepartmentHiringMetricSchema(
            id=row[0],
            department=row[1],
            hired=row[2]
        )
        for row in results
    ]
