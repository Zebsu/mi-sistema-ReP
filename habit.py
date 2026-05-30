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
DATA_FILE = "agenda_v5.json"
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                datos = json.load(f)
                datos.setdefault("on_time_log", {})
                datos.setdefault("shield_log", {})
                datos.setdefault("shields", 0)
                datos.setdefault("coins", 0)
                datos.setdefault("journal_log", {}) 
                datos.setdefault("monthly_review_log", {}) 
                for p in datos.setdefault("practicas", []):
                    p.setdefault("type", "swipe") 
                return datos
            except:
                pass
    return {
        "practicas": [], "lineas": [], "roles": [],
        "points_log": {}, "completed_log": {}, "on_time_log": {},
        "shield_log": {}, "shields": 0, "coins": 0,
        "journal_log": {}, "monthly_review_log": {}
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def toggle_histeric_item(r_idx, i_idx):
    """Callback para tachar/destachar elementos de la lista histérica"""
    current = st.session_state.data["roles"][r_idx]["histeric_list"][i_idx].get("done", False)
    st.session_state.data["roles"][r_idx]["histeric_list"][i_idx]["done"] = not current
    guardar_datos(st.session_state.data)

st.set_page_config(page_title="SENTIR Y CRECER", page_icon="⚡", layout="wide")

# ==========================================
# ESTILOS CSS (OPTMIZADOS PARA MÓVIL Y CALENDARIO)
# ==========================================
st.markdown("""
    <style>
    div[data-testid="stContainer"] {
        border: 1px solid #333 !important; border-radius: 12px !important;
        background: #16181c; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        padding: 10px 15px; margin-bottom: 12px;
    }
    div[data-testid="stContainer"]:hover { border-color: #00ff9d !important; }
    
    div[data-testid="stMetricValue"] { color: #00ff9d !important; font-weight: 800 !important; }
    
    button[kind="primary"] {
        background-color: #00ff9d !important; color: #0e1117 !important;
        border: none !important; font-weight: 900 !important;
        box-shadow: 0 0 10px rgba(0, 255, 157, 0.4) !important; transition: all 0.2s;
    }
    button[kind="primary"]:hover { box-shadow: 0 0 20px rgba(0, 255, 157, 0.8) !important; transform: scale(1.02) !important; }
    
    .streak-banner {
        background: linear-gradient(90deg, #ff4b4b, #ff8f00); padding: 15px 30px;
        border-radius: 12px; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(255, 75, 75, 0.2);
    }
    .streak-banner-title { color: white; font-size: 22px; font-weight: bold; margin: 0; }
    .streak-banner-number { color: white; font-size: 28px; font-weight: 900; margin: 0; }
    
    .level-banner {
        background: linear-gradient(90deg, #2c3e50, #000000); border: 1px solid #00ff9d;
        padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: center;
    }
    
    .quote-box {
        text-align: center; font-style: italic; color: #a0aec0;
        font-size: 18px; margin-bottom: 20px; letter-spacing: 0.5px;
    }
    .coach-box {
        background-color: #1e222b; border-left: 4px solid #8a2be2;
        padding: 15px; border-radius: 4px; margin-top: 15px;
    }
    
    /* CSS Mágico para forzar el Grid del Calendario en Móviles */
    @media (max-width: 768px) {
        div[data-testid="stContainer"] div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; }
        .streak-banner { padding: 15px; }
        .streak-banner-title { font-size: 18px; }
        .streak-banner-number { font-size: 22px; }
        .quote-box { font-size: 15px; }
        
        /* Regla exclusiva para las filas del calendario */
        #calendar-start ~ div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            overflow-x: hidden !important;
        }
        #calendar-start ~ div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 0 0 14.28% !important;
            min-width: 14.28% !important;
            padding: 0 2px !important;
        }
        #calendar-start ~ div[data-testid="stHorizontalBlock"] button {
            padding: 5px 0px !important;
            font-size: 12px !important;
        }
        #calendar-start ~ div[data-testid="stHorizontalBlock"] p {
            font-size: 12px !important;
            text-align: center !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = cargar_datos()

hoy = date.today()
str_hoy = hoy.isoformat()

st.session_state.data["points_log"].setdefault(str_hoy, 0)
st.session_state.data["completed_log"].setdefault(str_hoy, [])
st.session_state.data["on_time_log"].setdefault(str_hoy, False)
st.session_state.data["shield_log"].setdefault(str_hoy, False)

# ==========================================
# CÁLCULOS: PUNTOS, RACHA, NIVELES Y MONEDAS
# ==========================================
puntos_hoy = st.session_state.data["points_log"][str_hoy]
inicio_semana = hoy - timedelta(days=hoy.weekday())
puntos_semana = sum(st.session_state.data["points_log"].get((inicio_semana + timedelta(days=i)).isoformat(), 0) for i in range(7))
puntos_mes = sum(p for f, p in st.session_state.data["points_log"].items() if f.startswith(hoy.strftime("%Y-%m")))

total_xp = sum(st.session_state.data["points_log"].values())
nivel_actual = (total_xp // 100) + 1
xp_para_siguiente = 100 - (total_xp % 100)
porcentaje_xp = (total_xp % 100) / 100.0

titulos_niveles = ["Iniciado", "Aprendiz", "Constante", "Disciplinado", "Táctico", "Élite", "Maestro", "Leyenda", "Imparable", "Dios del Rendimiento"]
titulo_actual = titulos_niveles[min(nivel_actual - 1, len(titulos_niveles) - 1)]

racha_actual = 0
fecha_eval = hoy

if not st.session_state.data["on_time_log"].get(fecha_eval.isoformat(), False) and not st.session_state.data["shield_log"].get(fecha_eval.isoformat(), False):
    fecha_eval -= timedelta(days=1)

while st.session_state.data["on_time_log"].get(fecha_eval.isoformat(), False) or st.session_state.data["shield_log"].get(fecha_eval.isoformat(), False):
    racha_actual += 1
    fecha_eval -= timedelta(days=1)

frases = [
    "La disciplina es la infraestructura más crítica que construyes cada día.",
    "El esfuerzo de hoy es el peso que levantarás con facilidad mañana.",
    "Automatiza tus hábitos igual que automatizas tus procesos.",
    "Cada rutina completada es un bloque más en la arquitectura de tu vida.",
    "El éxito requiere la misma redundancia y seguridad que una red de misión crítica.",
    "Visualiza tu meta, optimiza tu ejecución, domina el día."
]
frase_del_dia = frases[sum(ord(c) for c in str_hoy) % len(frases)]

# ==========================================
# PANEL LATERAL (SIDEBAR, EDICIÓN Y TIENDA)
# ==========================================
with st.sidebar:
    st.header("⚙️ Panel de Control")
    tab_prac, tab_lineas, tab_edicion, tab_tienda = st.tabs(["+ Práctica", "+ Línea", "✏️ Modificar", "🛡️ Tienda"])
    
    with tab_prac:
        if not st.session_state.data["lineas"]:
            st.info("Crea una Línea primero en la pestaña de a lado.")
        else:
            def_name = st.session_state.get("draft_practice_name", "")
            
            p_nombre = st.text_input("Nombre de la Práctica", value=def_name, key="add_p_nombre")
            p_linea = st.selectbox("Línea", [l["name"] for l in st.session_state.data["lineas"]], key="add_p_linea")
            p_tipo = st.selectbox("Tipo de Práctica", ["Deslizar (Simple)", "Medible (Cantidad)", "Temporizador (Enfoque)"], key="add_p_tipo")
            
            p_meta, p_unidad, p_mins = None, None, None
            if p_tipo == "Medible (Cantidad)":
                c_m1, c_m2 = st.columns(2)
                p_meta = c_m1.number_input("Meta Numérica", min_value=1, value=10)
                p_unidad = c_m2.text_input("Unidad", placeholder="Ej. Km, Series, Litros")
            elif p_tipo == "Temporizador (Enfoque)":
                p_mins = st.number_input("Minutos de enfoque", min_value=1, value=25)
            
            p_is_allday = st.checkbox("Durante todo el día", key="add_p_allday")
            if not p_is_allday:
                p_hora_input = st.time_input("Hora", key="add_p_hora")
                p_time_str = p_hora_input.strftime("%H:%M")
            else:
                p_time_str = "Todo el día"
                
            p_freq = st.radio("Frecuencia", ["Todos los días", "Días específicos"], key="add_p_freq")
            p_dias = st.multiselect("Días", DIAS_SEMANA, default=DIAS_SEMANA) if p_freq == "Días específicos" else DIAS_SEMANA
            p_desc = st.text_area("Descripción", key="add_p_desc")
            
            if st.button("Guardar Práctica", use_container_width=True, key="btn_guardar_nueva"):
                if p_nombre and len(p_dias) > 0:
                    tipo_mapeado = "swipe" if "Deslizar" in p_tipo else "numeric" if "Medible" in p_tipo else "timer"
                    nueva = {
                        "id": str(uuid.uuid4()), "name": p_nombre, "linea": p_linea,
                        "time": p_time_str, "days": p_dias, "desc": p_desc,
                        "type": tipo_mapeado, "target": p_meta, "unit": p_unidad, "duration": p_mins
                    }
                    st.session_state.data["practicas"].append(nueva)
                    if "draft_practice_name" in st.session_state: del st.session_state["draft_practice_name"]
                    guardar_datos(st.session_state.data)
                    st.rerun()

    with tab_lineas:
        l_nombre = st.text_input("Nueva Línea", placeholder="Ej. Infraestructura", key="add_l_nombre")
        if st.button("Crear Línea", use_container_width=True, key="btn_crear_linea"):
            if l_nombre and not any(l["name"].lower() == l_nombre.lower() for l in st.session_state.data["lineas"]):
                st.session_state.data["lineas"].append({"id": str(uuid.uuid4()), "name": l_nombre})
                guardar_datos(st.session_state.data)
                st.rerun()

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
                    
                    is_allday = (p.get('time') == "Todo el día")
                    e_is_allday = st.checkbox("Durante todo el día", value=is_allday, key=f"e_allday_{p['id']}")
                    
                    if not e_is_allday:
                        def_time = datetime.strptime(p['time'], "%H:%M").time() if not is_allday else datetime.strptime("08:00", "%H:%M").time()
                        e_hora_input = st.time_input("Hora", value=def_time, key=f"e_hor_{p['id']}")
                        e_time_str = e_hora_input.strftime("%H:%M")
                    else:
                        e_time_str = "Todo el día"
                        
                    e_dias = st.multiselect("Días", DIAS_SEMANA, default=p.get('days', DIAS_SEMANA), key=f"e_dia_{p['id']}")
                    e_desc = st.text_area("Descripción", value=p.get('desc', ''), key=f"e_des_{p['id']}")
                    
                    c_g, c_b = st.columns(2)
                    if c_g.button("Guardar", key=f"e_save_{p['id']}", use_container_width=True):
                        st.session_state.data["practicas"][i].update({
                            "name": e_nombre, "linea": e_linea, "time": e_time_str,
                            "days": e_dias, "desc": e_desc
                        })
                        guardar_datos(st.session_state.data)
                        st.rerun()
                    if c_b.button("Borrar", type="primary", key=f"e_del_{p['id']}", use_container_width=True):
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

    with tab_tienda:
        st.markdown(f"🪙 **Tus Monedas:** {st.session_state.data['coins']}")
        st.markdown(f"🛡️ **Escudos en Inventario:** {st.session_state.data['shields']}")
        st.caption("Ganas 10 monedas por cada práctica completada. Usa escudos para no perder tu racha en días de descanso.")
        
        if st.button("Comprar Escudo (100 🪙)", use_container_width=True, key="btn_comprar_escudo"):
            if st.session_state.data['coins'] >= 100:
                st.session_state.data['coins'] -= 100
                st.session_state.data['shields'] += 1
                guardar_datos(st.session_state.data)
                st.rerun()
            else:
                st.error("No tienes suficientes monedas.")

# ==========================================
# LAYOUT PRINCIPAL
# ==========================================
st.title("⚡ SENTIR Y CRECER")
st.markdown(f"<div class='quote-box'>« {frase_del_dia} »</div>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="streak-banner">
        <p class="streak-banner-title">🔥 Racha Élite Actual</p>
        <p class="streak-banner-number">{racha_actual} días</p>
    </div>
    <div class="level-banner">
        <h4 style="margin:0; color:#00ff9d;">Nivel {nivel_actual}: {titulo_actual}</h4>
        <p style="margin:5px 0; color:#ccc; font-size:14px;">XP Total: {total_xp} | Faltan {xp_para_siguiente} XP para subir</p>
    </div>
""", unsafe_allow_html=True)
st.progress(porcentaje_xp)

# ==========================================
# MENÚ DESPLEGABLE SUPERIOR (NUEVO)
# ==========================================
st.write("")
vista = st.selectbox(
    "🧭 Navegación Principal", 
    ["📍 Agenda Diaria", "📔 Recolect Diaria", "📅 Calendario", "🎭 Roles", "📈 Tendencias", "🤖 Coach Élite", "🗓️ Revisión Semanal", "🌟 1 Mensual"]
)
st.divider()

col_principal, col_der = st.columns([3, 1.2])

with col_der:
    st.subheader("🏆 Resumen Hoy")
    st.metric(label="Puntos Hoy", value=puntos_hoy)
    st.metric(label="Puntos Semana", value=puntos_semana)
    
    st.divider()
    if st.session_state.data["shield_log"][str_hoy]:
        st.success("🛡️ Escudo Activo Hoy. Tu racha está protegida.")
    else:
        if st.session_state.data["shields"] > 0:
            if st.button("Activar 🛡️ Escudo Hoy", use_container_width=True, key="btn_usar_escudo"):
                st.session_state.data["shields"] -= 1
                st.session_state.data["shield_log"][str_hoy] = True
                guardar_datos(st.session_state.data)
                st.rerun()

with col_principal:
    # === VISTA: AGENDA DIARIA ===
    if vista == "📍 Agenda Diaria":
        st.subheader(f"Actividades ({DIAS_SEMANA[hoy.weekday()]})")
        nombre_dia_hoy = DIAS_SEMANA[hoy.weekday()]
        practicas_hoy = [p for p in st.session_state.data["practicas"] if nombre_dia_hoy in p["days"]]
        practicas_ordenadas = sorted(practicas_hoy, key=lambda x: "00:00" if x["time"] == "Todo el día" else x["time"])
        
        if not practicas_ordenadas:
            st.info("Día libre o sin agendar.")
        else:
            lineas_presentes = sorted(list(set([p['linea'] for p in practicas_ordenadas])))
            for linea in lineas_presentes:
                st.markdown(f"<h3 style='color: #00ff9d; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 20px; font-size: 20px;'>📂 {linea}</h3>", unsafe_allow_html=True)
                practicas_linea = [p for p in practicas_ordenadas if p['linea'] == linea]
                
                for p in practicas_linea:
                    ya_completado = p["id"] in st.session_state.data["completed_log"][str_hoy]
                    
                    with st.container():
                        if ya_completado:
                            st.success(f"✅ **🕒 {p['time']} | {p['name']}**")
                            continue
                            
                        if p.get("type", "swipe") == "swipe":
                            if p.get('desc', ''):
                                with st.expander(f"🕒 {p['time']} | **{p['name']}**"): st.write(p['desc'])
                            else:
                                st.markdown(f"**🕒 {p['time']} | {p['name']}**")
                                
                            swipe = st.select_slider("Desliza", options=["⏳ Pendiente", "➡️ Desliza ➡️", "🔥 ¡Hecho!"], value="⏳ Pendiente", label_visibility="collapsed", key=f"sw_{p['id']}")
                            if swipe == "🔥 ¡Hecho!":
                                st.session_state.data["completed_log"][str_hoy].append(p["id"])
                                st.session_state.data["points_log"][str_hoy] += 10
                                st.session_state.data["coins"] += 10
                                st.session_state.data["on_time_log"][str_hoy] = True
                                guardar_datos(st.session_state.data)
                                st.rerun()

                        elif p.get("type") == "numeric":
                            st.markdown(f"**🕒 {p['time']} | {p['name']}** (Meta: {p['target']} {p['unit']})")
                            c_num1, c_num2 = st.columns([3, 1])
                            val = c_num1.number_input(f"Ingresa {p['unit']}", min_value=0.0, step=1.0, key=f"num_{p['id']}")
                            if val >= float(p.get("target", 1)):
                                if c_num2.button("🔥 Completar", key=f"btn_n_{p['id']}", type="primary", use_container_width=True):
                                    st.session_state.data["completed_log"][str_hoy].append(p["id"])
                                    st.session_state.data["points_log"][str_hoy] += 10
                                    st.session_state.data["coins"] += 10
                                    st.session_state.data["on_time_log"][str_hoy] = True
                                    guardar_datos(st.session_state.data)
                                    st.rerun()

                        elif p.get("type") == "timer":
                            st.markdown(f"**🕒 {p['time']} | {p['name']}** ⏱️ {p['duration']} min")
                            t_key = f"t_start_{p['id']}"
                            
                            if t_key not in st.session_state:
                                if st.button(f"▶️ Iniciar Enfoque ({p['duration']}m)", key=f"btn_t_{p['id']}"):
                                    st.session_state[t_key] = datetime.now().isoformat()
                                    st.rerun()
                            else:
                                start_time = datetime.fromisoformat(st.session_state[t_key])
                                elapsed = (datetime.now() - start_time).total_seconds() / 60.0
                                remaining = max(0, p.get("duration", 25) - elapsed)
                                
                                st.progress(min(elapsed / p.get("duration", 25), 1.0))
                                
                                if elapsed >= p.get("duration", 25):
                                    if st.button("🔥 Reclamar Puntos", key=f"btn_t_claim_{p['id']}", type="primary"):
                                        st.session_state.data["completed_log"][str_hoy].append(p["id"])
                                        st.session_state.data["points_log"][str_hoy] += 10
                                        st.session_state.data["coins"] += 10
                                        st.session_state.data["on_time_log"][str_hoy] = True
                                        guardar_datos(st.session_state.data)
                                        del st.session_state[t_key]
                                        st.rerun()
                                else:
                                    c_t1, c_t2 = st.columns([3, 1])
                                    c_t1.write(f"⏳ Quedan {int(remaining)} minutos...")
                                    if c_t2.button("🔄 Actualizar", key=f"btn_t_ref_{p['id']}"): st.rerun()

    # === VISTA: RECOLECT DIARIA (JOURNALING) ===
    elif vista == "📔 Recolect Diaria":
        st.subheader("📔 Recolect Diaria")
        st.caption(f"Escribe tus reflexiones, ideas o descargar tu mente. Fecha: {str_hoy}")
        st.info("💡 Tip: Si tienes una práctica llamada exactamente **'Journaling'**, se completará automáticamente al guardar.")
        
        texto_diario = st.text_area("¿Qué tienes en mente hoy?", value=st.session_state.data["journal_log"].get(str_hoy, ""), height=250, key="journal_input")
        
        if st.button("Guardar Recolect", type="primary", use_container_width=True):
            st.session_state.data["journal_log"][str_hoy] = texto_diario
            
            journaling_practica = None
            for p in st.session_state.data["practicas"]:
                if p["name"].strip().lower() == "journaling":
                    journaling_practica = p
                    break
                    
            if journaling_practica:
                p_id = journaling_practica["id"]
                if p_id not in st.session_state.data["completed_log"][str_hoy]:
                    st.session_state.data["completed_log"][str_hoy].append(p_id)
                    st.session_state.data["points_log"][str_hoy] += 10
                    st.session_state.data["coins"] += 10
                    st.session_state.data["on_time_log"][str_hoy] = True
                    st.success("✅ ¡Práctica 'Journaling' completada automáticamente!")
            
            guardar_datos(st.session_state.data)
            st.rerun()

    # === VISTA: 1 MENSUAL CON HISTORIAL ===
    elif vista == "🌟 1 Mensual":
        st.subheader("🌟 Revisión: 1 Mensual")
        
        es_primer_sabado = hoy.weekday() == 5 and 1 <= hoy.day <= 7
        mes_actual = hoy.strftime("%Y-%m")
        ya_iniciado = mes_actual in st.session_state.data["monthly_review_log"]
        desbloqueo_manual = st.session_state.get("forzar_desbloqueo_mensual", False)
        
        if not (es_primer_sabado or ya_iniciado or desbloqueo_manual):
            st.warning("🔒 Esta sección normalmente solo se habilita el **primer sábado de cada mes**.")
            if st.button("🔓 Forzar Desbloqueo Manual", use_container_width=True):
                st.session_state["forzar_desbloqueo_mensual"] = True
                st.rerun()
        else:
            if es_primer_sabado and not ya_iniciado:
                st.success("✨ ¡Hoy es el primer sábado del mes! Tómate tu tiempo para hacer esta revisión.")
                
            rev_data = st.session_state.data["monthly_review_log"].setdefault(mes_actual, {"q1": "", "q2": "", "q3": ""})
            
            st.markdown("### 1. ¿Cómo llego aquí?")
            ans1 = st.text_area("Tus reflexiones:", value=rev_data["q1"], key="m_q1", height=150)
            
            st.markdown("### 2. ¿Dónde estoy ahora?")
            ans2 = st.text_area("Estado actual y limpieza:", value=rev_data["q2"], key="m_q2", height=100)
            
            st.markdown("### 3. ¿A dónde y cómo voy?")
            ans3 = st.text_area("Plan del próximo mes:", value=rev_data["q3"], key="m_q3", height=200)
            
            if st.button("Guardar Revisión Mensual", type="primary", use_container_width=True):
                st.session_state.data["monthly_review_log"][mes_actual] = {
                    "q1": ans1, "q2": ans2, "q3": ans3
                }
                guardar_datos(st.session_state.data)
                st.success("Revisión mensual guardada con éxito.")
                st.rerun()
                
        st.divider()
        st.markdown("### 📚 Historial de Revisiones Pasadas")
        if not st.session_state.data["monthly_review_log"]:
            st.caption("Aún no tienes revisiones guardadas.")
        else:
            meses_guardados = list(st.session_state.data["monthly_review_log"].keys())
            meses_guardados.sort(reverse=True) 
            
            mes_seleccionado = st.selectbox("Selecciona un mes para leer:", meses_guardados)
            if mes_seleccionado:
                data_mes = st.session_state.data["monthly_review_log"][mes_seleccionado]
                with st.expander(f"📖 Leer Revisión de {mes_seleccionado}", expanded=False):
                    st.markdown("**1. ¿Cómo llego aquí?**")
                    st.info(data_mes.get("q1", "") if data_mes.get("q1") else "Sin respuesta")
                    st.markdown("**2. ¿Dónde estoy ahora?**")
                    st.info(data_mes.get("q2", "") if data_mes.get("q2") else "Sin respuesta")
                    st.markdown("**3. ¿A dónde y cómo voy?**")
                    st.info(data_mes.get("q3", "") if data_mes.get("q3") else "Sin respuesta")

    # === VISTA: REVISIÓN SEMANAL (INBOX MEJORADO) ===
    elif vista == "🗓️ Revisión Semanal":
        st.subheader("🗓️ Planeación y Revisión Semanal")
        st.caption("Limpia tu mente, evalúa tus listas y convierte tus ideas en acciones concretas para la semana que viene.")
        
        st.divider()
        st.markdown("#### 📥 Bandeja de Entrada (De tus Listas Histéricas)")
        
        hay_pendientes = False
        for r_idx, rol in enumerate(st.session_state.data["roles"]):
            if rol.get("histeric_list"):
                hay_pendientes = True
                st.markdown(f"**Rol: {rol['name']}**")
                for i_idx, item in enumerate(rol["histeric_list"]):
                    is_done = item.get("done", False)
                    c_it1, c_it2, c_it3 = st.columns([0.5, 4.5, 1.5])
                    
                    # Casilla para tachar
                    c_it1.checkbox("✅", value=is_done, key=f"chk_{item['id']}", on_change=toggle_histeric_item, args=(r_idx, i_idx), label_visibility="collapsed")
                    
                    # Texto (Tachado si está hecho)
                    if is_done:
                        c_it2.markdown(f"<span style='text-decoration: line-through; color: #888;'>{item['text']}</span>", unsafe_allow_html=True)
                    else:
                        c_it2.write(item['text'])
                    
                    # Botón desactivado si está hecho
                    if c_it3.button("Crear Práctica", key=f"h_to_p_{item['id']}", disabled=is_done):
                        st.session_state["draft_practice_name"] = item['text']
                        # Ya no lo borra automáticamente, mejor dejarlo tachado para que lo veas
                        st.success("¡Copiado! Abre la barra lateral '⚙️ Panel de Control' para configurar los días y guardarla.")
        
        if not hay_pendientes:
            st.info("Tus listas histéricas están vacías. Tienes todo bajo control.")

    # === VISTA: COACH IA SIMULADO ===
    elif vista == "🤖 Coach Élite":
        st.subheader("🤖 Análisis de Desempeño Élite")
        st.write("Procesando tu historial de los últimos 7 días...")
        
        fechas_7 = [hoy - timedelta(days=i) for i in range(7)]
        lineas_conteo = {l['name']: 0 for l in st.session_state.data['lineas']}
        
        for f in fechas_7:
            f_str = f.isoformat()
            if f_str in st.session_state.data["completed_log"]:
                for p_id in st.session_state.data["completed_log"][f_str]:
                    for p in st.session_state.data["practicas"]:
                        if p["id"] == p_id and p["linea"] in lineas_conteo:
                            lineas_conteo[p["linea"]] += 1
                            
        if not lineas_conteo or sum(lineas_conteo.values()) == 0:
            st.info("Aún no hay suficientes datos esta semana para generar un análisis profundo. ¡Empieza a completar prácticas!")
        else:
            linea_fuerte = max(lineas_conteo, key=lineas_conteo.get)
            linea_debil = min(lineas_conteo, key=lineas_conteo.get)
            
            st.markdown(f"""
            <div class='coach-box'>
                <h4 style="color:#8a2be2; margin-top:0;">Reporte Táctico</h4>
                <p>He revisado la telemetría de tus hábitos esta semana. Tu enfoque en la línea de <strong>{linea_fuerte}</strong> es sumamente sólido, demostrando un alto nivel de disciplina.</p>
                <p>Sin embargo, detecto una caída en tu atención hacia <strong>{linea_debil}</strong>. Recuerda que un sistema estable requiere balance. Te recomiendo configurar una práctica "Enfoque (Temporizador)" de 20 minutos para {linea_debil} y ejecutarla mañana a primera hora para reequilibrar tus estadísticas.</p>
                <p><em>Mantén la inercia. El nivel de Maestro te está esperando.</em></p>
            </div>
            """, unsafe_allow_html=True)

    # === VISTA: CALENDARIO ===
    elif vista == "📅 Calendario":
        st.subheader("Registro Retroactivo y Diario")
        
        st.markdown('<div id="calendar-start"></div>', unsafe_allow_html=True)
        cal = calendar.monthcalendar(hoy.year, hoy.month)
        cols = st.columns(7)
        for i, dia in enumerate(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]): cols[i].markdown(f"**{dia}**")
            
        for semana in cal:
            cols = st.columns(7)
            for i, dia in enumerate(semana):
                if dia != 0:
                    fecha_str = f"{hoy.year}-{hoy.month:02d}-{dia:02d}"
                    p_dia = st.session_state.data["points_log"].get(fecha_str, 0)
                    
                    # Formato Corto para que no se rompa el Grid en el Celular
                    label = f"📍 Hoy" if fecha_str == str_hoy else f"✅ {dia}" if p_dia > 0 else f"{dia}"
                    
                    if cols[i].button(label, key=f"c_{fecha_str}", help=f"{p_dia} pts conseguidos", use_container_width=True): 
                        st.session_state.selected_cal_date = fecha_str
                else: cols[i].write("") 
        
        if "selected_cal_date" in st.session_state and st.session_state.selected_cal_date:
            sel_date_str = st.session_state.selected_cal_date
            sel_date_obj = date.fromisoformat(sel_date_str)
            st.divider()
            st.markdown(f"#### 🛠️ Datos del día: {sel_date_str}")
            
            if sel_date_str in st.session_state.data.get("journal_log", {}) and st.session_state.data["journal_log"][sel_date_str]:
                st.markdown("**📔 Recolect Diaria:**")
                st.info(st.session_state.data["journal_log"][sel_date_str])
            else:
                st.caption("No escribiste en tu Recolect este día.")
            
            st.write("")
            
            if sel_date_obj > hoy: st.warning("No puedes modificar el futuro.")
            elif sel_date_obj == hoy: st.info("Usa la Agenda Diaria para completar las prácticas de hoy.")
            else:
                st.markdown("**✔️ Prácticas:**")
                n_dia = DIAS_SEMANA[sel_date_obj.weekday()]
                prac_sel = [p for p in st.session_state.data["practicas"] if n_dia in p["days"]]
                prac_sel = sorted(prac_sel, key=lambda x: "00:00" if x["time"] == "Todo el día" else x["time"])
                
                if not prac_sel:
                    st.caption("No tenías prácticas programadas.")
                
                for p in prac_sel:
                    ya_c = p["id"] in st.session_state.data["completed_log"].setdefault(sel_date_str, [])
                    c1, c2 = st.columns([3.5, 1.5])
                    c1.markdown(f"**🕒 {p['time']} | {p['name']}**")
                    if not ya_c:
                        if c2.button("⏱️ +5 Pts", key=f"r_{p['id']}_{sel_date_str}", use_container_width=True):
                            st.session_state.data["completed_log"][sel_date_str].append(p["id"])
                            st.session_state.data["points_log"].setdefault(sel_date_str, 0)
                            st.session_state.data["points_log"][sel_date_str] += 5
                            st.session_state.data["coins"] += 5
                            guardar_datos(st.session_state.data)
                            st.rerun()
                    else: c2.button("✅ Listo", disabled=True, key=f"rd_{p['id']}")

    # === VISTA: TENDENCIAS ===
    elif vista == "📈 Tendencias":
        st.subheader("📈 Rendimiento (14 días)")
        f_14 = [hoy - timedelta(days=i) for i in range(13, -1, -1)]
        df_t = pd.DataFrame({"Puntos Diarios": [st.session_state.data["points_log"].get(d.isoformat(), 0) for d in f_14]}, index=[d.strftime("%d %b") for d in f_14])
        st.area_chart(df_t, color="#00ff9d")

    # === VISTA: ROLES ===
    elif vista == "🎭 Roles":
        st.subheader("🎭 Estrategia de Roles")
        
        tab_mis_roles, tab_crear_rol = st.tabs(["Mis Roles", "+ Crear Nuevo Rol"])
        
        with tab_crear_rol:
            st.markdown("### Crear un nuevo rol estratégico")
            c_r1, c_r2 = st.columns([3, 1])
            n_rol = c_r1.text_input("Nombre del Rol", placeholder="Ej. Arquitecto de Redes", key="n_rol_input")
            if c_r2.button("Añadir Rol", key="btn_add_rol", use_container_width=True) and n_rol:
                st.session_state.data["roles"].append({"id": str(uuid.uuid4()), "name": n_rol, "objective": "", "histeric_list": []})
                guardar_datos(st.session_state.data)
                st.rerun()
                
        with tab_mis_roles:
            if not st.session_state.data["roles"]:
                st.info("No tienes roles definidos. Ve a la pestaña '+ Crear Nuevo Rol' para empezar.")
            else:
                rol_sel = st.selectbox("Selecciona un Rol para gestionar:", [r["name"] for r in st.session_state.data["roles"]], key="sel_rol_activo")
                r_idx = next(i for i, r in enumerate(st.session_state.data["roles"]) if r["name"] == rol_sel)
                rol = st.session_state.data["roles"][r_idx]
                
                with st.container():
                    st.markdown(f"<div class='role-header'>{rol['name']}</div>", unsafe_allow_html=True)
                    
                    st.markdown("#### 🎯 Objetivo Estratégico")
                    edit_key = f"edit_obj_{rol['id']}"
                    if edit_key not in st.session_state: st.session_state[edit_key] = False
                    
                    if not rol.get("objective", "") or st.session_state[edit_key]:
                        obj = st.text_area("Define tu objetivo:", value=rol.get("objective", ""), key=f"obj_input_{rol['id']}")
                        c_btn1, c_btn2 = st.columns(2)
                        if c_btn1.button("Guardar Objetivo", key=f"btn_save_obj_{rol['id']}", type="primary", use_container_width=True): 
                            st.session_state.data["roles"][r_idx]["objective"] = obj
                            st.session_state[edit_key] = False
                            guardar_datos(st.session_state.data); st.rerun()
                        if c_btn2.button("Cancelar", key=f"btn_cancel_obj_{rol['id']}", use_container_width=True):
                            st.session_state[edit_key] = False; st.rerun()
                    else:
                        st.markdown(f"<div class='objective-box'>{rol.get('objective', '')}</div>", unsafe_allow_html=True)
                        if st.button("✏️ Editar Objetivo", key=f"btn_edit_obj_toggle_{rol['id']}"): st.session_state[edit_key] = True; st.rerun()
                    
                    st.divider()
                    st.markdown("#### 📑 Lista Histérica")
                    c_h1, c_h2 = st.columns([4, 1])
                    n_it = c_h1.text_input("Pendiente:", placeholder="Anota tu idea o tarea suelta aquí...", key=f"new_item_{rol['id']}")
                    if c_h2.button("Añadir", key=f"btn_add_item_{rol['id']}", use_container_width=True) and n_it:
                        st.session_state.data["roles"][r_idx].setdefault("histeric_list", []).append({"id": str(uuid.uuid4()), "text": n_it, "done": False})
                        guardar_datos(st.session_state.data); st.rerun()
                    
                    for i_idx, it in enumerate(rol.get("histeric_list", [])):
                        is_done = it.get("done", False)
                        c_it1, c_it2, c_it3 = st.columns([0.5, 4.5, 1])
                        
                        # Casilla para tachar
                        c_it1.checkbox("✅", value=is_done, key=f"chk_rol_{it['id']}", on_change=toggle_histeric_item, args=(r_idx, i_idx), label_visibility="collapsed")
                        
                        # Texto (Tachado si está hecho)
                        if is_done:
                            c_it2.markdown(f"<span style='text-decoration: line-through; color: #888;'>{it['text']}</span>", unsafe_allow_html=True)
                        else:
                            c_it2.write(it['text'])
                            
                        if c_it3.button("❌", key=f"del_item_{it['id']}"):
                            st.session_state.data["roles"][r_idx]["histeric_list"].pop(i_idx)
                            guardar_datos(st.session_state.data); st.rerun()
                    
                    st.write("")
                    with st.expander("⚠️ Opciones Avanzadas (Eliminar Rol)"):
                        if st.button("🗑️ Eliminar este Rol Completo", type="primary", key=f"del_full_role_{rol['id']}"):
                            st.session_state.data["roles"].pop(r_idx); guardar_datos(st.session_state.data); st.rerun()