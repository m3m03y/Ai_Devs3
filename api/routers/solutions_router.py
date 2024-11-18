"""Endpoints with task solutions"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from solutions.captcha_solver import find_hidden_data
from solutions.robot_dump import verification_process
from solutions.file_fixer import fix_file
from solutions.censorship import get_censored_file
from solutions.recording_analyzer import create_transcriptions, analyse_transcriptions
from solutions.report_processor import report_analysis
from solutions.article_reader import answer_questions
from solutions.keyword_extractor import extract_keywords

solutions_router = APIRouter()


@solutions_router.get("/task1/robot-catcha")
def complete_task_1() -> JSONResponse:
    """Solve task 1"""
    flag, links = find_hidden_data()
    return JSONResponse(content={"flag": flag, "links": links})


@solutions_router.get("/task2/robot-dump")
def complete_task_2() -> JSONResponse:
    """Solve task 2"""
    verification_result = verification_process()
    if verification_result is None:
        raise HTTPException(status_code=400, detail="Verification task failed.")
    return JSONResponse(content=verification_result)


@solutions_router.get("/task3/file-fix")
def complete_task_3() -> JSONResponse:
    """Solve task 3"""
    fixinig_result = fix_file()
    if fixinig_result is None:
        raise HTTPException(status_code=400, detail="Fixing file failed.")
    return JSONResponse(content=fixinig_result)


@solutions_router.get("/task5/censorship")
def complete_task_5() -> JSONResponse:
    """Solve task 5"""
    censorship_result = get_censored_file()
    if censorship_result is None:
        raise HTTPException(status_code=400, detail="Cannot censored file.")
    return JSONResponse(content=censorship_result)


@solutions_router.get("/task6/transcribe")
def complete_task_6() -> JSONResponse:
    """Solve task 6"""
    transcriptions = create_transcriptions()
    if transcriptions is None or len(transcriptions) == 0:
        raise HTTPException(status_code=400, detail="Cannot create transcriptions.")
    analysis_result = analyse_transcriptions(transcriptions)
    return JSONResponse(content=analysis_result)


@solutions_router.get("/task9/report-processor")
def complete_task_9() -> JSONResponse:
    """Solve task 9"""
    analysis_result = report_analysis()
    if analysis_result is None:
        raise HTTPException(status_code=400, detail="Cannot analyze recordings.")
    return JSONResponse(content=analysis_result)


@solutions_router.get("/task10/article-reader")
def complete_task_10() -> JSONResponse:
    """Solve task 10"""
    try:
        answers = answer_questions()
        if answers is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot answer to questions based on article content.",
            )
        return JSONResponse(content=answers)
    except ValueError:
        return JSONResponse(content={"error": "ValueError"})


@solutions_router.get("/task11/extract-keywords")
def complete_task_11() -> JSONResponse:
    """Solve task 11"""
    try:
        keywords_result = extract_keywords()
        if keywords_result is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot extract keywords.",
            )
        return JSONResponse(content=keywords_result)
    except ValueError:
        return JSONResponse(content={"error": "ValueError"})
