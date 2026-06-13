from app import db
from app.models import User, Trek, Booking, StaffProfile
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone, timedelta

def seed_database():
    """
    Populate database with dummy data for testing.
    
    Creates:
    - 1 admin (already exists)
    - 15 staff members (varied approval states)
    - 40 trekker users
    - 10 treks (varied statuses and slots)
    - 50+ bookings (mix of statuses)
    """
    
    print("Starting dummy data seeding...")
    
    # ==================== CLEAR EXISTING DATA ====================
    # WARNING: Only run this during development!
    print("Clearing existing data...")
    Booking.query.delete()
    Trek.query.delete()
    StaffProfile.query.delete()
    
    # Keep admin user, but delete others
    User.query.filter(User.role != 'admin').delete()
    db.session.commit()
    
    # ==================== CREATE STAFF MEMBERS ====================
    print("👥 Creating 15 staff members...")
    
    staff_users = []
    for i in range(1, 16):
        email = f"test_staff_{i}@example.com"
        name = f"Staff Member {i}"
        password = f"test_staff_{i}_123"
        
        staff_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='staff',
            status='active',
            contact_number=f"919999{i:05d}",
            whatsapp_number=f"919999{i:05d}"
        )
        db.session.add(staff_user)
        db.session.flush()  # Get the user ID
        
        # Create StaffProfile
        # Approve first 12, keep 3 pending
        approval_status = 'approved' if i <= 12 else 'pending'
        
        staff_profile = StaffProfile(
            user_id=staff_user.id,
            specialization=f"Specialization {i}",
            experience=f"{i * 2} years",
            status=approval_status,
            approved_by_admin=True if i <= 12 else False
        )
        db.session.add(staff_profile)
        staff_users.append(staff_user)
    
    db.session.commit()
    print(f"Created 15 staff members (12 approved, 3 pending)")
    
    # ==================== CREATE TREKKER USERS ====================
    print("Creating 40 trekker users...")
    
    trekker_users = []
    for i in range(1, 41):
        email = f"test_user_{i}@example.com"
        name = f"Test User {i}"
        password = f"test_user_{i}_123"
        
        # Blacklist user 39 and 40
        status = 'blacklisted' if i >= 39 else 'active'
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='trekker',
            status=status,
            contact_number=f"919999{i:05d}",
            whatsapp_number=f"919999{i:05d}"
        )
        db.session.add(user)
        trekker_users.append(user)
    
    db.session.commit()
    print(f"Created 40 trekker users (38 active, 2 blacklisted)")
    
    # ==================== CREATE TREKS ====================
    print("Creating 10 treks...")
    
    trek_data = [
        {
            'name': 'Himalayan Adventure',
            'location': 'Nepal',
            'difficulty': 'Hard',
            'duration': 14,
            'total_slots': 20,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=30),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=44),
            'status': 'Open'
        },
        {
            'name': 'Valley Trek',
            'location': 'Switzerland',
            'difficulty': 'Easy',
            'duration': 5,
            'total_slots': 30,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=10),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=15),
            'status': 'Open'
        },
        {
            'name': 'Mountain Pass',
            'location': 'Himalayas',
            'difficulty': 'Moderate',
            'duration': 8,
            'total_slots': 15,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=20),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=28),
            'status': 'Open'
        },
        {
            'name': 'Forest Walk',
            'location': 'Kerala',
            'difficulty': 'Easy',
            'duration': 3,
            'total_slots': 25,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=5),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=8),
            'status': 'Open'
        },
        {
            'name': 'Peak Challenge',
            'location': 'Ladakh',
            'difficulty': 'Extreme',
            'duration': 21,
            'total_slots': 10,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=60),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=81),
            'status': 'Pending'
        },
        {
            'name': 'Summer Trek 2026',
            'location': 'Uttarakhand',
            'difficulty': 'Moderate',
            'duration': 7,
            'total_slots': 20,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=45),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=52),
            'status': 'Approved'
        },
        {
            'name': 'Desert Expedition',
            'location': 'Rajasthan',
            'difficulty': 'Hard',
            'duration': 10,
            'total_slots': 12,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=50),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=60),
            'status': 'Open'
        },
        {
            'name': 'Coastal Walk',
            'location': 'Goa',
            'difficulty': 'Easy',
            'duration': 4,
            'total_slots': 35,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=15),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=19),
            'status': 'Open'
        },
        {
            'name': 'River Rafting',
            'location': 'Rishikesh',
            'difficulty': 'Moderate',
            'duration': 2,
            'total_slots': 40,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=12),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=14),
            'status': 'Closed'
        },
        {
            'name': 'Island Trek',
            'location': 'Andaman',
            'difficulty': 'Easy',
            'duration': 6,
            'total_slots': 25,
            'start_date': datetime.now(timezone.utc).date() + timedelta(days=90),
            'end_date': datetime.now(timezone.utc).date() + timedelta(days=96),
            'status': 'Pending'
        }
    ]
    
    treks = []
    for i, trek_info in enumerate(trek_data):
        trek = Trek(
            name=trek_info['name'],
            location=trek_info['location'],
            difficulty=trek_info['difficulty'],
            duration=trek_info['duration'],
            total_slots=trek_info['total_slots'],
            available_slots=trek_info['total_slots'],
            status=trek_info['status'],
            start_date=trek_info['start_date'],
            end_date=trek_info['end_date'],
            assigned_staff_id=staff_users[i].id if i < len(staff_users) else None
        )
        db.session.add(trek)
        treks.append(trek)
    
    db.session.commit()
    print(f"Created 10 treks with varied statuses")
    
    # ==================== CREATE BOOKINGS ====================
    print("Creating 50+ bookings...")
    
    booking_count = 0
    
    # Users 1-10 book Trek 1 (20 slots total)
    for i in range(1, 11):
        booking = Booking(
            user_id=trekker_users[i-1].id,
            trek_id=treks[0].id,  # Himalayan Adventure (20 slots)
            booking_date=datetime.now(timezone.utc),
            booking_status='Booked',
            payment_status='Completed' if i % 2 == 0 else 'Pending'
        )
        db.session.add(booking)
        booking_count += 1
    
    # Adjust available slots for trek 1
    treks[0].available_slots = 10
    
    # Users 11-20 book Trek 2 (30 slots total)
    for i in range(11, 21):
        booking = Booking(
            user_id=trekker_users[i-1].id,
            trek_id=treks[1].id,  # Valley Trek (30 slots)
            booking_date=datetime.now(timezone.utc),
            booking_status='Booked',
            payment_status='Completed'
        )
        db.session.add(booking)
        booking_count += 1
    
    # Adjust available slots for trek 2
    treks[1].available_slots = 20
    
    # Users 21-27 book Trek 3 (15 slots)
    for i in range(21, 28):
        booking = Booking(
            user_id=trekker_users[i-1].id,
            trek_id=treks[2].id,  # Mountain Pass
            booking_date=datetime.now(timezone.utc),
            booking_status='Booked',
            payment_status='Completed' if i % 3 == 0 else 'Pending'
        )
        db.session.add(booking)
        booking_count += 1
    
    # Adjust available slots for trek 3
    treks[2].available_slots = 8
    
    # Users 28-35 book Trek 4 (25 slots)
    for i in range(28, 36):
        booking = Booking(
            user_id=trekker_users[i-1].id,
            trek_id=treks[3].id,  # Forest Walk
            booking_date=datetime.now(timezone.utc),
            booking_status='Booked',
            payment_status='Completed'
        )
        db.session.add(booking)
        booking_count += 1
    
    # Adjust available slots for trek 4
    treks[3].available_slots = 17
    
    # Add some cancelled bookings
    for i in range(1, 4):
        booking = Booking(
            user_id=trekker_users[i + 35].id,
            trek_id=treks[7].id,  # Coastal Walk
            booking_date=datetime.now(timezone.utc) - timedelta(days=10),
            booking_status='Cancelled',
            payment_status='Pending'
        )
        db.session.add(booking)
        booking_count += 1
    
    # Add some completed bookings
    for i in range(1, 5):
        booking = Booking(
            user_id=trekker_users[i].id,
            trek_id=treks[6].id,  # Desert Expedition
            booking_date=datetime.now(timezone.utc) - timedelta(days=90),
            booking_status='Completed',
            payment_status='Completed'
        )
        db.session.add(booking)
        booking_count += 1
    
    db.session.commit()
    print(f"Created {booking_count} bookings with varied statuses")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*50)
    print("DUMMY DATA SEEDING COMPLETE!")
    print("="*50)
    print(f"Summary:")
    print(f"   • Admins: 1 (admin@tma.com / admin123)")
    print(f"   • Staff: 15 (test_staff_1 to test_staff_15)")
    print(f"      - Approved: 12")
    print(f"      - Pending: 3")
    print(f"   • Trekkers: 40 (test_user_1 to test_user_40)")
    print(f"      - Active: 38")
    print(f"      - Blacklisted: 2")
    print(f"   • Treks: 10 (varied statuses)")
    print(f"   • Bookings: {booking_count} (pending/completed/cancelled)")
    print("="*50)
    print("\nTest Credentials:")
    print("   Admin: admin@tma.com / admin123")
    print("   Staff: test_staff_1@example.com / test_staff_1_123")
    print("   User:  test_user_1@example.com / test_user_1_123")
    print("="*50)