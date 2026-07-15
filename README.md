# Trekking Management Application (TMA)

A Flask-based web application for managing organized treks end-to-end. TMA gives **Admins**, **Trek Staff**, and **Trekkers** role-based dashboards to create and life-cycle treks, manage bookings and participants, and track activity with Chart.js visuals.

---

## Features

### Admin
- View a dashboard with trekker/staff/trek/booking counts and an overview chart
- Create, edit, search, and delete treks (deletion blocked if bookings exist)
- Advance trek status forward only: `Pending → Approved → Open → Closed → Completed`
- Approve or reject pending Trek Staff registrations; view all staff profiles
- Search and manage trekkers (activate / blacklist)
- View all bookings and cancel active (`Booked`) reservations (slot refunded)

### Trek Staff
- View a dashboard of treks assigned to them, with participant counts and a chart
- Open trek detail pages listing registered participants
- Update available slot counts (with validation against booked participants)
- Advance assigned trek status: `Open → Closed` / `Open → Completed` / `Closed → Completed`
- Remove participants (cancels booking and refunds a slot)

### Trekker
- Register and log in; access a personal dashboard with upcoming bookings and charts
- Browse and search **Open** treks; view trek details and assigned staff info
- Book available treks (one active booking per trek; start date must be in the future)
- View booking confirmation and full booking history
- Cancel a booking before the trek start date (slot refunded)

---

## Tech Stack

| Technology | Version / notes |
|---|---|
| Flask | 3.1.3 |
| Flask-SQLAlchemy | 3.1.1 |
| SQLAlchemy | 2.0.50 |
| Flask-Login | 0.6.3 |
| Jinja2 | 3.1.6 |
| Werkzeug | 3.1.8 |
| SQLite | via `sqlite:///tma.db` (file under `instance/`) |
| Bootstrap | 5.3.0 (CDN) |
| Bootstrap Icons | 1.11.3 (CDN) |
| Chart.js | 4.4.1 (CDN; dashboards only) |

Versions for Python packages are pinned in `requirements.txt`. Frontend libraries are loaded from CDN in the templates.

---

## Project Structure

```
trekking-management-app/
├── run.py                 # App entry point; creates DB + seeds on first run
├── config.py              # SECRET_KEY and SQLite URI
├── requirements.txt       # Python dependencies
├── instance/              # Auto-created; holds tma.db (gitignored)
└── app/
    ├── __init__.py        # App factory, Flask-Login, default admin creation
    ├── models.py          # User, Trek, Booking, StaffProfile models
    ├── auth.py            # Login, logout, trekker/staff registration
    ├── admin_routes.py    # Admin dashboard, treks, staff, users, bookings
    ├── staff_routes.py    # Staff dashboard and assigned-trek management
    ├── user_routes.py     # Trekker dashboard, listing, booking, cancel
    ├── seeds.py           # Dummy data seeder for demos and testing
    ├── static/css/        # Custom styles on top of Bootstrap
    └── templates/         # Jinja2 templates (admin/, staff/, user/, partials/)
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd trekking-management-app
```

### 2. Create and activate a virtual environment

**Windows (PowerShell / cmd):**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

No `.env` file is required to run locally. Settings live in `config.py`:

- `SECRET_KEY` — reads `SECRET_KEY` from the environment if set; otherwise uses a development default (`tma-secret-key-change-in-production`)
- `SQLALCHEMY_DATABASE_URI` — `sqlite:///tma.db` (Flask-SQLAlchemy stores the file under `instance/tma.db`)

Optional (recommended for anything beyond local demo):

```bash
# Windows (PowerShell)
$env:SECRET_KEY="your-own-secret-key"

# macOS / Linux
export SECRET_KEY="your-own-secret-key"
```

### 5. Database

SQLite tables are created automatically on first run via `db.create_all()` in the app factory. You do **not** need to run migrations or create the database by hand.

---

## Running the App

From the project root (with the virtual environment activated):

```bash
python run.py
```

Then open:

**http://127.0.0.1:5000**

`run.py` starts Flask with `debug=True`. On the **first** launch (when `instance/tma.db` does not exist yet), it also seeds dummy demo data automatically. On later launches it skips seeding and reuses the existing database.

### Default admin login

| Field | Value |
|---|---|
| Email | `admin@tma.com` |
| Password | `admin123` |

> **Security note:** Change these credentials before any public or graded demo. The default admin is created automatically in `app/__init__.py` if no admin user exists.

---

## User Roles & How to Test Each

### Trekker

1. Open **http://127.0.0.1:5000/register/trekker** (or use the trekker registration link from the login page).
2. Submit name, email, password, and optional contact/WhatsApp numbers.
3. Log in at `/login` — you are redirected to the trekker dashboard (`/user/dashboard`).
4. Browse Open treks at `/user/treks`, book one, then check booking history.

If the auto-seed has run, you can also use:

| Email | Password |
|---|---|
| `test_user_1@example.com` | `test_user_1_123` |

### Trek Staff

1. Register at **http://127.0.0.1:5000/register/staff** with specialization and experience.
2. Staff accounts **cannot log in until an Admin approves them**.
3. Log in as Admin → **Pending Staff** → Approve.
4. Log in as the staff user — you are redirected to `/staff/dashboard`.
5. Manage only treks assigned to you (seed data assigns treks to approved staff).

If the auto-seed has run, use an already-approved account:

| Email | Password |
|---|---|
| `test_staff_1@example.com` | `test_staff_1_123` |

### Admin

1. Log in at `/login` with `admin@tma.com` / `admin123`.
2. You are redirected to `/admin/dashboard`.
3. From there you can manage treks, staff approvals, trekkers, and bookings.

---

## Database

- Engine: **SQLite**
- File path: `instance/tma.db` (created on first run; directory is gitignored)
- Schema is defined in `app/models.py` and applied with `db.create_all()` — there is no migration tooling

**After changing models:** delete the existing database so tables can be recreated cleanly:

```bash
# Windows
del instance\tma.db

# macOS / Linux
rm instance/tma.db
```

Then run `python run.py` again. Because the DB file is gone, tables are recreated and `seeds.py` runs automatically.

---

## Seed Data

Seed logic lives in `app/seeds.py` (`seed_database()`).

### Automatic (recommended)

1. Ensure `instance/tma.db` does **not** exist (fresh clone, or delete it as above).
2. Run:

```bash
python run.py
```

On first start, `run.py` creates tables and populates demo data, including approximately:

- 1 admin (preserved / already created by the app)
- 18 staff (15 approved, 3 pending)
- 70 trekkers (68 active, 2 blacklisted)
- 45 treks across statuses, assigned to approved staff
- Diverse bookings for dashboards and Chart.js history/trend views

### Re-seeding

Seeding **clears** non-admin users, staff profiles, treks, and bookings. The usual way to re-seed for a clean demo is:

```bash
# Delete DB, then start again (auto-seeds)
del instance\tma.db          # Windows
# rm instance/tma.db         # macOS / Linux
python run.py
```

> **Warning:** Only seed in development. Do not run against a database you care about keeping.

---

## Known Limitations / Notes

- **No payment gateway** — bookings record a `payment_status` field (e.g. Pending), but there is no online payment flow.
- **Trek–staff assignment** — staff are attached to treks via seed data / database (`assigned_staff_id`); there is no separate Admin UI action to assign staff when creating a trek.
- **Forward-only trek status** — transitions cannot skip stages or move backward (Admin: full lifecycle; Staff: only from `Open` / `Closed` toward `Completed`).
- **Minimal client JS** — interactive UI is server-rendered Jinja2 + Bootstrap; Chart.js is the main third-party script used on dashboards.
- **SQLite only** — suited for local demo/coursework, not concurrent production load.
- **Debug mode** — `run.py` uses `debug=True`; turn that off and set a real `SECRET_KEY` before any shared deployment.
- Completing a trek (Admin or Staff) marks that trek’s active `Booked` reservations as `Completed`.

---

## Citations

Bootstrap and Flask documentation were referenced while building TMA. Full academic citations belong in the project report rather than this README.
