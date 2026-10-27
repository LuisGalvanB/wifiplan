#!/usr/bin/env python3
"""
Run once after migrations to populate demo data.
Usage: python -m app.seeds.run
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.base import SessionLocal
from app.models.tenant import User, Organization, Membership, MembershipRole
from app.core.security import hash_password
from app.seeds.ap_catalog import seed_ap_catalog


DEMO_ORG = {"name": "Demo Corp", "slug": "demo-corp"}
DEMO_USER = {"email": "admin@demo.com", "password": "Demo1234!", "full_name": "Demo Admin"}


def seed_demo_user(db):
    org = db.query(Organization).filter(Organization.slug == DEMO_ORG["slug"]).first()
    if not org:
        org = Organization(**DEMO_ORG)
        db.add(org)
        db.flush()
        print(f"Created org: {org.name}")

    user = db.query(User).filter(User.email == DEMO_USER["email"]).first()
    if not user:
        user = User(
            email=DEMO_USER["email"],
            hashed_password=hash_password(DEMO_USER["password"]),
            full_name=DEMO_USER["full_name"],
        )
        db.add(user)
        db.flush()
        print(f"Created user: {user.email}")

    existing_m = db.query(Membership).filter(
        Membership.organization_id == org.id,
        Membership.user_id == user.id,
    ).first()
    if not existing_m:
        db.add(Membership(organization_id=org.id, user_id=user.id, role=MembershipRole.admin))

    db.commit()
    print(f"\nDemo credentials:\n  Email: {DEMO_USER['email']}\n  Password: {DEMO_USER['password']}")
    print(f"  Org ID: {org.id}")


def main():
    db = SessionLocal()
    try:
        print("=== Seeding database ===")
        seed_demo_user(db)
        seed_ap_catalog(db)
        print("\n=== Seed complete ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
