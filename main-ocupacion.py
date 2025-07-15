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

    # Obtener meses disponibles y preparar para ambos tabs
    meses_disponibles = sorted(personas_df["Mes"].dropna().unique().tolist())
    mes_actual = datetime.now().strftime("%b")  # Ej: "Jul"
    mes_default = mes_actual if mes_actual in meses_disponibles else meses_disponibles[0]

    tab1, tab2 = st.tabs(["📥 Revisión semanal", "📊 Dashboard global"])

    with tab1:
        # Selector de mes
        mes_seleccionado = st.selectbox("📆 Selecciona el mes a revisar:", meses_disponibles, index=meses_disponibles.index(mes_default))
        # Filtrar por mes actual
        filtro_mes = personas_df[personas_df["Mes"] == mes_seleccionado]
        # Agrupar por persona y sumar PMZ
        resumen = filtro_mes.groupby("Persona").agg({"PMZ": "sum"}).reset_index()
        resumen = resumen.sort_values("PMZ", ascending=True)
        st.markdown(f"### 👥 Personas con menor PMZ en **{mes_seleccionado}**")
        for i, row in resumen.iterrows():
            persona = row["Persona"]
            pmz = row["PMZ"]
            proyectos = filtro_mes[filtro_mes["Persona"] == persona]["Proyecto"].unique()
            st.markdown(f"**{persona}** — PMZ: {pmz}  \nProyectos: {', '.join(proyectos)}")
            comentario = st.text_input(f"✏️ Comentario / acción para {persona}", key=f"coment_{persona}_tab1")
            st.markdown("---")

    with tab2:
        # Leyenda de colores de semáforo
        st.markdown("#### 🟢 PMZ ≥ 15 &nbsp;&nbsp;&nbsp; 🟡 5 ≤ PMZ < 15 &nbsp;&nbsp;&nbsp; 🔴 PMZ < 5")
        # Obtener los 3 próximos meses (mes actual + 2 siguientes)
        meses_ordenados = sorted(meses_disponibles, key=lambda x: datetime.strptime(x, "%b").month)
        if mes_actual in meses_ordenados:
            idx = meses_ordenados.index(mes_actual)
        else:
            idx = 0
        meses_3 = meses_ordenados[idx:idx+3]
        st.markdown(f"#### Ocupación PMZ acumulada por persona para los próximos 3 meses: {', '.join(meses_3)}")
        filtro_3m = personas_df[personas_df["Mes"].isin(meses_3)]
        resumen_3m = filtro_3m.groupby("Persona").agg({"PMZ": "sum"}).reset_index()
        detalle_ocupacion = filtro_3m.pivot_table(index="Persona", columns="Mes", values="PMZ", aggfunc="sum").fillna(0)
        resumen_3m = resumen_3m.merge(detalle_ocupacion, on="Persona", how="left")
        # Semaforización
        def estado_pmz(total_pmz):
            if total_pmz < 5:
                return "🔴"
            elif total_pmz < 15:
                return "🟡"
            else:
                return "🟢"
        resumen_3m["Estado"] = resumen_3m["PMZ"].apply(estado_pmz)
        resumen_3m = resumen_3m.sort_values("PMZ", ascending=True)
        # Mostrar tabla y permitir comentarios editables
        for i, row in resumen_3m.iterrows():
            persona = row["Persona"]
            pmz = row["PMZ"]
            estado = row["Estado"]
            detalle = ', '.join([f"{mes}: {row[mes]}" for mes in meses_3 if mes in row])
            st.markdown(f"**{persona}** — PMZ total: {pmz} {estado}  \n{detalle}")
            comentario = st.text_input(f"✏️ Comentario / acción para {persona}", key=f"coment_{persona}_tab2")
            st.markdown("---")
else:
    st.info("Por favor sube un archivo para comenzar.")