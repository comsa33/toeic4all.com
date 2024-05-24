from typing import List, Optional

from langchain_core.pydantic_v1 import BaseModel, Field


class Vocabulary(BaseModel):
    word: str = Field(
        title="Vocabulary Word",
        description="This is the word that is used in the question text or the choices. It should be a common word that is used in the business, finance, economics, hiring, sales, marketing, and so on."
    )
    difficulty: int = Field(
        title="Difficulty Level",
        description="This is the difficulty level of the vocabulary word. It should be a number from 1 to 5 based on the complexity of the word."
    )
    part_of_speech: Optional[str] = Field(
        default=None,
        title="Part of Speech",
        description="This is the part of speech of the vocabulary word. It should be a noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, or phrase."
    )
    translation: str = Field(
        title="Translation of the Vocabulary Word into Korean",
        description="This is the translation of the vocabulary word into the Korean language. It is used for the Korean-speaking users to understand the word."
    )
    explanation: str = Field(
        title="Explanation of the Vocabulary Word",
        description="This is the explanation of the vocabulary word. It should be clear and concise to help the users understand the meaning and the usage of the word, especially in the context of the TOEIC test."
    )
    example: Optional[str] = Field(
        default=None,
        title="Example Sentence",
        description="This is an example sentence that uses the vocabulary word. It should be a simple sentence that is easy to understand but is likely to be used in TOEIC situations."
    )
    example_translation: Optional[str] = Field(
        default=None,
        title="Translation of the Example Sentence into Korean",
        description="This is the translation of the example sentence into the Korean language. It is used for the Korean-speaking users to understand the context of the example sentence."
    )


class P5GenModel(BaseModel):
    question_text: str = Field(
        title="TOEIC Part5 Question Text",
        description="This is the sentence with blank(6dash-lines '------') to fill for the quiz in TOEIC Part5. It should be like a real question in the TOEIC test in the field of business, finance, economics, hiring, sales, marketing, and so on."
    )
    choices: List[str] = Field(
        title="Choices",
        description="This is a list of 4 choices for the blank in the question text. The correct answer should be included in this list."
    )
    answer: str = Field(
        title="Answer",
        description="This is the correct answer for the blank in the question text. It should be one of the choices."
    )
    translation: str = Field(
        title="Translation of the Question Text into Korean",
        description="This is the translation of the question text into the Korean language. It is used for the Korean-speaking users to understand the question text."
    )
    explanation: str = Field(
        title="Explanation",
        description="This is the explanation written in Korean of the correct answer. It should be clear and concise to help the Korean users understand the context and the reason why the answer is correct."
    )
    vocabulary: Optional[List[Vocabulary]] = Field(
        default=[],
        title="Vocabulary",
        description="This is the vocabulary used in the question text or the choices. It should be a common word that is used in the business, finance, economics, hiring, sales, marketing, and so on. Its' attributes are word, difficulty, part_of_speech, translation(Korean), explanation, example, and example_translation(Korean)."
    )
