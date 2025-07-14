from pydantic import BaseModel, EmailStr
from datetime import datetime, time
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
       from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: str | None = None

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int

    class Config:
      class Config:
       from_attributes = True

class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: int

class AssignRoleResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    assigned_at: datetime

class TokenData(BaseModel):
    id: str | None = None

class Token(BaseModel):
    id: int
    access_token: str
    token_type: str
    message: str | None = None

class TeacherOut(BaseModel):
    id: int
    display_name: str
    email: str
    created_at: datetime
    updated_at: datetime
    school_id: int
    school_name: Optional[str] = None

    class Config:
        from_attributes = True

class SchoolOut(BaseModel):
    id: int
    name: str
    address: str
    locality: Optional[str]
    city: str
    state: str
    country: str
    zip_code: str
    contact_number_1: str
    contact_number_2: Optional[str]
    email: Optional[str]
    poc1: Optional[str]
    poc2: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchoolCreate(BaseModel):
    name: str
    address: str
    locality: Optional[str] = None
    city: str
    state: str
    country: str
    zip_code: str
    contact_number_1: str
    contact_number_2: Optional[str] = None
    email: Optional[str] = None
    poc1: Optional[str] = None
    poc2: Optional[str] = None

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    contact_number_1: Optional[str] = None
    contact_number_2: Optional[str] = None
    email: Optional[str] = None
    poc1: Optional[str] = None
    poc2: Optional[str] = None


class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    school_id: int

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    school_id: Optional[int] = None


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    school_id: int
    grade_id: int
    section_id: int

class StudentOut(BaseModel):
    id: int
    display_name: str
    email: str
    created_at: datetime
    updated_at: datetime
    school_id: int
    school_name: Optional[str] = None
    division_id: Optional[int] = None
    grade_id: Optional[int] = None
    section_id: Optional[int] = None
    grade_name: Optional[str] = None
    section_name: Optional[str] = None

    class Config:
        from_attributes = True

class DivisionCreate(BaseModel):
    grade_id: int
    section_id: int
    academic_year: str
    school_id: int

class DivisionOut(BaseModel):
    id: int
    grade_id: int
    section_id: int
    academic_year: str
    created_at: datetime
    updated_at: datetime
    school_id: int

    class Config:
        from_attributes = True

class DivisionOutWithNames(BaseModel):
    id: int
    grade_id: int
    section_id: int
    school_id: int
    grade_name: str
    section_name: str
    school_name: str
    academic_year: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentDivisionCreate(BaseModel):
    student_id: int
    division_id: int

class StudentDivisionOut(BaseModel):
    id: int
    student_id: int
    division_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    school_id: Optional[int] = None
    grade_id: Optional[int] = None
    section_id: Optional[int] = None

class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None

class SubjectOut(BaseModel):
    id: int
    name: str
    code: Optional[str]
    department: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DivisionSubjectCreate(BaseModel):
    school_id: int
    division_id: int
    subject_id: int

class DivisionSubjectBulkCreate(BaseModel):
    division_id: int
    subjects: dict[str, int]  # subject_name: subject_id mapping


class DivisionSubjectOut(BaseModel):
    id: int
    school_id: int
    division_id: int
    subject_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DivisionSubjectUpdate(BaseModel):
    school_id: Optional[int] = None
    division_id: Optional[int] = None
    subject_id: Optional[int] = None

class GradeSubjectCreate(BaseModel):
    grade: str
    subject_id: int
    is_compulsory: bool = True

class GradeSubjectOut(BaseModel):
    id: int
    grade: str
    subject_id: int
    is_compulsory: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AddSubjects(BaseModel):
    student_id: int
    subject_id: int

class AddSubjectsOut(BaseModel):
    student_name: str
    subject_name: str

class GetStudentSubjectsOut(BaseModel):
    subject_id: int
    subject_name: str

class AddTeacherDivision(BaseModel):
    teacher_id: int
    division_id: int
    subject_id: int

class GradeCreate(BaseModel):
    name: str

class GradeOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class SectionCreate(BaseModel):
    name: str

class SectionOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class BoardCreate(BaseModel):
    name: str

class BoardOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class SubjectTopicCreate(BaseModel):
    topic: str
    sub_topic: Optional[str] = None
    subject_id: int
    board_id: int
    grade_id: int

class SubjectTopicOut(BaseModel):
    id: int
    topic: str
    sub_topic: Optional[str] = None
    subject_id: int
    board_id: int
    grade_id: int
    subject_name: Optional[str] = None
    board_name: Optional[str] = None
    grade_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClassScheduleCreate(BaseModel):
    period: int
    date: Optional[str] = None  # Will be converted to Date
    subject_id: int
    division_id: int
    teacher_id: int
    start_time: time # Will be converted to DateTime
    end_time: time    # Will be converted to DateTime

class ClassScheduleOut(BaseModel):
    id: int
    period: int
    date: str  # Date as string
    subject_id: int
    division_id: int
    teacher_id: int
    start_time: str  # DateTime as string
    end_time: str    # DateTime as string
    created_at: datetime
    updated_at: datetime
    subject_name: Optional[str] = None
    division_name: Optional[str] = None
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class ClassScheduleUpdate(BaseModel):
    period: Optional[int] = None
    date: Optional[str] = None
    subject_id: Optional[int] = None
    division_id: Optional[int] = None
    teacher_id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class SetClassTopic(BaseModel):
    class_schedule_id: int
    subject_topic_id: int

class SetClassTopicOut(BaseModel):
    id: int
    class_schedule_id: int
    subject_topic_id: int
    class_schedule_details: dict
    subject_topic_details: dict

    class Config:
        from_attributes = True


