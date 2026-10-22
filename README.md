# Manual_app_deployment

A two-tier web application built with Python and MongoDB to practice manual deployment on a production server, covering application setup, database configuration, server management, and deployment troubleshooting.

> **Learning project — not production-ready.** The app has no authentication, no HTTPS, no backups, no monitoring and uses Flask's development server. Running something like this for real users needs extra security, reliability and configuration work. Learning about that work is the point of the later deployment stage.

---

## Table of contents

1. [Project overview and learning objectives](#1-project-overview-and-learning-objectives)
2. [Architecture: the two tiers](#2-architecture-the-two-tiers)
3. [Request flow](#3-request-flow)
4. [Project files explained](#4-project-files-explained)
5. [Prerequisites](#5-prerequisites)
6. [Step 1 — Start MongoDB (choose Option A or B)](#6-step-1--start-mongodb-choose-option-a-or-b)
7. [Step 2 — Set up and run the Python app](#7-step-2--set-up-and-run-the-python-app)
8. [Start, verify, stop and restart cheat sheet](#8-start-verify-stop-and-restart-cheat-sheet)
9. [Testing each feature](#9-testing-each-feature)
10. [Troubleshooting](#10-troubleshooting)
11. [Future Learning: Manual Production Deployment](#11-future-learning-manual-production-deployment)

---

## 1. Project overview and learning objectives

**Task Manager** is a small web app. You can:

- see a list of all tasks (or a friendly message when there are none),
- add a task with a title and a description,
- mark a task as completed,
- delete a task.

If MongoDB is unreachable the page shows a clear error message instead of crashing, and a `/health` endpoint reports whether the app can talk to the database.

**What you will learn in this (local) stage**

- How a web application and a database are two separate programs that talk over the network.
- How to run each one on its own and check that it is working.
- How configuration (database address, database name) is passed in through **environment variables** instead of being written in code.
- How to read errors and logs when something is broken.

**What comes later** (only after you approve it): deploying the same app on a Linux server with Nginx. See [section 11](#11-future-learning-manual-production-deployment).

## 2. Architecture: the two tiers

```
 ┌─────────────┐        ┌───────────────────────────┐        ┌──────────────┐
 │   Browser   │ ─────► │  Tier 1: Application      │ ─────► │ Tier 2: Data │
 │   (user)    │ ◄───── │  Python + Flask           │ ◄───── │  MongoDB     │
 └─────────────┘  HTTP  │  http://127.0.0.1:5000    │  Mongo │  port 27017  │
                        └───────────────────────────┘  wire  └──────────────┘
```

| Tier | Technology | Job | Default address |
|------|-----------|-----|-----------------|
| Application tier | Python + Flask | Receives HTTP requests, validates input, builds HTML pages | `http://127.0.0.1:5000` |
| Data tier | MongoDB | Stores tasks permanently in a collection named `tasks` | `localhost:27017` |

**Why two tiers?** Each tier is a separate process. You can start, stop, restart and troubleshoot them independently, and later place them on different servers. That is exactly how real deployments work.

**How Flask works:** Flask is a Python library that maps a URL (such as `/tasks`) and an HTTP method (such as `POST`) to a Python function. The function does the work and returns HTML (rendered from a template) or a redirect.

**How MongoDB works:** MongoDB is a database server that runs in the background and listens on TCP port `27017`. It stores data as *documents* (JSON-like objects) grouped in *collections*. Our database (`task_manager` by default) has one collection, `tasks`. A task document looks like this:

```json
{
  "_id": "665f...",          // unique id created by MongoDB
  "title": "Buy milk",
  "description": "2 litres",
  "completed": false,
  "created_at": "2026-01-01T10:00:00Z"
}
```

The Python library **PyMongo** is what lets Flask talk to MongoDB.

## 3. Request flow

Example: you click **Add task**.

1. **Browser** sends `POST /tasks` with the form fields `title` and `description` to Flask.
2. **Flask** (`app.py`, function `add_task`) trims and validates the input. An empty title is rejected with an error message.
3. **Flask → MongoDB:** PyMongo inserts a document into the `tasks` collection.
4. **Flask** replies with a redirect to `/`.
5. **Browser** requests `GET /`. Flask asks MongoDB for all tasks (newest first), fills `templates/index.html` with them, and returns the HTML.
6. **Browser** displays the page and also requests `/static/style.css` for the styling.

Why `POST`? Browsers use `GET` to read pages and `POST` for actions that change data. HTML forms can only send `GET` or `POST`, so "complete" and "delete" are also `POST` requests (`/tasks/<id>/complete` and `/tasks/<id>/delete`).

| Method | URL | What it does |
|--------|-----|--------------|
| GET | `/` | Homepage: list tasks and show the add form (optional `?filter=open` or `?filter=done`) |
| POST | `/tasks` | Create a task |
| POST | `/tasks/<id>/complete` | Mark a task completed |
| POST | `/tasks/<id>/delete` | Delete a task |
| GET | `/health` | JSON: can the app reach MongoDB? (200 = yes, 503 = no) |

## 4. Project files explained

```
Manual_app_deployment/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    └── style.css
```

| File | Purpose |
|------|---------|
| `app.py` | The whole backend: Flask routes, MongoDB access, validation, health check. |
| `requirements.txt` | The Python packages needed (Flask, PyMongo, python-dotenv) with pinned versions. |
| `.env.example` | A template listing the environment variables. You copy it to `.env` and edit it. It contains no secrets. |
| `.env` (you create it) | Your real local configuration. Ignored by Git so secrets are never committed. |
| `.gitignore` | Tells Git to ignore `.env`, the virtual environment (`venv/`) and Python cache files. |
| `templates/index.html` | The HTML page (a Jinja template). Flask fills in the task list and error messages. It also holds two tiny inline scripts: the delete confirmation and the light/dark switch. |
| `static/style.css` | The CSS styling (responsive layout, light and dark themes). Flask serves anything in `static/` at `/static/...`. *(Flask looks for static files in `static/`, which is why this lives there and not in `templates/`.)* |
| `README.md` | This guide. |

Environment variables used by `app.py`:

| Variable | Meaning | Default if not set |
|----------|---------|--------------------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `task_manager` |
| `FLASK_HOST` | (optional) Address Flask listens on | `127.0.0.1` |
| `FLASK_PORT` | (optional) Port Flask listens on | `5000` |
| `FLASK_DEBUG` | (optional) `1` enables debug mode | off |

## 5. Prerequisites

You need the following on your Windows machine. Nothing is installed for you.

| Tool | Needed for | Check command |
|------|-----------|---------------|
| Python 3.9 or newer | Running the app | `python --version` |
| Git | Cloning the repo (Git Bash comes with it) | `git --version` |
| MongoDB Community Server **or** Docker Desktop | The database (pick one) | see section 6 |
| A web browser | Using the app | — |

Install Python from <https://www.python.org/downloads/> (tick **"Add python.exe to PATH"** in the installer).

> **Where do I type commands?** Each command block below is labelled **PowerShell**, **Git Bash** or **Linux**. Open that program (Windows PowerShell from the Start menu; Git Bash from the Start menu or by right-clicking a folder → *Open Git Bash here*). Linux blocks are for the future server and are marked as such; do not run them on Windows.

Open a terminal in the project folder first:

```powershell
# PowerShell — move into the project folder (adjust the path to where you cloned it)
cd E:\Manual-app-deployment\Manual_app_deployment
```

```bash
# Git Bash — same thing, with Unix-style paths
cd /e/Manual-app-deployment/Manual_app_deployment
```

## 6. Step 1 — Start MongoDB (choose Option A or B)

Pick **one** option. Do not run both at the same time: they would both want port `27017`.

### Option A — Local MongoDB installation (Windows service)

**1. Install.** Download *MongoDB Community Server* for Windows (MSI) from <https://www.mongodb.com/try/download/community>. In the installer choose **Complete**, and keep **"Install MongoDB as a Service"** ticked (the default: *Run service as Network Service user*). MongoDB Compass (a GUI) is optional.

**2. Check that the service is running.**

```powershell
# PowerShell — shows the MongoDB service and whether it is Running or Stopped
Get-Service MongoDB
```

Expected output: `Status  Name  DisplayName` with `Running  MongoDB  MongoDB Server`.

**3. Start / stop / restart the service** (PowerShell **as Administrator**: right-click PowerShell → *Run as administrator*):

```powershell
# PowerShell (Administrator) — start MongoDB in the background
Start-Service MongoDB

# PowerShell (Administrator) — stop MongoDB
Stop-Service MongoDB

# PowerShell (Administrator) — restart MongoDB
Restart-Service MongoDB
```

**4. Verify that it is listening on port 27017.**

```powershell
# PowerShell — lists anything listening on port 27017; you should see one LISTENING line
netstat -ano | findstr :27017
```

Optional, if you installed the MongoDB Shell (`mongosh`):

```powershell
# PowerShell — connect to the database and ask it to answer "ping"
mongosh "mongodb://localhost:27017" --eval "db.runCommand({ ping: 1 })"
```

You should see `{ ok: 1 }`.

**5. Connection string for the app:** `MONGO_URI=mongodb://localhost:27017` (the default — no username or password on a fresh local install).

### Option B — MongoDB in Docker (database only)

Docker is used **only to run the database**. The Python app still runs directly on Windows. Install and start *Docker Desktop* first, then check it works:

```powershell
# PowerShell — confirms the Docker command-line tool is installed
docker --version

# PowerShell — confirms the Docker engine is running (errors if Docker Desktop is not started)
docker info
```

**1. Start a MongoDB container.** The command is long, so here is every part:

```powershell
# PowerShell — create and start a MongoDB container (run once)
docker run -d --name task-mongo -p 27017:27017 -v task-mongo-data:/data/db mongo:7
```

| Part | Meaning |
|------|---------|
| `docker run` | Create a new container from an image and start it |
| `-d` | Run in the background ("detached") |
| `--name task-mongo` | Give the container a name so we can refer to it later |
| `-p 27017:27017` | **Publish the port:** Windows `localhost:27017` → container port `27017`. This is how the Python app reaches the database. |
| `-v task-mongo-data:/data/db` | **Persistence:** store the database files in a Docker *volume* named `task-mongo-data`. Without this, deleting the container deletes all your tasks. |
| `mongo:7` | The official MongoDB image, version 7 (downloaded the first time) |

> In Git Bash the same command works as-is.

**2. Check status and logs.**

```powershell
# PowerShell — list running containers; "task-mongo" should show "Up"
docker ps

# PowerShell — list all containers, including stopped ones
docker ps -a

# PowerShell — show MongoDB's log output (look for "Waiting for connections")
docker logs task-mongo

# PowerShell — follow the log live (press Ctrl+C to stop following; the container keeps running)
docker logs -f task-mongo
```

**3. Stop and restart.**

```powershell
# PowerShell — stop the container (data is kept in the volume)
docker stop task-mongo

# PowerShell — start the stopped container again (do NOT use "docker run" again)
docker start task-mongo

# PowerShell — stop and start in one go
docker restart task-mongo
```

**4. Connecting the app.** Because of `-p 27017:27017`, the app uses the same string as Option A: `MONGO_URI=mongodb://localhost:27017`.

**5. Remove it completely** (only if you want to start from scratch):

```powershell
# PowerShell — delete the container (the data volume survives)
docker rm -f task-mongo

# PowerShell — delete the data volume too. THIS ERASES ALL YOUR TASKS.
docker volume rm task-mongo-data
```

> **Security note:** `-p 27017:27017` publishes MongoDB on all network interfaces of your PC and this container has no password. That is fine on a personal laptop for learning, but never do this on a server reachable from the internet. To restrict it to your own machine use `-p 127.0.0.1:27017:27017`.

## 7. Step 2 — Set up and run the Python app

Make sure MongoDB (Step 1) is running first.

### 7.1 Check the Python version

```powershell
# PowerShell
python --version
```
```bash
# Git Bash
python --version
```
Expected: `Python 3.9` or newer (for example `Python 3.11.5`). If you get "not recognized", reinstall Python with *Add to PATH* ticked, or try `py --version`.

### 7.2 Create a virtual environment

A virtual environment is a private folder of Python packages for this project, so they do not mix with other projects.

```powershell
# PowerShell or Git Bash, inside the project folder — creates a folder named "venv"
python -m venv venv
```

### 7.3 Activate it

```powershell
# PowerShell
.\venv\Scripts\Activate.ps1
```
```bash
# Git Bash
source venv/Scripts/activate
```

Your prompt now starts with `(venv)`.

> If PowerShell says *"running scripts is disabled on this system"*, run this once and try again:
> ```powershell
> # PowerShell — allow scripts for your user account only
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> (Alternative without changing policy: use Git Bash, or `cmd` with `venv\Scripts\activate.bat`.)

### 7.4 Install the dependencies

```powershell
# PowerShell or Git Bash, with (venv) active — installs the packages listed in requirements.txt
pip install -r requirements.txt
```

Check the result with `pip list` (you should see Flask, pymongo and python-dotenv).

### 7.5 Create your `.env` file

```powershell
# PowerShell — copy the template to a real config file
Copy-Item .env.example .env
```
```bash
# Git Bash — same thing
cp .env.example .env
```

### 7.6 Configure `MONGO_URI` and `MONGO_DB_NAME`

Open `.env` in any editor (for example `notepad .env`). For the default setups from section 6 it should read:

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=task_manager
```

- `MONGO_URI` — where MongoDB is. Format: `mongodb://HOST:PORT`. If your MongoDB needs a login it is `mongodb://USER:PASSWORD@HOST:PORT`. The password lives only in `.env`, which Git ignores.
- `MONGO_DB_NAME` — any name you like. MongoDB creates the database the first time something is saved.

`app.py` loads `.env` automatically at start-up. If `.env` is missing, the same defaults above are used.

### 7.7 Start the Flask app

```powershell
# PowerShell or Git Bash, with (venv) active — start the development server
python app.py
```

You should see output ending with `Running on http://127.0.0.1:5000`. This terminal is now busy running the app; leave it open (use a second terminal for other commands).

### 7.8 Open it in a browser

Go to <http://127.0.0.1:5000>. You should see "Task Manager" and an empty-state panel saying *"No tasks yet"*.

### 7.9 Test the health endpoint

In a **second** terminal:

```powershell
# PowerShell — ask the app whether it can reach MongoDB
Invoke-RestMethod http://127.0.0.1:5000/health
```
```bash
# Git Bash — same; -i also prints the HTTP status line
curl -i http://127.0.0.1:5000/health
```

Healthy: HTTP `200` and `{"database":"connected","status":"ok"}`.
MongoDB down: HTTP `503` and `{"database":"unreachable","status":"error"}`. (PowerShell's `Invoke-RestMethod` prints an error for a 503; that is expected.)

You can also just open <http://127.0.0.1:5000/health> in the browser.

### 7.10 Stop the app and deactivate the environment

```powershell
# In the terminal running the app: press Ctrl+C to stop Flask.

# PowerShell or Git Bash — leave the virtual environment
deactivate
```

## 8. Start, verify, stop and restart cheat sheet

**Start (always database first, then the app)**

| Step | Option A (Windows service) | Option B (Docker) |
|------|----------------------------|-------------------|
| 1. Start MongoDB | `Start-Service MongoDB` (PowerShell, Admin; usually already running) | `docker start task-mongo` (PowerShell) |
| 2. Verify MongoDB | `Get-Service MongoDB` | `docker ps` |
| 3. Activate venv | `.\venv\Scripts\Activate.ps1` (PowerShell) / `source venv/Scripts/activate` (Git Bash) | same |
| 4. Start app | `python app.py` | same |
| 5. Verify app | open `http://127.0.0.1:5000/health` | same |

**Stop (app first, then the database)**

| Step | Option A | Option B |
|------|----------|----------|
| 1. Stop app | `Ctrl+C` in its terminal, then `deactivate` | same |
| 2. Stop MongoDB | `Stop-Service MongoDB` (Admin) | `docker stop task-mongo` |

**Restart:** restart the database (`Restart-Service MongoDB` or `docker restart task-mongo`); the app reconnects by itself on the next request, no app restart needed. Restart the app (Ctrl+C, then `python app.py`) after editing `.env` or `app.py` (unless `FLASK_DEBUG=1`).

## 9. Testing each feature

With MongoDB and the app running, open <http://127.0.0.1:5000> and try:

| Feature | What to do | Expected result |
|---------|-----------|-----------------|
| Empty state | Open the page with no tasks | "No tasks yet" with a hint to use the form |
| Summary cards | Add/complete tasks | Total / Open / Completed counters in the page header update |
| Filter tabs | Click **All**, **Open**, **Completed** | List shows only matching tasks (URL gets `?filter=open` or `?filter=done`) |
| Light/dark switch | Click the **Dark mode / Light mode** button in the top bar, then reload | The theme changes and is remembered in your browser. Before you click it, the page follows your Windows theme |
| Add a task | Enter a title and description, click **Add task** | The task appears at the top of the list |
| Title validation | Enter only spaces as title (the browser's `required` check passes spaces) and submit | Red message "Please enter a task title." and nothing is saved |
| Length limits | Titles over 100 or descriptions over 500 characters | Rejected with a message (the browser also limits typing) |
| Complete a task | Click **Mark complete** | Title is struck through, the status changes from "Open" to "Completed", the button disappears |
| Delete a task | Click **Delete**, confirm the pop-up | The task disappears; with none left the empty message returns |
| Persistence | Stop and start the app, reload | Tasks are still there (they live in MongoDB, not in Python) |
| Database error | Stop MongoDB (`Stop-Service MongoDB` / `docker stop task-mongo`), reload the page (it takes ~3 s) | Red message "Cannot reach the database…", no crash, no connection details shown. `/health` returns 503 |
| Recovery | Start MongoDB again, reload | The page works again without restarting the app |
| Health | Open `/health` | `{"database":"connected","status":"ok"}` |

To look at the data directly:

```powershell
# PowerShell — requires mongosh. Prints every task document.
mongosh "mongodb://localhost:27017/task_manager" --eval "db.tasks.find().pretty()"
```
```powershell
# PowerShell — Docker alternative (mongosh is included in the mongo:7 image)
docker exec -it task-mongo mongosh task_manager --eval "db.tasks.find().pretty()"
```

## 10. Troubleshooting

### "Cannot reach the database" / connection refused

The app shows this when MongoDB is not answering. Check, in order:

1. Is MongoDB running? Option A: `Get-Service MongoDB`. Option B: `docker ps` (is `task-mongo` listed as `Up`? If not: `docker start task-mongo`, and look at `docker logs task-mongo`).
2. Is anything listening on 27017? `netstat -ano | findstr :27017`
3. Does `/health` return 503? That confirms the app-to-database link is the problem, not the page.
4. Docker only: did you forget `-p 27017:27017`? Check with `docker ps` — the PORTS column should show `0.0.0.0:27017->27017/tcp`.
5. Windows may need `127.0.0.1` instead of `localhost` (`localhost` can resolve to the IPv6 address `::1`). Try `MONGO_URI=mongodb://127.0.0.1:27017`.

The detailed error is printed in the terminal running Flask, not on the web page (on purpose, so connection details are never shown to visitors).

### Incorrect MongoDB URI

- It must start with `mongodb://` (or `mongodb+srv://`) — a typo gives an *InvalidURI* error when the app starts.
- Wrong host or port (e.g. `27018`) behaves like "connection refused".
- Wrong username/password gives an *authentication failed* error, and only on the first database operation.
- Special characters in a password (`@`, `:`, `/`) must be URL-encoded.
- After editing `.env`, **restart the app**; it only reads `.env` at start-up.
- Make sure the file is named exactly `.env` (not `.env.txt`). Check with `dir -Force` (PowerShell) or `ls -a` (Git Bash).

### Missing Python dependencies

Symptom: `ModuleNotFoundError: No module named 'flask'` (or `pymongo`, `dotenv`, `bson`).

- The virtual environment is probably not active. Look for `(venv)` in the prompt; if missing, activate it (section 7.3).
- Then run `pip install -r requirements.txt` again.
- `python -c "import flask, pymongo, dotenv"` should print nothing if all is well.

### Port conflicts

- **Flask port 5000 in use** (`Address already in use`): find what uses it with `netstat -ano | findstr :5000`; the last column is the process ID (PID). Check the process in Task Manager, or end it with `taskkill /PID <PID> /F` (PowerShell). Or run Flask on another port: set `FLASK_PORT=5001` in `.env`, restart, and browse to port 5001.
- **MongoDB port 27017 in use:** you probably have Option A and Option B running together. Stop one. For Docker you can instead publish a different host port, e.g. `-p 27018:27017`, and set `MONGO_URI=mongodb://localhost:27018`.

### Other common problems

| Problem | Likely cause / fix |
|---------|--------------------|
| `python` is not recognized | Python not on PATH; reinstall with *Add to PATH*, or use `py` |
| `Activate.ps1 cannot be loaded` | Execution policy; see section 7.3 |
| Browser says "refused to connect" | Flask is not running, or you used the wrong port |
| Docker: `error during connect` / `cannot find the file specified` | Docker Desktop isn't started |
| Docker: `container name "/task-mongo" is already in use` | It already exists; use `docker start task-mongo` |
| Page loads but has no styling | Check `static/style.css` exists; hard-refresh with Ctrl+F5 |

## 11. Future Learning: Manual Production Deployment

> **This section is only an outline. No deployment has been done and no deployment files exist in this repository.** We will start this stage only after you explicitly approve it, and you will write each configuration yourself.

In the next stage you will take this same application and deploy it by hand on a Linux server (Amazon Linux or Ubuntu). At a high level you will learn:

1. **Linux server preparation** — connecting over SSH, updating packages, creating a non-root user, and a sensible directory layout.
2. **Python runtime setup** — installing Python and creating a virtual environment on the server, and replacing Flask's development server with a production-grade application server.
3. **MongoDB connectivity** — installing MongoDB (or using a separate database host), choosing where it listens, enabling authentication, and pointing `MONGO_URI` at it.
4. **Application process management** — keeping the app running in the background, starting it on boot and restarting it if it crashes.
5. **Nginx reverse proxy configuration** — letting Nginx receive public traffic on port 80 and forward it to the Python application, plus serving static files.
6. **Firewall and security-group rules** — exposing only the ports that must be public (such as 80/443 and SSH) and keeping the database private.
7. **Troubleshooting** — reading Nginx, application and MongoDB logs, and diagnosing errors such as 502 Bad Gateway and connection refused.

Remember: even after this stage the project remains a learning exercise. A real production system would also need HTTPS, backups, monitoring, secret management, updates and more testing.
