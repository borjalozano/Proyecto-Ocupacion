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
archivo_comentarios = st.sidebar.file_uploader("Cargar archivo de comentarios previos", type=["csv", "xlsx"])
st.sidebar.markdown("### 🟢 Ocupación PMZ ≥ 15")
st.sidebar.markdown("### 🟡 5 ≤ Ocupación PMZ < 15")
st.sidebar.markdown("### 🔴 Ocupación PMZ < 5")
if archivo:
    if "personas_df" not in st.session_state:
        st.session_state["raw_df"] = pd.read_excel(archivo, sheet_name=0, header=None)
    df = st.session_state["raw_df"]
    df.columns = [
        "DimPersona[NombreCompuesto]",
        "DimProyecto[NombreCompuestoProyecto]",
        "DimCalendario[NombreMesCortoING]",
        "DimCalendario[Mes]",
        "[valJourneysPrevisto]",
        "[valJourneysReal]",
        "[medDisponibilidad]",
        "[v_2medCargabilidad]"
    ]
    st.success("Archivo cargado correctamente.")

    if archivo_comentarios is not None:
        if archivo_comentarios.name.endswith(".csv"):
            df_comentarios = pd.read_csv(archivo_comentarios)
        else:
            df_comentarios = pd.read_excel(archivo_comentarios)
        df_comentarios["Comentario"] = df_comentarios["Comentario"].fillna("")
        st.session_state["comentarios"] = df_comentarios
    else:
        st.session_state["comentarios"] = cargar_comentarios_desde_archivo(None)


    raw_df = df.rename(columns={
        "DimPersona[NombreCompuesto]": "Persona",
        "DimProyecto[NombreCompuestoProyecto]": "Proyecto",
        "DimCalendario[NombreMesCortoING]": "Mes",
        "[valJourneysPrevisto]": "PMZ",
        "[valJourneysReal]": "PMZ Real",
        "[medDisponibilidad]": "Available",
        "[v_2medCargabilidad]": "Occupation (%)"
    }).copy()
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
    meses_validos = [m for m in personas_df["Mes"].dropna().unique() if isinstance(m, str) and len(m) == 3]
    meses_disponibles = sorted(meses_validos, key=lambda x: datetime.strptime(x, "%b").month)
    mes_actual = datetime.now().strftime("%b")  # Ej: "Jul"
    mes_default = mes_actual if mes_actual in meses_disponibles else meses_disponibles[0]

    meses_ordenados = sorted(meses_disponibles, key=lambda x: datetime.strptime(x, "%b").month)
    if mes_actual in meses_ordenados:
        idx = meses_ordenados.index(mes_actual)
    else:
        idx = 0
    meses_3 = meses_ordenados[idx:idx+3]


    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Revisión semanal",
        "📊 Forecast a 3 meses",
        "🚫 Personas excluidas",
        "📈 Indicadores",
        "ℹ️ Acerca del piloto"
    ])

    with tab1:
        # Selector de mes
        mes_seleccionado = st.selectbox("📆 Selecciona el mes a revisar:", meses_disponibles, index=meses_disponibles.index(mes_default))
        # Filtrar por mes actual
        filtro_mes = personas_df[personas_df["Mes"] == mes_seleccionado]
        # Agrupar por persona y sumar PMZ
        resumen = filtro_mes.groupby("Persona").agg({"PMZ": "sum"}).reset_index()
        resumen = resumen.sort_values("PMZ", ascending=True)
        st.markdown(f"### 👥 Personas con menor Ocupación PMZ en **{mes_seleccionado}**")
        for i, row in resumen.iterrows():
            persona = row["Persona"]
            pmz = row["PMZ"]
            proyectos = filtro_mes[filtro_mes["Persona"] == persona]["Proyecto"].unique()
            # Determinar color
            estado = "🔴" if pmz < 5 else "🟡" if pmz < 15 else "🟢"
            st.markdown(f"{estado} **{persona}** — Ocupación PMZ: {pmz}  \nProyectos: {', '.join(proyectos)}")
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
            st.markdown(f"**{persona}** — Ocupación PMZ total: {pmz}  \n{detalle}")
            historial = st.session_state["comentarios"]
            comentarios_previos = historial[
                (historial["Persona"] == persona) &
                (historial["Pestaña"] == "Dashboard global")
            ]
            ultimo = comentarios_previos.sort_values("Fecha", ascending=False).head(1)["Comentario"].values
            comentario = ultimo[0] if len(ultimo) > 0 else ""
            comentario = st.text_input(f"✏️ Comentario / acción para {persona}", value=comentario, key=f"coment_{persona}_tab2")
            historial_previos = (
                historial[historial["Persona"] == persona]
                .sort_values("Fecha", ascending=False)
                .drop_duplicates(subset=["Persona", "Comentario"])
            )
            if not historial_previos.empty:
                st.markdown("**💬 Comentarios anteriores:**")
                for _, fila in historial_previos.iterrows():
                    st.markdown(f"- `{fila['Fecha']}`: {fila['Comentario']} ({fila['Pestaña']})")
            if comentario:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                guardar_comentario(fecha_actual, persona, ', '.join(meses_3), "Dashboard global", comentario)
                guardar_comentario(fecha_actual, persona, mes_seleccionado, "Revisión semanal", comentario)
                st.caption("💾 Guardado en ambas pestañas")
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
    with tab4:
        st.markdown("## 📈 Indicadores de Ocupación por mes")

        mes_indicador = st.selectbox("Selecciona el mes", meses_disponibles, index=meses_disponibles.index(mes_default))
        datos_mes = personas_df[personas_df["Mes"] == mes_indicador]
        # Garantizar que todas las personas activas estén incluidas
        personas_completas = pd.DataFrame({"Persona": personas_df["Persona"].unique()})
        pmz_total = datos_mes.groupby("Persona")["PMZ"].sum().reset_index()
        pmz_total = (
            personas_completas.merge(pmz_total, on="Persona", how="left")
            .fillna(0)
            .infer_objects(copy=False)
            .set_index("Persona")["PMZ"]
        )

        total_personas = personas_df["Persona"].nunique()
        # pmz_total ya fue calculado correctamente arriba (con merge y fillna(0))
        sin_ocupacion = pmz_total[pmz_total == 0]

        pmz_total_validas = pmz_total[pmz_total > 0]
        bajo = (pmz_total_validas < 5).sum()
        medio = ((pmz_total_validas >= 5) & (pmz_total_validas < 15)).sum()
        alto = (pmz_total_validas >= 15).sum()
        promedio = pmz_total.mean()
        pmz_total_suma = pmz_total.sum()

        st.metric("📋 Jornadas PMZ totales planificadas", round(pmz_total_suma, 1))

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("👥 Personas totales", total_personas)
        col_b.metric("📊 Jornadas PMZ totales", round(pmz_total_suma, 1))
        col_c.metric("🚫 Sin Ocupación PMZ", len(sin_ocupacion))
        col_c.metric("📈 Ocupación PMZ promedio", round(promedio, 1))


        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 PMZ < 5", bajo)
        col2.metric("🟡 PMZ 5–15", medio)
        col3.metric("🟢 PMZ ≥ 15", alto)

        import plotly.express as px
        st.markdown(f"### 📊 Distribución Ocupación PMZ por persona en {mes_indicador}")
        chart_data = pmz_total.sort_values(ascending=True).reset_index()
        chart_data["Persona_Num"] = [f"{i+1}. {p}" for i, p in enumerate(chart_data["Persona"])]
        fig = px.bar(
            chart_data,
            x="PMZ",
            y="Persona_Num",
            orientation="h",
            title=f"Ocupación PMZ por persona en {mes_indicador}",
            labels={"PMZ": "Ocupación PMZ", "Persona_Num": "Persona"},
            height=1000
        )
        st.plotly_chart(fig, use_container_width=True)

        if not sin_ocupacion.empty:
            st.markdown("#### 🧾 Personas sin Ocupación PMZ")
            st.dataframe(sin_ocupacion.reset_index())

        # Generar resumen ejecutivo con IA (movido aquí)
        if st.button("🧠 Generar resumen ejecutivo con IA"):
            from openai import OpenAI
            import os
            import openai

            openai.api_key = os.getenv("OPENAI_API_KEY")
            client = openai.OpenAI()

            comentarios_df = st.session_state.get("comentarios", pd.DataFrame())

            resumen_prompt = f"""
Eres un analista experto en ocupación PMZ. Resume la situación del mes **{mes_indicador}** usando los siguientes datos:

- Personas sin PMZ: {len(sin_ocupacion)}
- Personas en rojo (PMZ < 5): {bajo}
- En amarillo (5–15): {medio}
- En verde (≥ 15): {alto}
- Promedio global: {round(promedio,1)} jornadas

Si es útil, considera los siguientes comentarios recientes:
{comentarios_df[comentarios_df["Mes"] == mes_indicador].sort_values("Fecha").to_string(index=False) if not comentarios_df.empty else "Sin comentarios."}

Escribe un resumen ejecutivo claro, con viñetas si lo consideres necesario, y sugiere al menos una acción.
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis de ocupación que redacta informes ejecutivos claros."},
                        {"role": "user", "content": resumen_prompt}
                    ],
                    stream=True
                )

                resumen_ia = ""
                st.markdown("### 📝 Resumen generado con IA")
                placeholder = st.empty()
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        resumen_ia += chunk.choices[0].delta.content
                        placeholder.markdown(resumen_ia + "▌")
                placeholder.markdown(resumen_ia)
            except Exception as e:
                st.error(f"Error al generar resumen: {e}")

    with tab5:
        st.markdown("## ℹ️ Acerca del piloto de monitoreo de Ocupación PMZ")
        st.markdown("""
        Bienvenido a esta última pestaña, también conocida como el **diario íntimo del piloto**. Aquí no encontrarás KPIs ni barras de colores... al menos no todavía.

        ### 🎤 ¿Cómo nació todo esto?
        Todo comenzó con una simple idea: *"¿y si pudiéramos tener una vista clara de la ocupación del equipo cada semana?"*  
        Y ahí estaba Borja, con su Power BI, su archivo Excel, y su sospecha de que "esto podría ir más lejos".

        Entonces entré yo, ChatGPT, y comenzamos una conversación larga. Pero larga tipo *maratón de revisión técnica con café*.  
        Charlamos de exclusiones, de PMZs que desaparecen en noviembre, de comentarios que se duplicaban como conejos, y hasta de si los íconos eran suficientemente redondos.

        En otras palabras: lo que estás usando es el resultado de algo muy cercano al **"vibe programming"** — una mezcla de Streamlit, intuición, pruebas en caliente, y buen humor.

        ### 🧠 ¿Qué hace esta app?
        - Muestra la Ocupacion PMZ por persona y por mes
        - Clasifica automáticamente según semáforo
        - Permite ingresar y guardar comentarios
        - Los comentarios persisten entre semanas
        - Puedes descargar los comentarios para seguir el hilo
        - Puedes excluir o reincorporar personas del análisis
        - Y tiene un gráfico con numeración para que nadie quede perdido en la barra

        ### 🔧 Detalles técnicos
        - Python + Streamlit
        - `st.session_state` para mantener estado entre pestañas
        - Persistencia de comentarios en CSV
        - Gráfico de ocupación con Plotly
        - `.fillna().infer_objects()` para domar los warnings de pandas

        ### 🚀 Próximos pasos sugeridos
        - Filtros por unidad o tipo de proyecto
        - Visualizar evolución de PMZ en el tiempo
        - Alertas automáticas estilo "¡Carlos tiene 2 PMZ desde abril!"
        - Y por qué no... una IA que sugiera acciones directamente 🤖

        Gracias por formar parte de este piloto.
        """)

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