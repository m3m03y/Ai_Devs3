"""Endpoints with task solutions"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from models import Instruction

from solutions.captcha_solver import find_hidden_data
from solutions.robot_dump import verification_process
from solutions.file_fixer import fix_file
from solutions.censorship import get_censored_file
from solutions.recording_analyzer import create_transcriptions, analyse_transcriptions
from solutions.report_processor import report_analysis
from solutions.article_reader import answer_questions
from solutions.keyword_extractor import extract_keywords
from solutions.report_indexer import report_embeddings, get_answer
from solutions.datacenter_finder import run_query, answer_question
from solutions.searcher import find_missing_person
from solutions.grapher import get_shortest_path
from solutions.image_fixer import get_person_description
from solutions.research import prepare_data, classify_data
from solutions.softo import search_answers
from solutions.webhook import get_details, send_webhook_url
from solutions.notes import analyse_notes

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


@solutions_router.get("/task12/create-embeddings")
def create_embeddings_task_12() -> PlainTextResponse:
    """Create embeddings for task 12"""
    report_embeddings()
    return PlainTextResponse("Embeddings created successfully.")


@solutions_router.get("/task12/answer-question")
def complete_task_12(question: str) -> JSONResponse:
    """Solve task 12"""
    answer = get_answer(question)
    if answer is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot get answer based on embeddings.",
        )
    return JSONResponse(content=answer)


@solutions_router.post("/task13/run-query")
def run_query_task_13(query: str) -> JSONResponse:
    """Run query for task 13"""
    response = run_query(query)
    if response is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot run query.",
        )
    return JSONResponse(content=response)


@solutions_router.post("/task13/solution-query")
def solve_task_13(question: str) -> JSONResponse:
    """Solve task 13"""
    response = answer_question(question)
    if response is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot find answer.",
        )
    return JSONResponse(content=response)


@solutions_router.get("/task14/loop")
def solve_task_14(question: str) -> JSONResponse:
    """Solve task 14"""
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question must be provided.",
        )

    response = find_missing_person(question)
    if response is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot find answer.",
        )
    return JSONResponse(content=response)


@solutions_router.get("/task15/shortest_path")
def solve_task_15(
    user_from: str, user_to: str, initialize: bool = False
) -> JSONResponse:
    """Solve task 15"""
    if not (user_from and user_to):
        raise HTTPException(
            status_code=400,
            detail="Both usernames must be provided.",
        )

    shortest_path = get_shortest_path(user_from, user_to, initialize)
    if shortest_path is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot find shortest_path.",
        )
    return JSONResponse(content=shortest_path)


@solutions_router.get("/task16/image-fixer")
def solve_task_16() -> JSONResponse:
    """Solve task 16"""
    result = get_person_description()
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot process images.",
        )
    return JSONResponse(content=result)


@solutions_router.get("/task17/create-jsonl")
def prepare_data_task_17() -> JSONResponse:
    """Prepare data for task 17"""
    result = prepare_data()
    return JSONResponse(content=result)


@solutions_router.get("/task17/classify")
def solve_task_17() -> JSONResponse:
    """Solve task 17"""
    result = classify_data()
    return JSONResponse(content=result)


@solutions_router.get("/task18/search-answers")
def solve_task_18(build_urls: bool = False) -> JSONResponse:
    """Solve task 18"""
    result = search_answers(build_urls)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot find answers.",
        )
    return JSONResponse(content=result)


@solutions_router.post("/task19/webhook")
def webhook_task_19(instruction: Instruction) -> JSONResponse:
    """Api for task 19"""
    result = get_details(instruction)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot find field.",
        )
    return JSONResponse(content=result)


@solutions_router.get("/task19/send-answer")
def solve_task_19(webhook_url: str) -> JSONResponse:
    """Solve task 19"""
    result = send_webhook_url(webhook_url)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Webhook task failed.",
        )
    return JSONResponse(content=result)


@solutions_router.get("/task20/analyse-notes")
def solve_task_20(ai_ocr: bool = False, run_embedding: bool = False) -> JSONResponse:
    """Solve task 20"""
    result = analyse_notes(ai_ocr, run_embedding)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Notes analysis failed.",
        )
    return JSONResponse(content=result)
