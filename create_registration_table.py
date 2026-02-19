import sqlite3

conn = sqlite3.connect("online_voting.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registration_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    mobile TEXT,
    gender TEXT,
    dob TEXT,
    adhar_number TEXT,
    voter_id TEXT,
    password TEXT,
    conferm_password TEXT
)
""")

conn.commit()
conn.close()

print("registration_information table create zala 👍")