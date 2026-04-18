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

### Step 1 — Install Docker Desktop

Download and install Docker Desktop from:
**https://www.docker.com/products/docker-desktop/**

After installing, launch Docker Desktop and wait until it shows **"Engine running"** in the bottom left. Keep it open in the background the entire time.

> Restart your terminal after installing so the `docker` command is available.

---

### Step 2 — Install the Kaggle CLI

Open a terminal and run:

```bash
pip install kaggle
```

Then get your Kaggle API key:
1. Go to **https://www.kaggle.com** and log in
2. Click your profile picture → **Settings**
3. Scroll to the **API** section → click **Create New Token**
4. This downloads a file called `kaggle.json`

Place that file here (create the folder if it doesn't exist):
```
C:\Users\Ryan\.kaggle\kaggle.json
```

Verify it works:
```bash
kaggle --version
```

---

### Step 3 — Download the FER-2013 dataset

```bash
cd C:/Users/Ryan/Desktop/markie/AI-SEAS/ai-engine/training
kaggle datasets download -d msambare/fer2013
unzip fer2013.zip -d data
```

When done, the folder should look like:
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
    └── (same structure)
```

---

### Step 4 — Train the CNN model

```bash
cd C:/Users/Ryan/Desktop/markie/AI-SEAS/ai-engine
pip install -r requirements.txt
python training/train.py --train_dir training/data/train --test_dir training/data/test
```

Training takes **30–60 minutes on CPU**, or ~10 minutes on a GPU. When done you should see:

```
[RESULT] Test Accuracy: ...
[INFO] Model saved to .../ai-engine/models/emotion_model.h5
```

Confirm the file exists before continuing:
```bash
ls models/
# should show: emotion_model.h5
```

> **The AI engine container will not start without this file.**

---

### Step 5 — Configure the environment file

Copy the example file:
```bash
cd C:/Users/Ryan/Desktop/markie/AI-SEAS
cp .env.example .env
```

Generate an `APP_KEY` (run this in your terminal and copy the output):
```bash
python -c "import base64, os; print('base64:' + base64.b64encode(os.urandom(32)).decode())"
```

Generate a `JWT_SECRET` (run this and copy the output):
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

Open `.env` and paste the values in:
```env
APP_KEY=base64:...   # paste output from first command
JWT_SECRET=...       # paste output from second command
```

Leave everything else as-is for local development.

---

### Step 6 — Start all services

Make sure Docker Desktop is running, then from the project root:

```bash
cd C:/Users/Ryan/Desktop/markie/AI-SEAS
                                                                                                                                                                                                      
```

This starts:
- Laravel backend (SQLite database, auto-migrated on startup)
- FastAPI AI engine (loads the trained model)
- Next.js frontend
- Nginx reverse proxy on **port 80**

Wait until all containers show as healthy — about **30–60 seconds** on first run.

---

### Step 7 — Open the app

Go to: **http://localhost**

A default account is created automatically:

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

> For API calls to work, the backend and AI engine must also be running (via Docker).

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
The model file is missing. Make sure `ai-engine/models/emotion_model.h5` exists before starting Docker. Re-run Step 4.

**`docker` command not found**
Docker Desktop is not installed or you haven't restarted your terminal after installing. Re-run Step 1.

**`kaggle` command not found**
Run `pip install kaggle` and make sure `kaggle.json` is placed at `C:\Users\Ryan\.kaggle\kaggle.json`. Re-run Step 2.

**`from preprocess import` error during training**
Make sure you run the train command from the `ai-engine/` directory, not from `ai-engine/training/`. Re-run Step 4 from the correct directory.

**`php artisan migrate` fails**
Migrations run automatically on startup. If you need to run manually:
```bash
docker exec seas_backend php artisan migrate --force
docker exec seas_backend php artisan db:seed --force
```

**Camera not showing in browser**
Browsers require HTTPS for webcam access on non-localhost origins. For local development on `http://localhost` it works fine.

**Port 80 already in use**
Change the Nginx port in `docker-compose.yml`:
```yaml
ports:
  - "8888:80"   # use http://localhost:8888 instead
```
