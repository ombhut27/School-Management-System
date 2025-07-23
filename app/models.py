from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text,Text,Date,Boolean,UniqueConstraint,Time,DateTime,JSON,Computed,Enum as SQLEnum
from .database import Base
import enum

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at =  Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))


class UserRole(Base):
    __tablename__ = 'user_roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False) 
    description = Column(Text, nullable=True)

class UserRoleRel(Base):
    __tablename__ = 'user_roles_rel'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey('user_roles.id', ondelete="CASCADE"), nullable=False)
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class School(Base):
    __tablename__ = 'schools'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(200), nullable=False, unique=True)  
    address = Column(String, nullable=False)
    locality = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    contact_number_1 = Column(String(20), nullable=False)
    contact_number_2 = Column(String(20), nullable=True)
    email = Column(String(100), unique=True)  
    poc1 = Column(String(100))
    poc2 = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100), nullable=False) 
    code = Column(String(20), unique=True) 
    department = Column(String(25))
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class Division(Base):
    __tablename__ = 'divisions'
    id = Column(Integer, primary_key=True)
    grade_id = Column(Integer, ForeignKey('grades.id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.id', ondelete='CASCADE'), nullable=False)
    academic_year = Column(String(10), nullable=False)
    created_at =  Column(TIMESTAMP(timezone=True), nullable= False, server_default=text('now()'))
    updated_at =  Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    school_id = Column(Integer, ForeignKey('schools.id', ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint('grade_id', 'section_id', 'academic_year', 'school_id', name='unique_division_per_school_year'),
    )



# student

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)  # Added unique constraint
    created_at =  Column(TIMESTAMP(timezone=True), nullable= False, server_default=text('now()'))
    updated_at =  Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey('schools.id', ondelete="CASCADE"), nullable=False)


class StudentDivision(Base):
    __tablename__ = 'student_divisions'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete="CASCADE"), nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete="CASCADE"), nullable=False)
    is_current = Column(Boolean, nullable=False, server_default=text('true'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    __table_args__ = (
        UniqueConstraint('student_id', 'division_id', name='unique_student_division'),
    )

class StudentSubjectRel(Base):
    __tablename__='student_subject_rel'
    id = Column(Integer, primary_key=True, index=True)
    
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    division_id = Column(Integer,ForeignKey('divisions.id', ondelete='CASCADE'), nullable=True)
    is_active = Column(Boolean, server_default=text('true'), nullable=True)


    __table_args__ = (UniqueConstraint('subject_id', 'student_id', 'division_id','is_active', name='uq_student_subject'),)

    

#admin assigned subjects to division

class DivisionSubject(Base):
    __tablename__ = 'division_subjects'

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

    school_id = Column(Integer, ForeignKey('schools.id', ondelete='CASCADE'), nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        UniqueConstraint('school_id', 'division_id', 'subject_id', name='unique_division_subject'),
    )


# teacher

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)  # Added unique constraint
    created_at =  Column(TIMESTAMP(timezone=True), nullable= False, server_default=text('now()'))
    updated_at =  Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey('schools.id', ondelete="CASCADE"), nullable=False)

class TeacherDivision(Base):
    __tablename__ = 'teacher_division_subject_rel'
    id = Column(Integer, primary_key=True, index=True, nullable=False)

    division_id = Column(Integer, ForeignKey('divisions.id', ondelete='CASCADE'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
 
    __table_args__ = (
        UniqueConstraint('subject_id', 'teacher_id', 'division_id', name='uq_division_subject_teacher'),
    )


class Board(Base):
    __tablename__ = 'boards'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class SubjectTopic(Base):
    __tablename__ = 'subject_topics'
    id = Column(Integer, primary_key=True)
    topic = Column(String(50), nullable=False)
    sub_topic = Column(String(50), nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    board_id = Column(Integer, ForeignKey('boards.id', ondelete='CASCADE'), nullable=False)
    grade_id = Column(Integer, ForeignKey('grades.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    __table_args__ = (
        UniqueConstraint('topic', 'sub_topic', 'subject_id', 'board_id', 'grade_id', name='unique_subject_topic'),
    )

class ClassSchedule(Base):
    __tablename__ = 'class_schedules'
    id = Column(Integer, primary_key=True)
    period = Column(Integer, nullable=False)  
    date = Column(Date, nullable=False, server_default=text('CURRENT_DATE'))
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete="CASCADE"), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

class ClassDetailsRel(Base):
      __tablename__ = 'class_details_rel'
      id = Column(Integer, primary_key=True)
      class_schedule_id = Column(Integer, ForeignKey('class_schedules.id', ondelete="CASCADE"), nullable=False)
      subject_topic_id = Column(Integer, ForeignKey('subject_topics.id', ondelete="CASCADE"), nullable=False)
      __table_args__ = (
          UniqueConstraint('class_schedule_id', 'subject_topic_id', name='uq_schedule_topic'),
      )


# Quiz 

class QuestionState(str, enum.Enum):
    active = "active"
    draft = "draft"
    edited = "edited"

class Quiz(Base):
    __tablename__='quiz'

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    start_date = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # Duration stored in minutes
    due_date = Column(DateTime, Computed("start_date + interval '1 minute' * duration"), nullable=False)
    topic = Column(String(50), nullable=False)
    sub_topic = Column(String(50), nullable=False)
    quiz_type = Column(String(50), nullable=False, default='Assignment')
    is_public = Column(Boolean, server_default=text('true'))
    instructions = Column(JSON, nullable=True)
    total_marks = Column(Integer, nullable=True)

    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey('schools.id', ondelete="CASCADE"), nullable=False)


class Question(Base):
    __tablename__='questions'

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(JSON)
    is_objective = Column(Boolean, nullable=False, server_default=text('true'))
    answer = Column(JSON)
    choice_body = Column(JSON)
    topic = Column(String(50), nullable=False)
    sub_topic = Column(String(50), nullable=False)
    baseline_answer = Column(JSON)
    is_public = Column(Boolean, server_default=text('true'))
    state = Column(SQLEnum(QuestionState), default=QuestionState.active, nullable=True)

    #Fkey
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey('schools.id', ondelete='CASCADE'),nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete='CASCADE'),nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'),nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'title', 'subject_id', 'division_id', 'school_id', name='uq_question_user_title_context'),
    )

class QuizQuestion(Base):
    __tablename__='quiz_question_rel'

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    question_number = Column(Integer, nullable=False)

    # Fkeys
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quiz.id', ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint('quiz_id', 'question_id', name='uq_quiz_question'),
    )

class PublishedQuiz(Base):
    __tablename__ = 'published_quiz'
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_detail = Column(JSON)
    quiz_type = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)
    end_time = Column(DateTime, Computed("start_time + interval '1 minute' * duration"), nullable=False)
    quiz_id = Column(Integer, nullable=False) 
    teacher_task_id = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False) 
    
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey('schools.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer,ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint('quiz_id', 'division_id', 'school_id','quiz_type', name='uq_published_quiz_div_school'),)



class StudentQuizResponseRel(Base):
    __tablename__ = 'students_quiz_response_rel'

    id = Column(Integer, primary_key=True, index=True)
    quiz_detail = Column(JSON) 
    response = Column(JSON)
    quiz_type = Column(String(20)) # for tasks
    start_date = Column(DateTime) # for tasks
    duration = Column(Integer) # for tasks
    status = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    is_submitted = Column(Boolean, server_default=text('false'), nullable=False)
    submitted_at = Column(TIMESTAMP(timezone=True))

    
    student_id = Column(Integer, ForeignKey('students.id', ondelete="CASCADE"), nullable=False)
    quiz_rel_id = Column(Integer, ForeignKey('published_quiz.id'))


# Teacher task

class TaskTypeEnum(str, enum.Enum):
    Classwork = "Classwork"
    Homework = "Homework"
    Quiz = "Quiz"
    Assignment = "Assignment"
    ReadingMaterial = "ReadingMaterial"
    AICheck = "AICheck"
    SlipTest = "SlipTest"

class TeacherTasks(Base):
    __tablename__ = 'teacher_tasks'

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    title = Column(String(100),nullable=False)
    task_type = Column(SQLEnum(TaskTypeEnum), nullable=False) 
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    instructions = Column(JSON)
    status = Column(String, default="pending", nullable=True)

    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete="CASCADE"), nullable=False)
    division_id = Column(Integer, ForeignKey('divisions.id', ondelete="CASCADE"), nullable=False)
    class_schedule_id = Column(Integer, ForeignKey('class_schedules.id', ondelete="CASCADE"), nullable=True)
    quiz_id = Column(Integer, ForeignKey('quiz.id', ondelete='SET NULL'), nullable=True)
    published_quiz_id = Column(Integer, ForeignKey('published_quiz.id', ondelete='SET NULL'), nullable=True)
    
    __table_args__ = (UniqueConstraint('title','task_type','subject_id', 'teacher_id','division_id', 'class_schedule_id', name='uq_task_subject_teacher'),)


    