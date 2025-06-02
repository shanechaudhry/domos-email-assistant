# Domos Email Assistant

This project is a take-home assignment designed to simulate the real-world responsibilities of an AI assistant for property management. The assistant connects to a Gmail inbox, classifies and responds to incoming tenant emails, and creates actionable workflow items such as maintenance tickets or rent inquiries.

## Features

- Connects to a Gmail inbox via IMAP
- Fetches and processes all unread emails
- Loads mock tenant data including lease details and recent issues
- Generates plain-text replies using a combination of:
  - Mistral-7B via Together.ai API
  - Rule-based fallbacks for critical scenarios
- Creates structured action items and logs them in JSON
- Routes replies with stakeholder-specific CCs
- Sends emails using Gmail SMTP with retry and error handling
- Fully offline fallback support if the LLM API fails

## Setup

1. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/domos-email-assistant.git
cd domos-email-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory:

```
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
TOGETHER_API_KEY=your_together_ai_key
```

3. Configure your test Gmail account:
- Enable IMAP access
- Enable 2FA
- Generate an app password for email access

## Running the Assistant

```bash
python main.py
```

This will:
- Fetch unread emails
- Identify the request type (e.g., maintenance, rent, access)
- Generate a reply (LLM + fallback)
- Log a structured action item to `output/action_items.json`
- Send a reply email with relevant stakeholders CC'd

## Mock Tenant Data

Tenant context is mocked in `utils.py` and includes:
- Name
- Unit number
- Lease term
- Balance due
- Recent maintenance history

This is used both in reply generation and for enriching the action item metadata.

## LLM and Fallback Logic

Replies and action items are generated using:
- Mistral-7B via Together.ai for natural language classification and drafting
- Rule-based fallback logic for well-known issues or when API fails
- Workflow items are normalized and routed using a type-to-CC mapping defined in `utils.py`

## Error Handling

- SMTP send failures are caught and retried up to 3 times
- LLM API failures log to console and revert to rule-based logic
- Malformed LLM replies are parsed defensively with fallback logic

## Known Limitations

- No persistent storage or database
- Does not support threading or follow-up messages
- Fixed list of stakeholder routing addresses
- Not optimized for multilingual or mobile-friendly replies

## If I Had More Time

- Integrate with a real CRM or ticketing system for action item handling
- Track reply and triage performance by source (LLM vs rule)
- Add a web dashboard for previewing messages before sending
- Extend rule-based logic to handle more ambiguous phrasing
- Improve the CC LLM Triage System

## AI Notes

- I used ChatGPT for a majority of the physical coding. Mainly for syntax and ambiguous
- python specific nuances. ChatGPT is really good at setting up the environments but is
- still quite class specific. It will struggle seeing the bigger picture, so acting as a
- project manager and utlizing my design expertise is best for this project. There are
- other tools I have began looking into, one being Codex, which is OpenAIs newest coding
- tool. 

## Python Version

This project was developed and tested using Python 3.10
