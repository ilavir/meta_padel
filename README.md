# Meta Padle Dashboard

## Database Seeding

To populate the database with test data:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the seed script:
   ```
   python seed_data.py
   ```

This will create:
- 4 roles (admin, player, coach, guest)
- 10 test users with random roles
- 5 random scores per user

All test users have the password: `password123`

## Development

To run the application in development mode:
```
flask run
```

## DB init

Run for the first time

```
python init_db.py --create-admin --username admin --email admin@example.com --password secure_password
```
