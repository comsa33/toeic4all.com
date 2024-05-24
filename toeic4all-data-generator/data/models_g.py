from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from data.postgre import postgre_engine_answer4all_g_p5 as engine

Base = declarative_base()


class GeneratedQuestionType(Base):
    __tablename__ = 'generated_question_types'

    id = Column(Integer, primary_key=True)
    name_kor = Column(String)
    name_eng = Column(String)
    explanation = Column(String)


class GeneratedQuestionSubType(Base):
    __tablename__ = 'generated_question_sub_types'

    id = Column(Integer, primary_key=True)
    name_kor = Column(String)
    name_eng = Column(String)
    explanation = Column(String)
    question_type_id = Column(Integer, ForeignKey('generated_question_types.id'))


class GeneratedQuestion(Base):
    __tablename__ = 'generated_questions'

    id = Column(Integer, primary_key=True)
    question_text = Column(String)
    question_type_id = Column(Integer, ForeignKey('generated_question_types.id'))
    question_sub_type_id = Column(Integer, ForeignKey('generated_question_sub_types.id'))
    question_level = Column(Integer)
    translation = Column(String)
    explanation = Column(String)


class GeneratedAnswer(Base):
    __tablename__ = 'generated_answers'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    is_correct = Column(Boolean)
    question_id = Column(Integer, ForeignKey('generated_questions.id'))


class GeneratedVocabulary(Base):
    __tablename__ = 'generated_vocabularies'

    id = Column(Integer, primary_key=True)
    word = Column(String)
    translation = Column(String)
    difficulty = Column(Integer)
    explanation = Column(String)
    part_of_speech = Column(String, nullable=True)
    example = Column(String, nullable=True)
    example_translation = Column(String, nullable=True)
    question_id = Column(Integer, ForeignKey('generated_questions.id'))


Base.metadata.create_all(engine)
