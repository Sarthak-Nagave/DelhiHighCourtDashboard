# 🏛️ Delhi High Court Case Management Dashboard

A powerful, elegant, and developer-friendly platform to search, analyze, and visualize **Delhi High Court case data** — built with **Flask**, smart **OCR-based CAPTCHA solving**, and deep data logging.

This project lets you search real-time case information with ease, extract structured court data, handle CAPTCHAs, and generate downloadable PDFs — all in a responsive and modern UI.

🎥 [Watch Demo Video]([https://drive.google.com/your-video-link](https://drive.google.com/file/d/1NobiiChwMuN5hjMmdOf0sqCMlhrfRZ6R/view?usp=sharing))

---

## ✨ Features at a Glance

### 🔍 Core Functionality

* **Live Court Scraping** – Pulls real data directly from [https://delhihighcourt.nic.in](https://delhihighcourt.nic.in)
* **Case Search** – Find cases using Case Type, Number, and Year
* **CAPTCHA Solver** – Smart OCR-based CAPTCHA handling with image preprocessing
* **Database Logging** – All queries and results are stored with metadata
* **PDF Downloads** – Get printable, formatted case summary PDFs
* **Error Feedback** – Meaningful messages and logs when things go wrong

---

### 📊 Extracted Data Includes

* **Full Case Title** (Parties involved)
* **Filing & Hearing Dates**
* **Judge & Courtroom Info**
* **Latest Orders / Status**
* **PDF Links** to judgments/orders

---

### 🧠 Technical Highlights

* **Flask**-based modular backend
* **PostgreSQL** for logging queries/responses
* **Tesseract OCR** for CAPTCHA handling
* **Mock Data Mode** for testing without real scraping
* **REST API** for programmatic use
* **Bootstrap UI** (Dark theme + Mobile-friendly)

---

## 🧱 Tech Stack

| Layer    | Tech                                       |
| -------- | ------------------------------------------ |
| Backend  | Flask, SQLAlchemy, Requests, BeautifulSoup |
| OCR      | Tesseract + Pillow                         |
| Frontend | HTML, Bootstrap 5, JS, Font Awesome        |
| Database | PostgreSQL (or SQLite for dev)             |

---

## 📁 Project Structure

```
CourtDataDash/
├── app.py                 # Main Flask app
├── scraper.py            # Web scraping logic
├── models.py             # DB models & helper functions
├── mock_data.py          # Sample/mock case data
├── templates/            # HTML templates (Jinja2)
├── static/               # CSS + JS assets
├── project_requirements.txt
├── Dockerfile            # For containerization
└── .env.example          # Sample environment file
```

---

## 🚀 Getting Started

### ✅ Prerequisites

* Python 3.11+
* PostgreSQL or SQLite
* Tesseract OCR

---

### 📦 1. Install Dependencies

```bash
pip install -r project_requirements.txt
```

And install Tesseract:

* Ubuntu/Debian: `sudo apt install tesseract-ocr`
* macOS: `brew install tesseract`
* Windows: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)

---

### ⚙️ 2. Configure `.env`

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/court_cases
SESSION_SECRET=your-secret
USE_MOCK_SCRAPER=true  # switch to false for real scraping
```

---

### 🛠️ 3. Set Up Database

```bash
createdb court_cases
python -c "from app import app; from models import init_db; init_db(app)"
```

---

### ▶️ 4. Run the App

```bash
python app.py
```

It will run on:
👉 `http://127.0.0.1:5000`

---

## 🧪 Test Case Samples

| Case Type | Case No | Year | Status         |
| --------- | ------- | ---- | -------------- |
| W\.P.(C)  | 15234   | 2024 | 🟣 Pending     |
| CRL.A.    | 892     | 2023 | 🟡 Reserved    |
| FAO(OS)   | 445     | 2024 | 🔵 Mediation   |
| CRL.M.A.  | 12456   | 2024 | ✅ Bail Granted |

More mock cases are available in `mock_data.py`.

---

## 🧠 CAPTCHA Handling (Deep Dive)

* Multiple image preprocessing pipelines
* Smart Tesseract configurations
* ViewState / CSRF token extraction
* Session simulation & retries
* Fallback to manual if needed

```python
# Example: Preprocessing steps
image.convert('L')  # Grayscale
ImageEnhance.Contrast(...).enhance(2.0)
ImageFilter.EDGE_ENHANCE
```

---

## 🧾 SQLite + PostgreSQL Logging

All interactions are logged into:

* `queries` table
* `responses` table
* `captcha_logs` table

Supports:

* Success/Fail tracking
* Raw HTML snapshots
* CAPTCHA method performance analysis
* Token logging (ViewState, CSRF, etc.)

---

## 📡 API Endpoints

### Search Case (POST)

```http
POST /search-case
Content-Type: application/x-www-form-urlencoded
```

```bash
curl -X POST http://localhost:5000/search-case \
-d "case_type=W.P.(C)&case_number=15234&filing_year=2024"
```

### Get Stats (GET)

```http
GET /api/stats
```

---

## 🐳 Docker Support

```bash
docker build -t delhi-court-scraper .
docker run -d -p 5000:5000 delhi-court-scraper
```

---

## 🛡️ Legal & Ethical Use

* Built for **educational and research purposes only**
* Adheres to court website terms of use
* Does not store or misuse personal data
* CAPTCHA is bypassed responsibly

---

## 🙌 Contributing

Feel free to fork, improve, and submit pull requests.

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — you're free to use, modify, and distribute it.  
Please credit the original author and respect the terms outlined above.

