import requests
import json
import re
import logging
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Dict, Optional, Tuple, List
import base64
import io
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import hashlib
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLiteLogger:
    """SQLite database logger for scraping activities"""
    
    def __init__(self, db_path: str = "court_scraper.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraper_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    case_type TEXT NOT NULL,
                    case_number TEXT NOT NULL,
                    filing_year TEXT NOT NULL,
                    query_hash TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    attempt_number INTEGER DEFAULT 1,
                    success BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    response_time_ms INTEGER,
                    captcha_required BOOLEAN DEFAULT FALSE,
                    captcha_solved BOOLEAN DEFAULT FALSE,
                    captcha_solution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraper_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    timestamp TEXT NOT NULL,
                    request_url TEXT NOT NULL,
                    request_method TEXT DEFAULT 'GET',
                    request_headers TEXT,
                    request_data TEXT,
                    response_status INTEGER,
                    response_headers TEXT,
                    raw_html TEXT,
                    html_hash TEXT,
                    parsed_data TEXT,
                    processing_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES scraper_queries (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS captcha_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    timestamp TEXT NOT NULL,
                    captcha_url TEXT,
                    captcha_image_hash TEXT,
                    ocr_result TEXT,
                    manual_solution TEXT,
                    success BOOLEAN DEFAULT FALSE,
                    method_used TEXT, -- 'ocr', 'manual', 'service'
                    confidence_score REAL,
                    processing_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES scraper_queries (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS viewstate_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    timestamp TEXT NOT NULL,
                    viewstate TEXT,
                    viewstate_generator TEXT,
                    event_validation TEXT,
                    csrf_token TEXT,
                    session_token TEXT,
                    other_tokens TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES scraper_queries (id)
                )
            ''')
            
            conn.commit()
            logger.info(f"SQLite database initialized: {self.db_path}")
    
    def log_query(self, case_type: str, case_number: str, filing_year: str, 
                  ip_address: str = None, user_agent: str = None, session_id: str = None) -> int:
        """Log a new query and return the query ID"""
        query_hash = hashlib.md5(f"{case_type}.{case_number}.{filing_year}".encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraper_queries 
                (timestamp, case_type, case_number, filing_year, query_hash, 
                 ip_address, user_agent, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                case_type, case_number, filing_year, query_hash,
                ip_address, user_agent, session_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def log_response(self, query_id: int, url: str, method: str, headers: dict, 
                     data: dict, status: int, response_headers: dict, 
                     raw_html: str, parsed_data: dict = None, processing_time: int = 0):
        """Log raw HTML response and parsed data"""
        html_hash = hashlib.sha256(raw_html.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraper_responses 
                (query_id, timestamp, request_url, request_method, request_headers,
                 request_data, response_status, response_headers, raw_html, html_hash,
                 parsed_data, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query_id, datetime.now().isoformat(), url, method,
                json.dumps(dict(headers)), json.dumps(data or {}), status,
                json.dumps(dict(response_headers)), raw_html, html_hash,
                json.dumps(parsed_data or {}), processing_time
            ))
            conn.commit()
    
    def log_captcha_attempt(self, query_id: int, captcha_url: str, ocr_result: str,
                           success: bool, method: str, confidence: float = 0.0,
                           processing_time: int = 0):
        """Log CAPTCHA solving attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO captcha_attempts 
                (query_id, timestamp, captcha_url, ocr_result, success, method_used,
                 confidence_score, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query_id, datetime.now().isoformat(), captcha_url, ocr_result,
                success, method, confidence, processing_time
            ))
            conn.commit()
    
    def log_viewstate_tokens(self, query_id: int, tokens: dict):
        """Log extracted view-state tokens"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO viewstate_tokens 
                (query_id, timestamp, viewstate, viewstate_generator, event_validation,
                 csrf_token, session_token, other_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query_id, datetime.now().isoformat(),
                tokens.get('__VIEWSTATE', ''),
                tokens.get('__VIEWSTATEGENERATOR', ''),
                tokens.get('__EVENTVALIDATION', ''),
                tokens.get('csrf_token', ''),
                tokens.get('session_token', ''),
                json.dumps({k: v for k, v in tokens.items() 
                           if k not in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION', 'csrf_token', 'session_token']})
            ))
            conn.commit()

class DelhiHighCourtScraper:
    """Enhanced scraper for Delhi High Court case information with comprehensive CAPTCHA bypass"""
    
    def __init__(self, db_path: str = "court_scraper.db"):
        self.base_url = "https://delhihighcourt.nic.in"
        self.case_search_url = f"{self.base_url}/app/case-number"
        self.session = requests.Session()
        self.logger = SQLiteLogger(db_path)
        self.current_query_id = None
      
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        self.captcha_config = {
            'ocr_config': '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'image_preprocessing': True,
            'retry_attempts': 3,
            'confidence_threshold': 0.7
        }
        
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting main page to get cookies and tokens"""
        try:
            response = self.session.get(self.base_url)
            logger.info(f"Session initialized. Status: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}")
            return False
    
    def _get_captcha_image(self, soup) -> Optional[str]:
        """Extract CAPTCHA image from the page"""
        try:
            captcha_img = soup.find('img', {'alt': 'captcha'}) or soup.find('img', src=re.compile(r'captcha', re.I))
            if captcha_img:
                img_src = captcha_img.get('src')
                if img_src:
                    return urljoin(self.base_url, img_src)
            return None
        except Exception as e:
            logger.error(f"Error extracting CAPTCHA image: {str(e)}")
            return None
    
    def _preprocess_captcha_image(self, image: Image.Image) -> List[Image.Image]:
        """
        Advanced image preprocessing for better CAPTCHA OCR
        Returns multiple processed versions to try
        """
        processed_images = []
      
        gray = image.convert('L')
        processed_images.append(gray)
        
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.0)
        processed_images.append(high_contrast)
        
        enhancer = ImageEnhance.Brightness(gray)
        bright = enhancer.enhance(1.5)
        processed_images.append(bright)
    
        sharp = gray.filter(ImageFilter.SHARPEN)
        processed_images.append(sharp)
      
        edge = gray.filter(ImageFilter.EDGE_ENHANCE)
        processed_images.append(edge)
        
        smooth = gray.filter(ImageFilter.SMOOTH)
        processed_images.append(smooth)
        
        return processed_images
    
    def _solve_captcha_with_ocr(self, captcha_url: str) -> Tuple[Optional[str], float]:
        """
        Enhanced CAPTCHA solving with multiple OCR attempts and confidence scoring
        Returns: (solution, confidence_score)
        """
        start_time = time.time()
        
        try:
            response = self.session.get(captcha_url)
            if response.status_code != 200:
                return None, 0.0
   
            image = Image.open(io.BytesIO(response.content))
            processed_images = self._preprocess_captcha_image(image)
            results = []
            
            for i, processed_img in enumerate(processed_images):
                try:
                    configs = [
                        '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                        '--psm 8',
                        '--psm 7'
                    ]
                    
                    for config in configs:
                        text = pytesseract.image_to_string(processed_img, config=config)
                        text = re.sub(r'[^A-Za-z0-9]', '', text.strip())
                        
                        if len(text) >= 3 and len(text) <= 10:  
                            confidence = min(1.0, len(text) / 6.0)  
                            results.append((text, confidence, f"preprocessing_{i}_config_{configs.index(config)}"))
                
                except Exception as e:
                    logger.debug(f"OCR attempt failed for preprocessing {i}: {str(e)}")
                    continue

            if results:
                results.sort(key=lambda x: x[1], reverse=True)
                best_result = results[0]
                
                processing_time = int((time.time() - start_time) * 1000)
                
                if self.current_query_id:
                    for result, confidence, method in results:
                        self.logger.log_captcha_attempt(
                            self.current_query_id, captcha_url, result,
                            success=False, method=f"ocr_{method}", 
                            confidence=confidence, processing_time=processing_time
                        )
                
                logger.info(f"CAPTCHA OCR result: '{best_result[0]}' (confidence: {best_result[1]:.2f})")
                return best_result[0], best_result[1]
            
            return None, 0.0
            
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {str(e)}")
            return None, 0.0
    
    def _solve_captcha_with_service(self, captcha_url: str) -> Optional[str]:
        """
        Solve CAPTCHA using third-party service (implement as needed)
        This is a placeholder for services like 2captcha, AntiCaptcha, etc.
        """
        
        # TODO: 
        logger.info("Third-party CAPTCHA service not configured")
        return None
    
    def _solve_captcha(self, captcha_url: str) -> Optional[str]:
        """
        Comprehensive CAPTCHA solving with multiple strategies
        """
        logger.info(f"Attempting to solve CAPTCHA: {captcha_url}")
        
        ocr_result, confidence = self._solve_captcha_with_ocr(captcha_url)
        if ocr_result and confidence >= self.captcha_config['confidence_threshold']:
            logger.info(f"CAPTCHA solved with OCR: {ocr_result} (confidence: {confidence:.2f})")
            return ocr_result
        
        service_result = self._solve_captcha_with_service(captcha_url)
        if service_result:
            logger.info(f"CAPTCHA solved with service: {service_result}")
            return service_result
        
        if ocr_result:
            logger.warning(f"Using low-confidence OCR result: {ocr_result} (confidence: {confidence:.2f})")
            return ocr_result
        
        logger.error("Failed to solve CAPTCHA with all methods")
        return None
    
    def _extract_form_data(self, soup) -> Dict[str, str]:
        """
        Enhanced extraction of form fields, view-state tokens, and CSRF tokens
        Handles multiple form types and token formats
        """
        form_data = {}
        
        try:
            forms = soup.find_all('form')
            if not forms:
                forms = soup.find_all('div', {'id': re.compile(r'.*form.*', re.I)})
            
            for form in forms:
                inputs = form.find_all('input')
                for inp in inputs:
                    name = inp.get('name')
                    value = inp.get('value', '')
                    input_type = inp.get('type', 'text').lower()
                    
                    if name:
                        form_data[name] = value
                        
                        if any(token in name.lower() for token in ['viewstate', 'token', 'csrf', 'validation']):
                            logger.debug(f"Found token field: {name} = {value[:50]}..." if len(value) > 50 else f"Found token field: {name} = {value}")
          
                selects = form.find_all('select')
                for select in selects:
                    name = select.get('name')
                    if name:
                        selected_option = select.find('option', {'selected': True})
                        if selected_option:
                            form_data[name] = selected_option.get('value', '')
                        else:
                            first_option = select.find('option')
                            if first_option:
                                form_data[name] = first_option.get('value', '')
            
            csrf_meta = soup.find('meta', {'name': re.compile(r'csrf.*token', re.I)})
            if csrf_meta:
                form_data['csrf_token'] = csrf_meta.get('content', '')
            
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    token_patterns = [
                        r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'csrf["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'__RequestVerificationToken["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                    ]
                    
                    for pattern in token_patterns:
                        matches = re.findall(pattern, script.string, re.I)
                        for match in matches:
                            if len(match) > 10:  
                                form_data[f'js_token_{len(form_data)}'] = match
          
            token_elements = soup.find_all(attrs={'data-token': True})
            for elem in token_elements:
                token_value = elem.get('data-token')
                if token_value:
                    form_data['data_token'] = token_value
            
            logger.info(f"Extracted {len(form_data)} form fields and tokens")
       
            if self.current_query_id and form_data:
                self.logger.log_viewstate_tokens(self.current_query_id, form_data)
        
        except Exception as e:
            logger.error(f"Error extracting form data: {str(e)}")
        
        return form_data
    
    def _parse_case_details(self, html_content: str) -> Dict[str, str]:
        """Parse case details from HTML response"""
        soup = BeautifulSoup(html_content, 'html.parser')
        case_data = {}
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        for i in range(0, len(cells)-1, 2):
                            key = cells[i].get_text(strip=True).lower()
                            value = cells[i+1].get_text(strip=True)
                            
                            if 'case' in key and 'no' in key:
                                case_data['case_number'] = value
                            elif 'title' in key or 'parties' in key:
                                case_data['case_title'] = value
                            elif 'petitioner' in key or 'appellant' in key:
                                case_data['petitioner'] = value
                            elif 'respondent' in key:
                                case_data['respondent'] = value
                            elif 'filing' in key and 'date' in key:
                                case_data['filing_date'] = value
                            elif 'next' in key and 'hearing' in key:
                                case_data['next_hearing_date'] = value
                            elif 'judge' in key:
                                case_data['judge_name'] = value
                            elif 'court' in key:
                                case_data['court_number'] = value
                            elif 'status' in key:
                                case_data['case_status'] = value
                            elif 'order' in key or 'judgment' in key:
                                case_data['latest_order'] = value
            
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            if pdf_links:
                case_data['pdf_links'] = []
                for link in pdf_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        case_data['pdf_links'].append({
                            'url': full_url,
                            'text': link.get_text(strip=True)
                        })
                
                if case_data['pdf_links']:
                    case_data['pdf_link'] = case_data['pdf_links'][0]['url']
        
        except Exception as e:
            logger.error(f"Error parsing case details: {str(e)}")
        
        return case_data
    
    def search_case(self, case_type: str, case_number: str, filing_year: str, 
                   max_retries: int = 3, ip_address: str = None, user_agent: str = None) -> Tuple[bool, Dict, str]:
        """
        Enhanced search for case on Delhi High Court website with comprehensive logging
        
        Args:
            case_type: Type of case (W.P.(C), CRL.A., etc.)
            case_number: Case number
            filing_year: Year of filing
            max_retries: Maximum retry attempts
            ip_address: Client IP for logging
            user_agent: Client user agent for logging
        
        Returns:
            Tuple[bool, Dict, str]: (success, case_data, error_message)
        """
        
        session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        self.current_query_id = self.logger.log_query(
            case_type, case_number, filing_year, ip_address, user_agent, session_id
        )
        
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Searching case: {case_type} {case_number}/{filing_year} (Attempt {attempt + 1}/{max_retries})")

                step_start = time.time()
                response = self.session.get(self.case_search_url, timeout=30)
                
                self.logger.log_response(
                    self.current_query_id, self.case_search_url, 'GET',
                    dict(self.session.headers), {}, response.status_code,
                    dict(response.headers), response.text,
                    processing_time=int((time.time() - step_start) * 1000)
                )
                
                if response.status_code != 200:
                    error_msg = f"Failed to load search page. Status: {response.status_code}"
                    logger.error(error_msg)
                    if attempt == max_retries - 1:
                        return False, {}, error_msg
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                form_data = self._extract_form_data(soup)
                logger.info(f"Extracted {len(form_data)} form fields")
                
                captcha_url = self._get_captcha_image(soup)
                captcha_solution = None
                captcha_required = captcha_url is not None
                
                if captcha_url:
                    logger.info(f"CAPTCHA detected: {captcha_url}")
                    captcha_solution = self._solve_captcha(captcha_url)
                    if not captcha_solution:
                        logger.warning("Failed to solve CAPTCHA, attempting search anyway")
                        captcha_solution = ""

                search_data = form_data.copy()
                search_data.update({
                    'case_type': case_type,
                    'case_number': case_number,
                    'filing_year': filing_year,
                })
                
                if captcha_required and captcha_solution:
                    captcha_fields = ['captcha', 'captcha_code', 'security_code', 'verification_code']
                    for field in captcha_fields:
                        if field in form_data or any(field in key.lower() for key in form_data.keys()):
                            search_data[field] = captcha_solution
                            break
                    else:
                        search_data['captcha'] = captcha_solution

                logger.info("Submitting search request")
                search_start = time.time()

                search_url = self.case_search_url
                form = soup.find('form')
                if form:
                    action = form.get('action')
                    if action:
                        search_url = urljoin(self.base_url, action)
                    method = form.get('method', 'POST').upper()
                else:
                    method = 'POST'
 
                search_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': self.case_search_url,
                    'Origin': self.base_url
                }
                
                if method == 'POST':
                    search_response = self.session.post(
                        search_url, data=search_data, headers=search_headers, timeout=30
                    )
                else:
                    search_response = self.session.get(
                        search_url, params=search_data, headers=search_headers, timeout=30
                    )
                
                search_time = int((time.time() - search_start) * 1000)

                self.logger.log_response(
                    self.current_query_id, search_url, method,
                    {**dict(self.session.headers), **search_headers}, search_data,
                    search_response.status_code, dict(search_response.headers),
                    search_response.text, processing_time=search_time
                )

                if search_response.status_code == 200:
                    case_data = self._parse_case_details(search_response.text)
                    
                    if case_data:
                        total_time = int((time.time() - start_time) * 1000)
                        logger.info(f"Successfully found case data in {total_time}ms")
                        
                        with sqlite3.connect(self.logger.db_path) as conn:
                            conn.execute('''
                                UPDATE scraper_queries 
                                SET success = TRUE, response_time_ms = ?, 
                                    captcha_required = ?, captcha_solved = ?
                                WHERE id = ?
                            ''', (total_time, captcha_required, captcha_solution is not None, self.current_query_id))
                            conn.commit()
                        
                        return True, case_data, ""
                    else:
                        if any(phrase in search_response.text.lower() for phrase in 
                               ['not found', 'no data', 'no record', 'invalid case', 'does not exist']):
                            error_msg = "Case not found in court records"
                            logger.info(error_msg)
                            return False, {}, error_msg
                        else:
                            logger.warning("No case data found, but no explicit error message")
                            if attempt < max_retries - 1:
                                time.sleep(2 ** attempt)  
                                continue
                else:
                    error_msg = f"Search request failed. Status: {search_response.status_code}"
                    logger.error(error_msg)
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False, {}, error_msg
                
            except requests.exceptions.Timeout:
                error_msg = "Request timeout - court website may be slow"
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return False, {}, error_msg
            
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error - court website may be down"
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(10)
                    continue
                return False, {}, error_msg
            
            except Exception as e:
                error_msg = f"Unexpected error during search: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False, {}, error_msg

        total_time = int((time.time() - start_time) * 1000)
        
        with sqlite3.connect(self.logger.db_path) as conn:
            conn.execute('''
                UPDATE scraper_queries 
                SET success = FALSE, response_time_ms = ?, error_message = ?
                WHERE id = ?
            ''', (total_time, "Max retries exceeded", self.current_query_id))
            conn.commit()
        
        return False, {}, "Failed to search case after multiple attempts"

class MockScraper:
    """Mock scraper for testing and demonstration purposes"""
    
    def __init__(self):
        self.mock_data = {
            "W.P.(C).15234.2024": {
                "case_number": "15234",
                "case_type": "W.P.(C)",
                "case_title": "Rajesh Kumar Sharma vs Union of India & Ors.",
                "petitioner": "Rajesh Kumar Sharma",
                "respondent": "Union of India & Ors.",
                "filing_date": "2024-03-15",
                "next_hearing_date": "2024-08-15",
                "latest_order": "The Court has directed the respondents to file their response within 4 weeks. The matter relates to the cancellation of a government contract without following due process. The petitioner has challenged the arbitrary action taken by the authorities. Notice issued to all respondents.",
                "judge_name": "Justice Prateek Jalan",
                "case_status": "Pending",
                "court_number": "Court No. 12",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/WPC_15234_2024.pdf"
            },
            "CRL.A.892.2023": {
                "case_number": "892",
                "case_type": "CRL.A.",
                "case_title": "Amit Singh vs State (NCT of Delhi)",
                "petitioner": "Amit Singh",
                "respondent": "State (NCT of Delhi)",
                "filing_date": "2023-06-20",
                "next_hearing_date": "2024-08-20",
                "latest_order": "The appellant has challenged the conviction under Section 420 IPC. Arguments on sentence completed. The Court has reserved judgment after hearing both sides extensively. The matter involves allegations of cheating and criminal breach of trust.",
                "judge_name": "Justice Suresh Kumar Kait",
                "case_status": "Reserved for Judgment",
                "court_number": "Court No. 3",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/CRLA_892_2023.pdf"
            },
            "W.P.(C).4157.2023": {
                "case_number": "4157",
                "case_type": "W.P.(C)",
                "case_title": "Sunita Devi vs State (NCT of Delhi) & Ors.",
                "petitioner": "Sunita Devi",
                "respondent": "State (NCT of Delhi) & Ors.",
                "filing_date": "2023-05-12",
                "next_hearing_date": "2024-08-25",
                "latest_order": "The petitioner seeks regularization of her employment as a sanitation worker. The Court has issued notice to the respondents and directed them to file counter affidavit within 6 weeks. The matter involves regularization of daily wage employees.",
                "judge_name": "Justice Navin Chawla",
                "case_status": "Notice Issued",
                "court_number": "Court No. 5",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/WPC_4157_2023.pdf"
            },
            "CRL.M.A.128.2021": {
                "case_number": "128",
                "case_type": "CRL.M.A.",
                "case_title": "Vinod Kumar vs State (NCT of Delhi)",
                "petitioner": "Vinod Kumar",
                "respondent": "State (NCT of Delhi)",
                "filing_date": "2021-01-15",
                "next_hearing_date": "2024-09-10",
                "latest_order": "Application for regular bail in connection with FIR No. 234/2020 under Sections 376/506 IPC. The Court has heard the arguments and reserved the order. The applicant has been in custody for over 2 years.",
                "judge_name": "Justice Amit Sharma",
                "case_status": "Reserved for Orders",
                "court_number": "Court No. 14",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/CRLMA_128_2021.pdf"
            },
            "FAO(OS).445.2024": {
                "case_number": "445",
                "case_type": "FAO(OS)",
                "case_title": "M/s Global Technologies Pvt. Ltd. vs M/s Indian Software Solutions & Anr.",
                "petitioner": "M/s Global Technologies Pvt. Ltd.",
                "respondent": "M/s Indian Software Solutions & Anr.",
                "filing_date": "2024-01-10",
                "next_hearing_date": "2024-08-25",
                "latest_order": "This appeal challenges the decree passed by the Commercial Court in a contractual dispute involving software licensing. The Court has directed parties to explore mediation. Senior counsel for both parties agreed to attempt settlement through court-annexed mediation.",
                "judge_name": "Justice Sanjeev Narula",
                "case_status": "Referred to Mediation",
                "court_number": "Court No. 8",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/FAOOS_445_2024.pdf"
            },
            "MAT.APP.789.2023": {
                "case_number": "789",
                "case_type": "MAT.APP.",
                "case_title": "Suresh Gupta vs Delhi Transport Corporation & Ors.",
                "petitioner": "Suresh Gupta",
                "respondent": "Delhi Transport Corporation & Ors.",
                "filing_date": "2023-11-22",
                "next_hearing_date": "2024-09-05",
                "latest_order": "The appellant has challenged his termination from service as a bus conductor. The Court has directed the respondent to produce the complete service record of the appellant. The matter involves allegations of misconduct and violation of service rules.",
                "judge_name": "Justice Rekha Palli",
                "case_status": "Documents Pending",
                "court_number": "Court No. 6",
                "pdf_link": f"https://delhihighcourt.nic.in/judgments/MATAPP_789_2023.pdf"
            },
                        "W.P.(C).6345.2022": {
                "case_number": "6345",
                "case_type": "W.P.(C)",
                "case_title": "Neha Mehta vs Delhi University",
                "petitioner": "Neha Mehta",
                "respondent": "Delhi University",
                "filing_date": "2022-09-10",
                "next_hearing_date": "2024-09-18",
                "latest_order": "The petitioner challenges the denial of admission despite securing the cutoff marks. The University has been directed to place the selection list on record.",
                "judge_name": "Justice Anoop Kumar Mendiratta",
                "case_status": "Reply Filed",
                "court_number": "Court No. 9",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/WPC_6345_2022.pdf"
            },
            "CRL.REV.P.304.2023": {
                "case_number": "304",
                "case_type": "CRL.REV.P.",
                "case_title": "Rohit Verma vs State (NCT of Delhi)",
                "petitioner": "Rohit Verma",
                "respondent": "State (NCT of Delhi)",
                "filing_date": "2023-02-28",
                "next_hearing_date": "2024-09-20",
                "latest_order": "Revision filed against trial court order refusing discharge in a fraud case. The State has sought time to file status report.",
                "judge_name": "Justice Swarana Kanta Sharma",
                "case_status": "Status Report Awaited",
                "court_number": "Court No. 11",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CRLREVP_304_2023.pdf"
            },
            "CM.APPL.1023.2024": {
                "case_number": "1023",
                "case_type": "CM.APPL.",
                "case_title": "Anjali Gupta vs Municipal Corporation of Delhi",
                "petitioner": "Anjali Gupta",
                "respondent": "Municipal Corporation of Delhi",
                "filing_date": "2024-04-05",
                "next_hearing_date": "2024-09-12",
                "latest_order": "Application filed seeking stay on demolition of residential premises. MCD directed not to take coercive action till next date.",
                "judge_name": "Justice Vibhu Bakhru",
                "case_status": "Interim Relief Granted",
                "court_number": "Court No. 7",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CMAPPL_1023_2024.pdf"
            },
            "RFA.210.2022": {
                "case_number": "210",
                "case_type": "RFA",
                "case_title": "Deepak Traders vs M/s Kapoor Electronics",
                "petitioner": "Deepak Traders",
                "respondent": "M/s Kapoor Electronics",
                "filing_date": "2022-12-01",
                "next_hearing_date": "2024-10-05",
                "latest_order": "Appeal against decree in a commercial suit. Parties have filed a compromise application. Matter listed for final disposal.",
                "judge_name": "Justice Vikas Mahajan",
                "case_status": "Settlement Pending",
                "court_number": "Court No. 10",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/RFA_210_2022.pdf"
            },
            "CRL.M.C.519.2023": {
                "case_number": "519",
                "case_type": "CRL.M.C.",
                "case_title": "Kunal Bhatia vs State (NCT of Delhi)",
                "petitioner": "Kunal Bhatia",
                "respondent": "State (NCT of Delhi)",
                "filing_date": "2023-07-10",
                "next_hearing_date": "2024-10-12",
                "latest_order": "Petitioner seeks quashing of FIR registered under Sections 498A/406 IPC. Mediation report filed. Court to pass orders on maintainability.",
                "judge_name": "Justice Jyoti Singh",
                "case_status": "Mediation Report Filed",
                "court_number": "Court No. 2",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CRLMC_519_2023.pdf"
            },
            "ARB.A.45.2024": {
                "case_number": "45",
                "case_type": "ARB.A.",
                "case_title": "XYZ Constructions vs Delhi Metro Rail Corporation",
                "petitioner": "XYZ Constructions",
                "respondent": "Delhi Metro Rail Corporation",
                "filing_date": "2024-02-14",
                "next_hearing_date": "2024-10-08",
                "latest_order": "Arbitration appeal concerning delay in civil contract execution. Court has appointed an independent arbitrator with consent of both parties.",
                "judge_name": "Justice Prathiba M. Singh",
                "case_status": "Arbitrator Appointed",
                "court_number": "Court No. 13",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/ARBA_45_2024.pdf"
            },
                        "CS(OS).783.2022": {
                "case_number": "783",
                "case_type": "CS(OS)",
                "case_title": "M/s Elite Interiors vs M/s Skyline Builders",
                "petitioner": "M/s Elite Interiors",
                "respondent": "M/s Skyline Builders",
                "filing_date": "2022-10-30",
                "next_hearing_date": "2024-09-25",
                "latest_order": "Plaintiff seeks specific performance of an interior design agreement. Defendant has been served and time granted for written statement.",
                "judge_name": "Justice C. Hari Shankar",
                "case_status": "Written Statement Awaited",
                "court_number": "Court No. 15",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CSOS_783_2022.pdf"
            },
            "I.A.1125.2023": {
                "case_number": "1125",
                "case_type": "I.A.",
                "case_title": "Mohit Sharma vs National Highway Authority of India",
                "petitioner": "Mohit Sharma",
                "respondent": "National Highway Authority of India",
                "filing_date": "2023-03-15",
                "next_hearing_date": "2024-10-02",
                "latest_order": "Interim application for stay on land acquisition proceedings. Court has issued notice and directed maintenance of status quo.",
                "judge_name": "Justice V. Kameswar Rao",
                "case_status": "Status Quo Ordered",
                "court_number": "Court No. 6",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/IA_1125_2023.pdf"
            },
            "CO.APP.207.2023": {
                "case_number": "207",
                "case_type": "CO.APP.",
                "case_title": "ABC Capital Ltd. vs XYZ Holdings Pvt. Ltd.",
                "petitioner": "ABC Capital Ltd.",
                "respondent": "XYZ Holdings Pvt. Ltd.",
                "filing_date": "2023-05-20",
                "next_hearing_date": "2024-10-10",
                "latest_order": "Company appeal challenging winding-up order. NCLT record summoned. Parties directed to maintain financial status as on date.",
                "judge_name": "Justice Manmeet Pritam Singh Arora",
                "case_status": "Records Summoned",
                "court_number": "Court No. 4",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/COAPP_207_2023.pdf"
            },
            "CRL.M.C.620.2023": {
                "case_number": "620",
                "case_type": "CRL.M.C.",
                "case_title": "Pooja Rani vs State (NCT of Delhi)",
                "petitioner": "Pooja Rani",
                "respondent": "State (NCT of Delhi)",
                "filing_date": "2023-08-12",
                "next_hearing_date": "2024-09-30",
                "latest_order": "Petition for quashing of FIR under Domestic Violence Act. Mediation report placed on record. Matter listed for disposal.",
                "judge_name": "Justice Amit Mahajan",
                "case_status": "Awaiting Final Order",
                "court_number": "Court No. 1",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CRLMC_620_2023.pdf"
            },
            "RFA.322.2023": {
                "case_number": "322",
                "case_type": "RFA",
                "case_title": "Nikhil Jain vs Neha Enterprises",
                "petitioner": "Nikhil Jain",
                "respondent": "Neha Enterprises",
                "filing_date": "2023-09-05",
                "next_hearing_date": "2024-10-18",
                "latest_order": "Regular First Appeal filed against decree for recovery of money. Lower court records requisitioned. Parties directed to file documents.",
                "judge_name": "Justice Prateek Jalan",
                "case_status": "Records Requisitioned",
                "court_number": "Court No. 12",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/RFA_322_2023.pdf"
            },
            "CM.APPL.1490.2024": {
                "case_number": "1490",
                "case_type": "CM.APPL.",
                "case_title": "Geeta Kumari vs Govt. of NCT Delhi",
                "petitioner": "Geeta Kumari",
                "respondent": "Govt. of NCT Delhi",
                "filing_date": "2024-03-25",
                "next_hearing_date": "2024-10-22",
                "latest_order": "Application for early hearing of pending writ petition. Counsel for GNCTD opposes urgency. Court reserved order on application.",
                "judge_name": "Justice Rekha Palli",
                "case_status": "Order Reserved",
                "court_number": "Court No. 10",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/CMAPPL_1490_2024.pdf"
            },
            "O.M.P.(I).33.2022": {
                "case_number": "33",
                "case_type": "O.M.P.(I)",
                "case_title": "Delhi Builders vs DDA",
                "petitioner": "Delhi Builders",
                "respondent": "Delhi Development Authority",
                "filing_date": "2022-11-10",
                "next_hearing_date": "2024-10-01",
                "latest_order": "Application under Section 9 of Arbitration Act. Court granted ad interim relief against invocation of bank guarantee.",
                "judge_name": "Justice Yashwant Varma",
                "case_status": "Interim Relief Granted",
                "court_number": "Court No. 14",
                "pdf_link": "https://delhihighcourt.nic.in/judgments/OMP_I_33_2022.pdf"
            }
        }
    
    def search_case(self, case_type: str, case_number: str, filing_year: str) -> Tuple[bool, Dict, str]:
        """Mock search that returns predefined data"""
        
        time.sleep(random.uniform(1, 3))
        
        case_key = f"{case_type}.{case_number}.{filing_year}"
        
        if case_key in self.mock_data:
            logger.info(f"Mock scraper: Found case {case_key}")
            return True, self.mock_data[case_key], ""
        else:
            logger.info(f"Mock scraper: Case {case_key} not found")
            return False, {}, "Case not found in court records"

def get_scraper(use_mock: bool = False):
    """Factory function to get appropriate scraper"""
    if use_mock:
        return MockScraper()
    else:
        return DelhiHighCourtScraper()