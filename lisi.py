import streamlit as st

tab1, tab2, tab3, tab4 = st.tabs([
    "Simograma",
    "Datos",
    "Histórico",
    "Export"
])

with tab1:
    st.write("Simograma aquí")

with tab2:
    st.write("Datos aquí")

with tab3:
    st.write("Histórico aquí")

with tab4:
    st.write("Export aquí")
