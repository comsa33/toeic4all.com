from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from data.postgre import postgre_engine_answer4all as engine


Base = declarative_base()


class QuestionTypeMapping(Base):
    __tablename__ = 'question_types_mapping'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    question_type_id = Column(Integer, ForeignKey('question_types.id'))
    question_subtype_id = Column(Integer, ForeignKey('question_sub_types.id'))


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    altered_text = Column(String)
    difficulty_level = Column(Integer)
    correct_answer_id = Column(Integer, ForeignKey('answers.id'))
    translation = Column(String)

    # Relationship to QuestionTypeMapping
    types = relationship("QuestionTypeMapping", backref="question")


class QuestionType(Base):
    __tablename__ = 'question_types'

    id = Column(Integer, primary_key=True)
    name_kor = Column(String)
    name_eng = Column(String)
    explanation = Column(String)

    # Relationship to QuestionTypeMapping
    questions = relationship("QuestionTypeMapping", backref="question_type")


class QuestionSubType(Base):
    __tablename__ = 'question_sub_types'

    id = Column(Integer, primary_key=True)
    name_kor = Column(String)
    name_eng = Column(String)
    explanation = Column(String)
    question_type_id = Column(Integer, ForeignKey('question_types.id'))

    # Relationship to QuestionTypeMapping
    questions = relationship("QuestionTypeMapping", backref="question_subtype")


class Answer(Base):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    question_id = Column(Integer, ForeignKey('questions.id'))


class Explanation(Base):
    __tablename__ = 'explanations'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    answer_id = Column(Integer, ForeignKey('answers.id'))


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    publisher = Column(String)  # 출판사
    publication_year = Column(Integer)  # 출간연도


class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    book_id = Column(Integer, ForeignKey('books.id'))


class BookQuestion(Base):
    __tablename__ = 'book_questions'

    id = Column(Integer, primary_key=True)
    page_number = Column(Integer)
    question_number = Column(Integer)
    question_id = Column(Integer, ForeignKey('questions.id'))
    chapter_id = Column(Integer, ForeignKey('chapters.id'))


Base.metadata.create_all(engine)
