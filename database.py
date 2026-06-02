import sqlite3
import os

DB_PATH = "data/simogramme.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)
