from sqlalchemy import func
from dotenv import dotenv_values
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import sessionmaker

from data import variables as vars
from data.settings import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION
from data.models import QuestionType, QuestionSubType, QuestionTypeMapping, Question, Answer, Explanation, Book, Chapter, BookQuestion
from data.models_g import GeneratedQuestionType, GeneratedQuestionSubType
from data.postgre import postgre_engine_answer4all_g_p5 as engine_g
from models.p5_gen_models import P5GenModel
from prompts.p5_gen_prompts import chat_prompt


config = dotenv_values(".env")

model = AzureOpenAI(
    azure_endpoint=config["AZURE_OPENAI_ENDPOINT"],
    api_key=config["AZURE_OPENAI_API_KEY"],
    api_version=config["AZURE_OPENAI_API_VERSION"]
)

llm = AzureChatOpenAI(
    azure_deployment=config["AZURE_OPENAI_MODEL"],
    azure_endpoint=config["AZURE_OPENAI_ENDPOINT"],
    api_key=config["AZURE_OPENAI_API_KEY"],
    api_version=config["AZURE_OPENAI_API_VERSION"],
)

def get_sub_types():
    Session = sessionmaker(bind=engine_g)
    session = Session()
    sub_types = [type[0] for type in session.query(GeneratedQuestionSubType.name_kor).distinct()]
    session.close()
    return sub_types


def get_main_type_from_sub_type(sub_type, lang="eng"):
    Session = sessionmaker(bind=engine_g)
    session = Session()
    if lang == "kor":
        sub_type_obj = session.query(GeneratedQuestionSubType).filter_by(name_kor=sub_type).first()
    else:
        sub_type_obj = session.query(GeneratedQuestionSubType).filter_by(name_eng=sub_type).first()
    main_type_obj = session.query(GeneratedQuestionType).filter_by(id=sub_type_obj.question_type_id).first()
    session.close()
    if lang == "kor":
        return main_type_obj.name_kor
    return main_type_obj.name_eng


def get_main_type_explanation(main_type):
    Session = sessionmaker(bind=engine_g)
    session = Session()
    main_type_obj = session.query(GeneratedQuestionType).filter_by(name_kor=main_type).first()
    session.close()
    return main_type_obj.explanation


def get_sub_type_explanation(sub_type):
    Session = sessionmaker(bind=engine_g)
    session = Session()
    sub_type_obj = session.query(GeneratedQuestionSubType).filter_by(name_kor=sub_type).first()
    session.close()
    return sub_type_obj.explanation


def generate_part5_by_type_and_level(p5_type, p5_sub_type, p5_level):
    human_message = f"""quiz evel: {p5_level}
quiz type: {p5_type} ({vars.part5_type_explanation[p5_type]})
quiz detailed type: {p5_sub_type} ({vars.part5_sub_type_explanation[p5_type][p5_sub_type]})
"""
    runnable = chat_prompt | llm.with_structured_output(schema=P5GenModel)
    response = runnable.invoke({"text": human_message})

    return response.json()


def get_ocr_result_organized(ocr_result):
    completion = model.chat.completions.create(
        model="illunex-ai-gpt4-prompt",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who can organize the OCR result."},
            {"role": "user", "content": f"""
{vars.reconstruct_ocr_result_str}
Here are the texts:
{ocr_result}
"""}
        ]
        )

    return completion.choices[0].message.content


def get_question_type_and_difficulty_level(question_full_text, question_text, answer_no):
    completion = model.chat.completions.create(
        model="illunex-ai-gpt4-prompt",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who can classify the type and difficulty level of Part5 questions in TOEIC."},
            {"role": "user", "content": f"This is the factors that influence the difficulty level of questions of Part5 in TOEIC. {vars.part5_level_str1} {vars.part5_level_str2}"},
            {"role": "user", "content": f"""
1. Classify the type and difficulty level(5-Point Scale (1,2,3,4,5)) for this question.
Make sure to choose the type only from the following list. {vars.part5_sub_type_str}
Sometimes it is possible to have more than two types for one question.
2. Please slightly change proper nouns like company name, one's name, etc. in the question sentence, '{question_text}' , in order to avoid copyright issues.
The difficulty level, the structure of sentence, the location of missing part(------) and the type of question must be maintained as well as the gender of a person, the field of industry, etc.
3. Translate 'altered_text' into Korean considering the correct answer is {answer_no}.
4. Explain in Korean why choice ({answer_no}) should be correct in detail with grammatic or contextual reasons.
5. Please present them in a JSON format.
Given the question, 'Please congratulate Alan Schmit, ------- of the Leadership Award in Nursing at Knoll Hospital. (A) winner (B) won (C) winning (D) wins',
the output should be similar to the following:
"question_type": ['문제 유형', ...] (리스트 형태로),
"difficulty_level": 난이도 (1, 2, 3, 4, 5 중 하나)),
"altered_text": '저작권을 피하기 위해, 고유명사 등이 변경된 파트5 문제 영어 지문.(선택지는 제외해 주세요)'
"translation": 'altered_text의 한국말 번역 (정답을 빈칸에 적용했을때의 문장을 기준으로 해 주세요)',
"explanation": 'altered_text에 기존 선택지 정답 번호가 답이 되어야 하는 이유와 나머지는 오답인 이유를 문법적 혹은 문맥적으로 설명해 주세요.'
just show me only the json file. Here is the question and choices:
{question_full_text}"""}
        ]
    )

    return completion.choices[0].message.content


def add_book(session, book_name, publisher_name, publication_year):
    # 책이 이미 등록되어 있는지 확인
    book = session.query(Book).filter_by(name=book_name).first()

    # 책이 없으면 새로 추가
    if not book:
        book = Book(name=book_name, publisher=publisher_name, publication_year=publication_year)
        session.add(book)
        session.flush()  # ID 생성

    return book


def add_chapter(session, book, chapter_name):
    # 챕터가 이미 등록되어 있는지 확인
    chapter = session.query(Chapter).filter_by(name=chapter_name, book_id=book.id).first()

    # 챕터가 없으면 새로 추가
    if not chapter:
        chapter = Chapter(name=chapter_name, book_id=book.id)
        session.add(chapter)
        session.flush()  # ID 생성

    return chapter


def add_question_type(session, question_type_name):
    """문제 유형을 추가하거나 찾는 함수"""
    sub_type_obj = session.query(QuestionSubType).filter(func.lower(QuestionSubType.name_eng) == func.lower(question_type_name)).first()

    # sub_type_obj가 None인지 확인
    if sub_type_obj is None:
        print(f"Warning: Unknown question type {question_type_name}")
        return None, None

    main_type_obj = session.query(QuestionType).filter_by(id=sub_type_obj.question_type_id).first()

    if main_type_obj is None:
        print(f"Warning: No main question type found for {question_type_name}")
        return None, None

    return main_type_obj, sub_type_obj


def add_question_type_mapping(session, question, question_type, question_sub_type):
    """문제 유형 매핑을 추가하는 함수"""
    mapping = QuestionTypeMapping(question=question, question_type=question_type, question_subtype=question_sub_type)
    session.add(mapping)


def add_question(session, question_text, altered_text, difficulty_level, translation, correct_answer):
    """문제를 추가하는 함수"""
    question = Question(text=question_text, altered_text=altered_text, difficulty_level=difficulty_level, correct_answer_id=correct_answer, translation=translation)
    session.add(question)
    session.flush()  # ID 생성
    return question


def add_answer(session, question_id, text):
    """답안을 추가하는 함수"""
    answer = Answer(question_id=question_id, text=text)
    session.add(answer)
    session.flush()  # ID 생성
    return answer


def add_book_question(session, page_number, question_number, question, chapter):
    """책에서의 문제 위치 정보를 추가하는 함수"""
    book_question = BookQuestion(page_number=page_number, question_number=question_number, question_id=question.id, chapter_id=chapter.id)
    session.add(book_question)
    session.flush()  # ID 생성
    return book_question


def add_explanation(session, text, answer_id):
    explanation = Explanation(text=text, answer_id=answer_id)
    session.add(explanation)
    return explanation


def get_all_books(Session):
    session = Session()
    books = session.query(Book).all()
    return [(book.name, book.publisher, book.publication_year) for book in books]


def get_all_chapters(Session, book_name):
    session = Session()
    book = session.query(Book).filter_by(name=book_name[0]).first()  # Use only the book's name
    chapters = session.query(Chapter).filter_by(book_id=book.id).all()
    return [chapter.name for chapter in chapters]


def get_book(session, book_name):
    return session.query(Book).filter_by(name=book_name[0]).first()


def get_chapter(session, book, chapter_name):
    return session.query(Chapter).filter_by(name=chapter_name, book_id=book.id).first()


def parse_question_types(part5_type_str):
    part5_types = part5_type_str.strip().split('\n\n')
    question_types = {}
    for part in part5_types:
        main_type, *sub_types = part.split('\n')
        main_type = main_type.strip(":")
        sub_types = [subtype.split(". ")[1] for subtype in sub_types]
        question_types[main_type] = sub_types
    return question_types


def parse_question_types_dual_language(part5_type_str_eng, part5_type_str_kor):
    question_types_eng = parse_question_types(part5_type_str_eng)
    question_types_kor = parse_question_types(part5_type_str_kor)

    dual_language_question_types = {}

    for main_type_eng, sub_types_eng in question_types_eng.items():
        main_type_kor = next(iter(question_types_kor))
        sub_types_kor = question_types_kor.pop(main_type_kor)

        dual_language_question_types[(main_type_eng, main_type_kor)] = list(zip(sub_types_eng, sub_types_kor))

    return dual_language_question_types
