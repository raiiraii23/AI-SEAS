# SEAS — How to Run (Step-by-Step)

This guide is written for **this laptop** (`aprilyn salalila`). Follow the steps in order.

---

## What You Need (One-Time Setup)

| Requirement | Status on This Laptop |
|---|---|
| Docker Desktop | Already installed |
| Python + pip | Already installed |
| Trained model (`emotion_model.h5`) | Already exists |
| `.env` file | Already created |

If you are setting this up on a **different laptop**, start from Step 1. Otherwise jump to [Step 5 — Start the App](#step-5--start-the-app).

---

## Step 1 — Install Docker Desktop

Download from: **https://www.docker.com/products/docker-desktop/**

After installing:
1. Open Docker Desktop
2. Wait until the bottom-left corner shows **"Engine running"**
3. Keep Docker Desktop open in the background the whole time

Then restart your terminal so the `docker` command works.

Verify:
```bash
docker --version
```

---

## Step 2 — Install the Kaggle CLI

```bash
pip install kaggle
```

Then get your API key:
1. Go to **https://www.kaggle.com** and log in
2. Click your profile picture → **Settings**
3. Scroll to the **API** section → click **Create New Token**
4. It downloads a file called `kaggle.json`

Place that file here (create the folder if it does not exist):
```
C:\Users\aprilyn salalila\.kaggle\kaggle.json
```

Verify:
```bash
kaggle --version
```

---

## Step 3 — Download the FER-2013 Dataset

Open a terminal and run:
```bash
cd "C:\Users\aprilyn salalila\Desktop\AI-SEAS\ai-engine\training"
kaggle datasets download -d msambare/fer2013
tar -xf fer2013.zip -C data
```

When done, the folder should look like this:
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

## Step 4 — Train the CNN Model

```bash
cd "C:\Users\aprilyn salalila\Desktop\AI-SEAS\ai-engine"
pip install -r requirements.txt
python training/train.py --train_dir training/data/train --test_dir training/data/test
```

Training takes **30–60 minutes on CPU**. When done you will see:
```
[RESULT] Test Accuracy: ...
[INFO] Model saved to .../ai-engine/models/emotion_model.h5
```

Confirm the file exists:
```bash
ls models/
# should show: emotion_model.h5
```

The app will not start without this file.

---

## Step 5 — Create the `.env` File

Only do this if the `.env` file does not already exist in the project root.

```bash
cd "C:\Users\aprilyn salalila\Desktop\AI-SEAS"
copy .env.example .env
```

Generate an `APP_KEY`:
```bash
python -c "import base64, os; print('base64:' + base64.b64encode(os.urandom(32)).decode())"
```

Generate a `JWT_SECRET`:
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

Open `.env` and paste both values in:
```
APP_KEY=base64:...    <-- paste APP_KEY output here
JWT_SECRET=...        <-- paste JWT_SECRET output here
```

---

## Step 6 — Start the App

Make sure Docker Desktop is open and showing **"Engine running"**, then:

```bash
cd "C:\Users\aprilyn salalila\Desktop\AI-SEAS"
docker compose up -d 
```

This builds and starts 4 containers:
- `seas_backend` — Laravel API (auto-migrates database on first run)
- `seas_ai_engine` — FastAPI emotion detection server
- `seas_frontend` — Next.js dashboard
- `seas_nginx` — Reverse proxy on port 80

Wait about **30–60 seconds** for everything to come up, then check:
```bash
docker compose ps
```

All 4 containers should show **healthy** or **Up** in the STATUS column.

---

## Step 7 — Open the App

Open your browser and go to:

**http://localhost**

Log in with the default account:

| Field | Value |
|---|---|
| Email | `admin@seas.local` |
| Password | `password` |

Change your password after first login.

---

## Daily Use (App Already Set Up)

Every time you want to use the app:

1. Open **Docker Desktop** and wait for "Engine running"
2. Open a terminal and run:
   ```bash
   cd "C:\Users\aprilyn salalila\Desktop\AI-SEAS"
   docker compose up -d
   ```
3. Open **http://localhost** in your browser

To stop all containers when you're done:
```bash
docker compose down
```

---

## Useful Commands

| Task | Command |
|---|---|
| Start the app | `docker compose up -d` |
| Stop the app | `docker compose down` |
| Restart one container | `docker compose restart backend` |
| View live logs | `docker compose logs -f` |
| View logs for one service | `docker compose logs -f ai-engine` |
| Check container status | `docker compose ps` |
| Run manually: migrate DB | `docker exec seas_backend php artisan migrate --force` |
| Run manually: seed DB | `docker exec seas_backend php artisan db:seed --force` |

All commands must be run from the project folder:
```
C:\Users\aprilyn salalila\Desktop\AI-SEAS
```

---

## Troubleshooting

**App won't open at http://localhost**
- Make sure Docker Desktop is running
- Run `docker compose ps` — all containers should show Up
- Run `docker compose logs nginx` to check for errors

**AI engine keeps restarting**
- The model file is missing. Check that `ai-engine/models/emotion_model.h5` exists
- If it's missing, re-run Step 4

**`docker` command not found**
- Docker Desktop is not installed, or you haven't restarted your terminal after installing
- Re-run Step 1

**`kaggle` command not found**
- Run `pip install kaggle`
- Make sure `kaggle.json` is at `C:\Users\aprilyn salalila\.kaggle\kaggle.json`

**Backend shows unhealthy**
- Run `docker compose logs backend` to see the error
- Usually means the `.env` file is missing or has an empty `APP_KEY`

**Camera not working in browser**
- Browsers require HTTPS for webcam access on non-localhost origins
- On `http://localhost` it works without HTTPS — make sure you are using `localhost` not an IP address

**Port 80 already in use**
- Something else is using port 80 on your machine
- Edit `docker-compose.yml` and change:
  ```yaml
  ports:
    - "8888:80"
  ```
- Then open **http://localhost:8888** instead
