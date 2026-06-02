from db.database import get_connection

def save_simogramme(meta, kpis):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO simogrammes (
            reference, machine, pdc, date,
            temps_cycle, taux_machine,
            taux_operateur, pieces_heure, pieces_jour
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meta["reference"],
        meta["machine"],
        meta["pdc"],
        meta["date"],
        kpis["temps_cycle"],
        kpis["taux_machine"],
        kpis["taux_operateur"],
        kpis["pieces_heure"],
        kpis["pieces_jour"]
    ))

    conn.commit()
    conn.close()


def get_simogrammes():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM simogrammes")
    data = cur.fetchall()

    conn.close()
    return data
