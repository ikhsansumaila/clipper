# Clipper Project

Clipper is an automated workflow system designed to capture YouTube videos via Discord, process them using n8n, and expose the results. It uses **Claude Sonnet 4.5** AI model to intelligently identify and extract the most viral moments from videos.

## Features
- **Discord Integration:** Mention `@your-bot` with a YouTube link in Discord to start the clipping process
- **AI-Powered Analysis:** Uses Claude Sonnet 4.5 to find the most engaging 30-59 second moments
- **Automated Processing:** Transcribes, analyzes, cuts, and captions videos automatically
- **Results Server:** Serves the processed clips on a dedicated web interface

## Architecture & Services
The project runs via Docker Compose and consists of three main services:
1. **n8n_clipper:** The core n8n instance that handles the automation workflows.
2. **discord-bridge:** A Node.js application that listens to Discord messages, responds to mentions, and forwards YouTube links to n8n webhooks.
3. **clipper-results:** A Python-based server that serves the output files (clips).

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
- `MIHAKIDS_AI_API_KEY` - Bearer token for Claude Sonnet 4.5 API

### n8n Workflow Credentials

The n8n workflow requires the following credentials to be configured **inside n8n**:

| Credential Type | Purpose | Required | Notes |
|---|---|---|---|
| **SSH Password** | Execute Python scripts and server commands | ✅ Yes | Hostname, Username, and Password (or SSH key) |
| **HTTP Bearer Auth** | Claude Sonnet 4.5 AI API requests | ✅ Yes | Bearer token for AI model inference |
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
   - Analyzes the transcript using **Claude Sonnet 4.5** AI model
   - Identifies the most viral moment (30-59 seconds)
   - Cuts the video and adds captions
3. **Results Server** hosts the final clip for download

## Python Scripts

Located in `$WORKING_DIR/scripts/python/`, these scripts handle various video processing tasks and can be called from n8n via Execute Command nodes:

### check_url_exists.py
Checks if a YouTube URL has already been processed by looking it up in `history.json`.

**Usage:**
```bash
python3 scripts/python/check_url_exists.py --url "https://www.youtube.com/watch?v=..."
```

**Output:**
- `found` - if the URL exists in history
- `not_found` - if the URL is new

**n8n Integration:**
```bash
python3 ${WORKING_DIR}/scripts/python/check_url_exists.py --url "{{ $json.url }}"
```

### Other Scripts
- `download_file.py` - Download video files from URLs
- `transcribe.py` - Transcribe audio using Whisper
- `transcribe_supadata.py` - Alternative transcription service
- `cut_video.py` - Cut/trim video segments
- `director.py` - Director/editor for video processing
- `add_caption.py` - Add captions to videos
- `checkpoint_manager.py` - Manage processing checkpoints
- `config.py` - Shared configuration constants

## Recent Updates
- **check_url_exists.py:** New script to check URL existence in history.json, replacing bash grep approach for n8n SSH nodes
- **Discord Bridge Fix:** The `discord-bridge.js` was updated to properly check for bot mentions before processing messages, preventing both production and staging bots from responding simultaneously.