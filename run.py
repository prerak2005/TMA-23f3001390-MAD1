from app import create_app, db
from app.seeds import seed_database


if __name__ == '__main__':
    app = create_app()


    with app.app_context():
        # UNCOMMENT THESE 3 LINES ONLY WHEN YOU WANT TO RESET AND SEED
        # db.drop_all()
        # db.create_all()
        # seed_database()
        pass


    app.run(debug=True)
    