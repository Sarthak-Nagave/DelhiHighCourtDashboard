import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from models import init_db, log_query, log_response, get_recent_queries, get_successful_responses, db
from scraper import get_scraper
from mock_data import CASE_TYPES
from mock_data import MOCK_CASES

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

init_db(app)

USE_MOCK_SCRAPER = os.environ.get("USE_MOCK_SCRAPER", "true").lower() == "true"

@app.route('/')
def index():
    """Main page with case search form"""
    return render_template('index.html', case_types=CASE_TYPES)

@app.route('/search-case', methods=['POST'])
def search_case():
    """API endpoint to handle case search with real scraping"""
    try:
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        filing_year = request.form.get('filing_year', '').strip()

        if not all([case_type, case_number, filing_year]):
            return jsonify({
                'success': False,
                'error': 'All fields (case type, case number, filing year) are required'
            }), 400

        query = log_query(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            session_id=request.cookies.get('session')
        )
        
        logger.info(f"Searching case: {case_type} {case_number}/{filing_year} (Query ID: {query.id})")

        scraper = get_scraper(use_mock=USE_MOCK_SCRAPER)
        success, case_data, error_message = scraper.search_case(case_type, case_number, filing_year)
        
        response_log = log_response(
            query_id=query.id,
            raw_html=case_data.get('raw_html', ''),
            response_status=200 if success else 404,
            parsed_json=json.dumps(case_data) if case_data else None,
            case_title=case_data.get('case_title', ''),
            petitioner=case_data.get('petitioner', ''),
            respondent=case_data.get('respondent', ''),
            filing_date=case_data.get('filing_date', ''),
            next_hearing_date=case_data.get('next_hearing_date', ''),
            latest_order=case_data.get('latest_order', ''),
            judge_name=case_data.get('judge_name', ''),
            court_number=case_data.get('court_number', ''),
            case_status=case_data.get('case_status', ''),
            pdf_link=case_data.get('pdf_link', ''),
            scrape_success=success,
            error_message=error_message if not success else None
        )
        
        if success:
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({
                    'success': True,
                    'case_data': case_data,
                    'query_id': query.id,
                    'response_id': response_log.id
                })

            return render_template('case_details.html',
                                 case=case_data,
                                 case_key=f"{case_type}.{case_number}.{filing_year}",
                                 search_params={
                                     'case_type': case_type,
                                     'case_number': case_number,
                                     'filing_year': filing_year
                                 },
                                 query_id=query.id)
        else:
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'query_id': query.id,
                    'response_id': response_log.id
                }), 404
            
            flash(error_message, 'warning')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error in case search: {str(e)}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            return jsonify({
                'success': False,
                'error': 'An internal server error occurred while searching for the case'
            }), 500
        
        flash('An error occurred while searching for the case. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search_case_redirect():
    """Redirect old search endpoint to new API endpoint"""
    return search_case()

@app.route('/download_pdf/<case_key>')
def download_pdf(case_key):
    """Generate and download a mock PDF for the case"""
    try:
        case_data = MOCK_CASES.get(case_key)
        if not case_data:
            flash('Case not found for PDF generation.', 'error')
            return redirect(url_for('index'))

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "DELHI HIGH COURT")
        p.drawString(50, height - 70, "CASE ORDER/JUDGMENT")

        p.setFont("Helvetica", 12)
        y_position = height - 120
        
        p.drawString(50, y_position, f"Case Number: {case_data['case_number']}")
        y_position -= 20
        p.drawString(50, y_position, f"Case Type: {case_data['case_type']}")
        y_position -= 20
        p.drawString(50, y_position, f"Filing Date: {case_data['filing_date']}")
        y_position -= 20
        p.drawString(50, y_position, f"Next Hearing: {case_data['next_hearing_date']}")
        y_position -= 40

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position, "PARTIES:")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position, f"Petitioner: {case_data['petitioner']}")
        y_position -= 15
        p.drawString(50, y_position, f"Respondent: {case_data['respondent']}")
        y_position -= 30

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position, "LATEST ORDER:")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        order_text = case_data['latest_order']
        
        max_width = width - 100
        words = order_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if p.stringWidth(test_line, "Helvetica", 10) < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines:
            p.drawString(50, y_position, line)
            y_position -= 15
            if y_position < 50:
                break

        p.setFont("Helvetica", 8)
        p.drawString(50, 30, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.drawString(50, 20, "This is a system-generated document from Delhi High Court Case Management System")
        
        p.save()
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=case_{case_key.replace(".", "_")}.pdf'
        
        logger.info(f"PDF generated for case: {case_key}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        flash('An error occurred while generating the PDF. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/query_logs')
def view_query_logs():
    """View query logs from database (admin functionality)"""
    try:
        queries = get_recent_queries(limit=100)
        return render_template('query_logs.html', logs=queries)
    except Exception as e:
        logger.error(f"Error fetching query logs: {str(e)}")
        flash('Error loading query logs', 'error')
        return redirect(url_for('index'))

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:

        total_queries = Query.query.count()
        successful_responses = Response.query.filter_by(scrape_success=True).count()
        failed_responses = Response.query.filter_by(scrape_success=False).count()
        
        return jsonify({
            'total_queries': total_queries,
            'successful_responses': successful_responses,
            'failed_responses': failed_responses,
            'success_rate': round((successful_responses / max(total_queries, 1)) * 100, 2)
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_title="Page Not Found",
                         error_message="The page you are looking for does not exist."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_title="Internal Server Error", 
                         error_message="An internal server error occurred. Please try again later."), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
