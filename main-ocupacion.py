import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Gestor Semanal de Ocupación - Babel", page_icon="📊")
st.image("Logo Babel Horizontal (1).jpg", width=180)
st.title("Gestor Semanal de Ocupación - Babel")

st.sidebar.markdown("## 📥 Subir archivo de Power BI")
archivo = st.sidebar.file_uploader("Cargar archivo Excel exportado desde Power BI (formato resumido)", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo, sheet_name=0, header=None)
    st.success("Archivo cargado correctamente.")

    # Buscar filas que contengan IDs de personas (ej: 3531 | Nombre)
    personas_df = df[df[0].astype(str).str.contains(r"\d{4} \|", regex=True, na=False)].copy()
    personas_df.columns = ["ID_Nombre", "Proyecto", "Mes", "PMZ", "Occupation", "Available", "Occupation (%)"]
    personas_df["Persona"] = personas_df["ID_Nombre"].str.extract(r"\| (.+)")

    # Selector de mes
    meses_disponibles = personas_df["Mes"].dropna().unique().tolist()
    mes_actual = datetime.now().strftime("%b")  # Ej: "Jul"
    mes_default = mes_actual if mes_actual in meses_disponibles else meses_disponibles[0]
    mes_seleccionado = st.selectbox("📆 Selecciona el mes a revisar:", sorted(meses_disponibles), index=sorted(meses_disponibles).index(mes_default))

    # Filtrar por mes actual
    filtro_mes = personas_df[personas_df["Mes"] == mes_seleccionado]

    # Agrupar por persona y sumar PMZ
    resumen = filtro_mes.groupby("Persona").agg({"PMZ": "sum"}).reset_index()
    resumen = resumen.sort_values("PMZ", ascending=True)

    st.markdown(f"### 👥 Personas con menor PMZ en **{mes_seleccionado}**")
    for i, row in resumen.iterrows():
        persona = row["Persona"]
        pmz = row["PMZ"]
        st.markdown(f"**{persona}** — PMZ: {pmz}")
        comentario = st.text_input(f"✏️ Comentario / acción para {persona}", key=f"coment_{persona}")
        st.markdown("---")
else:
    st.info("Por favor sube un archivo para comenzar.")