# Clipper Project

Clipper is an automated workflow system designed to capture YouTube videos via Discord, process them using n8n, and expose the results. It uses an **AI model** (configurable) to intelligently identify and extract the most viral moments from videos.

## Features
- **Discord Integration:** Mention `@your-bot` with a YouTube link in Discord to start the clipping process
- **AI-Powered Analysis:** Uses advanced LLMs to find the most engaging 30-59 second moments
- **Automated Processing:** Transcribes, analyzes, cuts, and captions videos automatically
- **Results Server:** Serves the processed clips on a dedicated web interface

## Architecture & Services
The project runs via Docker Compose and consists of four main services:
1. **n8n_clipper:** The core n8n instance that handles the automation workflows.
2. **discord-bridge:** A Node.js application that listens to Discord messages, responds to mentions, and forwards YouTube links to n8n webhooks.
3. **clipper-pipeline:** A persistent Python 3.11 container with FFmpeg and AI libraries that acts as the execution engine for all video processing scripts.
4. **clipper-results:** A Python-based server that serves the output files (clips) and provides the web UI dashboard.

## Directory Structure
The project is organized functionally to separate data, pipeline logic, and web services:

```text
/home/ubuntu/clipper/
├── docker-compose.yml
├── .env
├── n8n_data/                # n8n database and settings
├── data/                    # Unified I/O and State Layer
│   ├── db/                  # state.json & history.json
│   ├── source/              # Downloaded raw videos & transcripts
│   ├── temp/                # Temporary processing files (cuts, subtitles)
│   └── results/             # Final MP4 clips and thumbnails
├── pipeline/                # Python Processing Engine
│   ├── Dockerfile           # Installs FFmpeg, Python 3, ML dependencies
│   ├── requirements.txt
│   └── src/                 # All Python logic scripts (config, director, etc.)
├── results-server/          # Web UI & API Server
│   ├── Dockerfile
│   ├── server.py
│   └── static/              # HTML/CSS/JS for the dashboard
└── discord-bridge/          # Discord Bot Service
    ├── discord-bridge.js
    └── package.json
```

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Node.js (for local script testing if needed)
- A Discord Bot Token
- An n8n Webhook URL

### Environment Variables
Copy `.env.example` to `.env` and fill in the required values:
```bash
cp .env.example .env
```
Ensure you have the following variables properly set:
- `DISCORD_BOT_TOKEN` - Token for production bot
- `DISCORD_BOT_STAGING_TOKEN` - Token for staging bot (n8n test workflow)
- `N8N_WEBHOOK_URL` - Production webhook endpoint
- `N8N_WEBHOOK_TEST_URL` - Staging webhook endpoint
- `SUPADATA_API_KEY` - For video metadata queries
- `MIHAKIDS_AI_API_KEY` - Bearer token for your AI model inference (e.g., OpenAI, Claude, etc.)

### n8n Workflow Credentials

The n8n workflow requires the following credentials to be configured **inside n8n**:

| Credential Type | Purpose | Required | Notes |
|---|---|---|---|
| **SSH Password** | Execute Python scripts and server commands | ✅ Yes | Hostname, Username, and Password (or SSH key) |
| **HTTP Bearer Auth** | AI API requests | ✅ Yes | Bearer token for AI model inference |
| **Discord Bot API** | Send messages to Discord channels | ✅ Yes (×2) | One for production (`your-bot`), one for staging |
| **Apify API** | YouTube metadata scraping & downloads | ✅ Yes (×2) | Primary and fallback API keys |
| **VideoSailor API** | Alternative video download service | ⚠️ Optional | Fallback if Apify fails |
| **Supadata API** | Video metadata queries | ⚠️ Optional | Alternative metadata source |

### Apify Actors Used

The workflow uses the following Apify actors for YouTube video processing:

| Node Name | Actor | Purpose |
|---|---|---|
| **Get video metadata** | [YouTube Scraper](https://apify.com/actors/h7sDV53CddomktSi5) | Scrape YouTube video metadata (title, duration, etc.) |
| **Get download url** | [YouTube Downloader](https://apify.com/actors/G1dli5lUik9LaUH0N) | Get direct download URLs for video files |
| **Get download url (API KEY 2)** | [YouTube Downloader](https://apify.com/actors/G1dli5lUik9LaUH0N) | Fallback YouTube Downloader with secondary API key |

> **Note:** You'll need valid Apify API credentials to use these actors. Create a free account at [apify.com](https://apify.com) to get started.

**Setup Instructions:**
1. Open your n8n instance
2. Go to **Settings > Credentials** 
3. Create new credentials for each type listed above
4. Copy the credential ID after creation
5. Update the n8n workflow JSON or re-configure the nodes with your new credentials

> ⚠️ **Security:** All credentials are stored securely in n8n. Never commit real credentials to version control.

### Running the Project
To start all services, run:
```bash
docker compose up -d
```
atau
```bash
docker-compose up -d
```

### Usage
In your configured Discord channel, mention the bot and include a YouTube link:
`@your-bot https://youtube.com/watch?v=...`

The bot will reply indicating that the video is being processed, and hand the link off to the n8n pipeline.

### How It Works
1. **Discord Bridge** receives the message and extracts the YouTube URL
2. **n8n Workflow** processes the video:
   - Downloads the video using Apify API
   - Transcribes audio with Whisper
   - Analyzes the transcript using an **AI model** (via API)
   - Identifies the most viral moment (30-59 seconds)
   - Cuts the video and adds captions
3. **Results Server** hosts the final clip for download

## Python Scripts (Pipeline Engine)

Located in `pipeline/src/`, these scripts handle various video processing tasks. They are executed securely inside the `clipper_pipeline` Docker container, keeping the host OS clean.

### The Wrapper Executor (`run.py`)
To prevent memory leaks and runaway processes, all scripts should be executed using the `run.py` wrapper. This script automatically enforces a virtual memory limit (`ulimit -v`) and a timeout.

**Default limits applied by `run.py`:**
- Memory Limit: 3,000,000 KB (approx 3GB)
- Timeout: 600 seconds (10 minutes)

If a process exceeds the timeout, it gracefully kills the script, outputs a clean timeout message, and exits with code 124.

**n8n Execution Pattern:**
Every Execute Command (SSH) node in n8n should follow this pattern:
```bash
docker exec clipper_pipeline python3 run.py [script_name.py] [arguments]
```

---

### check_url_exists.py
Checks if a YouTube URL has already been processed by looking it up in `data/db/history.json`.

**Usage (from host or via SSH in n8n):**
```bash
docker exec clipper_pipeline python3 run.py check_url_exists.py --url "https://www.youtube.com/watch?v=..."
```

**Output:**
- `found` - if the URL exists in history
- `not_found` - if the URL is new

**n8n Integration:**
```bash
docker exec clipper_pipeline python3 run.py check_url_exists.py --url "{{ $json.url }}"
```

### Other Scripts
Because the container's working directory is automatically set to `pipeline/src/`, you can call the rest of the scripts seamlessly from n8n using the wrapper:
- `docker exec clipper_pipeline python3 run.py transcribe_supadata.py` - AI Transcription
- `docker exec clipper_pipeline python3 run.py director.py` - LLM Analysis & Clip Selection
- `docker exec clipper_pipeline python3 run.py cut_video.py` - Trim video segments via FFmpeg
- `docker exec clipper_pipeline python3 run.py add_caption.py` - Render subtitles and thumbnails

*You can also override the default limits per-node if needed:*
```bash
# Example: Allow add_caption to run up to 20 minutes
docker exec clipper_pipeline python3 run.py add_caption.py --timeout 1200
```

*Helper modules:*
- `checkpoint_manager.py` - Manage processing checkpoints and re-clips
- `config.py` - Shared configuration and folder path definitions

## Recent Updates
- **Pipeline Dockerization:** Python scripts now run inside a dedicated `clipper_pipeline` container, isolating FFmpeg and AI dependencies from the host OS.
- **Wrapper Executor (`run.py`):** Replaced manual bash `ulimit` and `timeout` logic with a clean Python wrapper for all n8n node executions.
- **Directory Restructuring:** All output files, raw sources, and databases are now cleanly stored in the centralized `/data` directory.
- **check_url_exists.py:** Script automatically builds a fresh `state.json` when triggering a re-clip for a known URL.