import os
from pathlib import Path

from app import create_app, db
from app.seeds import seed_database

# Flask-SQLAlchemy places sqlite:///tma.db under the app instance folder
DB_PATH = Path(__file__).resolve().parent / 'instance' / 'tma.db'


if __name__ == '__main__':
    # Capture before create_app(): create_all() would create an empty file
    db_already_exists = DB_PATH.exists()

    app = create_app()

    with app.app_context():
        if not db_already_exists:
            print(f"No database found at {DB_PATH} — creating tables and seeding dummy data...")
            db.create_all()
            seed_database()
        else:
            print(f"Database found at {DB_PATH} — skipping seed.")

    app.run(debug=True)
