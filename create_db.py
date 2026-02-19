import sqlite3

# फक्त database create होईल (file)
conn = sqlite3.connect("online_voting.db")

conn.close()

print("SQLite database successfully create zala 👍")