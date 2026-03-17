# SEAS — Student Engagement Analysis System

A facial emotion recognition system that monitors student engagement in real time using a webcam. Built as a thesis project.

---

## How It Works

1. The browser captures webcam frames every second
2. Frames are sent to the AI engine, which detects the face and classifies the emotion using a CNN model
3. The emotion is mapped to an engagement state (Engaged / Neutral / Confused / Disengaged)
4. Results are displayed on a live dashboard and saved to the database

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | Python, FastAPI, TensorFlow/Keras, MediaPipe, OpenCV |
| Backend API | Laravel 11, SQLite *(temporary — will switch to PostgreSQL)*, JWT Auth |
| Frontend | Next.js 14, Tailwind CSS, Chart.js |
| Infrastructure | Docker, Nginx |

---

## Project Structure

```
/
├── ai-engine/          # CNN model + FastAPI inference server
│   ├── training/       # Training scripts and dataset goes here
│   └── models/         # Trained model file goes here (.h5)
├── backend/            # Laravel 11 REST API
├── frontend/           # Next.js dashboard
├── nginx/              # Reverse proxy config
├── docker-compose.yml
└── .env.example
```

---

## Setup Guide

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Python 3.11+](https://www.python.org/) (for model training only)
- [Kaggle CLI](https://www.kaggle.com/docs/api) (for downloading the dataset)

---

### Step 1 — Clone and configure environment

```bash
cd mark-thesis
cp .env.example .env
```

Open `.env` and fill in:

```env
APP_KEY=        # generate with: php artisan key:generate (or any 32-char string)
JWT_SECRET=     # generate with: php artisan jwt:secret (or any long random string)
```

> **Database note:** The project currently uses **SQLite** for development convenience.
> The database file is stored at `backend/database/database.sqlite` and is created automatically on first run.
> This will be switched to **PostgreSQL** before final deployment — see the commented-out `db` service in `docker-compose.yml`.

---

### Step 2 — Train the CNN model

The system needs a trained model file before the AI engine will work.

**2a. Download the FER-2013 dataset**

```bash
cd ai-engine/training
kaggle datasets download -d msambare/fer2013
unzip fer2013.zip -d data
```

The folder should look like:
```
ai-engine/training/data/
├── train/
│   ├── angry/
│   ├── disgust/
│   ├── fear/
│   ├── happy/
│   ├── neutral/
│   ├── sad/
│   └── surprise/
└── test/
    └── ...
```

**2b. Install Python dependencies and train**

```bash
cd ai-engine
pip install -r requirements.txt
python training/train.py --train_dir training/data/train --test_dir training/data/test
```

Training takes 30–60 minutes on a CPU, or ~10 minutes on a GPU. When done, the model is saved to:
```
ai-engine/models/emotion_model.h5
```

---

### Step 3 — Start all services

From the project root:

```bash
docker-compose up --build
```

This starts:
- PostgreSQL database
- Laravel backend (port 8080 internally)
- FastAPI AI engine (port 8000 internally)
- Next.js frontend (port 3000 internally)
- Nginx reverse proxy (port **80** externally)

Wait until all containers are healthy (about 30–60 seconds on first run).

---

### Step 4 — Run database migrations

Migrations and seeding run automatically on container startup. If you need to run them manually:

```bash
docker exec seas_backend php artisan migrate --force
docker exec seas_backend php artisan db:seed --force
```

---

### Step 5 — Open the app

Go to: **http://localhost**

A default account is created automatically by the seeder:

| Field | Value |
|---|---|
| Email | `admin@seas.local` |
| Password | `password` |
| Role | Teacher |

> Change the password after first login.

---

## Running the Frontend Locally (without Docker)

Useful for fast UI development:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

> For API calls to work, you also need the backend and AI engine running (either via Docker or separately).

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login, returns JWT token |
| `GET` | `/api/v1/sessions` | List engagement sessions |
| `POST` | `/api/v1/sessions` | Create a new session |
| `PATCH` | `/api/v1/sessions/:id` | Update session (e.g., end it) |
| `GET` | `/api/v1/sessions/:id/logs` | Get all logs for a session |
| `POST` | `/api/v1/sessions/:id/logs` | Save an engagement log entry |
| `GET` | `/api/v1/sessions/:id/summary` | Get engagement summary stats |
| `POST` | `/api/ai/emotion/predict` | Submit an image for emotion prediction |
| `GET` | `/api/ai/health` | AI engine health check |

---

## Troubleshooting

**AI engine keeps restarting**
The model file is missing. Make sure `ai-engine/models/emotion_model.h5` exists before starting Docker.

**`php artisan migrate` fails**
The database container may still be starting. Wait a few seconds and retry.

**Camera not showing in browser**
Browsers require HTTPS for webcam access on non-localhost origins. For local development on `http://localhost` it works fine.

**Port 80 already in use**
Change the Nginx port in `docker-compose.yml`:
```yaml
ports:
  - "8888:80"   # use http://localhost:8888 instead
```
