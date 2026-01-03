from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class DepartmentSchema(BaseModel):
    id: int
    department: str

    # The nested Config class contains configuration options for the Pydantic model. The from_attributes = True setting (formerly called orm_mode = True in older Pydantic versions) is particularly important when working with databases. It tells Pydantic to read data not just from dictionaries, but also from object attributes.
    # Why this matters: Without from_attributes = True, if you query a SQLAlchemy ORM object from your database and try to convert it to a JobSchema, Pydantic would fail because it expects dictionary-like access (e.g., obj['id']). With this setting enabled, Pydantic can read from ORM objects using attribute access (e.g., obj.id), making it seamless to convert database models to Pydantic schemas.
    class Config:   
        from_attributes = True


class JobSchema(BaseModel):
    id: int
    job: str

    class Config:
        from_attributes = True


class EmployeeSchema(BaseModel):
    id: int
    name: str
    datetime: str
    department_id: int
    job_id: int

    class Config:
        from_attributes = True


class DepartmentBatch(BaseModel):
    departments: List[DepartmentSchema] = Field(..., min_length=1, max_length=1000)

    @field_validator('departments')
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError('Batch size must be between 1 and 1000 rows')
        return v

        # A subtle gotcha here: This validator is actually redundant. Pydantic already enforces the min_length and max_length constraints specified in the Field() definition, so the custom validator performs the same check twice. If you remove the validate_batch_size method entirely, Pydantic will still raise a validation error for lists outside the 1-1000 range, though the error message will be slightly different.


class JobBatch(BaseModel):
    jobs: List[JobSchema] = Field(..., min_length=1, max_length=1000)

    @field_validator('jobs')
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError('Batch size must be between 1 and 1000 rows')
        return v


class EmployeeBatch(BaseModel):
    employees: List[EmployeeSchema] = Field(..., min_length=1, max_length=1000)

    @field_validator('employees')
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError('Batch size must be between 1 and 1000 rows')
        return v


class UploadResponse(BaseModel):
    message: str
    rows_inserted: int
