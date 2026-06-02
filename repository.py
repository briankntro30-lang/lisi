from database import get_connection


def save_simogramme(meta, kpis):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO simogrammes (
            reference,
            machine,
            pdc,
            date,
            temps_cycle,
            temps_machine,
            temps_operateur,
            temps_attente,
            taux_homme,
            taux_machine,
            pieces_jour
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meta["reference"],
        meta["machine"],
        meta["pdc"],
        meta["date"],
        kpis.get("temps_cycle", 0),
        kpis.get("temps_machine", 0),
        kpis.get("temps_operateur", 0),
        kpis.get("temps_attente", 0),
        kpis.get("taux_homme", 0),
        kpis.get("taux_machine", 0),
        kpis.get("pieces_jour", 0)
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
