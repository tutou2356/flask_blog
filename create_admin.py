#!/usr/bin/env python3
import argparse
import sys

from app_blog import app, db, User


def parse_args():
    parser = argparse.ArgumentParser(description='Create an admin user.')
    parser.add_argument('--username', required=True, help='Admin username')
    parser.add_argument('--email', required=True, help='Admin email')
    parser.add_argument('--password', required=True, help='Admin password')
    return parser.parse_args()


def main():
    args = parse_args()
    with app.app_context():
        existing = User.query.filter(
            (User.username == args.username) | (User.email == args.email)
        ).first()
        if existing:
            print('User already exists with the same username or email.', file=sys.stderr)
            return 1

        user = User(username=args.username, email=args.email, role='admin')
        user.set_password(args.password)
        db.session.add(user)
        db.session.commit()
        print('Admin user created.')
        print('Example:')
        print('  python create_admin.py --username admin --email admin@example.com --password "ChangeMe123"')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
