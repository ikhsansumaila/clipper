# Clipper Project

Clipper is an automated workflow system designed to capture YouTube videos via Discord, process them using n8n, and expose the results. 

## Features
- **Discord Integration:** Send a YouTube link in a Discord channel and tag the bot to initiate the clipping process.
- **n8n Workflow Automation:** Coordinates the processing of the videos seamlessly.
- **Results Server:** Serves the processed videos on a dedicated endpoint.

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
- `DISCORD_BOT_TOKEN`
- `DISCORD_BOT_STAGING_TOKEN`
- `N8N_WEBHOOK_URL`
- `N8N_WEBHOOK_TEST_URL`

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
`@octa-bot https://youtube.com/watch?v=...`

The bot will reply indicating that the video is being processed, and hand the link off to the n8n pipeline.

## Recent Updates
- **Discord Bridge Fix:** The `discord-bridge.js` was updated to properly check for bot mentions before processing messages, preventing both production and staging bots from responding simultaneously.