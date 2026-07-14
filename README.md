# Comfort Women History Archive Chatbot

A small Flask web app that answers questions about the history of Japan's
wartime military "comfort women" system, using retrieval-augmented
generation (RAG): questions are answered only from a curated text archive
(`data/comfortwomen_text.txt`), retrieved via a Pinecone vector index and
summarized by an OpenAI model.

The app is aimed at museum visitors — often from other countries and new to
this history — so it is **multilingual** (ask in any language and get an
answer in the language you choose) and answers in a clear, newcomer-friendly
way while staying strictly grounded in the archive.

## What changed in this cleanup

- **Fixed a broken import.** `app.py` and `rag.py` imported from a
  `src.rag` / `src.tools` package that didn't exist in this project — the
  app could not have started before this fix.
- **Removed the duplicate `chat.py`.** Its logic was merged into `rag.py`,
  which also had the more robust, more recently edited version of the
  code. Having two near-identical files with different bugs fixed in each
  was a maintenance hazard.
- **Separated indexing from querying.** The old code re-uploaded the
  *entire* knowledge base to Pinecone on every single chat message (inside
  `get_response`). That's slow, burns API quota, and can create duplicate
  or stale records. Indexing now happens once via `python ingest.py`,
  which you re-run only when you update the source text.
- **Removed debug `print()` statements** that were dumping raw Pinecone
  results to the server console on every request.
- **Added error handling** around the OpenAI and Pinecone calls so a
  missing API key or a network hiccup returns a clear message instead of
  crashing the request.
- **Enriched the knowledge base** with survivor biographies, an overview
  of victims from other countries, the Kono Statement, Japanese court
  cases, the Asian Women's Fund, UN/ILO/US House findings, the 2000
  Women's International War Crimes Tribunal, Korean government responses,
  and the January 2021 Seoul Central District Court ruling — drawn from
  the documents you had uploaded to the project.
- **Rebuilt the front end** as a proper Flask `templates/` +
  `static/` app (the old single HTML file couldn't be served by
  `render_template` without a `templates/` folder), with a calmer,
  purpose-built design instead of default form styling.
- **Added multilingual support.** A language selector lets visitors read the
  interface and receive answers in English, Korean, Japanese, Chinese,
  Spanish, French, or German (with an auto-detect option that replies in
  whatever language the question was asked in). The search still runs against
  the English archive — the question is translated to English internally for
  retrieval, and the final answer is written in the visitor's language.
- **Tuned the answer style for newcomers.** The assistant now briefly explains
  key terms and context for readers unfamiliar with this history, while still
  using only facts found in the archive and never inventing details.
- **Fixed a Python 3.9 incompatibility.** The `X | None` type hints crashed on
  import under Python 3.9; adding `from __future__ import annotations` makes the
  app run on Python 3.9 as well as newer versions.

## Project structure

```
.
├── app.py                  # Flask server (routes: /, /chat, /reset, /health)
├── rag.py                  # Chat orchestration: calls the LLM + retrieval
├── tools.py                # Retrieval: queries Pinecone, with keyword fallback
├── ingest.py                # Run this once to build/refresh the Pinecone index
├── requirements.txt
├── Procfile                 # Process definition for Heroku-style deploys
├── sheet_logger.py           # Optional: logs each Q&A to a Google Sheet
├── .env.example             # Copy to .env and fill in your keys
├── data/
│   └── comfortwomen_text.txt   # Source archive the chatbot answers from
├── templates/
│   └── chatbot.html
└── static/
    ├── style.css
    └── script.js
```

## Prerequisites

- Python 3.9 or newer
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Pinecone API key](https://app.pinecone.io) (free tier is enough to start)

## 1. Set up the project

```bash
# From the project folder
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## 2. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `FLASK_SECRET_KEY` — generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

## 3. Build the search index

This reads `data/comfortwomen_text.txt` and uploads it to Pinecone. You only
need to run this once — and again any time you edit that text file.

```bash
python ingest.py
```

You should see it create the index and upsert each chunk.

## 4. Run the chatbot locally

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

To use a different port: `PORT=8080 python app.py`.

## 5. Try it

Ask things like:
- "Who was Kim Hak-soon?"
- "What was the Kono Statement?"
- "Where is the House of Sharing located?"
- "What happened at the Women's International War Crimes Tribunal?"

If the archive doesn't contain the answer, the bot will say so rather than
guessing — it's instructed to only use the retrieved material.

## Updating the knowledge base

1. Edit `data/comfortwomen_text.txt`. Keep entries as short paragraphs
   separated by a blank line — each paragraph becomes one retrievable chunk.
2. Re-run `python ingest.py` to refresh the Pinecone index.
3. Restart `app.py` if it's already running.

## Deploying (optional)

For a real deployment, don't use Flask's built-in dev server. Use the
included `gunicorn`:

```bash
gunicorn -w 2 -b 0.0.0.0:8080 app:app
```

Whatever platform you deploy to (Render, Railway, Fly.io, a VPS, etc.),
set the same environment variables from `.env` in that platform's
dashboard/secrets manager — don't upload your `.env` file itself.

## Optional: log Q&A pairs to a Google Sheet

The chatbot can append every question/answer pair (with a timestamp and
language) to a Google Sheet, so museum staff can review what visitors are
asking. This is off by default and entirely optional — the chatbot works
fine without it.

**1. Create a Google service account** (a robot identity Google APIs use
instead of a personal login):
- Go to [console.cloud.google.com](https://console.cloud.google.com) and
  create/select a project.
- **APIs & Services → Library** → search "Google Sheets API" → **Enable**.
- **APIs & Services → Credentials → + Create Credentials → Service account**.
  Give it a name, click through the remaining steps (no project role needed).
- Open the service account → **Keys** tab → **Add Key → Create new key** →
  choose **JSON**. This downloads a key file — treat it like a password.

**2. Share your Sheet with it**
- Open the downloaded JSON and copy the `client_email` value
  (looks like `something@your-project.iam.gserviceaccount.com`).
- Open the Google Sheet you want to log to, click **Share**, paste that
  email, and give it **Editor** access.

**3. Configure the app**
- Save the JSON key file somewhere in the project folder (it's already
  gitignored — never commit it) and set in `.env`:
  ```
  GOOGLE_SHEETS_CREDENTIALS_PATH=google_credentials.json
  GOOGLE_SHEET_ID=<the long ID in the sheet's URL>
  ```
- The target worksheet (tab) defaults to `Sheet1` and is created
  automatically with headers if it doesn't exist; override the name with
  `GOOGLE_SHEET_WORKSHEET_NAME` if you want a different tab.

**On Render:** don't upload the JSON key as a normal environment variable —
use Render's **Secret Files** feature instead (Dashboard → your service →
Environment → Secret Files) to mount the file at a path like
`/etc/secrets/google_credentials.json`, then set
`GOOGLE_SHEETS_CREDENTIALS_PATH=/etc/secrets/google_credentials.json` as a
regular environment variable.

Logging is best-effort: if the Sheet isn't configured, or a write fails
(network hiccup, revoked access, etc.), the chatbot still answers normally
and just skips that row — it never blocks or breaks a chat response.

## Notes on content

`data/comfortwomen_text.txt` is written in a respectful, factual register
appropriate for a memorial/educational archive. If you add more source
material, keep entries fact-based, cite specific dates and events where
possible, and avoid graphic detail that isn't necessary for historical
understanding.
