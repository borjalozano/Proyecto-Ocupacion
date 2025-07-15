import streamlit as st
import pandas as pd
from datetime import datetime
import re
import os

COMENTARIOS_FILE = "comentarios_sesion.csv"

def cargar_comentarios_desde_archivo(uploaded_file):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    elif os.path.exists(COMENTARIOS_FILE):
        return pd.read_csv(COMENTARIOS_FILE)
    else:
        return pd.DataFrame(columns=["Fecha", "Persona", "Mes", "Pestaña", "Comentario"])

def guardar_comentario(fecha, persona, mes, pestana, comentario):
    historico = st.session_state.get("comentarios", pd.DataFrame(columns=["Fecha", "Persona", "Mes", "Pestaña", "Comentario"]))
    nuevo = pd.DataFrame([{
        "Fecha": fecha,
        "Persona": persona,
        "Mes": mes,
        "Pestaña": pestana,
        "Comentario": comentario
    }])
    st.session_state["comentarios"] = pd.concat([historico, nuevo], ignore_index=True)

st.set_page_config(page_title="Gestor Semanal de Ocupación - Babel", page_icon="📊")
st.image("Logo Babel Horizontal (1).jpg", width=180)
st.title("Gestor Semanal de Ocupación - Babel")

st.sidebar.markdown("## 📥 Subir archivo de Power BI")
archivo = st.sidebar.file_uploader("Cargar archivo Excel exportado desde Power BI (formato resumido)", type=["xlsx"])
st.sidebar.markdown("## 💬 Comentarios sesión anterior")
archivo_comentarios = st.sidebar.file_uploader("Cargar archivo de comentarios previos", type=["csv"])
st.sidebar.markdown("### 🟢 PMZ ≥ 15")
st.sidebar.markdown("### 🟡 5 ≤ PMZ < 15")
st.sidebar.markdown("### 🔴 PMZ < 5")
if archivo:
    if "personas_df" not in st.session_state:
        st.session_state["raw_df"] = pd.read_excel(archivo, sheet_name=0, header=None)
    df = st.session_state["raw_df"]
    st.success("Archivo cargado correctamente.")

    st.session_state["comentarios"] = cargar_comentarios_desde_archivo(archivo_comentarios)

    raw_df = df[df[0].astype(str).str.contains(r"\d{4} \|", regex=True, na=False)].copy()
    raw_df.columns = ["ID_Nombre", "Proyecto", "Mes", "PMZ", "Occupation", "Available", "Occupation (%)"]
    raw_df["Persona"] = raw_df["ID_Nombre"].str.extract(r"\| (.+)")

    # Inicializar estado de exclusión manual
    if "personas_excluidas" not in st.session_state:
        # Aplicar lógica de exclusión automática inicial
        pmz_total = raw_df.groupby("Persona")["PMZ"].sum()
        sin_pmz = pmz_total[pmz_total == 0].index.tolist()
        enfermedad = raw_df["Proyecto"].str.upper().str.contains("ENFERMEDAD", na=False)
        desocupacion = raw_df["Proyecto"].str.upper().str.contains("DESOCUPACIÓN", na=False)
        excluidas = raw_df[raw_df["Persona"].isin(sin_pmz) & ~enfermedad & ~desocupacion]["Persona"].unique().tolist()
        st.session_state["personas_excluidas"] = excluidas

    # Construir personas_df y excluidos_df en base al estado
    personas_df = raw_df[~raw_df["Persona"].isin(st.session_state["personas_excluidas"])].copy()
    excluidos_df = raw_df[raw_df["Persona"].isin(st.session_state["personas_excluidas"])].copy()

    # Obtener meses disponibles y preparar para ambos tabs
    meses_disponibles = sorted(personas_df["Mes"].dropna().unique().tolist(), key=lambda x: datetime.strptime(x, "%b").month)
    mes_actual = datetime.now().strftime("%b")  # Ej: "Jul"
    mes_default = mes_actual if mes_actual in meses_disponibles else meses_disponibles[0]

    meses_ordenados = sorted(meses_disponibles, key=lambda x: datetime.strptime(x, "%b").month)
    if mes_actual in meses_ordenados:
        idx = meses_ordenados.index(mes_actual)
    else:
        idx = 0
    meses_3 = meses_ordenados[idx:idx+3]

    tab1, tab2, tab3 = st.tabs(["📥 Revisión semanal", "📊 Dashboard global", "🚫 Personas excluidas"])

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
            # Determinar color
            estado = "🔴" if pmz < 5 else "🟡" if pmz < 15 else "🟢"
            st.markdown(f"{estado} **{persona}** — PMZ: {pmz}  \nProyectos: {', '.join(proyectos)}")
            historial = st.session_state["comentarios"]
            comentarios_previos = historial[historial["Persona"] == persona]
            comentario_reciente = comentarios_previos.sort_values("Fecha", ascending=False).head(1)["Comentario"].values
            if len(comentario_reciente) > 0:
                st.markdown("**💬 Último comentario:**")
                st.markdown(f"- {comentario_reciente[0]}")
            comentario = st.text_input(f"✏️ Comentario / acción para {persona}", key=f"coment_{persona}_tab1")
            if comentario:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                guardar_comentario(fecha_actual, persona, mes_seleccionado, "Revisión semanal", comentario)
                guardar_comentario(fecha_actual, persona, ", ".join(meses_3), "Dashboard global", comentario)
                st.caption("💾 Guardado en ambas pestañas")
            if st.button(f"❌ Excluir a {persona}", key=f"excluir_{persona}"):
                st.session_state["personas_excluidas"].append(persona)
                st.rerun()
            st.markdown("---")

    with tab2:
        # Leyenda de colores de semáforo
        # st.markdown("#### 🟢 PMZ ≥ 15 &nbsp;&nbsp;&nbsp; 🟡 5 ≤ PMZ < 15 &nbsp;&nbsp;&nbsp; 🔴 PMZ < 5")
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
            def color_pmz(valor):
                return "🔴" if valor < 5 else "🟡" if valor < 15 else "🟢"
            detalle = ', '.join([f"{mes}: {row[mes]} {color_pmz(row[mes])}" for mes in meses_3 if mes in row])
            st.markdown(f"**{persona}** — PMZ total: {pmz}  \n{detalle}")
            historial = st.session_state["comentarios"]
            comentarios_previos = historial[
                (historial["Persona"] == persona) &
                (historial["Pestaña"] == "Dashboard global")
            ]
            if not comentarios_previos.empty:
                st.markdown("**💬 Comentarios previos:**")
                for _, fila in comentarios_previos.iterrows():
                    st.markdown(f"- `{fila['Fecha']}`: {fila['Comentario']}")
            st.caption("✏️ Comentarios editables solo en la pestaña 1.")
            st.markdown("---")
    with tab3:
        st.markdown("### 🚫 Personas excluidas del análisis")
        if excluidos_df.empty:
            st.info("No se detectaron personas excluidas.")
        else:
            excluidos_resumen = excluidos_df[["Persona", "Proyecto", "Mes", "PMZ"]].drop_duplicates()
            personas_reincorporadas = []

            for persona in excluidos_resumen["Persona"].unique():
                st.markdown(f"**{persona}**")
                persona_df = excluidos_resumen[excluidos_resumen["Persona"] == persona]
                st.dataframe(persona_df[["Proyecto", "Mes", "PMZ"]])
                if st.button(f"Incluir nuevamente a {persona}"):
                    personas_reincorporadas.append(persona)

            if personas_reincorporadas:
                reincorporar_df = excluidos_df[excluidos_df["Persona"].isin(personas_reincorporadas)]
                excluidos_df = excluidos_df[~excluidos_df["Persona"].isin(personas_reincorporadas)]
                for persona in personas_reincorporadas:
                    if persona in st.session_state["personas_excluidas"]:
                        st.session_state["personas_excluidas"].remove(persona)
                st.rerun()
else:
    st.info("Por favor sube un archivo para comenzar.")

import io
from datetime import date

historico = st.session_state.get("comentarios", pd.DataFrame())
buffer = io.StringIO()
historico.to_csv(buffer, index=False)
csv_data = buffer.getvalue()
filename = f"comentarios_{date.today()}.csv"
st.sidebar.download_button(
    label="⬇️ Descargar comentarios de la sesión",
    data=csv_data,
    file_name=filename,
    mime="text/csv"
)