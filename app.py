import gradio as gr
import pandas as pd
import os
from datetime import datetime

ARCHIVO = "guias.csv"
COLUMNAS = ["Guia","Fecha","Remitente","Destinatario","Origen","Destino","Peso","Valor","Estado","Telefono"]

# === CAMBIA ESTAS 3 CLAVES POR LAS TUYAS, SOLO TU LAS SABES ===
CLAVE_JEFE = "jefe2026"
CLAVE_REPARTIDOR = "Repartidor2026"
CLAVE_CLIENTE = "Cliente2026"

def cargar_df():
    if not os.path.exists(ARCHIVO):
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_csv(ARCHIVO, index=False)
        return df
    return pd.read_csv(ARCHIVO, dtype=str).fillna("")

def guardar_df(df):
    df.to_csv(ARCHIVO, index=False)

def crear_guia(remitente, destinatario, origen, destino, peso, valor, telefono):
    df = cargar_df()
    num = len(df) + 1001
    codigo = f"GC-{num}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nueva = pd.DataFrame([[codigo, fecha, remitente, destinatario, origen, destino, peso, valor, "En Bodega", telefono]], columns=COLUMNAS)
    df = pd.concat([df, nueva], ignore_index=True)
    guardar_df(df)
    return f"✅ Guía creada: {codigo} | {remitente} -> {destinatario} | Estado: En Bodega", df.values.tolist()

def rastrear(codigo):
    df = cargar_df()
    r = df[df["Guia"] == codigo.strip().upper()]
    if r.empty:
        return "❌ Guía no encontrada. Verifica el código Ej: GC-1001"
    fila = r.iloc[0]
    return f"📦 GUÍA {fila['Guia']}\nFecha: {fila['Fecha']}\nDe: {fila['Remitente']} ({fila['Origen']})\nPara: {fila['Destinatario']} ({fila['Destino']})\nPeso: {fila['Peso']} kg | Valor a cobrar: ${fila['Valor']}\nESTADO: {fila['Estado']}"

def actualizar(codigo, nuevo_estado):
    df = cargar_df()
    idx = df[df["Guia"] == codigo.strip().upper()].index
    if len(idx) == 0:
        return "❌ Guía no encontrada", df.values.tolist()
    df.loc[idx, "Estado"] = nuevo_estado
    guardar_df(df)
    return f"✅ Guía {codigo.upper()} actualizada a: {nuevo_estado}", df.values.tolist()

def login(usuario, clave):
    u = usuario.strip().lower()
    if u == "jefe" and clave == CLAVE_JEFE:
        return "✅ Bienvenido JEFE", gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    if u == "repartidor" and clave == CLAVE_REPARTIDOR:
        return "✅ Bienvenido REPARTIDOR", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    if u == "cliente" and clave == CLAVE_CLIENTE:
        return "✅ Bienvenido CLIENTE", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    return "❌ Usuario o clave incorrecta", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

with gr.Blocks(title="GUZMAN CARGO") as demo:
    gr.Markdown("# GUZMAN CARGO - Sistema de Logística\n### Cartagena | Guías, Tracking y Control")
    
    with gr.Column() as login_box:
        gr.Markdown("### 🔐 Iniciar Sesión")
        user_in = gr.Textbox(label="Usuario", placeholder="Escribe tu usuario")
        pass_in = gr.Textbox(label="Clave", type="password", placeholder="Escribe tu clave")
        btn_login = gr.Button("Entrar", variant="primary")
        msg_login = gr.Textbox(label="Resultado")

    with gr.Tab("Nueva Guía", visible=False) as tab_nueva:
        remitente = gr.Textbox(label="Remitente")
        destinatario = gr.Textbox(label="Destinatario")
        origen = gr.Textbox(label="Origen", value="Cartagena")
        destino = gr.Textbox(label="Destino")
        peso = gr.Number(label="Peso (kg)", value=0)
        valor = gr.Number(label="Valor a cobrar $", value=0)
        telefono = gr.Textbox(label="Teléfono cliente")
        btn_crear = gr.Button("Generar Guía", variant="primary")
        res_crear = gr.Textbox(label="Resultado")
        tabla1 = gr.Dataframe(headers=COLUMNAS, label="Todas las Guías")

    with gr.Tab("Rastrear", visible=False) as tab_rastrear:
        cod_r = gr.Textbox(label="Código de Guía Ej: GC-1001", placeholder="GC-1001")
        btn_r = gr.Button("Buscar", variant="primary")
        res_r = gr.Textbox(label="Estado del envío", lines=6)

    with gr.Tab("Actualizar Estado", visible=False) as tab_actualizar:
        cod_a = gr.Textbox(label="Código Guía")
        estado_a = gr.Dropdown(["En Bodega","En Camino","En Reparto","Entregado","Devuelto"], value="En Bodega", label="Nuevo Estado")
        btn_a = gr.Button("Actualizar", variant="primary")
        res_a = gr.Textbox(label="Resultado")
        tabla2 = gr.Dataframe(headers=COLUMNAS, label="Todas las Guías")

    with gr.Tab("Todas las Guías", visible=False) as tab_todas:
        btn_t = gr.Button("Actualizar Tabla")
        tabla3 = gr.Dataframe(headers=COLUMNAS, label="Todas las Guías")

    btn_login.click(login, [user_in, pass_in], [msg_login, tab_nueva, tab_rastrear, tab_actualizar, tab_todas, login_box])
    btn_crear.click(crear_guia, [remitente, destinatario, origen, destino, peso, valor, telefono], [res_crear, tabla1])
    btn_r.click(rastrear, [cod_r], [res_r])
    btn_a.click(actualizar, [cod_a, estado_a], [res_a, tabla2])
    btn_t.click(lambda: cargar_df().values.tolist(), [], [tabla3])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
