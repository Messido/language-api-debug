# Language Learning API

FastAPI backend for the language learning app - serves vocabulary from Google Sheets.

## Quick Start

### 1. Create Virtual Environment

```bash
cd language-api
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google Sheets (See detailed steps below)

1. Create Google Cloud project
2. Enable Google Sheets API
3. Create Service Account
4. Download credentials JSON
5. Share your Google Sheet with the service account email

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your SPREADSHEET_ID and credentials path
```

### 5. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`

## API Endpoints

| Endpoint                               | Description                                |
| -------------------------------------- | ------------------------------------------ |
| `GET /`                                | Health check                               |
| `GET /api/vocabulary`                  | Get all vocabulary (with optional filters) |
| `GET /api/vocabulary?level=A1`         | Filter by CEFR level                       |
| `GET /api/vocabulary?category=animals` | Filter by category                         |
| `GET /api/vocabulary/lesson/1`         | Get words for lesson 1                     |
| `GET /api/vocabulary/levels`           | Get available CEFR levels                  |
| `GET /api/vocabulary/categories`       | Get available categories                   |

## Google Sheets Setup (Detailed)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (e.g., `language-app-api`)

### Step 2: Enable Google Sheets API

1. Go to APIs & Services → Library
2. Search for "Google Sheets API"
3. Click Enable

### Step 3: Create Service Account

1. Go to APIs & Services → Credentials
2. Create Credentials → Service Account
3. Name it (e.g., `sheets-reader`)
4. Create and Continue → Done

### Step 4: Download Credentials

1. Click on your service account
2. Go to Keys tab
3. Add Key → Create new key → JSON
4. Save as `credentials.json` in this folder

### Step 5: Share the Google Sheet

1. Open the credentials.json file
2. Copy the `client_email` value
3. Open your Google Sheet → Share
4. Add the email with Viewer access

### Step 6: Get Spreadsheet ID

From your Google Sheet URL:

```
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID_HERE/edit
```

Add this ID to your `.env` file.

## Project Structure

```
language-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── __init__.py
│   │   └── vocabulary.py    # Vocabulary endpoints
│   └── services/
│       ├── __init__.py
│       └── google_sheets.py # Google Sheets integration
├── credentials.json         # Google credentials (DO NOT COMMIT)
├── .env                     # Environment variables (DO NOT COMMIT)
├── .env.example            # Example environment config
├── .gitignore
├── requirements.txt
└── README.md
```

## Environment Variables

| Variable                         | Description                       |
| -------------------------------- | --------------------------------- |
| `SPREADSHEET_ID`                 | Your Google Sheet ID              |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | Path to credentials.json          |
| `GOOGLE_CREDENTIALS_JSON`        | Full JSON string (for production) |
