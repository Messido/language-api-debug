# Language Learning API

> **LLM Context**: This is the FastAPI backend for a French language learning application. It connects to a private Google Sheet containing vocabulary data and serves it to the React frontend (`language-app`).

## Project Overview

### What This API Does

- Fetches French vocabulary from a **private Google Sheet** maintained by the client
- Transforms raw CSV-like data into flashcard-friendly format
- Serves vocabulary to the React frontend with filtering capabilities
- Keeps Google credentials secure (not exposed to frontend)

### Architecture

```
┌─────────────┐     fetch      ┌─────────────────┐   Google API   ┌───────────────┐
│  React App  │  ───────────►  │  This FastAPI   │  ───────────►  │ Google Sheets │
│ language-app│  ◄───────────  │    Backend      │  ◄───────────  │   (Private)   │
│ :5173       │     JSON       │    :8000        │     JSON       │  Vocabulary   │
└─────────────┘                └─────────────────┘                └───────────────┘
```

### Key Features

- **Private Sheet Access**: Uses Google Service Account to access non-public sheets
- **Real-time Updates**: When client updates the sheet, API returns fresh data
- **Filtering**: Filter by CEFR level (A1, A2, B1, B2, C1) or category
- **Pagination**: Get words by lesson for structured learning
- **Data Transformation**: Converts raw sheet data to flashcard format

---

## Data Structure

### Google Sheet Columns (Expected)

The API expects these columns in the vocabulary Google Sheet:

| Column Name               | Description                  | Example           |
| ------------------------- | ---------------------------- | ----------------- |
| Unique ID                 | Unique identifier            | `N001`            |
| English Word              | English translation          | `Dog`             |
| Masculine                 | Masculine French form        | `Chien`           |
| Feminine                  | Feminine French form         | `Chienne`         |
| No Gender                 | Gender-neutral form          | -                 |
| Pronunciation             | Phonetic pronunciation       | `shee-en`         |
| Pronunciation - Masculine | Masculine pronunciation      | -                 |
| Pronunciation - Feminine  | Feminine pronunciation       | -                 |
| French Sentence           | Example sentence in French   | `Le chien court.` |
| English Sentence          | Example sentence translation | `The dog runs.`   |
| CEFR Level                | Language proficiency level   | `A1`, `A2`, `B1`  |
| Category                  | Word category                | `Animals`, `Food` |
| Sub Category              | Sub-category                 | `Pets`, `Farm`    |

### API Response Format (Flashcard)

The API transforms sheet data into this frontend-friendly format:

```json
{
  "id": "N001",
  "english": "Dog",
  "forms": [
    {
      "word": "Chien",
      "gender": "Masculine ♂",
      "genderColor": "text-sky-500",
      "pronunciation": "shee-en"
    },
    {
      "word": "Chienne",
      "gender": "Feminine ♀",
      "genderColor": "text-pink-500",
      "pronunciation": "shee-en"
    }
  ],
  "exampleTarget": "Le chien court.",
  "exampleNative": "The dog runs.",
  "phonetic": "shee-en",
  "level": "A1",
  "category": "Animals",
  "image": ""
}
```

---

## API Endpoints

| Endpoint                           | Method | Description                   |
| ---------------------------------- | ------ | ----------------------------- |
| `/`                                | GET    | Root health check             |
| `/health`                          | GET    | Health status                 |
| `/api/vocabulary`                  | GET    | Get all vocabulary words      |
| `/api/vocabulary?level=A1`         | GET    | Filter by CEFR level          |
| `/api/vocabulary?category=animals` | GET    | Filter by category            |
| `/api/vocabulary?limit=20`         | GET    | Limit results                 |
| `/api/vocabulary?transform=false`  | GET    | Return raw sheet data         |
| `/api/vocabulary/lesson/{id}`      | GET    | Get words for specific lesson |
| `/api/vocabulary/levels`           | GET    | List available CEFR levels    |
| `/api/vocabulary/categories`       | GET    | List available categories     |

### Example Requests

```bash
# Get all A1 level words
curl http://localhost:8000/api/vocabulary?level=A1

# Get lesson 1 (first 10 words)
curl http://localhost:8000/api/vocabulary/lesson/1

# Get 5 words from "Animals" category
curl http://localhost:8000/api/vocabulary?category=Animals&limit=5
```

---

## Project Structure

```
language-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   │                            # - CORS configuration
│   │                            # - Router includes
│   │                            # - Health endpoints
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── vocabulary.py        # Vocabulary endpoints
│   │                            # - /api/vocabulary
│   │                            # - /api/vocabulary/lesson/{id}
│   │                            # - transform_to_flashcard()
│   │
│   └── services/
│       ├── __init__.py
│       └── google_sheets.py     # Google Sheets integration
│                                # - get_credentials()
│                                # - fetch_vocabulary()
│
├── credentials.json             # Google Service Account key (DO NOT COMMIT)
├── .env                         # Environment variables (DO NOT COMMIT)
├── .env.example                 # Example env config
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Related Frontend Files

The React frontend (`language-app`) consumes this API:

| File                                                | Purpose                        |
| --------------------------------------------------- | ------------------------------ |
| `src/services/vocabularyApi.js`                     | API client functions           |
| `src/features/vocabulary/pages/LessonLearnPage.jsx` | Flashcard learning page        |
| `src/features/vocabulary/components/lesson-learn/`  | Extracted flashcard components |

### Frontend API Service Location

```
language-app/src/services/vocabularyApi.js
```

### Environment Variable (Frontend)

```env
VITE_API_URL=http://localhost:8000
```

---

## Quick Start

### 1. Create Virtual Environment

```bash
cd language-api
python -m venv venv

# Windows (Git Bash)
source venv/Scripts/activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google Sheets

See [Google Sheets Setup](#google-sheets-setup-detailed) section below.

### 4. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your SPREADSHEET_ID
```

### 5. Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access API docs at: `http://localhost:8000/docs`

---

## Google Sheets Setup (Detailed)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: `language-app-api`

### Step 2: Enable Google Sheets API

1. Go to **APIs & Services** → **Library**
2. Search for **"Google Sheets API"**
3. Click **Enable**

### Step 3: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Name: `sheets-reader`
4. Click **Create and Continue** → **Done**

### Step 4: Download Credentials

1. Click on your service account
2. Go to **Keys** tab
3. **Add Key** → **Create new key** → **JSON**
4. Save as `credentials.json` in `language-api/` folder

### Step 5: Share Google Sheet

1. Open `credentials.json`
2. Copy the `client_email` value (e.g., `sheets-reader@project.iam.gserviceaccount.com`)
3. Open your vocabulary Google Sheet
4. Click **Share** → Paste email → Set **Viewer** access

### Step 6: Get Spreadsheet ID

From the Google Sheet URL:

```
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
```

Add to `.env`:

```env
SPREADSHEET_ID=YOUR_SPREADSHEET_ID
```

---

## Environment Variables

| Variable                         | Description              | Required       |
| -------------------------------- | ------------------------ | -------------- |
| `SPREADSHEET_ID`                 | Google Sheet ID from URL | Yes            |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | Path to credentials.json | For local dev  |
| `GOOGLE_CREDENTIALS_JSON`        | Full JSON string         | For production |

---

## Security Notes

- ✅ **Sheet stays private** - only the service account can access it
- ✅ **Credentials on server only** - never exposed to frontend
- ✅ **Read-only access** - service account cannot modify sheet
- ⚠️ **Never commit** `credentials.json` or `.env` files

---

## Development Notes

### Adding New Endpoints

1. Add route function in `app/routes/vocabulary.py`
2. Router is already included in `main.py`

### Modifying Data Transformation

Edit `transform_to_flashcard()` in `app/routes/vocabulary.py` to change how sheet data maps to flashcard format.

### Adding Caching

To reduce Google API calls, add caching in `app/services/google_sheets.py`:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def fetch_vocabulary_cached():
    return fetch_vocabulary()
```

---

## Future Improvements

- [ ] Add caching to reduce API calls
- [ ] Add user progress tracking
- [ ] Implement spaced repetition endpoints
- [ ] Add image URL support for flashcards
- [ ] Add pronunciation audio endpoints
