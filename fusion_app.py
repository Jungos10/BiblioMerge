
# fusion_app.py
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")

st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

# Carga de archivos principales
file_scopus = st.file_uploader("Sube archivo Scopus (.csv)", type="csv")
file_wos = st.file_uploader("Sube archivo WoS (.txt)", type="txt")
file_equiv = st.file_uploader("Sube archivo de equivalencias (.xlsx)", type="xlsx")

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

        # Aplicar equivalencias si se sube Excel
        if file_equiv is not None:
            try:
                equivalencias = pd.read_excel(file_equiv, sheet_name=None)  # lee todas las hojas
                st.success("✔️ Archivo de equivalencias cargado correctamente")

                # Depurar autores
                if 'authors' in equivalencias:
                    dic_autores = dict(zip(equivalencias['authors'].iloc[:, 0], equivalencias['authors'].iloc[:, 1]))
                    if 'Authors' in df_combined_cleaned.columns:
                        df_combined_cleaned['Authors'] = df_combined_cleaned['Authors'].replace(dic_autores)

                # Depurar author keywords
                if 'author_keywords' in equivalencias:
                    dic_auth_kw = dict(zip(equivalencias['author_keywords'].iloc[:, 0], equivalencias['author_keywords'].iloc[:, 1]))
                    if 'Author Keywords' in df_combined_cleaned.columns:
                        df_combined_cleaned['Author Keywords'] = df_combined_cleaned['Author Keywords'].replace(dic_auth_kw)

                # Depurar index keywords
                if 'index_keywords' in equivalencias:
                    dic_index_kw = dict(zip(equivalencias['index_keywords'].iloc[:, 0], equivalencias['index_keywords'].iloc[:, 1]))
                    if 'Index Keywords' in df_combined_cleaned.columns:
                        df_combined_cleaned['Index Keywords'] = df_combined_cleaned['Index Keywords'].replace(dic_index_kw)

                # Depurar cited references
                if 'cited_refs' in equivalencias:
                    dic_refs = dict(zip(equivalencias['cited_refs'].iloc[:, 0], equivalencias['cited_refs'].iloc[:, 1]))
                    if 'Cited References' in df_combined_cleaned.columns:
                        df_combined_cleaned['Cited References'] = df_combined_cleaned['Cited References'].replace(dic_refs)

                st.success("✔️ Depuración aplicada con éxito")

            except Exception as e:
                st.error(f"⚠️ Error al procesar el archivo de equivalencias: {e}")

        # Previsualización
        st.dataframe(df_combined_cleaned.head(10))

        # Exportación en varios formatos
        csv = df_combined_cleaned.to_csv(index=False).encode("utf-8")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_combined_cleaned.to_excel(writer, index=False, sheet_name='Fusión')
            writer.save()
        txt = df_combined_cleaned.to_string(index=False)

        st.download_button("📥 Descargar como CSV", csv, "fusionado.csv", "text/csv")
        st.download_button("📥 Descargar como Excel", excel_buffer.getvalue(), "fusionado.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("📥 Descargar como TXT", txt, "fusionado.txt", "text/plain")

        # Visualizaciones
        st.subheader("🔍 Análisis de frecuencia")

        col1, col2 = st.columns(2)

        with col1:
            if 'Authors' in df_combined_cleaned.columns:
                top_authors = df_combined_cleaned['Authors'].value_counts().head(20)
                st.write("#### Autores más frecuentes")
                fig1, ax1 = plt.subplots()
                top_authors.plot(kind='barh', ax=ax1)
                ax1.invert_yaxis()
                ax1.set_xlabel("Número de documentos")
                st.pyplot(fig1)

            if 'Cited References' in df_combined_cleaned.columns:
                top_refs = df_combined_cleaned['Cited References'].dropna().str.strip().value_counts().head(20)
                st.write("#### Referencias citadas más frecuentes")
                fig3, ax3 = plt.subplots()
                top_refs.plot(kind='barh', ax=ax3)
                ax3.invert_yaxis()
                ax3.set_xlabel("Frecuencia")
                st.pyplot(fig3)

        with col2:
            if 'Author Keywords' in df_combined_cleaned.columns:
                keywords_series = df_combined_cleaned['Author Keywords'].dropna().str.split(';|,').explode().str.strip()
                top_keywords = keywords_series.value_counts().head(20)
                st.write("#### Keywords más frecuentes")
                fig2, ax2 = plt.subplots()
                top_keywords.plot(kind='barh', ax=ax2)
                ax2.invert_yaxis()
                ax2.set_xlabel("Frecuencia")
                st.pyplot(fig2)

            if 'Index Keywords' in df_combined_cleaned.columns:
                index_kw_series = df_combined_cleaned['Index Keywords'].dropna().str.split(';|,').explode().str.strip()
                top_index_kw = index_kw_series.value_counts().head(20)
                st.write("#### Index Keywords más frecuentes")
                fig4, ax4 = plt.subplots()
                top_index_kw.plot(kind='barh', ax=ax4)
                ax4.invert_yaxis()
                ax4.set_xlabel("Frecuencia")
                st.pyplot(fig4)

    except Exception as e:
        st.error(f"❌ Error procesando los archivos: {e}")

else:
    st.info("🔄 Esperando que subas los archivos de Scopus y WoS...")
