
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos, limpiar duplicados y generar tablas de análisis.")

# Mostrar campos para carga de archivos
scopus_files = st.file_uploader("Sube archivos CSV de Scopus", type="csv", accept_multiple_files=True)
wos_files = st.file_uploader("Sube archivos TXT de WoS", type="txt", accept_multiple_files=True)

if scopus_files and wos_files:
    if st.button("🔄 Iniciar fusión"):
        st.success("Archivos recibidos correctamente. Aquí empezaría la fusión.")
