from db.database import get_connection

def init_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS simogrammes (
        id INTEGER PRIMARY KEY,
        reference TEXT,
        machine TEXT,
        pdc TEXT,
        date TEXT,
        temps_cycle REAL,
        taux_machine REAL,
        taux_operateur REAL,
        pieces_heure REAL,
        pieces_jour REAL
    )
    """)

    conn.commit()
    conn.close()
