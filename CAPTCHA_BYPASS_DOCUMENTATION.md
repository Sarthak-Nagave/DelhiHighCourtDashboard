# 🤖 CAPTCHA Bypass & Logging System – Documentation

This document walks you through the **intelligent CAPTCHA handling** and **deep logging mechanisms** used in the Delhi High Court Case Scraper project.

Whether you're debugging your own scraper or optimizing performance, this guide explains how everything works under the hood — from OCR pipelines to SQLite logging schemas.

---

## 🔐 CAPTCHA Bypass System

### 🧠 Strategy Overview

CAPTCHAs are tackled using multiple smart strategies:

* Automated OCR with image preprocessing
* Token + session preservation
* Optional third-party CAPTCHA service hooks
* Fallback mechanisms for resilience

---

### 🧪 OCR-Based CAPTCHA Solving (Primary Method)

We use **Tesseract OCR** with a multi-step image enhancement pipeline.

#### 🔧 Image Preprocessing Steps

Each CAPTCHA image is processed using several filters:

* 🖤 **Grayscale** conversion
* 🎯 **Contrast** boost (2x)
* ☀️ **Brightness** tuning
* ✏️ **Sharpening**
* 🧱 **Edge Enhancement**
* 🔇 **Noise Reduction**

#### 🔠 Tesseract Configurations Used

We run multiple OCR passes using varying `--psm` modes and character whitelists:

```python
configs = [
    '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    '--psm 8',
    '--psm 7'
]
```

#### 🎯 Confidence Scoring

* Prioritizes 6-character results (most common pattern)
* Scores based on character clarity and consistency
* Accepts results if confidence ≥ `0.7`

---

### 🧾 Session & Cookie Handling

* **Cookies are preserved** across requests
* **Form tokens like `__VIEWSTATE`, CSRF** are extracted and reused
* Sessions are **persisted and reused** to avoid triggering new CAPTCHAs

---

### 🔌 Optional CAPTCHA Service Support

The system is ready for integration with:

* `2captcha`
* `AntiCaptcha`
* `CapMonster`
* `DeathByCaptcha`

You just need to plug in your API key — fallback to manual or OCR still works.

---

### 🛡️ Fallbacks & Failsafes

Even when OCR isn't confident:

* Tries submission anyway
* Optionally shows image for **manual entry**
* Handles sites that accept **empty CAPTCHA** fields

---

## 🔐 Token Extraction Engine

### 💡 What Tokens Are Handled?

Common ASP.NET + CSRF fields:

* `__VIEWSTATE`
* `__VIEWSTATEGENERATOR`
* `__EVENTVALIDATION`
* Hidden form CSRFs
* JavaScript-embedded CSRFs
* Meta tags + `data-*` attributes

#### Token Patterns Detected From:

* `<input type="hidden" ...>`
* `<meta name="csrf-token" ...>`
* `<script>csrf: 'token'</script>`
* `<div data-token="...">`

The system uses:

* **Regex + DOM traversal**
* **Script parsing**
* **Attribute scanning**

---

## 🧱 SQLite Logging System

Every action your scraper takes — every query, token, image, and response — is logged.

---

### 📋 Tables & Schema

#### 🔍 `scraper_queries`

Tracks every search made.

```sql
CREATE TABLE scraper_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_type TEXT, case_number TEXT, filing_year TEXT,
    query_hash TEXT UNIQUE,
    ip_address TEXT, user_agent TEXT,
    session_id TEXT,
    attempt_number INTEGER DEFAULT 1,
    success BOOLEAN,
    error_message TEXT,
    captcha_required BOOLEAN, captcha_solved BOOLEAN,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### 🌐 `scraper_responses`

Stores the actual HTML and headers received.

```sql
CREATE TABLE scraper_responses (
    id INTEGER PRIMARY KEY,
    query_id INTEGER,
    request_url TEXT, response_status INTEGER,
    request_headers TEXT, response_headers TEXT,
    raw_html TEXT,
    html_hash TEXT,
    parsed_data TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### 🧩 `captcha_attempts`

Logs every OCR or manual CAPTCHA solve attempt.

```sql
CREATE TABLE captcha_attempts (
    id INTEGER PRIMARY KEY,
    query_id INTEGER,
    captcha_url TEXT,
    ocr_result TEXT, manual_solution TEXT,
    method_used TEXT,  -- e.g., 'ocr', 'manual'
    success BOOLEAN,
    confidence_score REAL,
    processing_time_ms INTEGER
);
```

---

#### 🔑 `viewstate_tokens`

Captures all form token values for each session.

```sql
CREATE TABLE viewstate_tokens (
    id INTEGER PRIMARY KEY,
    query_id INTEGER,
    viewstate TEXT, csrf_token TEXT,
    viewstate_generator TEXT, event_validation TEXT,
    session_token TEXT,
    other_tokens TEXT
);
```

---

## 📊 Analytics & Insights

### 🔐 CAPTCHA Success Rate

```sql
SELECT method_used, COUNT(*) as attempts,
       SUM(success) as successes,
       ROUND(AVG(confidence_score), 2) as avg_conf,
       ROUND(AVG(processing_time_ms), 1) as avg_time
FROM captcha_attempts
GROUP BY method_used;
```

---

### 🚀 Query Performance Over Time

```sql
SELECT DATE(created_at), COUNT(*) as total,
       AVG(response_time_ms) as avg_time,
       SUM(success) as successes
FROM scraper_queries
GROUP BY DATE(created_at);
```

---

### 🧪 Token Effectiveness

```sql
SELECT COUNT(*) as with_tokens,
       AVG(LENGTH(viewstate)) as avg_vs_len,
       COUNT(csrf_token) as csrf_present
FROM viewstate_tokens;
```

---

## 🧰 Developer Usage Examples

### Basic Search with Logging

```python
scraper = DelhiHighCourtScraper(db_path="court_scraper.db")

success, data, error = scraper.search_case(
    "W.P.(C)", "15234", "2024",
    ip_address="192.168.0.10",
    user_agent="Mozilla/5.0"
)

if success:
    print(data["case_title"])
else:
    print("Error:", error)
```

---

### Query CAPTCHA Logs

```python
import sqlite3
conn = sqlite3.connect("court_scraper.db")

rows = conn.execute("""
SELECT method_used, COUNT(*), ROUND(AVG(confidence_score),2)
FROM captcha_attempts GROUP BY method_used
""").fetchall()

for row in rows:
    print(row)
```

---

## ⚙️ Configuration & Environment Variables

```env
# General
CAPTCHA_CONFIDENCE_THRESHOLD=0.7
CAPTCHA_MAX_RETRIES=3

# OCR
TESSERACT_CMD=/usr/bin/tesseract
OCR_PREPROCESSING=true

# Database
SQLITE_DB_PATH=court_scraper.db
LOG_LEVEL=INFO
```

---

## 🔒 Security Considerations

* Session reuse avoids raising flags
* Tokens are stored securely
* No personal/private data is stored
* Logs are audit-friendly

---

## 🧠 Troubleshooting

| Issue                | Fix                                                         |
| -------------------- | ----------------------------------------------------------- |
| OCR fails            | Enable all preprocessing, install correct Tesseract version |
| Tokens not found     | Check `raw_html` logs, inspect hidden inputs                |
| CAPTCHA always fails | Lower confidence threshold, enable manual fallback          |
| DB not writing       | Check file permissions or disk space                        |

---

## 🔧 Performance Tips

* Clean old logs regularly
* Batch search multiple cases
* Optimize database indices
* Enable debug logging only when needed

---

This system was designed with care to balance **scraping accuracy**, **legal boundaries**, and **robust diagnostics**. You're in control — and well-informed — at every step.

---

