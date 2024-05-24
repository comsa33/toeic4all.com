from random import shuffle
from collections import defaultdict
from datetime import datetime, timedelta
import re

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc, Date, Integer
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import GeneratedQuestionType, GeneratedQuestionSubType, GeneratedQuestion, GeneratedAnswer, GeneratedVocabulary
from app.models import QuestionReport, MyQuestions, UserTestDetail, UserTestQuestionsDetail, UserVocabulary
from app import db


api = Blueprint('api', __name__)


@api.route('/question_types', methods=['GET'])
@jwt_required(optional=True)
def get_question_types():
    # Fetch all question types
    question_types = GeneratedQuestionType.query.all()

    result = []
    for question_type in question_types:
        # Format each question type and add it to the result
        formatted_question_type = {
            'Id': question_type.id,
            'NameKor': question_type.name_kor,
            'Explanation': question_type.explanation
        }
        result.append(formatted_question_type)

    return jsonify(result)


def create_formatted_question(question):
    # 레벨에 따른 권장 시간 매핑
    recommended_times = {
        1: 10,
        2: 15,
        3: 20,
        4: 25,
        5: 30
    }

    answers = GeneratedAnswer.query.filter(GeneratedAnswer.question_id == question.id).all()
    vocabularies = GeneratedVocabulary.query.filter(GeneratedVocabulary.question_id == question.id).all()
    question_type = GeneratedQuestionType.query.get(question.question_type_id)
    question_sub_type = GeneratedQuestionSubType.query.get(question.question_sub_type_id)

    formatted_question = {
        'QuestionId': question.id,
        'QuestionText': question.question_text,
        'QuestionTypeId': question_type.id,
        'QuestionType': question_type.name_kor,
        'QuestionSubTypeId': question_sub_type.id,
        'QuestionSubType': question_sub_type.name_kor,
        'QuestionLevel': question.question_level,
        'RecommendedTime': recommended_times.get(question.question_level, 0),
        'Translation': question.translation,
        'Explanation': question.explanation,
        'Vocabulary': [{'Word': v.word, 'Translation': v.translation, 'POS': v.part_of_speech, 'Explanation': v.explanation, 'Example': v.example, 'ExampleTranslation': v.example_translation} for v in vocabularies],
        'Choices': [a.text for a in answers],
        'CorrectAnswer': next((a.text for a in answers if a.is_correct), None)
    }

    return formatted_question


@api.route('/questions', methods=['GET'])
@jwt_required()
def get_questions():
    type_id = request.args.get('typeId')
    level = request.args.get('level')
    num_questions = request.args.get('num_questions', default=30, type=int)

    if type_id:
        question_types = [GeneratedQuestionType.query.get(type_id)]
    else:
        question_types = GeneratedQuestionType.query.all()

    questions_per_type = num_questions // len(question_types)
    remaining_questions = num_questions % len(question_types)

    result = []
    used_questions = set()  # 이 집합에 이미 사용된 문제의 ID를 저장합니다.
    for question_type in question_types:
        questions_query = GeneratedQuestion.query.filter_by(question_type_id=question_type.id)
        if level:
            questions_query = questions_query.filter(GeneratedQuestion.question_level == level)
        questions = questions_query.order_by(func.random()).limit(questions_per_type).all()

        for question in questions:
            used_questions.add(question.id)  # 문제 ID를 사용된 문제 ID 집합에 추가합니다.
            formatted_question = create_formatted_question(question)
            result.append(formatted_question)

    remaining_question_types = list(question_types)
    while remaining_questions > 0:
        shuffle(remaining_question_types)
        for question_type in remaining_question_types:
            if remaining_questions <= 0:
                break
            question_query = GeneratedQuestion.query.filter_by(question_type_id=question_type.id)
            if level:
                question_query = question_query.filter(GeneratedQuestion.question_level == level)
            question = question_query.filter(GeneratedQuestion.id.notin_(used_questions)).order_by(func.random()).first()
            if question is None:
                continue
            used_questions.add(question.id)  # 문제 ID를 사용된 문제 ID 집합에 추가합니다.
            formatted_question = create_formatted_question(question)
            result.append(formatted_question)
            remaining_questions -= 1

    return jsonify(result)


# 문제를 리포트하는 API
@api.route('/report/question', methods=['POST'])
@jwt_required()
def report_question():
    question_id = request.json.get('question_id')
    report_content = request.json.get('report_content')
    report_type = request.json.get('report_type')  # New field

    user_id = get_jwt_identity()  # Get user ID from JWT token

    # Validate inputs
    if not all([question_id, report_content, report_type]):
        return jsonify({"error": "Question ID, report content, and report type are required"}), 400

    # Create new report
    new_report = QuestionReport(question_id=question_id, user_id=user_id, report_content=report_content, report_type=report_type)

    # Save to database
    db.session.add(new_report)
    db.session.commit()

    return jsonify({"message": "Report has been sent successfully", "report_id": new_report.id}), 201


@api.route('/favourite/question', methods=['POST'])
@jwt_required()
def add_to_favourites():
    question_id = request.json.get('question_id')
    username = get_jwt_identity()  # Get username from JWT token

    # Validate input
    if not question_id:
        return jsonify({"error": "Question ID is required"}), 400

    # Check if the question is already added
    existing_entry = MyQuestions.query.filter_by(username=username, question_id=question_id).first()
    if existing_entry:
        return jsonify({"error": "This question is already added to your favourites"}), 409

    # Add the question to the user's favourites
    new_favourite = MyQuestions(username=username, question_id=question_id)

    # Save to database
    db.session.add(new_favourite)
    db.session.commit()

    return jsonify({"message": "Question has been added to your favourites", "favourite_id": new_favourite.id}), 201


@api.route('/favourite/question', methods=['DELETE'])
@jwt_required()
def remove_from_favourites():
    question_id = request.json.get('question_id')
    username = get_jwt_identity()  # Get username from JWT token

    # Validate input
    if not question_id:
        return jsonify({"error": "Question ID is required"}), 400

    # Check if the question is in the user's favourites
    favourite_entry = MyQuestions.query.filter_by(username=username, question_id=question_id).first()
    if not favourite_entry:
        return jsonify({"error": "This question is not in your favourites"}), 404

    # Remove the question from the user's favourites
    db.session.delete(favourite_entry)
    db.session.commit()

    return jsonify({"message": "Question has been removed from your favourites"}), 200


# Get favourite status API
@api.route('/get_favourite_status', methods=['GET'])
@jwt_required()
def get_favourite_status():
    username = get_jwt_identity()  # Get user ID from JWT token
    question_id = request.args.get('question_id')

    # Check if the question is in the user's favourites
    favourite = MyQuestions.query.filter_by(username=username, question_id=question_id).first()

    if favourite is not None:
        return jsonify({"status": "favourite"}), 200
    else:
        return jsonify({"status": "not favourite"}), 200


def fetch_questions_by_ids(question_ids):
    # fetch questions from the database by their ids
    questions_data = db.session.query(
        GeneratedQuestion, GeneratedQuestionType, GeneratedQuestionSubType
    ).filter(
        GeneratedQuestion.id.in_(question_ids),
        GeneratedQuestion.question_type_id == GeneratedQuestionType.id,
        GeneratedQuestion.question_sub_type_id == GeneratedQuestionSubType.id,
    ).all()

    vocabularies_data = db.session.query(
        GeneratedVocabulary
    ).filter(
        GeneratedVocabulary.question_id.in_(question_ids)
    ).all()

    answers_data = db.session.query(
        GeneratedAnswer
    ).filter(
        GeneratedAnswer.question_id.in_(question_ids)
    ).all()

    vocabularies_dict = defaultdict(list)
    answers_dict = defaultdict(list)
    correct_answers_dict = {}

    for v in vocabularies_data:
        vocabularies_dict[v.question_id].append({"Word": v.word, "Translation": v.translation, 'POS': v.part_of_speech, 'Explanation': v.explanation, 'Example': v.example, 'ExampleTranslation': v.example_translation})

    for a in answers_data:
        answers_dict[a.question_id].append(a.text)
        if a.is_correct:
            correct_answers_dict[a.question_id] = a.text

    # convert questions to dictionary
    questions_dict = [{
        "QuestionId": data.GeneratedQuestion.id,
        "QuestionText": data.GeneratedQuestion.question_text,
        "QuestionTypeId": data.GeneratedQuestionType.id,
        "QuestionType": data.GeneratedQuestionType.name_kor,
        "QuestionSubTypeId": data.GeneratedQuestionSubType.id,
        "QuestionSubType": data.GeneratedQuestionSubType.name_kor,
        "QuestionLevel": data.GeneratedQuestion.question_level,
        "Translation": data.GeneratedQuestion.translation,
        "Explanation": data.GeneratedQuestion.explanation,
        "Vocabularies": vocabularies_dict.get(data.GeneratedQuestion.id, []),
        "Choices": answers_dict.get(data.GeneratedQuestion.id, []),
        "CorrectAnswer": correct_answers_dict.get(data.GeneratedQuestion.id)
    } for data in questions_data]

    return questions_dict


# Get favourite questions for a user
@api.route('/favourite_questions', methods=['GET'])
@jwt_required()
def get_favourite_questions():
    username = get_jwt_identity()  # Get username from JWT token
    favourite_questions = MyQuestions.query.filter_by(username=username).all()
    question_ids = [favourite.question_id for favourite in favourite_questions]
    questions = fetch_questions_by_ids(question_ids)
    return jsonify(questions)


@api.route('/test-question-detail', methods=['POST'])
@jwt_required()
def add_test_question_detail():
    username = get_jwt_identity()  # Get username from JWT token
    question_details = request.json.get('question_details')

    # Validate input
    for detail in question_details:
        if not detail.get('test_id') or not detail.get('question_id') or detail.get('is_correct') is None or not detail.get('time_record_per_question'):
            return jsonify({"error": "Test ID, Question ID, correctness and time record are required"}), 400

        # Check if the entry already exists
        existing_entry = UserTestQuestionsDetail.query.filter_by(
            username=username,
            question_id=detail.get('question_id'),
            test_id=detail.get('test_id')
            ).first()
        if existing_entry:
            return jsonify({"error": "This entry already exists"}), 400

        # Add the question detail to the database
        new_question_detail = UserTestQuestionsDetail(
            username=username,
            test_id=detail.get('test_id'),
            question_id=detail.get('question_id'),
            is_correct=detail.get('is_correct'),
            time_record_per_question=detail.get('time_record_per_question')
            )

        # Save to database
        db.session.add(new_question_detail)

    db.session.commit()

    return jsonify({"message": "Test question details have been added"}), 201


@api.route('/user-test-detail', methods=['POST'])
@jwt_required()
def save_user_test_detail():
    data = request.get_json()
    username = get_jwt_identity()  # Get username from JWT token
    test_id = data.get('test_id')
    test_type = data.get('test_type')
    test_level = data.get('test_level')
    question_count = data.get('question_count')
    time_record = data.get('time_record')

    # Validate input
    if not all([test_id, test_type, test_level, question_count, time_record]):
        return jsonify({"error": "All fields are required"}), 400

    # Create the record
    new_record = UserTestDetail(
        username=username,
        test_id=test_id,
        test_type=test_type,
        test_level=test_level,
        question_count=question_count,
        time_record=time_record,
    )

    # Save to database
    db.session.add(new_record)
    db.session.commit()

    return jsonify({"message": "Test detail has been saved", "test_detail_id": new_record.id}), 201


def serialize_user_test_detail(test):
    """Return object data in easily serializable format"""
    wrong_count = UserTestQuestionsDetail.query.filter_by(test_id=test.id, is_correct=False).count()

    return {
        'id': test.id,
        'username': test.username,
        'test_id': test.test_id,
        'test_type': test.test_type,
        'test_level': test.test_level,
        'question_count': test.question_count,
        'wrong_count': wrong_count,
        'time_record': test.time_record,
        'created_at': test.created_at.isoformat() if test.created_at else None,
    }


@api.route('/my-note/tests', methods=['GET'])
@jwt_required()
def get_user_tests():
    username = get_jwt_identity()
    page = request.args.get('page', default=1, type=int)

    pagination = db.session.query(UserTestDetail)\
        .filter(UserTestDetail.username == username)\
        .order_by(desc(UserTestDetail.created_at))\
        .paginate(page=page, per_page=30, error_out=False)

    tests = pagination.items

    return jsonify({"tests": [serialize_user_test_detail(test) for test in tests]}), 200


@api.route('/my-note/tests/<int:test_id>/wrong-questions', methods=['GET'])
@jwt_required()
def get_wrong_questions_for_test(test_id):
    username = get_jwt_identity()

    # UserTestQuestionsDetail 테이블에서 사용자의 테스트에 대한 문제 세부 정보를 불러옵니다.
    user_question_details = UserTestQuestionsDetail.query.filter_by(test_id=test_id, username=username).all()

    # is_correct가 False인 문제들만 뽑아냅니다.
    wrong_question_ids = [detail.question_id for detail in user_question_details if not detail.is_correct]
    questions = fetch_questions_by_ids(wrong_question_ids)

    return jsonify(questions), 200


# 사용자 분석 API
@api.route('/performance/question-type', methods=['GET'])
@jwt_required()
def get_performance_question_type():
    username = get_jwt_identity()

    # 질문 유형에 따른 사용자의 정답률을 계산합니다.
    results = db.session.query(
        GeneratedQuestionType.name_kor,
        db.func.avg(db.case((UserTestQuestionsDetail.is_correct == True, 1), else_=0)).label('accuracy')
    ).join(
        UserTestDetail, UserTestDetail.id == UserTestQuestionsDetail.test_id
    ).join(
        GeneratedQuestion, GeneratedQuestion.id == UserTestQuestionsDetail.question_id
    ).join(
        GeneratedQuestionType, GeneratedQuestionType.id == GeneratedQuestion.question_type_id
    ).filter(
        UserTestDetail.username == username
    ).group_by(
        GeneratedQuestionType.name_kor
    ).all()

    # 쿼리 결과를 사전으로 변환
    results = [{"question_type": row.name_kor, "accuracy": row.accuracy} for row in results]

    return jsonify({"results": results}), 200


@api.route('/performance/question-subtype', methods=['GET'])
@jwt_required()
def get_performance_question_subtype():
    username = get_jwt_identity()

    # 주 유형에 따른 세부 유형의 틀린 문제의 개수와 문제 풀이에 걸린 평균 시간을 동시에 계산합니다.
    results = db.session.query(
        GeneratedQuestionType.name_kor.label('question_type'),
        GeneratedQuestionSubType.name_kor,
        db.func.count(db.case((UserTestQuestionsDetail.is_correct == False, UserTestQuestionsDetail.id), else_=None)).label('wrong_count'),
        db.func.avg(UserTestQuestionsDetail.time_record_per_question).label('average_time')
    ).join(
        UserTestDetail, UserTestDetail.id == UserTestQuestionsDetail.test_id
    ).join(
        GeneratedQuestion, GeneratedQuestion.id == UserTestQuestionsDetail.question_id
    ).join(
        GeneratedQuestionSubType, GeneratedQuestionSubType.id == GeneratedQuestion.question_sub_type_id
    ).join(
        GeneratedQuestionType, GeneratedQuestionType.id == GeneratedQuestionSubType.question_type_id
    ).filter(
        UserTestDetail.username == username
    ).group_by(
        GeneratedQuestionType.name_kor,
        GeneratedQuestionSubType.name_kor
    ).all()

    # 쿼리 결과를 사전으로 변환
    results_dict = {}
    for row in results:
        if row.question_type not in results_dict:
            results_dict[row.question_type] = []
        results_dict[row.question_type].append({
            "question_subtype": row.name_kor, 
            "average_time": row.average_time, 
            "wrong_count": row.wrong_count
        })

    return jsonify(results_dict), 200


@api.route('/performance/question-level', methods=['GET'])
@jwt_required()
def get_performance_question_level():
    username = get_jwt_identity()

    # question_level로 그룹화하고, 각 그룹별 정답률과 평균 소요 시간을 계산합니다.
    results = db.session.query(
        GeneratedQuestion.question_level,
        db.func.avg(db.case((UserTestQuestionsDetail.is_correct == True, 1), else_=0)).label('accuracy'),
        db.func.avg(UserTestQuestionsDetail.time_record_per_question).label('average_time')
    ).join(
        GeneratedQuestion, UserTestQuestionsDetail.question_id == GeneratedQuestion.id
    ).filter(
        UserTestQuestionsDetail.username == username
    ).group_by(
        GeneratedQuestion.question_level
    ).all()

    # 쿼리 결과를 사전으로 변환
    results = [{"question_level": row.question_level, "accuracy": row.accuracy, "average_time": row.average_time} for row in results]

    return jsonify({"results": results}), 200


@api.route('/performance/time-spent', methods=['GET'])
@jwt_required()
def get_performance_time_spent():
    username = get_jwt_identity()

    # 각 문제 유형에 대한 사용자의 평균 소요 시간을 계산합니다.
    results = db.session.query(
        GeneratedQuestionType.name_kor,
        db.func.avg(UserTestQuestionsDetail.time_record_per_question).label('average_time')
    ).join(
        GeneratedQuestion, UserTestQuestionsDetail.question_id == GeneratedQuestion.id
    ).join(
        GeneratedQuestionType, GeneratedQuestion.question_type_id == GeneratedQuestionType.id
    ).filter(
        UserTestQuestionsDetail.username == username
    ).group_by(
        GeneratedQuestionType.name_kor
    ).all()

    # 쿼리 결과를 사전으로 변환
    results = [{"question_type": row.name_kor, "average_time": row.average_time} for row in results]

    return jsonify({"results": results}), 200


# 기본 페이지 크기를 정의합니다.
DEFAULT_PAGE_SIZE = 10


@api.route('/growth', methods=['GET'])
@jwt_required()
def get_growth():
    username = get_jwt_identity()

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=DEFAULT_PAGE_SIZE, type=int)

    # 시간에 따른 사용자의 정답률을 계산합니다.
    results = db.session.query(
        UserTestDetail.test_id,
        db.func.max(UserTestDetail.created_at).label('latest_created_at'),
        db.func.avg(db.case((UserTestQuestionsDetail.is_correct == True, 1), else_=0)).label('accuracy')
    ).join(
        UserTestQuestionsDetail, UserTestDetail.id == UserTestQuestionsDetail.test_id
    ).filter(
        UserTestDetail.username == username
    ).group_by(
        UserTestDetail.test_id
    ).order_by(
        db.func.max(UserTestDetail.created_at)
    ).limit(per_page).offset((page - 1) * per_page).all()  # Use 'limit' and 'offset' for paging

    # 쿼리 결과를 사전으로 변환
    results = [{"created_at": row.latest_created_at, "accuracy": row.accuracy} for row in results]

    return jsonify({"results": results}), 200


@api.route('/performance/daily', methods=['GET'])
@jwt_required()
def get_daily_performance():
    username = get_jwt_identity()

    # 일자별로 사용자의 테스트 수를 집계합니다.
    results = db.session.query(
        func.count(UserTestDetail.id).label('test_count'),
        func.cast(UserTestDetail.created_at, Date).label('date')
    ).filter(
        UserTestDetail.username == username
    ).group_by(
        func.cast(UserTestDetail.created_at, Date)
    ).all()

    # 쿼리 결과를 사전으로 변환
    results = [{"date": row.date.isoformat(), "test_count": row.test_count} for row in results]

    return jsonify({"results": results}), 200


# 랭킹 API
@api.route('/ranking', defaults={'question_type': None}, methods=['GET'])
@api.route('/ranking/<int:question_type>', methods=['GET'])
def get_user_ranking(question_type):
    activity_weight = 0.5
    difficulty_weight = 0.5

    query = db.session.query(
        UserTestDetail.username.label('username'),
        (func.sum(func.cast(UserTestQuestionsDetail.is_correct, Integer)) / func.count(UserTestQuestionsDetail.id)).label('accuracy_score'),
        func.count(UserTestQuestionsDetail.id).label('activity_score'),
        func.avg(GeneratedQuestion.question_level).label('difficulty_score')
    ).join(
        UserTestDetail, UserTestDetail.id == UserTestQuestionsDetail.test_id
    ).join(
        GeneratedQuestion, GeneratedQuestion.id == UserTestQuestionsDetail.question_id
    )

    if question_type is not None:
        query = query.filter(GeneratedQuestion.question_type_id == question_type)

    query = query.group_by(UserTestDetail.username)

    ranking = [user._asdict() for user in query.all()]

    def normalize(value, min_val, max_val):
        # 분모가 0인 경우 처리
        if max_val - min_val == 0:
            return 1  # 모든 점수가 같다면 1을 반환하여 모든 사용자가 같은 점수를 받도록 처리
        else:
            return (value - min_val) / (max_val - min_val)

    min_activity_score = min([user['activity_score'] for user in ranking])
    max_activity_score = max([user['activity_score'] for user in ranking])

    min_difficulty_score = min([user['difficulty_score'] for user in ranking])
    max_difficulty_score = max([user['difficulty_score'] for user in ranking])

    for i in range(len(ranking)):
        user = ranking[i]

        # Normalize activity_score and difficulty_score
        user['activity_score'] = normalize(user['activity_score'], min_activity_score, max_activity_score)
        user['difficulty_score'] = normalize(user['difficulty_score'], min_difficulty_score, max_difficulty_score)

        user['final_score'] = (float(user['accuracy_score']) *
                               (user['activity_score'] * activity_weight +
                                float(user['difficulty_score']) * difficulty_weight))
        ranking[i] = user

    ranking.sort(key=lambda x: x['final_score'], reverse=True)

    return jsonify(ranking)


# TOEIC 시험 일정을 크롤링합니다.
@api.route('/toeic-info', methods=['GET'])
def get_toeic_info():
    url = "https://exam.toeic.co.kr/receipt/examSchList.php"

    now = datetime.now() + timedelta(hours=9)  # Add 9 hours to current time

    try:
        response = requests.get(url)
        html = response.text
    except Exception as e:
        return jsonify({'error': 'Failed to get TOEIC schedule', 'details': str(e)}), 500

    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('table tr')

    results = []

    for row in rows:
        columns = row.select('td')
        if len(columns) > 2:
            try:
                # 회차에서 숫자만 추출
                exam_number = re.search(r'\d+', columns[0].get_text()).group()
                # 시험일시에서 날짜와 시간 추출
                exam_date_time = re.search(r'\d{4}\.\d{2}\.\d{2}.+\d{1,2}시\d{1,2}분', columns[1].get_text()).group()
            except Exception as e:
                return jsonify({'error': 'Failed to parse TOEIC schedule information', 'details': str(e)}), 500

            try:
                # 시간 정보를 정규화합니다 (예: "오전 9시20분" -> "09:20")
                time_info = re.search(r'(\d{1,2})시(\d{1,2})분', exam_date_time)
                hour = int(time_info.group(1))
                minute = int(time_info.group(2))
                if '오후' in exam_date_time and hour < 12:
                    hour += 12
                # 날짜와 시간 정보를 datetime 객체로 변환합니다.
                date_info = re.search(r'\d{4}\.\d{2}\.\d{2}', exam_date_time).group()
                formatted_date_time = datetime.strptime(date_info, '%Y.%m.%d').replace(hour=hour, minute=minute)
                # 딕셔너리에 담아 리스트에 추가
                if formatted_date_time > now:  # 시험 일정이 현재 시간 이후인 경우만 결과에 추가합니다.
                    results.append({
                        "toeic_test_no": exam_number,
                        "toeic_test_datetime": formatted_date_time.isoformat()
                    })

            except Exception as e:
                return jsonify({'error': 'Failed to normalize TOEIC schedule information', 'details': str(e)}), 500

    return jsonify({"results": results}), 200


# 어휘 테스트 관련 API
@api.route('/vocabularies', methods=['GET'])
def get_vocabularies():
    page = request.args.get('page', 1, type=int)
    vocabularies = GeneratedVocabulary.query.order_by(func.random()).paginate(page=page, per_page=5, error_out=False).items

    data = []
    for vocab in vocabularies:
        wrong_answers = GeneratedVocabulary.query.filter(GeneratedVocabulary.id != vocab.id).order_by(func.random()).limit(3).all()
        data.append({
            'id': vocab.id,
            'word': vocab.word,
            'part_of_speech': vocab.part_of_speech,
            'translation': vocab.translation,
            'explanation': vocab.explanation,
            'question_id': vocab.question_id,
            'wrong_translations': [wrong.translation for wrong in wrong_answers]
        })

    return {'vocabularies': data}, 200


@api.route('/user_vocabularies', methods=['GET'])
@jwt_required()
def get_user_vocabularies():
    username = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    only_wrong = request.args.get('only_wrong', 'false') == 'true'

    query = db.session.query(
        UserVocabulary.word_id, UserVocabulary.wrong_count,
        GeneratedVocabulary.word, GeneratedVocabulary.translation, GeneratedVocabulary.question_id, GeneratedVocabulary.explanation, GeneratedVocabulary.part_of_speech
    ).join(
        GeneratedVocabulary, UserVocabulary.word_id == GeneratedVocabulary.id
    ).filter(
        UserVocabulary.username == username
    )

    if only_wrong:
        query = query.filter(UserVocabulary.wrong_count > 0)

    results = query.paginate(page=page, per_page=per_page, error_out=False)

    question_ids = [row.question_id for row in results.items]
    questions_info = fetch_questions_by_ids(question_ids)

    data = [
        {
            'word_id': row.word_id,
            'wrong_count': row.wrong_count,
            'word': row.word,
            'part_of_speech': row.part_of_speech,  # Added 'part_of_speech' field
            'translation': row.translation,
            'explanation': row.explanation,
            'question_id': row.question_id,
            'question_info': next((question for question in questions_info if question["QuestionId"] == row.question_id), None)
        } for row in results.items
    ]

    return {
        'user_vocabularies': data,
        'total_pages': results.pages,
        'current_page': page
    }, 200


@api.route('/user_vocabularies', methods=['POST'])
@jwt_required()
def add_to_user_vocabularies():
    username = get_jwt_identity()
    data = request.get_json()

    word_id = data.get('word_id')
    wrong_count = data.get('wrong_count')

    user_vocabulary = UserVocabulary.query.filter_by(username=username, word_id=word_id).first()

    if user_vocabulary:
        user_vocabulary.wrong_count += wrong_count
    else:
        user_vocabulary = UserVocabulary(username=username, word_id=word_id, wrong_count=wrong_count)
        db.session.add(user_vocabulary)

    db.session.commit()

    return {'message': 'User vocabulary updated successfully.'}, 200
