# fusion_app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")

st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

# Carga de archivos
file_scopus = st.file_uploader("Sube archivo Scopus (.csv)", type="csv")
file_wos = st.file_uploader("Sube archivo WoS (.txt)", type="txt")

if file_scopus and file_wos:
    try:
        df_scopus = pd.read_csv(file_scopus)
        df_wos = pd.read_csv(file_wos, sep="\t", encoding="utf-8", engine="python")

        st.subheader("Resumen de datos cargados")
        st.write(f"🔹 Scopus: {df_scopus.shape[0]} registros, {df_scopus.shape[1]} columnas")
        st.write(f"🔹 WoS: {df_wos.shape[0]} registros, {df_wos.shape[1]} columnas")

        # Fusión y eliminación de duplicados
        df_combined = pd.concat([df_scopus, df_wos], ignore_index=True)
        df_combined_cleaned = df_combined.drop_duplicates()

        st.success(f"✔️ Fusionado completo. Total final: {df_combined_cleaned.shape[0]} registros.")

        # Previsualización y descarga
        st.dataframe(df_combined_cleaned.head(10))

        csv = df_combined_cleaned.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar CSV fusionado", csv, "fusionado.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error procesando los archivos: {e}")

else:
    st.info("🔄 Esperando que subas ambos archivos...")
