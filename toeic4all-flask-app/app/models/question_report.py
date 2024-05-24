from .. import db


class QuestionReport(db.Model):
    __tablename__ = 'question_reports'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('generated_questions.id'))
    user_id = db.Column(db.String)
    report_content = db.Column(db.String)
    report_type = db.Column(db.String)  # New field
    report_date = db.Column(db.DateTime, default=db.func.current_timestamp())
