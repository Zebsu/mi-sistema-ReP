import streamlit as st
from datetime import date, datetime, timedelta
import calendar
import json
import os
import uuid
import pandas as pd 

# ==========================================
# CONFIGURACIÓN INICIAL Y PERSISTENCIA
# ==========================================
DATA_FILE = "agenda_v4.json"
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                pass
    return {
        "practicas": [],
        "lineas": [],
        "roles": [],
        "points_log": {},
        "completed_log": {}
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# Configuración de página
st.set_page_config(page_title="Sistema de Productividad Élite", page_icon="⚡", layout="wide")

# ==========================================
# ESTILOS CSS (INCLUYE OPTIMIZACIÓN MÓVIL)
# ==========================================
st.markdown("""
    <style>
    /* Estilo de los contenedores de prácticas */
    div[data-testid="stContainer"] {
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        background: #16181c;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        padding: 10px 15px;
        margin-bottom: 12px;
    }
    div[data-testid="stContainer"]:hover {
        border-color: #00ff9d !important;
    }
    
    /* Forzar que las columnas de las prácticas NO se apilen en móviles */
    @media (max-width: 768px) {
        div[data-testid="stContainer"] div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
        }
        div[data-testid="stContainer"] div[data-testid="column"]:nth-child(1) {
            width: 70% !important;
            flex: 1 1 70% !important;
            min-width: 70% !important;
        }
        div[data-testid="stContainer"] div[data-testid="column"]:nth-child(2) {
            width: 30% !important;
            flex: 1 1 30% !important;
            min-width: 30% !important;
            margin-top: 0 !important;
        }
    }

    /* Métricas */
    div[data-testid="stMetricValue"] {
        color: #00ff9d !important;
        font-weight: 800 !important;
    }
    
    /* Botón Llamativo (Primary) */
    button[kind="primary"] {
        background-color: #00ff9d !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: 900 !important;
        box-shadow: 0 0 10px rgba(0, 255, 157, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
        padding: 0.5rem !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.8) !important;
        transform: scale(1.03) !important;
    }
    
    /* Elementos de Roles */
    .role-header {
        color: #00ff9d;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .objective-box {
        background-color: #1e222b;
        border-left: 4px solid #00ff9d;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    
    /* Banner Superior de Racha */
    .streak-banner {
        background: linear-gradient(90deg, #ff4b4b, #ff8f00);
        padding: 15px 30px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(255, 75, 75, 0.2);
    }
    .streak-banner-title {
        color: white;
        font-size: 22px;
        font-weight: bold;
        margin: 0;
    }
    .streak-banner-number {
        color: white;
        font-size: 28px;
        font-weight: 900;
        margin: 0;
    }
    @media (max-width: 768px) {
        .streak-banner {
            padding: 15px;
        }
        .streak-banner-title { font-size: 18px; }
        .streak-banner-number { font-size: 22px; }
    }
    
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar datos en la sesión
if 'data' not in st.session_state:
    st.session_state.data = cargar_datos()

hoy = date.today()
str_hoy = hoy.isoformat()

if str_hoy not in st.session_state.data["points_log"]:
    st.session_state.data["points_log"][str_hoy] = 0
if str_hoy not in st.session_state.data["completed_log"]:
    st.session_state.data["completed_log"][str_hoy] = []

# ==========================================
# CÁLCULOS DE PUNTOS Y RACHA (STREAK)
# ==========================================
puntos_hoy = st.session_state.data["points_log"].get(str_hoy, 0)

inicio_semana = hoy - timedelta(days=hoy.weekday())
puntos_semana = sum(
    st.session_state.data["points_log"].get((inicio_semana + timedelta(days=i)).isoformat(), 0)
    for i in range(7)
)

puntos_mes = sum(
    puntos for fecha, puntos in st.session_state.data["points_log"].items()
    if fecha.startswith(hoy.strftime("%Y-%m"))
)

racha_actual = 0
fecha_eval = hoy

if st.session_state.data["points_log"].get(fecha_eval.isoformat(), 0) == 0:
    fecha_eval -= timedelta(days=1)

while st.session_state.data["points_log"].get(fecha_eval.isoformat(), 0) > 0:
    racha_actual += 1
    fecha_eval -= timedelta(days=1)

# ==========================================
# PANEL LATERAL DESPLEGABLE (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("⚙️ Panel de Control")
    tab_prac, tab_lineas, tab_edicion = st.tabs(["+ Práctica", "+ Línea", "✏️ Modificar"])
    
    with tab_prac:
        if not st.session_state.data["lineas"]:
            st.info("Crea una Línea de acción en la pestaña '+ Línea'.")
        else:
            p_nombre = st.text_input("Nombre de la Práctica", key="add_p_nombre")
            p_linea = st.selectbox("Asignar a Línea", [l["name"] for l in st.session_state.data["lineas"]], key="add_p_linea")
            p_hora = st.time_input("Hora sugerida", key="add_p_hora")
            p_freq = st.radio("Frecuencia", ["Todos los días", "Días específicos"], key="add_p_freq")
            
            if p_freq == "Días específicos":
                p_dias = st.multiselect("Selecciona los días", DIAS_SEMANA, key="add_p_dias")
            else:
                p_dias = DIAS_SEMANA
                
            p_desc = st.text_area("Descripción de ejecución", key="add_p_desc")
            
            if st.button("Guardar Práctica", use_container_width=True):
                if p_nombre and len(p_dias) > 0:
                    nueva_practica = {
                        "id": str(uuid.uuid4()),
                        "name": p_nombre,
                        "linea": p_linea,
                        "time": p_hora.strftime("%H:%M"),
                        "days": p_dias,
                        "desc": p_desc
                    }
                    st.session_state.data["practicas"].append(nueva_practica)
                    guardar_datos(st.session_state.data)
                    
                    del st.session_state["add_p_nombre"]
                    del st.session_state["add_p_desc"]
                    if "add_p_dias" in st.session_state:
                        del st.session_state["add_p_dias"]
                    st.rerun()
                else:
                    st.error("Llena el nombre y selecciona los días.")

    with tab_lineas:
        l_nombre = st.text_input("Nombre de la Nueva Línea", placeholder="Ej. Desarrollo Técnico", key="add_l_nombre")
        if st.button("Crear Línea", use_container_width=True):
            if l_nombre:
                if not any(l["name"].lower() == l_nombre.lower() for l in st.session_state.data["lineas"]):
                    st.session_state.data["lineas"].append({"id": str(uuid.uuid4()), "name": l_nombre})
                    guardar_datos(st.session_state.data)
                    del st.session_state["add_l_nombre"]
                    st.rerun()
                else:
                    st.warning("Esa línea ya existe.")

    with tab_edicion:
        st.markdown("**Editar o Eliminar Prácticas**")
        if not st.session_state.data["practicas"]:
            st.caption("No hay prácticas registradas.")
        else:
            for i, p in enumerate(st.session_state.data["practicas"]):
                with st.expander(f"✏️ {p['name']}"):
                    e_nombre = st.text_input("Nombre", value=p['name'], key=f"e_nom_{p['id']}")
                    
                    nombres_lineas = [l["name"] for l in st.session_state.data["lineas"]]
                    idx_linea = nombres_lineas.index(p['linea']) if p['linea'] in nombres_lineas else 0
                    e_linea = st.selectbox("Línea", nombres_lineas, index=idx_linea, key=f"e_lin_{p['id']}")
                    
                    e_hora = st.time_input("Hora", value=datetime.strptime(p['time'], "%H:%M").time(), key=f"e_hor_{p['id']}")
                    e_dias = st.multiselect("Días", DIAS_SEMANA, default=p.get('days', DIAS_SEMANA), key=f"e_dia_{p['id']}")
                    e_desc = st.text_area("Descripción", value=p['desc'], key=f"e_des_{p['id']}")
                    
                    col_btn_guardar, col_btn_borrar = st.columns(2)
                    with col_btn_guardar:
                        if st.button("Guardar", key=f"e_save_{p['id']}", use_container_width=True):
                            st.session_state.data["practicas"][i].update({
                                "name": e_nombre,
                                "linea": e_linea,
                                "time": e_hora.strftime("%H:%M"),
                                "days": e_dias,
                                "desc": e_desc
                            })
                            guardar_datos(st.session_state.data)
                            st.rerun()
                    with col_btn_borrar:
                        if st.button("Eliminar", type="primary", key=f"e_del_{p['id']}", use_container_width=True):
                            st.session_state.data["practicas"].pop(i)
                            guardar_datos(st.session_state.data)
                            st.rerun()

        st.divider()
        st.markdown("**Eliminar Líneas**")
        if not st.session_state.data["lineas"]:
            st.caption("No hay líneas registradas.")
        for i, l in enumerate(st.session_state.data["lineas"]):
            cols_l = st.columns([3, 1])
            cols_l[0].caption(l["name"])
            if cols_l[1].button("🗑️", key=f"del_l_{l['id']}"):
                st.session_state.data["lineas"].pop(i)
                guardar_datos(st.session_state.data)
                st.rerun()

# ==========================================
# LAYOUT PRINCIPAL (BANNER, AGENDA Y MÉTRICAS)
# ==========================================
st.title("⚡ Sistema de Gestión del Rendimiento")

# Banner de Racha movido a la parte superior
st.markdown(f"""
    <div class="streak-banner">
        <p class="streak-banner-title">🔥 Racha Élite Actual</p>
        <p class="streak-banner-number">{racha_actual} días</p>
    </div>
""", unsafe_allow_html=True)

# División Principal
col_principal, col_der = st.columns([3, 1.2])

with col_principal:
    vista = st.radio(
        "Cambiar Vista:", 
        ["📍 Agenda Diaria", "📅 Calendario", "🎭 Roles", "📈 Tendencias"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    st.write("") 
    
    # === VISTA: AGENDA DIARIA ===
    if vista == "📍 Agenda Diaria":
        st.subheader(f"Prácticas para hoy ({DIAS_SEMANA[hoy.weekday()]})")
        
        nombre_dia_hoy = DIAS_SEMANA[hoy.weekday()]
        practicas_hoy = [p for p in st.session_state.data["practicas"] if nombre_dia_hoy in p["days"]]
        practicas_ordenadas = sorted(practicas_hoy, key=lambda x: x["time"])
        
        if not practicas_ordenadas:
            st.info("No hay prácticas agendadas para el día de hoy.")
        else:
            lineas_presentes = sorted(list(set([p['linea'] for p in practicas_ordenadas])))
            
            for linea in lineas_presentes:
                st.markdown(f"<h3 style='color: #00ff9d; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 20px; font-size: 20px;'>📂 {linea}</h3>", unsafe_allow_html=True)
                
                practicas_linea = [p for p in practicas_ordenadas if p['linea'] == linea]
                
                for p in practicas_linea:
                    ya_completado = p["id"] in st.session_state.data["completed_log"][str_hoy]
                    
                    with st.container():
                        c_info, c_accion = st.columns([3.5, 1.5])
                        
                        with c_info:
                            if p['desc']:
                                with st.expander(f"🕒 {p['time']} | **{p['name']}**"):
                                    st.write(p['desc'])
                            else:
                                st.markdown(f"**🕒 {p['time']} | {p['name']}**")
                        
                        with c_accion:
                            if not ya_completado:
                                # Botón con texto optimizado para móvil
                                if st.button("🔥 +10 Pts", key=f"do_{p['id']}", type="primary", use_container_width=True):
                                    st.session_state.data["completed_log"][str_hoy].append(p["id"])
                                    st.session_state.data["points_log"][str_hoy] += 10
                                    guardar_datos(st.session_state.data)
                                    st.rerun()
                            else:
                                st.button("✅ Listo", key=f"done_{p['id']}", disabled=True, use_container_width=True)

    # === VISTA: CALENDARIO ===
    elif vista == "📅 Calendario":
        st.subheader(f"Desempeño Mensual - {hoy.strftime('%B %Y').capitalize()}")
        cal = calendar.monthcalendar(hoy.year, hoy.month)
        
        cols = st.columns(7)
        for i, dia in enumerate(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]):
            cols[i].markdown(f"**{dia}**")
            
        for semana in cal:
            cols = st.columns(7)
            for i, dia in enumerate(semana):
                if dia != 0:
                    fecha_str = f"{hoy.year}-{hoy.month:02d}-{dia:02d}"
                    puntos_dia = st.session_state.data["points_log"].get(fecha_str, 0)
                    
                    bg_color = "#262730" if fecha_str == str_hoy else "transparent"
                    borde = "1px solid #00ff9d" if puntos_dia > 0 else "1px solid #333"
                    
                    with cols[i]:
                        st.markdown(f"""
                        <div style="border: {borde}; background-color: {bg_color}; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                            <div style="font-size: 16px; font-weight: bold;">{dia}</div>
                            <div style="color: #00ff9d; font-size: 11px; margin-top: 5px;">+{puntos_dia} pts</div>
                        </div>
                        """, unsafe_allow_html=True)

    # === VISTA: TENDENCIAS ===
    elif vista == "📈 Tendencias":
        st.subheader("📈 Rendimiento de los últimos 14 días")
        
        fechas_14_dias = [hoy - timedelta(days=i) for i in range(13, -1, -1)]
        etiquetas_fechas = [d.strftime("%d %b") for d in fechas_14_dias]
        puntos_historial = [st.session_state.data["points_log"].get(d.isoformat(), 0) for d in fechas_14_dias]
        
        df_tendencias = pd.DataFrame(
            {"Puntos Diarios": puntos_historial}, 
            index=etiquetas_fechas
        )
        
        st.area_chart(df_tendencias, color="#00ff9d")
        st.info("💡 Este gráfico muestra tu constancia. Mantén la línea elevada para no perder tu racha de fuego.")

    # === VISTA: ROLES ===
    else:
        st.subheader("🎭 Mapeo Estratégico de Roles")
        
        cols_r = st.columns([3, 1])
        nuevo_rol_nombre = cols_r[0].text_input("Nombre del nuevo Rol", placeholder="Ej. Líder Técnico", key="add_role_input")
        if cols_r[1].button("Añadir Rol", use_container_width=True):
            if nuevo_rol_nombre:
                st.session_state.data["roles"].append({
                    "id": str(uuid.uuid4()),
                    "name": nuevo_rol_nombre,
                    "objective": "",
                    "histeric_list": []
                })
                guardar_datos(st.session_state.data)
                st.rerun()

        st.write("")
        
        if not st.session_state.data["roles"]:
            st.info("Aún no has definido ningún rol.")
        else:
            rol_seleccionado_nombre = st.selectbox("Selecciona el Rol para planificar:", [r["name"] for r in st.session_state.data["roles"]])
            
            idx_rol = next(i for i, r in enumerate(st.session_state.data["roles"]) if r["name"] == rol_seleccionado_nombre)
            rol = st.session_state.data["roles"][idx_rol]
            
            with st.container():
                st.markdown(f"<div class='role-header'>Rol: {rol['name']}</div>", unsafe_allow_html=True)
                
                st.markdown("#### 🎯 Objetivo")
                if not rol["objective"]:
                    obj_input = st.text_input("Define el objetivo estratégico:", key=f"obj_in_{rol['id']}")
                    if st.button("Fijar Objetivo", key=f"btn_obj_{rol['id']}"):
                        st.session_state.data["roles"][idx_rol]["objective"] = obj_input
                        guardar_datos(st.session_state.data)
                        st.rerun()
                else:
                    st.markdown(f"<div class='objective-box'>{rol['objective']}</div>", unsafe_allow_html=True)
                    if st.button("Modificar Objetivo", key=f"edit_obj_{rol['id']}"):
                        st.session_state.data["roles"][idx_rol]["objective"] = ""
                        guardar_datos(st.session_state.data)
                        st.rerun()
                
                st.divider()
                st.markdown("#### 📑 Lista Histérica")
                
                cols_h = st.columns([4, 1])
                nuevo_item = cols_h[0].text_input("Añadir pendiente:", key=f"new_h_{rol['id']}")
                if cols_h[1].button("Añadir", key=f"btn_h_{rol['id']}", use_container_width=True):
                    if nuevo_item:
                        st.session_state.data["roles"][idx_rol]["histeric_list"].append({
                            "id": str(uuid.uuid4()),
                            "text": nuevo_item
                        })
                        guardar_datos(st.session_state.data)
                        st.rerun()
                
                if not rol["histeric_list"]:
                    st.caption("_La lista histérica está limpia._")
                else:
                    for idx_item, item in enumerate(rol["histeric_list"]):
                        col_it_text, col_it_del = st.columns([5, 1])
                        col_it_text.markdown(f"- {item['text']}")
                        if col_it_del.button("❌", key=f"del_item_{item['id']}"):
                            st.session_state.data["roles"][idx_rol]["histeric_list"].pop(idx_item)
                            guardar_datos(st.session_state.data)
                            st.rerun()
                
                st.write("")
                if st.button("Eliminar este Rol Completo", type="primary", key=f"del_full_role_{rol['id']}"):
                    st.session_state.data["roles"].pop(idx_rol)
                    guardar_datos(st.session_state.data)
                    st.rerun()

# ------------------------------------------
# PANEL DERECHO: MÉTRICAS DE PUNTOS
# ------------------------------------------
with col_der:
    # La racha se eliminó de aquí y ahora está arriba
    st.subheader("🏆 Resumen Élite")
    
    st.metric(label="Puntos Hoy", value=puntos_hoy)
    st.metric(label="Puntos Semanales", value=puntos_semana)
    st.metric(label="Puntos Mensuales", value=puntos_mes)
    
    st.divider()
    st.markdown("**Cumplimiento Diario**")
    
    nombre_dia_hoy = DIAS_SEMANA[hoy.weekday()]
    total_hoy = len([p for p in st.session_state.data["practicas"] if nombre_dia_hoy in p["days"]])
    hechos_hoy = len(st.session_state.data["completed_log"][str_hoy])
    
    if total_hoy > 0:
        st.progress(hechos_hoy / total_hoy)
        st.caption(f"Ejecutadas: {hechos_hoy} / {total_hoy} prácticas")
    else:
        st.caption("Sin prácticas programadas para hoy.")