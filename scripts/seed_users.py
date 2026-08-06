"""One-off script to seed local test users for each role (dev/test only).

Usage:
    python -m scripts.seed_users

Creates 2 users per role (6 total). Change the passwords immediately if this
is ever run against anything but a local/dev database.
"""

from app.auth.security import hash_password
from app.db import SessionLocal, engine
from app.models import Base, Role, User

TEST_USERS: list[tuple[str, str, str, Role]] = [
    ("req1", "req1@example.com", "ChangeMe123!", Role.REQUESTER),
    ("req2", "req2@example.com", "ChangeMe123!", Role.REQUESTER),
    ("zoneadmin1", "zoneadmin1@example.com", "ChangeMe123!", Role.ZONE_ADMIN),
    ("zoneadmin2", "zoneadmin2@example.com", "ChangeMe123!", Role.ZONE_ADMIN),
    ("cloudops1", "cloudops1@example.com", "ChangeMe123!", Role.CLOUDOPS_ADMIN),
    ("cloudops2", "cloudops2@example.com", "ChangeMe123!", Role.CLOUDOPS_ADMIN),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)  # convenience for dev; Alembic remains source of truth
    db = SessionLocal()
    try:
        created = 0
        for username, email, password, role in TEST_USERS:
            if db.query(User).filter(User.username == username).first():
                continue
            db.add(User(username=username, email=email, password_hash=hash_password(password), role=role))
            created += 1
        db.commit()
        print(f"Seeded {created} new test user(s); {len(TEST_USERS) - created} already existed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
