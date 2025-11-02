# Link Persona Bot

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=flat&logo=discord&logoColor=white)
![Koyeb](https://img.shields.io/badge/Koyeb-00CBFC.svg?style=flat&logo=koyeb&logoColor=white)

Discord bot that reads URL links posted in chat and summarizes the content with a unique personality using AI. The bot transforms articles into character-driven summaries, creating an entertaining and engaging way to share content.

## Features

- **Personality-driven summaries**: Articles are summarized with unique personalities (e.g., sarcastic, professor, anime character)
- **Automatic link processing**: Detects URLs in Discord messages and automatically creates summaries
- **Customizable personas**: Easy to add new personalities via YAML templates
- **Debate mode**: Challenge the article's content with counter-arguments
- **Context memory**: Remembers user preferences and history for personalized interactions

## Tech Stack

- **Discord Bot**: Built with discord.py
- **API Server**: FastAPI for processing requests
- **Web Scraping**: trafilatura for clean text extraction
- **LLM**: Qwen API for summarization and personality injection
- **Hosting**: Deployed on Koyeb
- **Container**: Docker for consistent deployment

## Architecture

The bot monitors Discord messages, detects URLs, and sends them to a Koyeb-hosted API service that:
1. Extracts clean text from the URL using trafilatura
2. Analyzes content and selects an appropriate personality
3. Generates a character-driven summary using Qwen API
4. Posts the result back to Discord as an embedded message
