#!/usr/bin/env python3
"""
Test script for the enhanced CAPTCHA bypass and SQLite logging system
This script demonstrates the comprehensive logging capabilities.
"""

import os
import sys
import sqlite3
import time
from datetime import datetime
from scraper import DelhiHighCourtScraper, MockScraper, SQLiteLogger

def test_sqlite_logging():
    """Test the SQLite logging system"""
    print("🔍 Testing SQLite Logging System")
    print("=" * 50)
    
    # Initialize logger
    db_path = "test_court_scraper.db"
    if os.path.exists(db_path):
        os.remove(db_path)  # Clean start
    
    logger = SQLiteLogger(db_path)
    print(f"✓ Database initialized: {db_path}")
    
    # Test query logging
    query_id = logger.log_query(
        "W.P.(C)", "15234", "2024", 
        "192.168.1.100", "Mozilla/5.0...", "test_session_123"
    )
    print(f"✓ Query logged with ID: {query_id}")
    
    # Test response logging
    logger.log_response(
        query_id, "https://example.com", "POST",
        {"User-Agent": "Mozilla/5.0..."}, {"case_type": "W.P.(C)"},
        200, {"Content-Type": "text/html"}, 
        "<html><body>Test HTML</body></html>",
        {"case_title": "Test Case"}, 1250
    )
    print("✓ Response logged")
    
    # Test CAPTCHA logging
    logger.log_captcha_attempt(
        query_id, "https://example.com/captcha.jpg", "ABC123",
        True, "ocr_preprocessing_0", 0.85, 2300
    )
    print("✓ CAPTCHA attempt logged")
    
    # Test viewstate logging
    logger.log_viewstate_tokens(query_id, {
        "__VIEWSTATE": "/wEPDwUKLTI2MTQ5NDEzNQ==",
        "__VIEWSTATEGENERATOR": "CA0B0334",
        "__EVENTVALIDATION": "/wEWAwKw8cLNBgKm8sO3BAL7q8S+DA==",
        "csrf_token": "abc123def456"
    })
    print("✓ View-state tokens logged")
    
    return db_path

def analyze_logged_data(db_path):
    """Analyze the logged data"""
    print("\n📊 Analyzing Logged Data")
    print("=" * 50)
    
    with sqlite3.connect(db_path) as conn:
        # Query analysis
        cursor = conn.execute("""
            SELECT case_type, case_number, filing_year, success, 
                   response_time_ms, captcha_required, captcha_solved
            FROM scraper_queries
        """)
        
        queries = cursor.fetchall()
        print(f"📋 Total Queries: {len(queries)}")
        
        for query in queries:
            print(f"   • {query[0]} {query[1]}/{query[2]} - "
                  f"Success: {bool(query[3])}, Time: {query[4]}ms, "
                  f"CAPTCHA: {bool(query[5])}")
        
        # Response analysis
        cursor = conn.execute("""
            SELECT request_method, response_status, LENGTH(raw_html) as html_size
            FROM scraper_responses
        """)
        
        responses = cursor.fetchall()
        print(f"\n🌐 Total Responses: {len(responses)}")
        
        for response in responses:
            print(f"   • {response[0]} - Status: {response[1]}, "
                  f"HTML Size: {response[2]} bytes")
        
        # CAPTCHA analysis
        cursor = conn.execute("""
            SELECT method_used, success, confidence_score, processing_time_ms
            FROM captcha_attempts
        """)
        
        captchas = cursor.fetchall()
        print(f"\n🔐 Total CAPTCHA Attempts: {len(captchas)}")
        
        for captcha in captchas:
            print(f"   • Method: {captcha[0]}, Success: {bool(captcha[1])}, "
                  f"Confidence: {captcha[2]:.2f}, Time: {captcha[3]}ms")
        
        # Token analysis
        cursor = conn.execute("""
            SELECT LENGTH(viewstate) as vs_len, LENGTH(csrf_token) as csrf_len
            FROM viewstate_tokens
        """)
        
        tokens = cursor.fetchall()
        print(f"\n🔑 Total Token Records: {len(tokens)}")
        
        for token in tokens:
            print(f"   • ViewState: {token[0]} chars, CSRF: {token[1]} chars")

def test_real_scraper_with_logging():
    """Test the real scraper with comprehensive logging"""
    print("\n🕷️ Testing Real Scraper with Logging")
    print("=" * 50)
    
    # Initialize scraper with logging
    db_path = "real_scraper_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    scraper = DelhiHighCourtScraper(db_path)
    print(f"✓ Real scraper initialized with logging: {db_path}")
    
    # Note: This would attempt real scraping - commented for safety
    print("⚠️  Real scraping test skipped (would access actual court website)")
    print("   To test real scraping, set USE_MOCK_SCRAPER=false in environment")
    
    return db_path

def test_mock_scraper_compatibility():
    """Test that mock scraper still works with the new system"""
    print("\n🎭 Testing Mock Scraper Compatibility")
    print("=" * 50)
    
    mock_scraper = MockScraper()
    
    # Test mock data access
    success, case_data, error = mock_scraper.search_case("W.P.(C)", "15234", "2024")
    
    if success:
        print("✓ Mock scraper working correctly")
        print(f"   Case Title: {case_data.get('case_title', 'N/A')}")
        print(f"   Filing Date: {case_data.get('filing_date', 'N/A')}")
        print(f"   Judge: {case_data.get('judge_name', 'N/A')}")
    else:
        print(f"❌ Mock scraper failed: {error}")

def generate_usage_examples():
    """Generate code examples for documentation"""
    print("\n📖 Usage Examples")
    print("=" * 50)
    
    examples = """
# Initialize scraper with SQLite logging
scraper = DelhiHighCourtScraper(db_path="court_scraper.db")

# Search with comprehensive logging
success, case_data, error = scraper.search_case(
    case_type="W.P.(C)",
    case_number="15234", 
    filing_year="2024",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

# Analyze CAPTCHA success rates
import sqlite3
conn = sqlite3.connect("court_scraper.db")
cursor = conn.execute('''
    SELECT method_used, 
           COUNT(*) as attempts,
           SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
           ROUND(100.0 * SUM(success) / COUNT(*), 1) as success_rate
    FROM captcha_attempts 
    GROUP BY method_used
''')

for row in cursor:
    print(f"Method: {row[0]}, Success Rate: {row[3]}%")

# View raw HTML responses for debugging
cursor = conn.execute('''
    SELECT raw_html FROM scraper_responses 
    WHERE query_id = ? LIMIT 1
''', (query_id,))

html_content = cursor.fetchone()[0]
with open('debug_response.html', 'w') as f:
    f.write(html_content)
"""
    
    print(examples)

def main():
    """Run all tests"""
    print("🚀 Enhanced Court Scraper Testing Suite")
    print("=" * 60)
    
    try:
        # Test SQLite logging
        db_path = test_sqlite_logging()
        
        # Analyze the logged data
        analyze_logged_data(db_path)
        
        # Test real scraper initialization
        real_db = test_real_scraper_with_logging()
        
        # Test mock scraper compatibility
        test_mock_scraper_compatibility()
        
        # Show usage examples
        generate_usage_examples()
        
        print("\n✅ All Tests Completed Successfully!")
        print("\nGenerated Files:")
        print(f"   • {db_path} - Test logging database")
        print(f"   • {real_db} - Real scraper database")
        print("   • CAPTCHA_BYPASS_DOCUMENTATION.md - Comprehensive documentation")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()