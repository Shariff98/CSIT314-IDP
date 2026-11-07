"""Fills the database with random test data: 100+ records per data type.

Run from the project folder:   python scripts/generate_data.py
Smaller set for a quick try:   python scripts/generate_data.py --size 20

It deletes the old database first, so every run gives the same, fresh demo data.
Every generated account uses the password: password123"""
import argparse
import os
import random
import struct
import sys
import zlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.notify_milestone_controller import NotifyMilestoneController  # noqa: E402
from entity import db, storage  # noqa: E402
from entity.category import Category  # noqa: E402
from entity.company import Company  # noqa: E402
from entity.favourite import Favourite  # noqa: E402
from entity.idp import IDP  # noqa: E402
from entity.idp_photo import IDPPhoto  # noqa: E402
from entity.team_member import TeamMember  # noqa: E402
from entity.user_account import UserAccount  # noqa: E402
from entity.user_profile import UserProfile  # noqa: E402

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Quinn"]
LAST = ["Tan", "Lim", "Wong", "Ng", "Lee", "Chen", "Goh", "Ong", "Koh", "Teo"]
STYLES = ["Modern", "Minimalist", "Scandinavian", "Industrial", "Japandi", "Classic", "Tropical",
          "Contemporary", "Luxury", "Rustic"]
EXTRA_CATEGORIES = ["Dining Room", "Kids Room", "Study", "Balcony", "Walk-in Wardrobe", "Entryway", "Laundry",
                    "Home Theatre", "Retail Shop", "Cafe", "Restaurant", "Clinic", "Hotel Lobby", "Showroom", "Gym"]
LOCATIONS = ["Tampines", "Punggol", "Jurong East", "Bishan", "Toa Payoh", "Bukit Timah", "Woodlands", "Clementi",
             "Sengkang", "Bedok", "Novena", "Orchard", "Pasir Ris", "Queenstown", "Yishun"]
AREAS = ["Central", "North", "South", "East", "West", "North-East"]
PROPERTY_TYPES = ["HDB", "Condo", "Landed", "Commercial"]
SERVICES = ["Full renovation", "Space planning", "Carpentry", "Lighting design", "Kitchen design",
            "3D rendering", "Project management", "Furniture sourcing"]
POSITIONS = ["Lead designer", "Junior designer", "Project manager", "3D visualiser", "Site supervisor"]
COLOURS = [(196, 164, 132), (120, 144, 156), (233, 196, 106), (42, 157, 143), (231, 111, 81), (38, 70, 83),
           (180, 180, 170), (110, 90, 80)]


def name(i):
    return f"{FIRST[i % 10]} {LAST[(i // 10) % 10]}"


def png(width, height, colour):
    """A plain single-colour PNG with a lighter band, written without any image library."""
    light = tuple(min(255, c + 40) for c in colour)
    rows = b"".join(b"\x00" + bytes(light if height // 3 < y < height // 2 else colour) * width
                    for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def clustered_budget(rng=random):
    """Budgets cluster where customers ask, so the budget chatbot has real choices:
    40% from $8k to $14k, 25% from $14k to $40k, 20% from $40k to $120k, 15% from $5k to $8k."""
    roll = rng.random()
    if roll < 0.40:
        low, high = 8_000, 14_000
    elif roll < 0.65:
        low, high = 14_000, 40_000
    elif roll < 0.85:
        low, high = 40_000, 120_000
    else:
        low, high = 5_000, 8_000
    return int(round(rng.uniform(low, high), -2))


def stamp(moment):
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def random_time_between(start, end):
    return start + timedelta(seconds=random.randint(0, max(int((end - start).total_seconds()), 1)))


def main(size=100, db_path=None, upload_dir=None):
    random.seed(314)
    db_path = db_path or os.environ.get("DB_PATH", os.path.join(PROJECT_DIR, "platform.db"))
    upload_dir = upload_dir or os.environ.get("UPLOAD_DIR", os.path.join(PROJECT_DIR, "uploads"))
    if os.path.exists(db_path):
        os.remove(db_path)
    db.configure(db_path)
    storage.configure(upload_dir)
    db.init_db()

    now = datetime.now()
    start = now - timedelta(days=180)

    # ---------- user profiles and accounts ----------
    UserProfile.create("Moderator", "Example custom profile: reviews reported projects (no extra pages yet).")
    UserAccount.create("Admin", "admin@example.com", "password123", "UserAdmin", stamp(start))
    UserAccount.create("Platform Manager", "manager@example.com", "password123", "PlatformManager", stamp(start))
    designers = [UserAccount.create(name(i), f"designer{i}@example.com", "password123", "InteriorDesigner",
                                    stamp(random_time_between(start, now - timedelta(days=60)))) for i in range(size)]
    customers = [UserAccount.create(name(i), f"customer{i}@example.com", "password123", "Customer",
                                    stamp(random_time_between(start, now))) for i in range(size)]
    for account in random.sample(customers, max(1, size // 20)):
        account.suspend()

    # ---------- categories ----------
    for category in EXTRA_CATEGORIES:
        Category.create(category, f"{category} projects.", stamp(random_time_between(start, now)))
    categories = [c.name for c in Category.all_active()]

    # ---------- companies and team members ----------
    members = 0
    for i, designer in enumerate(designers):
        company = Company.create(designer.id, f"{LAST[i % 10]} & {FIRST[(i // 10) % 10]} Interiors {i}",
                                 f"2019{i:05d}K", f"{random.randint(1, 999)} {random.choice(LOCATIONS)} Road",
                                 f"6{random.randint(1000000, 9999999)}", f"studio{i}@example.com",
                                 "We turn houses into homes with thoughtful, practical design.")
        low = random.randrange(5000, 40000, 5000)
        company.save(specialisations=", ".join(random.sample(STYLES, 3)),
                     service_areas=", ".join(random.sample(AREAS, 2)), services=", ".join(random.sample(SERVICES, 3)),
                     budget_min=low, budget_max=low + random.randrange(20000, 100000, 10000),
                     years_experience=random.randint(1, 25), certifications="BCA Green Mark" if i % 3 == 0 else "",
                     awards="Singapore Interior Design Award" if i % 7 == 0 else "")
        for _ in range(random.randint(1, 3)):
            TeamMember.add(company.id, name(random.randint(0, 99)), random.choice(POSITIONS))
            members += 1

    # ---------- projects (IDPs) with a cover photo each ----------
    photos = [png(160, 100, colour) for colour in COLOURS]
    idps = []
    for i in range(size * 3):
        designer = random.choice(designers)
        style, room = random.sample(STYLES, 2), random.choice(categories)
        created = random_time_between(start, now - timedelta(days=1))
        status = random.choice(["Current", "Past", "Past"])
        idp = IDP.create(designer.id, f"{style[0]} {room} #{i + 1}",
                         f"A {style[0].lower()} {room.lower()} renovation with {style[1].lower()} touches.",
                         room, clustered_budget(), style_tags=", ".join(style),
                         property_type=random.choice(PROPERTY_TYPES), location=random.choice(LOCATIONS),
                         completion_date=(created + timedelta(days=random.randint(20, 90))).date().isoformat()
                         if status == "Past" else None,
                         published=random.random() > 0.1, status=status, created_at=stamp(created))
        IDPPhoto.create(idp.id, random.choice(photos), "png", is_cover=True)
        idps.append((idp, created))

    # ---------- views and favourites, spread over time ----------
    published = [(idp, created) for idp, created in idps if idp.is_published]
    view_count = saved = 0
    for customer in customers:
        for idp, created in random.sample(published, min(len(published), random.randint(3, 12))):
            for _ in range(random.randint(1, 4)):
                idp.record_view(customer_id=customer.id, session_key=f"seed-{customer.id}-{view_count}",
                                viewed_at=stamp(random_time_between(created, now)))
                view_count += 1
            if random.random() < 0.35:
                saved += Favourite.add(customer.id, idp.id, saved_at=stamp(random_time_between(created, now)))
    for idp, created in random.sample(published, min(len(published), size)):    # anonymous visitors
        for _ in range(random.randint(1, 15)):
            idp.record_view(session_key=f"guest-{view_count}", viewed_at=stamp(random_time_between(created, now)))
            view_count += 1

    notifications = sum(len(NotifyMilestoneController().check(IDP.find_by_id(idp.id))) for idp, _ in idps)

    print(f"Database: {db_path}")
    print(f"Created {len(designers) + len(customers) + 2} accounts, {len(UserProfile.search())} user profiles, "
          f"{len(categories)} categories, {len(designers)} companies, {members} team members,")
    print(f"        {len(idps)} projects with photos, {view_count} views, {saved} favourites, "
          f"{notifications} notifications.")
    print("Log in with admin@example.com, manager@example.com, designer0@example.com or customer0@example.com "
          "(password: password123).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", type=int, default=100, help="designers and customers to create (default 100)")
    main(parser.parse_args().size)
