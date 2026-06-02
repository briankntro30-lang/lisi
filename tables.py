import streamlit as st
import pandas as pd

def render_tables():

    dfs = []

    for m in st.session_state["machines"]:

        st.subheader(f"Tableau {m}")

        df = st.data_editor(
            pd.DataFrame({
                "Etape": [""],
                "Début": [0.0],
                "Durée": [0.0],
                "TT": [False],
                "TM": [False],
                "TTM": [False],
                "TR": [False],
                "TF": [False],
            }),
            num_rows="dynamic",
            key=m
        )

        for i in range(1, len(df)):
            if df.loc[i, "Début"] == 0:
                df.loc[i, "Début"] = df.loc[i-1, "Début"] + df.loc[i-1, "Durée"]

        df["Fin"] = df["Début"] + df["Durée"]
        df["Sys"] = m

        dfs.append(df)

    return dfs
