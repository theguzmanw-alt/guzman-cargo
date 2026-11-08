import gradio as gr
import pandas as pd
import os
from datetime import datetime

ARCHIVO = "guias.csv"
COLUMNAS = ["Guia","Fecha","Remitente","Destinatario","Origen","Destino","Peso","Valor","Estado","Telefono"]

# === CAMBIA ESTAS CLAVES ===
CLAVE_JEFE = "guzman2026"
CLAVE_REPARTIDOR = "reparto2026"
CLAVE_cliente = "cliente2026"

def cargar_df():
    if not os.path.exists(ARCHIVO):
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_csv(ARCHIVO, index=False)
        return df
    return pd.read_csv(ARCHIVO, dtype=str).fillna("")

def guardar_df(df):
    df.to_csv(ARCHIVO, index=False)

def dinero_por_cobrar():
    df = cargar_df()
    if df.empty:
        return "💰 Total por cobrar: $0\n📦 Total guías: 0\n✅ Entregadas: 0\n🚚 Pendientes: 0"
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    total = df[df["Estado"] != "Entregado"]["Valor"].sum()
    total_todo = df["Valor"].sum()
    entregadas = len(df[df["Estado"] == "Entregado"])
    pendientes = len(df[df["Estado"] != "Entregado"])
    return f"💰 POR COBRAR (pendiente): ${total:,.0f}\n💵 Total vendido: ${total_todo:,.0f}\n📦 Total guías: {len(df)}\n✅ Entregadas: {entregadas}\n🚚 Pendientes por entregar: {pendientes}"

def crear_guia(remitente, destinatario, origen, destino, peso, valor, telefono):
    df = cargar_df()
    num = len(df) + 1001
    codigo = f"GC-{num}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nueva = pd.DataFrame([[codigo, fecha, remitente, destinatario, origen, destino, peso, valor, "En Bodega", telefono]], columns=COLUMNAS)
    df = pd.concat([df, nueva], ignore_index=True)
    guardar_df(df)
    return f"✅ Guía creada: {codigo} | {remitente} -> {destinatario}", df.values.tolist(), dinero_por_cobrar()

def pedir_envio(nombre, telefono, recoge, entrega, que_es):
    df = cargar_df()
    num = len(df) + 1001
    codigo = f"GC-{num}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nueva = pd.DataFrame([[codigo, fecha, nombre, "POR CONFIRMAR", recoge, entrega, "0", "0", "Solicitud Nueva", telefono]], columns=COLUMNAS)
    df = pd.concat([df, nueva], ignore_index=True)
    guardar_df(df)
    return f"✅ ¡Solicitud recibida {nombre}!\nTu código es: {codigo}\nTe llamamos al {telefono} para confirmar precio.\nRecogemos en: {recoge}\nLlevamos a: {entrega}"

def rastrear(codigo):
    df = cargar_df()
    r = df[df["Guia"] == codigo.strip().upper()]
    if r.empty:
        return "❌ No encontré esa guía. Revisa el código Ej: GC-1001"
    f = r.iloc[0]
    barra = {"En Bodega":"🟩⬜⬜⬜ En Bodega","Solicitud Nueva":"🟩⬜⬜⬜ Solicitud Recibida","En Camino":"🟩🟩⬜⬜ En Camino","En Reparto":"🟩🟩🟩⬜ En Reparto","Entregado":"🟩🟩🟩🟩 Entregado ✅","Devuelto":"⬛ Devuelto"}.get(f["Estado"], f["Estado"])
    return f"📦 GUÍA {f['Guia']}\n{barra}\n\nDe: {f['Remitente']} ({f['Origen']})\nPara: {f['Destinatario']} ({f['Destino']})\nPeso: {f['Peso']} kg | A cobrar: ${f['Valor']}\nFecha: {f['Fecha']}"

def actualizar(codigo, nuevo_estado):
    df = cargar_df()
    idx = df[df["Guia"] == codigo.strip().upper()].index
    if len(idx)==0:
        return "❌ Guía no encontrada", df.values.tolist()
    df.loc[idx, "Estado"] = nuevo_estado
    guardar_df(df)
    return f"✅ {codigo.upper()} -> {nuevo_estado}", df.values.tolist()

def lista_hoy():
    df = cargar_df()
    hoy = datetime.now().strftime("%Y-%m-%d")
    pendientes = df[(df["Estado"].isin(["En Bodega","En Camino","En Reparto","Solicitud Nueva"])) & (df["Fecha"].str.contains(hoy, na=False) | True)]
    if pendientes.empty:
        return "🎉 No tienes entregas pendientes"
    return pendientes.values.tolist()

def login(usuario, clave):
    u = usuario.strip().lower()
    if u == "jefe" and clave == CLAVE_JEFE:
        return "✅ Bienvenido JEFE", gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)
    if u == "repartidor" and clave == CLAVE_REPARTIDOR:
        return "✅ Bienvenido REPARTIDOR", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    return "❌ Usuario o clave incorrecta", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

CSS = """
body {background:#ECE5DD !important;}
.gradio-container {background:#ECE5DD !important;}
h1 {color:#075E54 !important; text-align:center;}
button.primary {background:#25D366 !important; border:none !important; color:white !important; font-weight:bold !important;}
"""

with gr.Blocks(title="GUZMAN CARGO", css=CSS) as demo:
    gr.Markdown("# 🚚 GUZMAN CARGO\n### Cartagena | Rápido, Seguro y Confiable")
    
    # --- CLIENTE - SIEMPRE VISIBLE, SIN CLAVE ---
    gr.Markdown("## 👤 SOY CLIENTE")
    with gr.Tab("📦 Rastrear Mi Paquete"):
        cod_r = gr.Textbox(label="Tu código", placeholder="Ej: GC-1001")
        btn_r = gr.Button("🔍 Ver dónde va mi paquete", variant="primary")
        res_r = gr.Textbox(label="Estado", lines=8)
        btn_r.click(rastrear, [cod_r], [res_r])
    
    with gr.Tab("💲 Precios"):
        gr.Markdown("""
        ### 💲 NUESTROS PRECIOS - CARTAGENA
        | Destino | Precio |
        |---|---|
        | **Dentro de Cartagena** | **$10.000** |
        | **Turbaco / Arjona** | **$15.000** |
        | **Barranquilla** | **$25.000** |
        | **Santa Marta** | **$30.000** |
        | **Bogotá / Medellín** | **$35.000** |
        
        *Precio base hasta 5kg. Pregunta por paquetes grandes.*
        """)
    
    with gr.Tab("🛵 Pedir Un Envío"):
        p_nombre = gr.Textbox(label="Tu nombre")
        p_tel = gr.Textbox(label="Tu WhatsApp / Teléfono")
        p_recoge = gr.Textbox(label="¿Dónde recogemos?")
        p_entrega = gr.Textbox(label="¿Dónde entregamos?")
        p_que = gr.Textbox(label="¿Qué envías?")
        btn_pedir = gr.Button("✅ Pedir Recogida", variant="primary")
        res_pedir = gr.Textbox(label="Resultado", lines=5)
        btn_pedir.click(pedir_envio, [p_nombre, p_tel, p_recoge, p_entrega, p_que], [res_pedir])

    # --- PERSONAL ---
    gr.Markdown("---\n## 🔐 SOLO PERSONAL GUZMAN CARGO")
    with gr.Column() as login_box:
        user_in = gr.Textbox(label="Usuario", placeholder="Escribe tu usuario")
        pass_in = gr.Textbox(label="Clave", type="password", placeholder="Escribe tu clave")
        btn_login = gr.Button("Entrar", variant="primary")
        msg_login = gr.Textbox(label="Resultado")

    with gr.Tab("👑 JEFE - Crear Guía", visible=False) as tab_jefe:
        remitente = gr.Textbox(label="Remitente")
        destinatario = gr.Textbox(label="Destinatario")
        origen = gr.Textbox(label="Origen", value="Cartagena")
        destino = gr.Textbox(label="Destino")
        peso = gr.Number(label="Peso (kg)", value=0)
        valor = gr.Number(label="Valor a cobrar $", value=10000)
        telefono = gr.Textbox(label="Teléfono cliente")
        btn_crear = gr.Button("Generar Guía", variant="primary")
        res_crear = gr.Textbox(label="Resultado")
        tabla1 = gr.Dataframe(headers=COLUMNAS, label="Guías")
        btn_crear.click(crear_guia, [remitente, destinatario, origen, destino, peso, valor, telefono], [res_crear, tabla1, dinero_txt])

    with gr.Tab("💰 JEFE - Dinero y Resumen", visible=False) as tab_dinero:
        dinero_txt = gr.Textbox(label="Resumen", lines=5, value=dinero_por_cobrar())
        btn_dinero = gr.Button("🔄 Actualizar Dinero")
        btn_dinero.click(dinero_por_cobrar, [], [dinero_txt])

    with gr.Tab("🛵 REPARTIDOR - Mis Entregas Hoy", visible=False) as tab_repa:
        gr.Markdown("### 📋 Lo que tienes que entregar hoy")
        btn_hoy = gr.Button("Ver mis entregas de hoy")
        tabla_hoy = gr.Dataframe(headers=COLUMNAS)
        btn_hoy.click(lista_hoy, [], [tabla_hoy])
        gr.Markdown("### 🔄 Cambiar Estado")
        cod_a = gr.Textbox(label="Código Guía Ej: GC-1001")
        estado_a = gr.Dropdown(["En Bodega","En Camino","En Reparto","Entregado","Devuelto"], value="En Reparto", label="Nuevo Estado")
        btn_a = gr.Button("Actualizar Estado", variant="primary")
        res_a = gr.Textbox(label="Resultado")
        btn_a.click(actualizar, [cod_a, estado_a], [res_a, tabla_hoy])

    with gr.Tab("📋 JEFE - Todas las Guías", visible=False) as tab_todas:
        btn_t = gr.Button("Actualizar Tabla")
        tabla3 = gr.Dataframe(headers=COLUMNAS)
        btn_t.click(lambda: cargar_df().values.tolist(), [], [tabla3])

    btn_login.click(login, [user_in, pass_in], [msg_login, tab_jefe, tab_dinero, tab_repa, tab_todas, login_box])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
