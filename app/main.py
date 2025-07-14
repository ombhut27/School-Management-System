from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users,auth,teacher,school,roles,student,divison,subjects,grade,section,board,subject_topic,class_schedule

# Create all tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("Connected to the database and ensured all tables are created.")
except Exception as e:
    print("Error creating tables:", e)

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(teacher.router)
app.include_router(school.router)
app.include_router(roles.router)
app.include_router(student.router)
app.include_router(divison.router)
app.include_router(subjects.router)
app.include_router(grade.router)
app.include_router(section.router)
app.include_router(board.router)
app.include_router(subject_topic.router)
app.include_router(class_schedule.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}


