"""Mock data for Delhi High Court cases"""

# Case types available in Delhi High Court
CASE_TYPES = [
    "W.P.(C)",  # Writ Petition (Civil)
    "CRL.A.",   # Criminal Appeal
    "FAO(OS)",  # First Appeal from Original Side
    "CRL.M.A.", # Criminal Miscellaneous Application
    "MAT.APP.", # Matter Appeal
    "CO.APP.",  # Company Appeal
    "CS(OS)",   # Civil Suit (Original Side)
    "I.A.",     # Interim Application
    "CRL.REV.P.", # Criminal Revision Petition
    "O.M.P.(I)", # Original Miscellaneous Petition (I)
]

# Mock case database
MOCK_CASES = {
    "W.P.(C).15234.2024": {
        "case_number": "15234",
        "case_type": "W.P.(C)",
        "filing_date": "2024-03-15",
        "next_hearing_date": "2024-08-15",
        "petitioner": "Rajesh Kumar Sharma",
        "respondent": "Union of India & Ors.",
        "latest_order": "The Court has directed the respondents to file their response within 4 weeks. The matter relates to the cancellation of a government contract without following due process. The petitioner has challenged the arbitrary action taken by the authorities. Notice issued to all respondents.",
        "judge_name": "Justice Prateek Jalan",
        "status": "Pending",
        "court_number": "Court No. 12"
    },
    
    "CRL.A.892.2023": {
        "case_number": "892",
        "case_type": "CRL.A.",
        "filing_date": "2023-06-20",
        "next_hearing_date": "2024-08-20",
        "petitioner": "Amit Singh",
        "respondent": "State (NCT of Delhi)",
        "latest_order": "The appellant has challenged the conviction under Section 420 IPC. Arguments on sentence completed. The Court has reserved judgment after hearing both sides extensively. The matter involves allegations of cheating and criminal breach of trust.",
        "judge_name": "Justice Suresh Kumar Kait",
        "status": "Reserved for Judgment",
        "court_number": "Court No. 3"
    },
    
    "FAO(OS).445.2024": {
        "case_number": "445",
        "case_type": "FAO(OS)",
        "filing_date": "2024-01-10",
        "next_hearing_date": "2024-08-25",
        "petitioner": "M/s Global Technologies Pvt. Ltd.",
        "respondent": "M/s Indian Software Solutions & Anr.",
        "latest_order": "This appeal challenges the decree passed by the Commercial Court in a contractual dispute involving software licensing. The Court has directed parties to explore mediation. Senior counsel for both parties agreed to attempt settlement through court-annexed mediation.",
        "judge_name": "Justice Sanjeev Narula",
        "status": "Referred to Mediation",
        "court_number": "Court No. 8"
    },
    
    "CRL.M.A.12456.2024": {
        "case_number": "12456",
        "case_type": "CRL.M.A.",
        "filing_date": "2024-05-08",
        "next_hearing_date": "2024-08-10",
        "petitioner": "Priya Mehta",
        "respondent": "State (NCT of Delhi) & Anr.",
        "latest_order": "Application for anticipatory bail in connection with FIR No. 245/2024 under Section 406/420 IPC. The Court has heard the counsel for the applicant and Public Prosecutor. Considering the nature of allegations and the fact that the applicant is a woman, bail is granted subject to conditions.",
        "judge_name": "Justice Amit Sharma",
        "status": "Bail Granted",
        "court_number": "Court No. 15"
    },
    
    "MAT.APP.789.2023": {
        "case_number": "789",
        "case_type": "MAT.APP.",
        "filing_date": "2023-11-22",
        "next_hearing_date": "2024-09-05",
        "petitioner": "Suresh Gupta",
        "respondent": "Delhi Transport Corporation & Ors.",
        "latest_order": "The appellant has challenged his termination from service as a bus conductor. The Court has directed the respondent to produce the complete service record of the appellant. The matter involves allegations of misconduct and violation of service rules.",
        "judge_name": "Justice Rekha Palli",
        "status": "Documents Pending",
        "court_number": "Court No. 6"
    },
    
    "CO.APP.123.2024": {
        "case_number": "123",
        "case_type": "CO.APP.",
        "filing_date": "2024-02-28",
        "next_hearing_date": "2024-08-30",
        "petitioner": "M/s Delhi Developers Ltd.",
        "respondent": "M/s Capital Builders & Ors.",
        "latest_order": "Appeal against the winding up order passed by the Company Court. The Court has stayed the winding up proceedings subject to the appellant depositing 50% of the admitted amount within 8 weeks. The matter involves disputes over construction contracts.",
        "judge_name": "Justice Vibhu Bakhru",
        "status": "Stay Granted",
        "court_number": "Court No. 4"
    },
    
    "CS(OS).567.2023": {
        "case_number": "567",
        "case_type": "CS(OS)",
        "filing_date": "2023-09-14",
        "next_hearing_date": "2024-08-18",
        "petitioner": "Mrs. Sunita Agarwal",
        "respondent": "M/s Real Estate Ventures & Ors.",
        "latest_order": "Suit for specific performance of agreement to sell. The Court has directed the defendants to file written statement within 30 days. Plaintiff seeks possession of property and damages for breach of contract. Issues to be framed at next hearing.",
        "judge_name": "Justice C. Hari Shankar",
        "status": "Written Statement Pending",
        "court_number": "Court No. 10"
    },
    
    "I.A.9876.2024": {
        "case_number": "9876",
        "case_type": "I.A.",
        "filing_date": "2024-04-12",
        "next_hearing_date": "2024-08-12",
        "petitioner": "Vikash Enterprises",
        "respondent": "Municipal Corporation of Delhi",
        "latest_order": "Interim application seeking stay of demolition of commercial property. The Court has granted interim stay for 4 weeks and directed the respondent to show cause why the demolition order should not be stayed. The matter involves allegations of illegal construction.",
        "judge_name": "Justice Navin Chawla",
        "status": "Interim Stay Granted",
        "court_number": "Court No. 13"
    },
    
    "CRL.REV.P.334.2023": {
        "case_number": "334",
        "case_type": "CRL.REV.P.",
        "filing_date": "2023-12-05",
        "next_hearing_date": "2024-08-22",
        "petitioner": "Mohit Sharma",
        "respondent": "State (NCT of Delhi) & Anr.",
        "latest_order": "Revision petition against the order of conviction and sentence passed by the Sessions Court. The Court has heard arguments on the question of law involved. The matter relates to interpretation of Section 138 of Negotiable Instruments Act. Reserved for orders.",
        "judge_name": "Justice Anup Jairam Bhambhani",
        "status": "Reserved for Orders",
        "court_number": "Court No. 7"
    },
    
    "O.M.P.(I).2345.2024": {
        "case_number": "2345",
        "case_type": "O.M.P.(I)",
        "filing_date": "2024-01-25",
        "next_hearing_date": "2024-08-28",
        "petitioner": "Tech Solutions India Pvt. Ltd.",
        "respondent": "Digital Services Corp. & Ors.",
        "latest_order": "Application under Section 9 of Arbitration and Conciliation Act, 2015 seeking interim measures. The Court has directed the respondents to maintain status quo regarding the disputed software IP. The arbitral tribunal has been constituted and proceedings are ongoing.",
        "judge_name": "Justice Amit Bansal",
        "status": "Status Quo Directed",
        "court_number": "Court No. 11"
    }
}

# Years available for filing
FILING_YEARS = list(range(2015, 2026))
