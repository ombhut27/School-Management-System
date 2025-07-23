from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user
from app.models import QuizQuestion, Quiz, Question
from sqlalchemy import insert
from app import schemas 
from app.models import PublishedQuiz, StudentQuizResponseRel

router = APIRouter()


@router.post("/api/add_quiz", response_model=schemas.QuizCreate)
def create_quiz(
    quiz: schemas.QuizCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate each ID individually
    school_exists = db.query(models.School).filter(models.School.id == quiz.school_id).first()
    division_exists = db.query(models.Division).filter(models.Division.id == quiz.division_id).first()
    subject_exists = db.query(models.Subject).filter(models.Subject.id == quiz.subject_id).first()
    if not (school_exists and division_exists and subject_exists):
        raise HTTPException(status_code=400, detail="Invalid school_id, division_id, or subject_id")

    # Validate instructions
    if not isinstance(quiz.instructions, dict):
        raise HTTPException(status_code=400, detail="instructions must be an object")
    required_instruction_fields = ["description", "passing_score"]
    for field in required_instruction_fields:
        if field not in quiz.instructions or not quiz.instructions[field]:
            raise HTTPException(status_code=400, detail=f"Instruction '{field}' is required and must be > 0")

    db_quiz = models.Quiz(**quiz.model_dump(), user_id=current_user.id)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@router.post("/api/add_question", response_model=schemas.QuestionCreate)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate each ID 
    school_exists = db.query(models.School).filter(models.School.id == question.school_id).first()
    division_exists = db.query(models.Division).filter(models.Division.id == question.division_id).first()
    subject_exists = db.query(models.Subject).filter(models.Subject.id == question.subject_id).first()
    if not (school_exists and division_exists and subject_exists):
        raise HTTPException(status_code=400, detail="Invalid school_id, division_id, or subject_id")
    db_question = models.Question(**question.model_dump(exclude={"user_id"}), user_id=current_user.id)
    try:
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A question with this title already exists for this user in the same subject, division, and school."
        )

@router.post("/api/add_questions_bulk", response_model=List[schemas.QuestionCreate])
def create_questions_bulk(
    data: schemas.BulkQuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    created_questions = []
    for question in data.questions:
        # Validate each ID individually
        school_exists = db.query(models.School).filter(models.School.id == question.school_id).first()
        division_exists = db.query(models.Division).filter(models.Division.id == question.division_id).first()
        subject_exists = db.query(models.Subject).filter(models.Subject.id == question.subject_id).first()
        if not (school_exists and division_exists and subject_exists):
            raise HTTPException(status_code=400, detail=f"Invalid school_id, division_id, or subject_id for question {question.title}")
        db_question = models.Question(**question.model_dump(exclude={"user_id"}), user_id=current_user.id)
        try:
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            created_questions.append(db_question)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"A question with this title already exists for this user in the same subject, division, and school for question {question.title}"
            )
    return created_questions

@router.post("/api/{quiz_id}/add_existing_question", response_model=Dict[str, Any])
async def add_existing_question_to_quiz(
    quiz_id: int,
    question_id: int,
    question_number: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if quiz exists and is owned by user
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or not authorized")
    # Check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if question is already in this quiz
    existing = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id,
        QuizQuestion.question_id == question_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Question already exists in this quiz")

    # Determine question number
    if question_number is None:
        max_number = db.query(QuizQuestion.question_number).filter(
            QuizQuestion.quiz_id == quiz_id
        ).order_by(QuizQuestion.question_number.desc()).first()
        question_number = (max_number[0] if max_number else 0) + 1

    quiz_question = QuizQuestion(
        quiz_id=quiz_id,
        question_id=question_id,
        question_number=question_number,
        user_id=current_user.id
    )

    db.add(quiz_question)
    db.commit()

    return {
        "message": "Question added to quiz successfully",
        "question_id": question_id,
        "question_number": question_number,
        "question_title": question.title
    }

@router.post("/api/{quiz_id}/add_questions_bulk")
async def add_questions_bulk(
    quiz_id: int,
    data: schemas.BulkQuizQuestionAdd,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Verify quiz exists and user owns it
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or not authorized")

    # Get current max question_number
    max_number = db.query(QuizQuestion.question_number).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.question_number.desc()).first()
    next_number = (max_number[0] if max_number else 0) + 1

    added = []
    for qid in data.question_ids:
        # Check for duplicates
        exists = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id,
            QuizQuestion.question_id == qid
        ).first()
        if exists:
            continue 

        quiz_question = QuizQuestion(
            quiz_id=quiz_id,
            question_id=qid,
            question_number=next_number,
            user_id=current_user.id
        )
        db.add(quiz_question)
        added.append(qid)
        next_number += 1

    db.commit()
    return {
        "message": f"Added {len(added)} questions to quiz.",
        "added_question_ids": added
    } 

@router.patch("/api/quiz/{quiz_id}", response_model=schemas.QuizCreate)
def update_quiz(
    quiz_id: int,
    quiz_update: schemas.QuizUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.user_id != current_user.id: #type: ignore
        raise HTTPException(status_code=403, detail="Not authorized to edit this quiz")

    update_data = quiz_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quiz, key, value)

    db.commit()
    db.refresh(quiz)
    return quiz 

@router.get("/api/questions/state/{quiz_id}")
async def get_quiz_questions_with_states(
    quiz_id: int,
    include_drafts: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found or not authorized"
            )

        quiz_questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()

        all_questions = []
        for qq_rel in quiz_questions:
            question = db.query(Question).filter(Question.id == qq_rel.question_id).first()
            if question is None:
                continue  # skip if question is missing
            question_data = {
                "id": question.id,
                "question_id": question.id,
                "title": question.title,
                "body": question.body,
                "is_objective": question.is_objective,
                "answer": question.answer,
                "choice_body": question.choice_body,
                "state": question.state.value if hasattr(question.state, 'value') else question.state,
                "topic": question.topic,
                "sub_topic": question.sub_topic,
                "question_number": qq_rel.question_number
            }
            all_questions.append(question_data)

        # Group questions by state
        questions_by_state = {
            "active": [],
            "draft": [],
            "edited": []
        }
        for q_data in all_questions:
            state = q_data["state"]
            if state == "active" or (state == "draft" and include_drafts) or state == "edited":
                questions_by_state[state].append(q_data)

        # Sort by question number within each state
        for state in questions_by_state:
            questions_by_state[state].sort(key=lambda x: x.get("question_number", 0))

        # Prepare summary
        summary = {
            "total": len(all_questions),
            "active": len(questions_by_state["active"]),
            "draft": len(questions_by_state["draft"]),
            "edited": len(questions_by_state["edited"])
        }

        # Quiz info (add more fields as needed)
        quiz_info = {
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "question_count": len(all_questions)
        }

        return {
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "questions": questions_by_state,
            "summary": summary,
            "quiz_info": quiz_info
        }
    except HTTPException:
        raise
    except Exception :
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching quiz questions"
        ) 

@router.get("/api/get_quiz/{quiz_id}")
async def get_quiz_questions(
    quiz_id: int,
    db: Session = Depends(get_db)
):

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"quiz with id {quiz_id} is not found")

    quiz_questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.question_number).all()

    questions_data = []
    for qq in quiz_questions:
        question = db.query(Question).filter(Question.id == qq.question_id).first()
        if question is not None:
            # Ensure state is always a string, not a SQLAlchemy column or expression
            state = question.state.value if hasattr(question.state, 'value') else str(question.state)
            if state == "active":
                is_objective = question.__dict__.get("is_objective", False) == True
                questions_data.append({
                    "question_id": question.id,
                    "question_number": qq.question_number,
                    "title": question.title,
                    "body": question.body,
                    "is_objective": is_objective,
                    "topic": question.topic,
                    "sub_topic": question.sub_topic,
                    "answer": question.answer,
                    "choice_body": question.choice_body if is_objective else None
                })

    if not questions_data:
        raise HTTPException(status_code=404, detail="No questions found for this quiz")

    quiz_response = {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "start_date": getattr(quiz, 'start_date', None),
        "duration": getattr(quiz, 'duration', None),
        "topic": getattr(quiz, 'topic', None),
        "sub_topic": getattr(quiz, 'sub_topic', None),
        "quiz_type": getattr(quiz, 'quiz_type', None),
        "is_public": getattr(quiz, 'is_public', None),
        "total_marks": getattr(quiz, 'total_marks', None),
        "questions": questions_data
    }
    return quiz_response 

@router.post("/api/publish_quiz/{task_id}")
async def publish_quiz(
    published_quiz: schemas.PublishQuiz,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    division = db.query(models.Division).filter(models.Division.id == published_quiz.division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division/class not found")

    # Fetch grade and section for division name
    grade = db.query(models.Grade).filter(models.Grade.id == division.grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    section = db.query(models.Section).filter(models.Section.id == division.section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    school = db.query(models.School).filter(models.School.id == division.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    quiz_main = db.query(models.Quiz).filter(models.Quiz.id == published_quiz.quiz_id).first()
    if not quiz_main:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Fetch subject directly since there is no relationship
    subject = db.query(models.Subject).filter(models.Subject.id == quiz_main.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    questions = db.query(models.Question, models.QuizQuestion.question_number).join(
        models.QuizQuestion,
        models.QuizQuestion.question_id == models.Question.id
    ).filter(
        models.QuizQuestion.quiz_id == quiz_main.id,
        models.Question.state == "active"
    ).all()

    question_detail = []
    question_number = 1
    for q in questions:
        question_detail.append({
            "id": q.Question.id,
            "question_number": question_number,
            "title": q.Question.title,
            "body": q.Question.body,
            "is_objective": q.Question.is_objective,
            "answer": q.Question.answer,
            "choice_body": q.Question.choice_body,
            "topic": q.Question.topic,
            "sub_topic": q.Question.sub_topic,
            "baseline_answer": q.Question.baseline_answer
        })
        question_number += 1

    quiz_out = {
        "title": quiz_main.title,  
        "duration": published_quiz.duration, 
        "topic": quiz_main.topic,  
        "sub_topic": quiz_main.sub_topic, 
        "quiz_type": published_quiz.quiz_type,  
        "school_name": school.name,  
        "division_name": grade.name + " " + section.name,  
        "subject_name": subject.name,  
        "questions": question_detail
    }

    new_quiz = PublishedQuiz(
        user_id=current_user.id,
        quiz_detail=quiz_out,
        quiz_type=published_quiz.quiz_type,
        start_time=published_quiz.start_time,
        duration=published_quiz.duration,
        status='published',
        quiz_id=quiz_main.id,
        division_id=division.id,
        school_id=school.id
    )

    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)

    # Teacher task logic: link published quiz to teacher task if task_id is provided
    if task_id != 0:
        teacher_task = db.query(models.TeacherTasks).filter(models.TeacherTasks.id == task_id).first()
        if not teacher_task:
            raise HTTPException(status_code=404, detail=f"Teacher task with id {task_id} not found")
        teacher_task.published_quiz_id = new_quiz.id
        db.commit()
        db.refresh(teacher_task)

    student_details = db.query(models.StudentDivision).filter(models.StudentDivision.division_id == division.id).all()
    student_quiz_data = [{
        "quiz_detail": new_quiz.quiz_detail,
        "response": {},
        "status": "active",
        "student_id": item.student_id,
        "quiz_rel_id": new_quiz.id
    } for item in student_details]

    if student_quiz_data:
        db.execute(insert(StudentQuizResponseRel), student_quiz_data)
        db.commit()

    return {
        "message": "Quiz published successfully",
        "published_quiz_id": new_quiz.id,
        "quiz_id": new_quiz.quiz_id
    } 

