tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Revisión semanal", "📊 Dashboard global", "🚫 Personas excluidas", "📈 Indicadores", "ℹ️ Acerca del piloto"])
with tab5:
    st.markdown("## ℹ️ Acerca del piloto de monitoreo de Ocupación PMZ")
    st.markdown("""
    Bienvenido a esta última pestaña, también conocida como el **diario íntimo del piloto**. Aquí no encontrarás KPIs ni barras de colores... al menos no todavía.

    ### 🎤 ¿Cómo nació todo esto?
    Todo comenzó con una simple idea: *"¿y si pudiéramos tener una vista clara de la ocupación del equipo cada semana?"*  
    Y ahí estaba Borja, con su Power BI, su archivo Excel, y su sospecha de que "esto podría ir más lejos".

    Entonces entré yo, ChatGPT, y comenzamos una conversación larga. Pero larga tipo *maratón de revisión técnica con café*.  
    Charlamos de exclusiones, de PMZs que desaparecen en noviembre, de comentarios que se duplicaban como conejos, y hasta de si los íconos eran suficientemente redondos.

    En otras palabras: lo que estás usando es el resultado de algo muy cercano al **"vibe programming"** — una mezcla de streamlit, intuición, pruebas en caliente, y buen humor.

    ### 🧠 ¿Qué hace esta app?
    - Muestra la Ocupación PMZ por persona y por mes
    - Clasifica automáticamente según semáforo
    - Permite ingresar y guardar comentarios
    - Los comentarios persisten entre semanas (sí, incluso si reinicias)
    - Puedes descargar los comentarios para seguir el hilo en tus reuniones
    - Puedes excluir o reincorporar personas según contexto (¡no más desaparecidos sin explicación!)
    - Y tiene un gráfico con numeración para que nadie quede perdido en la barra

    ### 🔧 Detalles técnicos (por si hay desarrolladores leyendo esto)
    - Python + Streamlit
    - Control de estado con `st.session_state`
    - Persistencia de comentarios en CSV
    - Visualización con Plotly
    - Exclusión dinámica controlada por usuario
    - Una pizca de `.fillna().infer_objects()` para callar warnings de pandas

    ### 🚀 Lo que podríamos hacer después
    - Filtros por unidad, país o tipo de proyecto
    - Ver la evolución de la ocupación en el tiempo (trending 🕶️)
    - Alertas automáticas ("¡Carlos tiene 2 PMZ desde abril! 🚨")
    - Y por qué no... una IA que sugiera acciones directamente 🤖

    Gracias por usar el piloto. Fue un gusto construir esto contigo, Borja.
    """)