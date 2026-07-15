from app import db
from app.models import User, Trek, Booking, StaffProfile
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone, timedelta


def seed_database():
    """
    Populate database with dummy data for testing.

    Creates:
    - 1 admin (already exists; preserved)
    - 18 staff members (15 approved, 3 pending)
    - 70 trekker users (68 active, 2 blacklisted)
    - 45 treks (3 non-overlapping per approved staff; every approved
      staff has at least one past Completed trek)
    - Diverse bookings across many months (Booked / Cancelled / Completed)
      so user/staff history and booking-trend charts look genuine
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

    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)

    # ==================== CREATE STAFF MEMBERS ====================
    print("Creating 18 staff members...")

    staff_data = [
        # 15 approved
        {'name': 'Priya Sharma', 'email': 'test_staff_1@example.com', 'specialization': 'High Altitude Guide', 'experience': 8},
        {'name': 'Rahul Mehta', 'email': 'test_staff_2@example.com', 'specialization': 'Alpine Trekking', 'experience': 6},
        {'name': 'Ananya Patel', 'email': 'test_staff_3@example.com', 'specialization': 'Wildlife Trails', 'experience': 5},
        {'name': 'Vikram Singh', 'email': 'test_staff_4@example.com', 'specialization': 'Desert Expeditions', 'experience': 10},
        {'name': 'Meera Nair', 'email': 'test_staff_5@example.com', 'specialization': 'Coastal Routes', 'experience': 4},
        {'name': 'Arjun Reddy', 'email': 'test_staff_6@example.com', 'specialization': 'Rock Scrambling', 'experience': 7},
        {'name': 'Kavya Iyer', 'email': 'test_staff_7@example.com', 'specialization': 'Forest Trails', 'experience': 3},
        {'name': 'Siddharth Joshi', 'email': 'test_staff_8@example.com', 'specialization': 'Winter Treks', 'experience': 9},
        {'name': 'Neha Kapoor', 'email': 'test_staff_9@example.com', 'specialization': 'Beginner Groups', 'experience': 5},
        {'name': 'Rohan Desai', 'email': 'test_staff_10@example.com', 'specialization': 'River Valleys', 'experience': 6},
        {'name': 'Ishita Banerjee', 'email': 'test_staff_11@example.com', 'specialization': 'Himalayan Routes', 'experience': 11},
        {'name': 'Aditya Rao', 'email': 'test_staff_12@example.com', 'specialization': 'Multi-day Camping', 'experience': 4},
        {'name': 'Sanya Gupta', 'email': 'test_staff_13@example.com', 'specialization': 'Photography Treks', 'experience': 7},
        {'name': 'Kabir Malhotra', 'email': 'test_staff_14@example.com', 'specialization': 'Extreme Peaks', 'experience': 12},
        {'name': 'Diya Krishnan', 'email': 'test_staff_15@example.com', 'specialization': 'Family Treks', 'experience': 3},
        # 3 pending
        {'name': 'Nikhil Bose', 'email': 'test_staff_16@example.com', 'specialization': 'Jungle Safaris', 'experience': 2},
        {'name': 'Tara Menon', 'email': 'test_staff_17@example.com', 'specialization': 'Hill Stations', 'experience': 1},
        {'name': 'Aarav Chauhan', 'email': 'test_staff_18@example.com', 'specialization': 'Trail Mapping', 'experience': 4},
    ]

    staff_users = []
    approved_staff = []
    for i, info in enumerate(staff_data, start=1):
        approval_status = 'approved' if i <= 15 else 'pending'
        password = f"test_staff_{i}_123"
        contact = f"9188{10000000 + i:08d}"

        staff_user = User(
            name=info['name'],
            email=info['email'],
            password=generate_password_hash(password),
            role='staff',
            status='active',
            contact_number=contact,
            whatsapp_number=contact,
        )
        db.session.add(staff_user)
        db.session.flush()

        staff_profile = StaffProfile(
            user_id=staff_user.id,
            specialization=info['specialization'],
            experience=info['experience'],
            status=approval_status,
            approved_by_admin=(approval_status == 'approved'),
        )
        db.session.add(staff_profile)
        staff_users.append(staff_user)
        if approval_status == 'approved':
            approved_staff.append(staff_user)

    db.session.commit()
    print("Created 18 staff members (15 approved, 3 pending)")

    # ==================== CREATE TREKKER USERS ====================
    print("Creating 70 trekker users...")

    trekker_names = [
        'Aarav Sharma', 'Vihaan Patel', 'Aditi Verma', 'Ishaan Reddy', 'Anvi Mehta',
        'Kabir Singh', 'Myra Kapoor', 'Reyansh Joshi', 'Sara Nair', 'Vivaan Desai',
        'Anaya Iyer', 'Arnav Gupta', 'Diya Banerjee', 'Shaurya Rao', 'Kiara Malhotra',
        'Advait Krishnan', 'Pari Bose', 'Rudra Menon', 'Aisha Chauhan', 'Yash Thakur',
        'Nisha Pillai', 'Dev Agarwal', 'Saanvi Chopra', 'Krish Bhat', 'Mira Saxena',
        'Rohan Nambiar', 'Tanya Sethi', 'Harsh Kulkarni', 'Pooja Dutta', 'Aryan Bajaj',
        'Rhea Shetty', 'Kunal Pandey', 'Simran Gill', 'Nikhil Trivedi', 'Pallavi Hegde',
        'Abhinav Suri', 'Mehak Arora', 'Varun Lakhani', 'Shruti Jain', 'Pranav Kohli',
        'Lavanya Sinha', 'Gaurav Bansal', 'Naina Mathur', 'Soham Vora', 'Ritika Sengupta',
        'Manav Chatterjee', 'Esha Rangan', 'Tirth Solanki', 'Jhanvi Latif', 'Omkar Phadke',
        'Aanya Dhar', 'Farhan Qureshi', 'Vedika Baruah', 'Samar Walia', 'Ira Fernandes',
        'Lakshya Rawat', 'Zara Merchant', 'Harshita Goel', 'Dhruv Menaria', 'Sanvi Khatri',
        'Yuvraj Bindra', 'Amrita Sehgal', 'Parth Chawla', 'Nivedita Das', 'Riyan Khanna',
        'Suhana Rege', 'Ishaan Tiwari', 'Kavya Bhave', 'Tejas Naidu', 'Anushka More',
    ]

    trekker_users = []
    for i, name in enumerate(trekker_names, start=1):
        email = f"test_user_{i}@example.com"
        password = f"test_user_{i}_123"
        status = 'blacklisted' if i >= 69 else 'active'
        contact = f"9199{10000000 + i:08d}"

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='trekker',
            status=status,
            contact_number=contact,
            whatsapp_number=contact,
        )
        db.session.add(user)
        trekker_users.append(user)

    db.session.commit()
    print("Created 70 trekker users (68 active, 2 blacklisted)")

    # ==================== CREATE TREKS ====================
    print("Creating 45 treks (3 per approved staff, non-overlapping dates)...")

    trek_templates = [
        {'name': 'Himalayan Adventure', 'location': 'Nepal', 'difficulty': 'Hard', 'duration': 14, 'total_slots': 20},
        {'name': 'Valley of Flowers', 'location': 'Uttarakhand', 'difficulty': 'Easy', 'duration': 5, 'total_slots': 30},
        {'name': 'Mountain Pass Trek', 'location': 'Himachal Pradesh', 'difficulty': 'Moderate', 'duration': 8, 'total_slots': 15},
        {'name': 'Western Ghats Walk', 'location': 'Kerala', 'difficulty': 'Easy', 'duration': 3, 'total_slots': 25},
        {'name': 'Peak Challenge', 'location': 'Ladakh', 'difficulty': 'Extreme', 'duration': 21, 'total_slots': 10},
        {'name': 'Alpine Meadows', 'location': 'Switzerland', 'difficulty': 'Moderate', 'duration': 7, 'total_slots': 18},
        {'name': 'Desert Expedition', 'location': 'Rajasthan', 'difficulty': 'Hard', 'duration': 10, 'total_slots': 12},
        {'name': 'Coastal Trail', 'location': 'Goa', 'difficulty': 'Easy', 'duration': 4, 'total_slots': 35},
        {'name': 'River Valley Trek', 'location': 'Rishikesh', 'difficulty': 'Moderate', 'duration': 6, 'total_slots': 22},
        {'name': 'Island Explorers', 'location': 'Andaman', 'difficulty': 'Easy', 'duration': 6, 'total_slots': 20},
        {'name': 'Snow Line Traverse', 'location': 'Sikkim', 'difficulty': 'Hard', 'duration': 12, 'total_slots': 14},
        {'name': 'Forest Canopy Trek', 'location': 'Meghalaya', 'difficulty': 'Moderate', 'duration': 5, 'total_slots': 24},
        {'name': 'Plateau Circuit', 'location': 'Spiti', 'difficulty': 'Hard', 'duration': 9, 'total_slots': 16},
        {'name': 'Lakeside Circuit', 'location': 'Kashmir', 'difficulty': 'Easy', 'duration': 4, 'total_slots': 28},
        {'name': 'Ridge Runner', 'location': 'Garhwal', 'difficulty': 'Extreme', 'duration': 15, 'total_slots': 8},
    ]

    # Slot 0 = past Completed (every staff gets finished trek history)
    # Slot 1 = near future Open/Closed
    # Slot 2 = further out Approved/Pending/Open
    # Mix: Completed 15, Open 12, Closed 3, Approved 8, Pending 7
    per_staff_start_offsets = [
        (-180, 25, 130),
        (-155, 40, 145),
        (-210, 50, 160),
        (-125, 18, 115),
        (-240, 35, 150),
        (-95, 55, 170),
        (-165, 22, 135),
        (-200, 45, 155),
        (-140, 60, 175),
        (-250, 12, 120),
        (-110, 70, 185),
        (-190, 32, 140),
        (-175, 48, 165),
        (-220, 28, 125),
        (-85, 65, 190),
    ]

    slot0_statuses = ['Completed'] * 15
    slot1_statuses = ['Open'] * 12 + ['Closed'] * 3
    slot2_statuses = ['Approved'] * 8 + ['Pending'] * 7  # 15 far-future

    treks = []

    for staff_idx, staff_user in enumerate(approved_staff):
        offsets = per_staff_start_offsets[staff_idx]
        slot_statuses = [
            slot0_statuses[staff_idx],
            slot1_statuses[staff_idx],
            slot2_statuses[staff_idx],
        ]
        for slot in range(3):
            template = trek_templates[(staff_idx + slot) % len(trek_templates)]
            duration = template['duration']
            start_date = today + timedelta(days=offsets[slot])
            end_date = start_date + timedelta(days=duration - 1)
            status = slot_statuses[slot]

            trek = Trek(
                name=f"{template['name']} — {staff_user.name.split()[0]}",
                location=template['location'],
                difficulty=template['difficulty'],
                duration=duration,
                total_slots=template['total_slots'],
                available_slots=template['total_slots'],
                status=status,
                start_date=start_date,
                end_date=end_date,
                assigned_staff_id=staff_user.id,
            )
            db.session.add(trek)
            treks.append(trek)

    db.session.commit()
    print(f"Created {len(treks)} treks with varied statuses and non-overlapping staff schedules")

    # ==================== CREATE BOOKINGS ====================
    print("Creating diverse bookings across months...")

    booking_count = 0
    cancelled_count = 0
    completed_booking_count = 0
    booked_count = 0

    slots_used = {trek.id: 0 for trek in treks}
    # Avoid the same user booking the same trek twice
    booked_pairs = set()
    active_trekkers = [u for u in trekker_users if u.status == 'active']

    completed_treks = [t for t in treks if t.status == 'Completed']
    open_treks = [t for t in treks if t.status == 'Open']
    closed_treks = [t for t in treks if t.status == 'Closed']
    approved_treks = [t for t in treks if t.status == 'Approved']
    pending_treks = [t for t in treks if t.status == 'Pending']
    upcoming_bookable = open_treks + closed_treks + approved_treks

    def can_book(trek, extra=1):
        return slots_used[trek.id] + extra <= trek.total_slots

    def booking_dt_for_trek(trek, prefer_before_start_days, jitter_days=0):
        """Place booking_date realistically before trek start, clamped into the past."""
        if trek.start_date:
            base = datetime(
                trek.start_date.year,
                trek.start_date.month,
                trek.start_date.day,
                10, 0, 0,
                tzinfo=timezone.utc,
            ) - timedelta(days=prefer_before_start_days + jitter_days)
        else:
            base = now - timedelta(days=prefer_before_start_days + jitter_days)
        # Never schedule booking_date in the future
        if base > now:
            base = now - timedelta(days=1 + (jitter_days % 14))
        return base

    def add_booking(user, trek, booking_status, payment_status, booking_dt):
        nonlocal booking_count, cancelled_count, completed_booking_count, booked_count
        pair = (user.id, trek.id)
        if pair in booked_pairs:
            return False
        if booking_status in ('Booked', 'Completed') and not can_book(trek):
            return False

        booking = Booking(
            user_id=user.id,
            trek_id=trek.id,
            booking_date=booking_dt,
            booking_status=booking_status,
            payment_status=payment_status,
        )
        db.session.add(booking)
        booked_pairs.add(pair)
        booking_count += 1
        if booking_status == 'Booked':
            slots_used[trek.id] += 1
            booked_count += 1
        elif booking_status == 'Cancelled':
            cancelled_count += 1
        elif booking_status == 'Completed':
            slots_used[trek.id] += 1
            completed_booking_count += 1
        return True

    # --- 1) Dense Completed history on every past trek (staff + user history) ---
    for i, trek in enumerate(completed_treks):
        fill = min(trek.total_slots - 1, 7 + (i % 5))  # 7–11 per completed trek
        for j in range(fill):
            user = active_trekkers[(i * 7 + j * 3) % len(active_trekkers)]
            days_before = 10 + ((i + j) % 40)
            jitter = (i * 5 + j * 11) % 20
            dt = booking_dt_for_trek(trek, days_before, jitter)
            add_booking(user, trek, 'Completed', 'Completed', dt)

    # --- 2) Give the first 20 trekkers a multi-month personal history ---
    # Each gets 2–3 completed + 1–2 upcoming Booked + sometimes a Cancelled
    for u_idx in range(min(20, len(active_trekkers))):
        user = active_trekkers[u_idx]

        # Completed: pick 2–3 different past treks
        for k in range(2 + (u_idx % 2)):
            trek = completed_treks[(u_idx + k * 4) % len(completed_treks)]
            dt = booking_dt_for_trek(trek, 14 + k * 9, u_idx + k)
            add_booking(user, trek, 'Completed', 'Completed', dt)

        # Upcoming Booked
        for k in range(1 + (u_idx % 2)):
            trek = upcoming_bookable[(u_idx + k * 5) % len(upcoming_bookable)]
            days_ago = 5 + u_idx * 3 + k * 17  # spread across recent months
            dt = now - timedelta(days=days_ago)
            payment = 'Completed' if (u_idx + k) % 2 == 0 else 'Pending'
            add_booking(user, trek, 'Booked', payment, dt)

        # Occasional cancel further back
        if u_idx % 3 == 0:
            trek = upcoming_bookable[(u_idx + 9) % len(upcoming_bookable)]
            dt = now - timedelta(days=40 + u_idx * 7)
            add_booking(user, trek, 'Cancelled', 'Pending', dt)

    # --- 3) Fill remaining Open/Approved/Closed capacity for trends ---
    cursor = 20
    for i, trek in enumerate(upcoming_bookable):
        target = min(trek.total_slots - 1, 3 + (i % 4))  # 3–6 active bookings
        added = 0
        attempts = 0
        while added < target and attempts < target * 4:
            attempts += 1
            user = active_trekkers[cursor % len(active_trekkers)]
            cursor += 1
            days_ago = 3 + ((i * 11 + attempts * 13) % 75)  # ~2.5 months of variety
            dt = now - timedelta(days=days_ago)
            payment = 'Completed' if attempts % 3 != 0 else 'Pending'
            if add_booking(user, trek, 'Booked', payment, dt):
                added += 1

    # --- 4) Extra cancellations sprinkled over older months ---
    cancel_pool = open_treks + approved_treks + pending_treks + closed_treks
    for i in range(20):
        trek = cancel_pool[i % len(cancel_pool)]
        user = active_trekkers[(30 + i * 2) % len(active_trekkers)]
        dt = now - timedelta(days=20 + i * 9)  # spread ~6 months
        add_booking(user, trek, 'Cancelled', 'Pending', dt)

    # Sync available_slots
    for trek in treks:
        trek.available_slots = max(0, trek.total_slots - slots_used[trek.id])

    db.session.commit()
    print(
        f"Created {booking_count} bookings "
        f"(Booked={booked_count}, Completed={completed_booking_count}, Cancelled={cancelled_count})"
    )

    # ==================== SUMMARY ====================
    status_counts = {}
    for trek in treks:
        status_counts[trek.status] = status_counts.get(trek.status, 0) + 1

    print("\n" + "=" * 50)
    print("DUMMY DATA SEEDING COMPLETE!")
    print("=" * 50)
    print("Summary:")
    print("   • Admins: 1 (admin@tma.com / admin123)")
    print("   • Staff: 18")
    print("      - Approved: 15")
    print("      - Pending: 3")
    print("   • Trekkers: 70 (test_user_1 to test_user_70)")
    print("      - Active: 68")
    print("      - Blacklisted: 2")
    print(f"   • Treks: {len(treks)} (3 per approved staff; each has 1 past Completed)")
    for status_name, count in sorted(status_counts.items()):
        print(f"      - {status_name}: {count}")
    print(f"   • Bookings: {booking_count}")
    print(f"      - Booked: {booked_count}")
    print(f"      - Completed: {completed_booking_count}")
    print(f"      - Cancelled: {cancelled_count}")
    print("=" * 50)
    print("\nTest Credentials:")
    print("   Admin: admin@tma.com / admin123")
    print("   Staff: test_staff_1@example.com / test_staff_1_123  (Priya Sharma, approved)")
    print("   User:  test_user_1@example.com / test_user_1_123  (Aarav Sharma — rich history)")
    print("=" * 50)
