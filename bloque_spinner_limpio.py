            with st.spinner("🔄 Fusionando archivos y limpiando registros..."):
                mensaje_proceso.markdown("✅ **Fusión iniciada correctamente. Procesando datos...**")

    mensaje_proceso.empty()
    st.success("✅ Fusión completada con éxito. Puedes continuar con los informes.")
    st.session_state["fusion_en_proceso"] = False
