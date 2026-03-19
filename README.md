# TalkBits
Cause Google Translate can't wingman

![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Django](https://img.shields.io/badge/django-5.2.7-green.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

## About

> TalkBits is a comprehensive language learning web application built with Django that enables users to learn multiple Indian languages (Tamil, Hindi, Telugu, English) through structured courses, interactive lessons, progress tracking, audio support and sign language mapping.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [How the app works](#how-the-app-works)
- [Features](#features)
- [Security & privacy notes](#security--privacy-notes)
- [Future Improvements](#future-improvements)
- [License](#license)

## Tech Stack

- Language: Python 3.8+
- Framework: Django 5.2.7
- Authentication: Django Allauth (with Google OAuth)
- Translation: deep_translator (Google Translate API)
- Text-to-Speech: gTTS (Google Text-to-Speech)
- Database: SQLite
- Frontend: HTML, CSS ,JavaScript

## Project Structure (key files)

- `manage.py` — Django management script
- `GenTech/` — Django project settings and configuration
  - `settings.py` — Project settings including installed apps and authentication
  - `urls.py` — Main URL configuration
- `app/` — Main Django app
  - `models.py` — Database models (User, Profile, Course, Unit, Lesson, UserProgress)
  - `views.py` — View functions handling requests and responses
  - `urls.py` — App URL patterns
  - `templates/app/` — HTML templates for the application
  - `static/` — Static files (CSS, JS, audio files)
- `app/languages/lessons/` — JSON files containing lesson data for different languages
- `generate\_audio.py` — Script to generate audio files for lessons using gTTS
- `translate\_json.py` — Script to translate lesson content using deep_translator
- `requirements.txt` — Python dependencies
- `db.sqlite3` — SQLite database file

## Setup & Installation

1) Clone the repository and navigate to the project directory

2) Create and activate virtual environment

```bash

python -m venv venv

\# Windows (PowerShell)

venv\\Scripts\\Activate.ps1

\# Windows (cmd)

venv\\Scripts\\Activate

\# macOS / Linux

source venv/bin/activate

```

3) Install dependencies

```bash

pip install -r requirements.txt

```

4) Apply database migrations

```bash

python manage.py migrate

```

5) (Optional) Generate audio files for lessons

```bash

python generate\_audio.py

```

6) (Optional) Translate lesson content

```bash

python translate\_json.py

```

7) Run the development server

```bash

python manage.py runserver

```

8) Access the application at `http://127.0.0.1:8000/`

## How the app works

1. Users create profiles and register, selecting languages they want to learn and known languages
2. The app provides structured courses divided into units and lessons
3. Lesson content includes vocabulary, phrases and dialogues with translations and and sign language mapping
4. Audio files are generated for pronunciation practice using Google Text-to-Speech
5. User progress is tracked, including completed lessons and exercise scores
6. The platform supports multiple language pairs for translation and learning

## Features

- Multi-language support (Tamil, Hindi, Telugu, English)
- User authentication and profile management
- Course and lesson structure with sign language mapping for vocabulary and phrases
- Progress tracking with XP
- Audio pronunciation support
- Exercise submission and scoring
- Social authentication (Google OAuth)
- Responsive web interface

## Security & privacy notes

- User data stored in SQLite database — ensure proper backup and security measures for production
- Authentication handled through Django's secure framework and Allauth
- Static files served securely through Django's static file handling

## Future Improvements

- Add more languages and language pairs
- Add interactive exercises and quizzes
- Integrate speech recognition for pronunciation assessment
- Mobile app development
- Add Docker support for easier deployment
- Implement CI/CD pipeline for automated testing and deployment

## License

MIT — see `LICENSE`.
