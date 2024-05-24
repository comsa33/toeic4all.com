import re
import json
import datetime
import traceback
from collections import defaultdict

from icecream import ic
import streamlit as st
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from random import sample
from sqlalchemy import and_
from sqlalchemy import func as sql_func
from stqdm import stqdm

from data.postgre import postgre_engine_answer4all as engine
from data.postgre import postgre_engine_answer4all_g_p5 as engine_g
from data.models import Book, QuestionType, QuestionSubType, QuestionTypeMapping, Question, Answer, Explanation, Chapter, BookQuestion, Base
from data.models_g import GeneratedQuestionType, GeneratedQuestionSubType, GeneratedQuestion, GeneratedAnswer, GeneratedVocabulary, Base as Base_g
from core import functions as func
from data import variables as vars


Base.metadata.create_all(engine)
Base_g.metadata.create_all(engine_g)


def register_types():
    if st.button('문제 유형 등록하기'):
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            dual_language_question_types = func.parse_question_types_dual_language(vars.part5_type_str, vars.part5_type_str_kor)
            for (main_type_eng, main_type_kor), sub_types_dual in dual_language_question_types.items():
                # Check if the main question type already exists
                main_type_obj = session.query(QuestionType).filter_by(name_eng=main_type_eng).first()
                # If it doesn't exist, create a new one
                if not main_type_obj:
                    main_type_obj = QuestionType(
                        name_eng=main_type_eng,
                        name_kor=main_type_kor,
                        explanation=vars.part5_type_explanation_kor[main_type_kor]  # Add explanation here
                    )
                else:  # If it exists, update it
                    main_type_obj.name_kor = main_type_kor
                    main_type_obj.explanation = vars.part5_type_explanation_kor[main_type_kor]
                session.add(main_type_obj)
                session.commit()  # Ensure that main_type_obj gets an ID

                for sub_type_eng, sub_type_kor in sub_types_dual:
                    # Check if the sub question type already exists
                    sub_type_obj = session.query(QuestionSubType).filter_by(name_eng=sub_type_eng).first()
                    # If it doesn't exist, create a new one
                    if not sub_type_obj:
                        sub_type_obj = QuestionSubType(
                            name_eng=sub_type_eng,
                            name_kor=sub_type_kor,
                            explanation=vars.part5_sub_type_explanation_kor[main_type_kor][sub_type_kor],  # Add explanation here
                            question_type_id=main_type_obj.id
                        )
                    else:  # If it exists, update it
                        sub_type_obj.name_kor = sub_type_kor
                        sub_type_obj.explanation = vars.part5_sub_type_explanation_kor[main_type_kor][sub_type_kor]
                        sub_type_obj.question_type_id = main_type_obj.id
                    session.add(sub_type_obj)
                session.commit()
            st.success("문제 유형이 성공적으로 등록되었습니다.")
        except Exception as e:
            st.error(f"Error occurred: {e}")


def register_types_g():
    if st.button('문제 유형[파트5 문제 생성 테이블] 등록하기'):
        try:
            Session = sessionmaker(bind=engine_g)
            session = Session()

            dual_language_question_types = func.parse_question_types_dual_language(vars.part5_type_str, vars.part5_type_str_kor)
            for (main_type_eng, main_type_kor), sub_types_dual in dual_language_question_types.items():
                # Check if the main question type already exists
                main_type_obj = session.query(GeneratedQuestionType).filter_by(name_eng=main_type_eng).first()
                # If it doesn't exist, create a new one
                if not main_type_obj:
                    main_type_obj = GeneratedQuestionType(
                        name_eng=main_type_eng,
                        name_kor=main_type_kor,
                        explanation=vars.part5_type_explanation_kor[main_type_kor]  # Add explanation here
                    )
                else:  # If it exists, update it
                    main_type_obj.name_kor = main_type_kor
                    main_type_obj.explanation = vars.part5_type_explanation_kor[main_type_kor]
                session.add(main_type_obj)
                session.commit()  # Ensure that main_type_obj gets an ID

                for sub_type_eng, sub_type_kor in sub_types_dual:
                    # Check if the sub question type already exists
                    sub_type_obj = session.query(GeneratedQuestionSubType).filter_by(name_eng=sub_type_eng).first()
                    # If it doesn't exist, create a new one
                    if not sub_type_obj:
                        sub_type_obj = GeneratedQuestionSubType(
                            name_eng=sub_type_eng,
                            name_kor=sub_type_kor,
                            explanation=vars.part5_sub_type_explanation_kor[main_type_kor][sub_type_kor],  # Add explanation here
                            question_type_id=main_type_obj.id
                        )
                    else:  # If it exists, update it
                        sub_type_obj.name_kor = sub_type_kor
                        sub_type_obj.explanation = vars.part5_sub_type_explanation_kor[main_type_kor][sub_type_kor]
                        sub_type_obj.question_type_id = main_type_obj.id
                    session.add(sub_type_obj)
                session.commit()
            st.success("문제 유형이 성공적으로 등록되었습니다.")
        except Exception as e:
            st.error(f"Error occurred: {e}")


def register_books():
    Session = sessionmaker(bind=engine)

    st.title('문제집 등록')

    # 사용자 입력 받기
    book_name = st.text_input('문제집 이름 입력')
    publisher_name = st.text_input('출판사 이름 입력')
    publication_year = st.number_input('출간연도 입력', min_value=2015, max_value=2050, step=1, format='%d')

    if st.button('DB에 문제집 등록'):
        try:
            session = Session()

            book = func.add_book(session, book_name, publisher_name, publication_year)

            session.commit()

            st.success(f'Successfully registered book "{book_name}" in DB.')

        except exc.SQLAlchemyError as e:
            st.error(f"Error occurred: {e}")
            session.rollback()

        finally:
            session.close()


def register_chapters():
    Session = sessionmaker(bind=engine)

    st.title('챕터 등록')

    # 데이터베이스 세션 생성
    session = Session()

    # 사용자 입력 받기
    selected_book = st.selectbox('문제집 선택', func.get_all_books(Session))
    chapter_name = st.text_input('챕터 이름 입력')

    if st.button('DB에 챕터 등록'):
        try:
            # 선택된 책 객체 가져오기
            book = session.query(Book).filter_by(name=selected_book[0], publisher=selected_book[1], publication_year=selected_book[2]).first()

            chapter = func.add_chapter(session, book, chapter_name)

            session.commit()

            st.success(f'Successfully registered chapter "{chapter_name}" for book "{selected_book[0]}"')

        except exc.SQLAlchemyError as e:
            st.error(f"Error occurred: {e}")
            session.rollback()

        finally:
            session.close()


def register_questions(book_name, chapter_name, page_number, question_number, question_full_text, correct_answer_option):

    Session = sessionmaker(bind=engine)
    try:
        session = Session()

        # 문제와 답안 선택지를 분리
        split_text = re.split(r'\s\([A-D]\)', question_full_text)
        question_text = split_text[0]  # 첫 번째 줄이 문제
        answer_choices = [choice.strip() for choice in split_text[1:]]  # 나머지 줄들이 답안 선택지

        # GPT api를 통해 난이도, 유형 예측
        result = json.loads(func.get_question_type_and_difficulty_level(question_full_text, question_text, correct_answer_option))
        ic(result)
        question_type_names = result['question_type']  # It may predict multiple question types
        difficulty_level = result['difficulty_level']
        translation = result['translation']
        explanation = result['explanation']
        altered_text = result['altered_text']

        # 책 찾기
        book = func.get_book(session, book_name)

        # 챕터 찾기
        chapter = func.get_chapter(session, book, chapter_name)

        # 답안 추가
        answers = []
        for text in answer_choices:
            answer = func.add_answer(session, None, text)  # question_id=None initially
            answers.append(answer)

        # 문제 추가
        question = func.add_question(session, question_text, altered_text, difficulty_level, translation, None)  # correct_answer_id=None initially

        # 답안에 question_id 추가 및 정답 업데이트
        for i, answer in enumerate(answers):
            answer.question_id = question.id
            if chr(i + 65) == correct_answer_option:  # 65는 ASCII 코드에서 'A'에 해당
                question.correct_answer_id = answer.id  # Update correct_answer_id field in Question object

        # Explanation 추가
        explanation = func.add_explanation(session, explanation, question.correct_answer_id)

        # 문제 유형 매핑 추가
        for question_type_name in question_type_names:
            question_type, question_sub_type = func.add_question_type(session, question_type_name)
            # Assert that both question_type and question_sub_type are not None
            assert question_type and question_sub_type, f"Unknown question type: {question_type_name}"
            func.add_question_type_mapping(session, question, question_type, question_sub_type)

        # 책에서의 문제 위치 정보 추가
        func.add_book_question(session, page_number, question_number, question, chapter)

        session.commit()

        st.success(f'Successfully registered question:\n"{question_text}"\nDifficulty level: {difficulty_level}\nQuestion types: {question_type_names}')

    except json.JSONDecodeError as e:
        st.error(f"Error occurred while parsing JSON: {e}")
        session.rollback()

    except exc.SQLAlchemyError as e:
        st.error(f"Error occurred: {e}")
        session.rollback()

    finally:
        session.close()


def register_questions_batch(book_name, chapter_name, page_number, ocr_result, answers):
    if st.button('DB에 문제 일괄 등록'):
        gpt_result = func.get_ocr_result_organized(ocr_result)
        st.write(f'Type of gpt_result: {type(gpt_result)}')  # gpt_result의 데이터 타입 출력
        st.write(f'gpt_result: {gpt_result}')  # gpt_result의 내용 출력

        if isinstance(gpt_result, str):
            results = json.loads(gpt_result)
        else:
            results = gpt_result

        for i, result in enumerate(results):
            question_number = int(result['question_number'])
            question_full_text = result['question']
            correct_answer_option = answers[i]
            st.caption('----------------------------------------------')
            st.write(f'문제 번호: {question_number}')
            st.write(f'문제: {question_full_text}')
            st.write(f'정답: {correct_answer_option}')
            register_questions(book_name, chapter_name, page_number, question_number, question_full_text, correct_answer_option)


def get_question():
    # 데이터베이스 세션 생성
    Session = sessionmaker(bind=engine)
    session = Session()

    # 모든 책의 목록과 출판연도 가져오기
    books = session.query(Book).all()
    book_names = [(book.name, book.publication_year) for book in books]
    selected_book_name, selected_book_year = st.selectbox('문제집 선택', book_names, key='book_name3')

    # 선택한 책과 출판연도의 모든 챕터 가져오기
    selected_book = session.query(Book).filter_by(name=selected_book_name, publication_year=selected_book_year).first()
    chapters = session.query(Chapter).filter_by(book_id=selected_book.id).all()
    chapter_names = [chapter.name for chapter in chapters]
    selected_chapter_name = st.selectbox('챕터 선택', chapter_names, key='chapter_name3')

    # 선택한 챕터의 모든 문제 가져오기
    selected_chapter = session.query(Chapter).filter_by(name=selected_chapter_name).first()
    book_questions = session.query(BookQuestion).filter_by(chapter_id=selected_chapter.id).all()
    question_numbers = sorted([book_question.question_number for book_question in book_questions])
    selected_question_number = st.selectbox('문제 번호 선택', question_numbers, key='question_number3')

    # 선택한 문제의 정보 가져오기
    selected_question = session.query(BookQuestion).filter_by(question_number=selected_question_number).first()
    question = session.query(Question).filter_by(id=selected_question.question_id).first()

    # 선택한 문제의 모든 유형 가져오기
    question_type_mappings = session.query(QuestionTypeMapping).filter_by(question_id=question.id).all()

    # 정보 표시
    st.caption('----------------------------------------------')
    st.write('★' * question.difficulty_level + '☆' * (5 - question.difficulty_level))
    # 각 유형에 대해 정보를 가져오고 출력
    for mapping in question_type_mappings:
        question_type = session.query(QuestionType).filter_by(id=mapping.question_type_id).first()
        question_subtype = session.query(QuestionSubType).filter_by(id=mapping.question_subtype_id).first()
        st.write(f'[**{question_type.name_kor}** / **{question_subtype.name_kor if question_subtype else "-"}**]')

    st.subheader(f'{selected_question_number}. {question.altered_text if question.altered_text else question.text}')
    st.markdown(f'▶ {question.translation if question.translation else "번역 없음"}')

    # 선택한 문제의 모든 보기 가져오기
    answers = session.query(Answer).filter_by(question_id=question.id).all()

    # 각 보기에 대해 정보를 가져오고 출력
    for i, answer in enumerate(answers):
        if answer.id == question.correct_answer_id:
            st.subheader(f'**({chr(i + 65)}) {answer.text}** ✅')
            explanation = session.query(Explanation).filter_by(answer_id=answer.id).first()
            st.caption(f'※ {explanation.text if explanation else "해설 없음"}')
        else:
            st.subheader(f'({chr(i + 65)}) {answer.text}')


def filter_questions_by_type_and_level():
    Session = sessionmaker(bind=engine)
    session = Session()

    # Streamlit components for selection
    question_sub_type = st.selectbox('문제 유형을 선택하세요', [type[0] for type in session.query(QuestionSubType.name_kor).distinct()])
    difficulty_level = st.selectbox('문제 난이도를 선택하세요', [1, 2, 3, 4, 5])

    # Display the explanations for the chosen types
    question_type = func.get_main_type_from_sub_type(question_sub_type, lang='kor')
    st.markdown(f"**선택한 문제 주 유형({question_type}) 설명:**")
    st.info(func.get_main_type_explanation(question_type))
    st.markdown(f"**선택한 문제 서브 유형({question_sub_type}) 설명:**")
    st.info(func.get_sub_type_explanation(question_sub_type))

    # Querying the database
    query = session.query(Question).join(QuestionTypeMapping).join(QuestionSubType).filter(QuestionSubType.name_kor == question_sub_type, Question.difficulty_level == difficulty_level)
    questions = query.all()

    level_with_stars = '★' * difficulty_level + '☆' * (5 - difficulty_level)
    st.title(f'{question_sub_type} {level_with_stars}')

    # Displaying the questions
    st.caption(f'총 {len(questions)}개의 문제가 있습니다.')
    st.warning('⚠️ 저작권 문제로 인해 문제 내용이 일부 변경되었지만, 문제 유형 및 난이도는 동일합니다.')
    for i, question in enumerate(questions):
        st.caption('----------------------------------------------')
        st.subheader(f'{i+1}. {question.altered_text if question.altered_text else question.text}')

        # Fetch the answers for the current question
        answers = session.query(Answer).filter_by(question_id=question.id).all()

        # Create a list of tuples for the radio button options
        options = [f'({chr(j + 65)}) {answer.text}' for j, answer in enumerate(answers)]
        options.insert(0, '정답을 선택하세요')  # Insert an empty option at the start

        answers2id = {f'({chr(j + 65)}) {answer.text}': answer.id for j, answer in enumerate(answers)}
        id2answers = {answer.id: f'({chr(j + 65)}) {answer.text}' for j, answer in enumerate(answers)}

        # Create a radio button selection for the answers
        selected_answer = st.radio('', options, label_visibility='collapsed')
        # Only check the answer if the user has made a selection
        if selected_answer != '정답을 선택하세요':
            selected_answer_id = answers2id[selected_answer]
            answer_no = id2answers[question.correct_answer_id]
            # Check if the selected answer is correct
            if selected_answer_id == question.correct_answer_id:
                st.success("정답입니다!")
            else:
                st.error("오답입니다.")

            with st.expander("정답 및 해설 보기"):
                st.markdown(f"정답: {answer_no}")
                st.markdown(f"번역: {question.translation}")
                st.markdown(f"해설: {session.query(Explanation.text).filter(Explanation.answer_id == question.correct_answer_id).scalar()}")
                st.caption('----------------------------------------------')
                st.caption('출처')
                st.caption(f'- 문제집: {session.query(Book.name).join(Chapter).join(BookQuestion).filter(BookQuestion.question_id == question.id).scalar()}')
                st.caption(f'- 챕터: {session.query(Chapter.name).filter(Chapter.id == session.query(BookQuestion.chapter_id).filter(BookQuestion.question_id == question.id).scalar()).scalar()}')
                st.caption(f'- 문제 번호: {session.query(BookQuestion.question_number).filter(BookQuestion.question_id == question.id).scalar()}')
                st.caption(f'- 페이지: {session.query(BookQuestion.page_number).filter(BookQuestion.question_id == question.id).scalar()}')

    session.close()


def insert_generated_question_to_db(generated_question, question_sub_type, difficulty_level):
    Session = sessionmaker(bind=engine_g)
    session = Session()
    try:
        sub_type = session.query(GeneratedQuestionSubType).filter(GeneratedQuestionSubType.name_eng == question_sub_type).first()
        question = GeneratedQuestion(
            question_text=generated_question['question_text'],
            question_type_id=sub_type.question_type_id,
            question_sub_type_id=sub_type.id,
            question_level=difficulty_level,
            translation=generated_question['translation'],
            explanation=generated_question['explanation']
        )
        session.add(question)
        session.commit()
        for choice in generated_question['choices']:
            answer = GeneratedAnswer(
                text=choice,
                is_correct=(choice == generated_question['answer']),
                question_id=question.id
            )
            session.add(answer)
        session.commit()
        for voca_dict in generated_question['vocabulary']:
            vocabulary = GeneratedVocabulary(
                word=voca_dict['word'],
                translation=voca_dict['translation'],
                explanation=voca_dict['explanation'],
                difficulty=voca_dict['difficulty'],
                part_of_speech=voca_dict['part_of_speech'],
                example=voca_dict['example'],
                example_translation=voca_dict['example_translation'],
                question_id=question.id
            )
            session.add(vocabulary)
        session.commit()
    except SQLAlchemyError as e:
        detail_error = traceback.format_exc()
        st.error(f"An error occurred while inserting the generated question into the database: {e}\n{detail_error}")
    finally:
        session.close()


def generate_and_register_part5():
    st.title('TOEIC Part5 문제 생성기')

    Session = sessionmaker(bind=engine_g)
    session = Session()

    question_types = session.query(GeneratedQuestionType).all()

    # Divide the question types into two rows
    half_len = len(question_types) // 2 + len(question_types) % 2
    first_row_types = question_types[:half_len]
    second_row_types = question_types[half_len:]

    selected_sub_types = []
    for question_types_in_row in [first_row_types, second_row_types]:
        cols = st.columns(len(question_types_in_row))
        for i, question_type in enumerate(question_types_in_row):
            sub_types = session.query(GeneratedQuestionSubType).filter_by(question_type_id=question_type.id).all()
            sub_type_names = [sub_type.name_eng for sub_type in sub_types]
            selected_sub_types += cols[i].multiselect(f'{question_type.name_eng} 문제 유형 선택', sub_type_names)

    difficulty_levels = st.multiselect('문제 난이도를 선택하세요', [1, 2, 3, 4, 5], [3])  # Default to 3

    num_questions_per_type = st.number_input('각 유형당 생성할 문제 수를 입력하세요', min_value=1, value=5)

    if st.button('생성하기'):
        progress_bar = st.progress(0)  # Move this line outside of the loop
        for question_sub_type in selected_sub_types:
            question_type = func.get_main_type_from_sub_type(question_sub_type)
            for difficulty_level in difficulty_levels:
                st.write(f"{num_questions_per_type}개의 {question_sub_type} 유형의 {difficulty_level} 난이도 문제를 생성합니다...")
                success_count = 0
                for i in stqdm(range(num_questions_per_type)):
                    try:
                        generated_question = func.generate_part5_by_type_and_level(question_type, question_sub_type, difficulty_level)
                        insert_generated_question_to_db(json.loads(generated_question), question_sub_type, difficulty_level)
                        success_count += 1
                        progress_bar.progress((i + 1) / num_questions_per_type)  # Update the same progress bar
                        st.caption('----------------------------------------------')
                        st.json(json.loads(generated_question))
                    except Exception as e:
                        detail_error = traceback.format_exc()
                        st.error(f"An error occurred while generating a question: {e}\n{detail_error}")
                st.success(f"{success_count}개의 문제가 성공적으로 생성되었습니다!")


def generate_and_show_test():
    st.title('TOEIC Part5 문제집')

    difficulty = st.selectbox('난이도를 선택하세요', ['초급', '중급', '고급'])
    if difficulty == '초급':
        difficulty_levels = [1, 2]
    elif difficulty == '중급':
        difficulty_levels = [2, 3, 4]
    else:
        difficulty_levels = [4, 5]

    if st.button('문제 추천받기'):
        Session = sessionmaker(bind=engine_g)
        session = Session()

        question_types = session.query(GeneratedQuestionType).all()

        questions = []
        for question_type in question_types:
            for level in difficulty_levels:
                questions += session.query(GeneratedQuestion).join(GeneratedQuestionSubType).filter(
                    and_(GeneratedQuestionSubType.question_type_id == question_type.id,
                         GeneratedQuestion.question_level == level)).all()

        selected_questions = sample(questions, 30)  # Select 30 questions randomly

        # Get current date and format it as yyyy-mm-dd
        current_date = datetime.date.today().isoformat()

        html = f'<h1><center>{difficulty} 토익 파트5 기출변형</center></h1>'
        html += '<div style="column-count: 2"><ol style="list-style-type: none">'
        answer_key_html = "<h1><center>정답</center></h1><table>"
        explanation_html = "<h1><center>해설</center></h1><div style='column-count: 2'>"

        for i, question in enumerate(selected_questions, 101):
            answers = session.query(GeneratedAnswer).filter_by(question_id=question.id).all()
            correct_answer = next((a for a in answers if a.is_correct), None)
            answer_key_html += f"<tr><td>{i}</td><td>({chr(65+answers.index(correct_answer))})</td></tr>"

            sub_type = session.query(GeneratedQuestionSubType).join(GeneratedQuestion).filter(GeneratedQuestion.id == question.id).first()
            explanation_html += f"<h4>{i}.</h4>"
            explanation_html += f"<p><b>[문제 유형] </b> {sub_type.name_kor}</p>"
            explanation_html += f"<p><b>[해석] </b> {question.translation}<br/><br/><b>[해설] </b> {question.explanation}</p>"

            vocabulary = session.query(GeneratedVocabulary).filter_by(question_id=question.id).all()
            if vocabulary:
                explanation_html += "<b>어휘:</b><ul>"
                for v in vocabulary:
                    explanation_html += f"<li>{v.word} : {v.explanation}</li>"
                explanation_html += "</ul>"

            # Add question ID to the explanation
            explanation_html += f"<p style='font-size: small; text-align: right'>id: {question.id}</p>"

            answers_html = ''.join(f'<li style="list-style-type: none">({chr(65+j)}) {answer.text}</li>' for j, answer in enumerate(answers))
            html += f'<li style="list-style-type: none">{i}. {question.question_text}<ul style="list-style-type: none">{answers_html}</ul></li><br>'
        html += '</ol></div>'
        html += f'<footer><center>© answer4all. All rights reserved. <br>문제집 파일명: toeic_part5_{current_date}.html</center></footer>'
        answer_key_html += "</table>"
        explanation_html += '</div>'
        explanation_html += f'<footer><center>© answer4all. All rights reserved. <br>해설지 파일명: toeic_part5_{current_date}_explanations.html</center></footer>'

        combined_html = html + explanation_html
        st.download_button('문제집과 해설지 다운로드', data=combined_html.encode('utf-8'), file_name=f'toeic_part5_{current_date}_combined.html', mime='text/html')
        st.markdown(html, unsafe_allow_html=True)
        # Combine answer key and explanations
        explanation_html = answer_key_html + explanation_html
        with st.expander('해설지 보기'):
            st.markdown(explanation_html, unsafe_allow_html=True)


def recommend_questions_based_on_errors():
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Streamlit components for selection
    book_name = st.selectbox('문제집을 선택하세요', [book[0] for book in session.query(Book.name).distinct()])
    book_id = session.query(Book.id).filter(Book.name == book_name).scalar()

    chapter_name = st.selectbox('챕터를 선택하세요', [chapter[0] for chapter in session.query(Chapter.name).filter(Chapter.book_id == book_id).distinct()])
    chapter_id = session.query(Chapter.id).filter(Chapter.name == chapter_name, Chapter.book_id == book_id).scalar()

    # Display selected book and chapter
    st.markdown(f"**선택한 문제집:** {book_name}")
    st.markdown(f"**선택한 챕터:** {chapter_name}")

    # Now, let's get the questions for the selected book and chapter
    book_questions = session.query(BookQuestion).filter_by(chapter_id=chapter_id).all()

    # Now, let's ask the user to select the questions they got wrong
    wrong_questions = st.multiselect('어떤 문제들을 틀렸나요?', [q.question_number for q in book_questions])

    if st.button("문제 추천 받기"):  # Add this button
        # Get the question_ids for the selected wrong questions
        wrong_question_ids = [q.question_id for q in book_questions if q.question_number in wrong_questions]

        # Now, let's get the types and levels for the wrong questions
        wrong_types_and_levels = session.query(QuestionTypeMapping.question_subtype_id, Question.difficulty_level).join(Question).filter(Question.id.in_(wrong_question_ids)).all()

        # Group the types and levels by question_id
        grouped_types_and_levels = defaultdict(list)
        for type_id, level in wrong_types_and_levels:
            grouped_types_and_levels[type_id].append(level)

        # Fetch the descriptions for the subtypes of the wrong questions
        wrong_subtypes = [type_id for type_id, _ in wrong_types_and_levels]
        wrong_subtypes_descriptions = session.query(QuestionSubType.explanation).filter(QuestionSubType.id.in_(wrong_subtypes)).all()

        # Display the descriptions to the user
        st.markdown("**틀린 문제 유형에 대한 설명:**")
        for description in wrong_subtypes_descriptions:
            st.caption(f"- {description[0]}")

        # Now, we need to connect to the second database to get the generated questions
        Session_g = sessionmaker(bind=engine_g)
        session_g = Session_g()

        # Let's loop through the types_and_levels and get the generated questions
        st.session_state.gen_questions = []  # Initialize gen_questions as an empty list
        for type_id, levels in grouped_types_and_levels.items():
            for level in levels:
                questions = session_g.query(GeneratedQuestion).filter_by(question_sub_type_id=type_id, question_level=level).order_by(sql_func.random()).limit(5).all()
                st.session_state.gen_questions.extend(questions)  # Add the generated questions to the list

        for i, question in enumerate(st.session_state.gen_questions):
            st.caption('----------------------------------------------')
            st.subheader(f'{i+1}. {question.question_text}')

            # Fetch the answers for the current question
            answers = session_g.query(GeneratedAnswer).filter_by(question_id=question.id).all()

            # Create a list of tuples for the radio button options
            for j, answer in enumerate(answers):
                st.write(f'({chr(j + 65)}) {answer.text}')

            id2answers = {answer.id: f'({chr(j + 65)}) {answer.text}' for j, answer in enumerate(answers)}

            correct_answer_id = session_g.query(GeneratedAnswer.id).filter_by(question_id=question.id, is_correct=True).scalar()

            # Show the explanation, translation, and vocabulary with st.expander
            with st.expander('정답 및 해설 보기'):
                st.caption(f'**정답:** {id2answers[correct_answer_id]}')
                st.caption(f"**번역:** {question.translation}")
                st.caption(f"**해설:** {question.explanation}")
                vocabularies = session_g.query(GeneratedVocabulary).filter_by(question_id=question.id).all()
                for vocab in vocabularies:
                    st.caption(f"{vocab.word}: {vocab.explanation}")
            st.caption(f"id: {question.id}")

        session_g.close()
    session.close()


st.set_page_config(
    page_title="Answer4All Admin Page",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto"
)


def app():
    st.sidebar.title("DB 등록 메뉴")
    page = st.sidebar.selectbox(
        "선택하세요",
        [
            "문제집 등록",
            "챕터 등록",
            "문제 개별 등록",
            "문제 일괄 등록",
            "문제 유형 등록",
            "문제 확인",
            "문제 유형 및 난이도 필터링",
            "오답 문제 추천받기",
            "TOEIC Part5 문제 생성",
            "TOEIC Part5 문제집 생성"
        ]
    )

    if page == "문제집 등록":
        register_books()

    elif page == "챕터 등록":
        register_chapters()

    elif page == "문제 개별 등록":
        Session = sessionmaker(bind=engine)

        st.title('문제 개별 등록')

        # 사용자 입력 받기
        book_name = st.selectbox('문제집 선택', func.get_all_books(Session), key='book_name1')
        chapter_name = st.selectbox('챕터 선택', func.get_all_chapters(Session, book_name), key='chapter_name1')
        page_number = st.number_input('페이지 입력', min_value=0, max_value=500, step=1, format='%d', key='page_number1')
        question_number = st.number_input('문제 번호 입력', min_value=101, max_value=130, step=1, format='%d')
        question_full_text = st.text_area('문제 입력')
        correct_answer_option = st.selectbox('정답 입력', ['A', 'B', 'C', 'D'])
        if st.button('DB에 문제 등록'):
            register_questions(book_name, chapter_name, page_number, question_number, question_full_text, correct_answer_option)

    elif page == "문제 일괄 등록":
        Session = sessionmaker(bind=engine)

        st.title('문제 일괄 등록')

        # 사용자 입력 받기
        book_name = st.selectbox('문제집 선택', func.get_all_books(Session), key='book_name2')
        chapter_name = st.selectbox('챕터 선택', func.get_all_chapters(Session, book_name), key='chapter_name2')
        page_number = st.number_input('페이지 입력', min_value=0, max_value=500, step=1, format='%d', key='page_number2')
        ocr_result = st.text_area('OCR 결과 입력')
        answers = list(st.text_area('답안 입력'))

        register_questions_batch(book_name, chapter_name, page_number, ocr_result, answers)

    elif page == "문제 유형 등록":
        st.title('문제 유형 등록')
        register_types()
        register_types_g()

    elif page == "문제 확인":
        get_question()

    elif page == "문제 유형 및 난이도 필터링":
        filter_questions_by_type_and_level()

    elif page == "오답 문제 추천받기":
        recommend_questions_based_on_errors()

    elif page == "TOEIC Part5 문제 생성":
        generate_and_register_part5()

    elif page == "TOEIC Part5 문제집 생성":
        generate_and_show_test()


if __name__ == '__main__':
    app()
