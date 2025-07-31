# models.py
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Query(db.Model):
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(50), nullable=False)
    case_number = db.Column(db.String(20), nullable=False)
    filing_year = db.Column(db.String(4), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    session_id = db.Column(db.String(255))

    responses = db.relationship('Response', backref='query', lazy=True, cascade='all, delete-orphan')

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('queries.id'), nullable=False)

    raw_html = db.Column(db.Text)
    response_status = db.Column(db.Integer)
    response_headers = db.Column(db.Text)
    parsed_json = db.Column(db.Text)
    case_title = db.Column(db.Text)
    petitioner = db.Column(db.Text)
    respondent = db.Column(db.Text)
    filing_date = db.Column(db.String(20))
    next_hearing_date = db.Column(db.String(20))
    latest_order = db.Column(db.Text)
    judge_name = db.Column(db.String(255))
    court_number = db.Column(db.String(50))
    case_status = db.Column(db.String(100))
    pdf_link = db.Column(db.Text)
    judgment_pdf = db.Column(db.Text)
    order_pdf = db.Column(db.Text)
    scrape_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    scrape_success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)

class CaptchaLog(db.Model):
    __tablename__ = 'captcha_logs'
    id = db.Column(db.Integer, primary_key=True)
    captcha_image_url = db.Column(db.Text)
    captcha_text = db.Column(db.String(20))
    solution_attempt = db.Column(db.String(20))
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///court.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

def log_query(case_type, case_number, filing_year, ip_address=None, user_agent=None, session_id=None):
    query = Query(case_type=case_type, case_number=case_number, filing_year=filing_year,
                  ip_address=ip_address, user_agent=user_agent, session_id=session_id)
    db.session.add(query)
    db.session.commit()
    return query

def log_response(query_id, **kwargs):
    response = Response(query_id=query_id, **kwargs)
    db.session.add(response)
    db.session.commit()
    return response

def log_captcha(**kwargs):
    captcha = CaptchaLog(**kwargs)
    db.session.add(captcha)
    db.session.commit()
    return captcha

def get_recent_queries(limit=50):
    return Query.query.order_by(Query.timestamp.desc()).limit(limit).all()

def get_successful_responses(limit=20):
    return Response.query.filter_by(scrape_success=True).order_by(
        Response.scrape_timestamp.desc()).limit(limit).all()
