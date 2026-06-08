# Slack AI Agent

An intelligent Slack bot that automatically analyzes new workspace members and provides AI-powered insights to help your team engage with potential leads, partners, or key hires.

Built with **FastAPI**, **LangChain**, **Groq (Llama 3.3 70B)**, and **PostgreSQL**.

---

## Features

- **Automatic Member Analysis** — When someone joins your Slack workspace or a specific channel, the agent instantly profiles them.
- **Smart Research** — Fetches company website info and GitHub profile data automatically.
- **LLM-Powered Insights** — Uses Groq-hosted Llama 3.3 70B to score fit, generate observations, and suggest engagement strategies.
- **Color-Coded Slack Reports** — Posts rich, color-coded messages (green/amber/orange/red) based on fit score.
- **PostgreSQL Persistence** — Every analysis is stored for historical reference and reporting.
- **Test Endpoint** — Development-only API to test the AI pipeline without Slack or database.

---

## Architecture

```
Slack Workspace
    │
    │ Socket Mode (WebSocket)
    ▼
FastAPI ──► LangChain ──► Groq (Llama 3.3 70B)
    │                           │
    │                           ▼
    │                    PostgreSQL Database
    │                           │
    ▼                           │
Slack Channel ◄─────────────────┘
```

---

## Tech Stack

| Layer        | Technology                                      |
| ------------ | ----------------------------------------------- |
| Framework    | FastAPI + Uvicorn                               |
| LLM          | Llama 3.3 70B Versatile via Groq                |
| LLM Toolkit  | LangChain (langchain-groq, langchain-core)      |
| Slack SDK    | slack-sdk (Socket Mode + Web API)               |
| Database     | PostgreSQL + SQLAlchemy (async) + asyncpg       |
| HTTP Client  | httpx                                           |
| Config       | Pydantic Settings + python-dotenv               |
| Validation   | Pydantic                                        |

---

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, error handler
│   ├── config.py            # Pydantic settings from .env
│   ├── database.py          # Async SQLAlchemy engine & session
│   ├── models.py            # ORM model: member_analyses table
│   ├── schemas.py           # Pydantic request/response models
│   ├── logger.py            # Logging configuration
│   ├── llm.py               # ChatGroq setup & analysis chain
│   ├── research.py          # Company website + GitHub research
│   ├── slack_client.py      # Slack Socket Mode + Web API client
│   └── routers/
│       ├── health.py        # GET /health
│       └── test.py          # POST /test/analyze-member
├── .env                     # Environment variables (secrets)
├── .env.example             # Template for .env
├── requirements.txt         # Python dependencies
├── runtime.txt              # Python version (for Render)
├── render.yaml              # Render deployment config
├── run.py                   # Entry point
└── COMPY.txt                # Full project documentation
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL database
- Slack App with Socket Mode enabled
- Groq API key

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd slack-ai-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual tokens
```

### Required Environment Variables

| Variable                 | Description                           | Where to Get It                         |
| ------------------------ | ------------------------------------- | --------------------------------------- |
| `SLACK_BOT_TOKEN`        | Bot OAuth token (xoxb-...)            | Slack API → OAuth & Permissions         |
| `SLACK_SIGNING_SECRET`   | App signing secret                    | Slack API → Basic Information           |
| `SLACK_APP_TOKEN`        | App-level token (xapp-...)            | Slack API → Basic Information           |
| `SLACK_PRIVATE_CHANNEL_ID` | Channel for analysis posts          | Right-click channel → Copy link         |
| `GROQ_API_KEY`           | Groq API key (gsk_...)                | https://console.groq.com/keys           |
| `DATABASE_URL`           | PostgreSQL connection string          | Your database provider                  |

Optional: `COMPANY_NAME`, `COMPANY_PRODUCT`, `PORT`, `NODE_ENV`

### Run

```bash
python run.py
```

Or directly with uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

| Method | Path                     | Description                        | Availability |
| ------ | ------------------------ | ---------------------------------- | ------------ |
| GET    | `/health`                | Health check                      | Always       |
| POST   | `/test/analyze-member`   | Run AI pipeline (no Slack/DB save) | Dev only     |

### Testing the AI Pipeline

```bash
curl -X POST http://localhost:8000/test/analyze-member \
  -H "Content-Type: application/json" \
  -d '{
    "memberInfo": {
      "name": "Jane Doe",
      "email": "jane@google.com",
      "title": "VP Engineering"
    }
  }'
```

Sample response:

```json
{
  "success": true,
  "analysis": {
    "fitScore": 90,
    "insights": [
      "VP Engineering title suggests significant technical influence..."
    ],
    "recommendations": [
      "Reach out via email to introduce CloudNest Deploy..."
    ]
  },
  "timestamp": "2026-06-06T07:19:31.200392+00:00"
}
```

---

## How the Pipeline Works

1. **Event Trigger** — A user joins the workspace (`team_join`) or a channel (`member_joined_channel`). Slack sends the event via Socket Mode WebSocket.

2. **Profile Fetch** — `slack_client.get_user_info()` calls Slack's `users.info` API to retrieve the member's name, email, title, and timezone.

3. **Research Phase** — `research.do_basic_research()`:
   - Skips personal email domains (gmail, yahoo, etc.)
   - Visits the member's company website and extracts the `<title>` tag
   - Searches GitHub for matching profiles

4. **AI Analysis** — `llm.analyze_with_ai()`:
   - Builds a prompt with company context, member details, and research data
   - Calls Groq's Llama 3.3 70B via LangChain
   - Parses the JSON response (fitScore, insights, recommendations)

5. **Database Persistence** — `slack_client.save_member_analysis()` inserts the full analysis into PostgreSQL.

6. **Slack Posting** — `slack_client.post_analysis_to_channel()` builds a rich Slack message with color-coded fit score and posts it to your private channel.

7. **Status Update** — The analysis record is marked as `sent_to_slack = true`.

---

## Deployment

### Render

A `render.yaml` is included for one-click deployment. Connect your GitHub repo to Render and it will automatically:

- Detect the Python service
- Install dependencies via `pip install -r requirements.txt`
- Start the server with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set all environment variables in Render's dashboard.

### Manual Deployment

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For production, use a process manager like `gunicorn` with Uvicorn workers or deploy via Docker.

---

## Slack App Configuration

1. Go to https://api.slack.com/apps and create a new app
2. Enable **Socket Mode**
3. Add Bot Token Scopes: `channels:join`, `channels:read`, `chat:write`, `users:read`, `team:read`
4. Subscribe to Bot Events: `team_join`, `member_joined_channel`
5. Install the app to your workspace
6. Copy the Bot Token, Signing Secret, and App Token into your `.env`

---

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoint available (requires NODE_ENV=development)
curl http://localhost:8000/health
curl -X POST http://localhost:8000/test/analyze-member ...
```

---

## License

MIT
