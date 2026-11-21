\# ClaimGraph – Evidence-Based Misinformation Investigator



ClaimGraph is a web-based application designed to extract candidate claims from text and collect relevant evidence sources to support preliminary evidence analysis.



It uses Natural Language Processing (NLP), text similarity, and keyword-based techniques to help users investigate information more systematically.



\## Problem Statement



Online misinformation and misleading claims can make it difficult to identify relevant and reliable information. Manually searching for evidence across multiple sources can be time-consuming.



\## Solution



ClaimGraph provides a structured workflow to:

\- Extract candidate claims from submitted text.

\- Identify named entities.

\- Collect relevant evidence sources from the web.

\- Analyze textual relevance between claims and evidence.

\- Store investigation results for review.



\## Key Features



\- Text-based claim extraction

\- Named Entity Recognition

\- Automated evidence collection

\- TF-IDF-based text similarity

\- Keyword overlap analysis

\- Preliminary evidence relevance assessment

\- Investigation and evidence history

\- Web-based user interface



\## Technology Stack



| Component | Technologies |

|---|---|

| Frontend | HTML, CSS, JavaScript |

| Backend | Python, FastAPI |

| Database | SQLite, SQLAlchemy |

| NLP | spaCy, NLTK |

| Text Analysis | Scikit-learn |

| Evidence Search | DDGS |

| Server | Uvicorn |



\## Project Workflow



1\. User submits text for investigation.

2\. ClaimGraph extracts candidate claims.

3\. Relevant entities are identified.

4\. Evidence sources are collected.

5\. Evidence is analyzed using textual similarity and keyword signals.

6\. Results are stored for further review.



\## Project Structure



```text

ClaimGraph/

│

├── backend/

│   ├── app/

│   │   ├── nlp/

│   │   ├── services/

│   │   ├── static/

│   │   ├── database.py

│   │   ├── main.py

│   │   ├── models.py

│   │   └── schemas.py

│   │

│   └── requirements.txt

│

├── .gitignore

├── package-lock.json

└── README.md

```



\## Installation and Setup



\### 1. Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd ClaimGraph

```



\### 2. Create a virtual environment



```bash

cd backend

python -m venv .venv

```



\### 3. Activate the virtual environment



Windows PowerShell:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



\### 4. Install dependencies



```bash

python -m pip install -r requirements.txt

```



\### 5. Start the application



```bash

python -m uvicorn app.main:app --reload --port 8001

```



\### 6. Open the application



Web Interface:



http://127.0.0.1:8001/app



API Documentation:



http://127.0.0.1:8001/docs



\## Limitations



\- Claim extraction uses rule-based NLP methods.

\- Evidence analysis uses preliminary text similarity and keyword signals.

\- Similarity scores do not represent the probability that a claim is true.

\- The application does not independently verify whether a claim is true or false.

\- Original sources should always be reviewed for context and reliability.



\## Future Enhancements



\- Advanced claim extraction models

\- Improved source credibility analysis

\- Better contextual evidence matching

\- Enhanced visual analytics dashboard

\- Multilingual claim analysis



\## Project Purpose



ClaimGraph is an academic project developed to explore NLP, evidence collection, text analysis, and misinformation investigation.



\*\*Note:\*\* ClaimGraph is an evidence investigation support tool, not an automated fact-checking authority.



