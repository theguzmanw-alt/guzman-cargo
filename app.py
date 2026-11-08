import gradio as gr
import pandas as pd
import os
from datetime import datetime

ARCHIVO = "guias.csv"
COLUMNAS = ["Guia", "Fecha", "Remitente", "Destinatario", "Origen", "Destino", "Peso", "Valor", "Estado", "Telefono", "Cedula_Repartidor"]

# ================= CONFIGURACION DE ACCESO =================
# CAMBIA ESTOS DATOS POR TUS DATOS REALES ANTES DE PUBLICAR
JEFE_CEDULA = "1000000000"
JEFE_CLAVE = "Guzman2026"

REPARTIDOR_1_CEDULA = "2000000000"
REPARTIDOR_1_CLAVE = "Reparto2026"
REPARTIDOR_1_NOMBRE = "Repartidor 1"

REPARTIDORES = {
    REPARTIDOR_1_CEDULA: {"clave": REPARTIDOR_1_CLAVE, "nombre": REPARTIDOR_1_NOMBRE}
}
# ===========================================================

def cargar_df():
    if not os.path.exists(ARCHIVO):
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_csv(ARCHIVO, index=False)
        return df
    try:
        df = pd.read_csv(ARCHIVO, dtype=str).fillna("")
        for c in COLUMNAS:
            if c not in df.columns:
                df[c] = ""
        return df
    except Exception:
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_csv(ARCHIVO, index=False)
        return df

def guardar_df(df):
    df.to_csv(ARCHIVO, index=False)

def dinero_por_cobrar():
    df = cargar_df()
    if df.empty:
        return "RESUMEN FINANCIERO\n\nTotal por cobrar: $0\nTotal vendido: $0\nTotal guias: 0\nEntregadas: 0\nPendientes: 0"
    df_calc = df.copy()
    df_calc["Valor"] = pd.to_numeric(df_calc["Valor"], errors="coerce").fillna(0)
    total = df_calc[df_calc["Estado"] != "Entregado"]["Valor"].sum()
    total_todo = df_calc["Valor"].sum()
    entregadas = len(df_calc[df_calc["Estado"] == "Entregado"])
    pendientes = len(df_calc[df_calc["Estado"] != "Entregado"])
    return f"RESUMEN FINANCIERO\n\nTotal por cobrar (pendiente): ${total:,.0f}\nTotal vendido: ${total_todo:,.0f}\nTotal guias: {len(df_calc)}\nEntregadas: {entregadas}\nPendientes por entregar: {pendientes}"

def crear_guia(remitente, destinatario, origen, destino, peso, valor, telefono):
    # CORREGIDO: siempre devuelve 6 valores, igual que el boton espera
    if not remitente or not destinatario or not destino:
        return "Error: Remitente, Destinatario y Destino son obligatorios.", cargar_df().values.tolist(), remitente, destinatario, destino, telefono
    df = cargar_df()
    if not df.empty and "Guia" in df.columns:
        nums = df["Guia"].str.extract(r'(\d+)').dropna()
        next_num = int(nums[0].max()) + 1 if not nums.empty else 1001
    else:
        next_num = 1001
    codigo = f"GC-{next_num}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nueva = pd.DataFrame([[codigo, fecha, remitente.strip(), destinatario.strip(), origen.strip(), destino.strip(), str(peso), str(valor), "En Bodega", str(telefono).strip(), ""]], columns=COLUMNAS)
    df = pd.concat([df, nueva], ignore_index=True)
    guardar_df(df)
    # CORREGIDO: sin emoji, y limpia los campos para la proxima guia
    return f"Guia creada exitosamente: {codigo} | {remitente} -> {destinatario} | Valor: ${float(valor):,.0f}", df.values.tolist(), "", "", "", ""

def pedir_envio(nombre, telefono, recoge, entrega, que_es):
    if not nombre or not telefono or not recoge or not entrega:
        return "Error: Completa todos los campos obligatorios para solicitar la recogida."
    df = cargar_df()
    if not df.empty and "Guia" in df.columns:
        nums = df["Guia"].str.extract(r'(\d+)').dropna()
        next_num = int(nums[0].max()) + 1 if not nums.empty else 1001
    else:
        next_num = 1001
    codigo = f"GC-{next_num}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    nueva = pd.DataFrame([[codigo, fecha, nombre.strip(), "POR CONFIRMAR", recoge.strip(), entrega.strip(), "0", "0", "Solicitud Nueva", str(telefono).strip(), ""]], columns=COLUMNAS)
    df = pd.concat([df, nueva], ignore_index=True)
    guardar_df(df)
    return f"Solicitud recibida, {nombre}.\n\nSu codigo de seguimiento es: {codigo}\nNos comunicaremos al {telefono} para confirmar el valor.\nRecogida en: {recoge}\nEntrega en: {entrega}\nContenido: {que_es}"

def rastrear(codigo):
    if not codigo:
        return "Ingrese su codigo de guia. Ejemplo: GC-1001"
    df = cargar_df()
    r = df[df["Guia"].str.upper() == codigo.strip().upper()]
    if r.empty:
        return "No se encontro ninguna guia con ese codigo. Verifique e intente nuevamente. Ejemplo: GC-1001"
    f = r.iloc[0]
    estados = ["En Bodega", "En Camino", "En Reparto", "Entregado"]
    if f["Estado"] == "Solicitud Nueva":
        progreso = "[1/4] Solicitud Recibida - En espera de confirmacion"
    elif f["Estado"] == "Devuelto":
        progreso = "Estado Final: Devuelto"
    elif f["Estado"] in estados:
        idx = estados.index(f["Estado"]) + 1
        progreso = f"Progreso: {idx}/4 - {f['Estado']}"
    else:
        progreso = f"Estado: {f['Estado']}"
    try:
        val_formateado = f"${float(f['Valor']):,.0f}"
    except:
        val_formateado = f"${f['Valor']}"
    return f"GUZMAN CARGO - SEGUIMIENTO\n\nGuia: {f['Guia']}\n{progreso}\n\nRemitente: {f['Remitente']} ({f['Origen']})\nDestinatario: {f['Destinatario']} ({f['Destino']})\nPeso: {f['Peso']} kg | Valor a cobrar: {val_formateado}\nFecha de registro: {f['Fecha']}"

def actualizar(codigo, nuevo_estado, cedula_rep):
    if not codigo:
        return "Error: Ingrese un codigo de guia valido.", cargar_df().values.tolist()
    df = cargar_df()
    mask = df["Guia"].str.upper() == codigo.strip().upper()
    if not mask.any():
        return "Error: Guia no encontrada.", df.values.tolist()
    df.loc[mask, "Estado"] = nuevo_estado
    df.loc[mask, "Cedula_Repartidor"] = str(cedula_rep)
    guardar_df(df)
    pendientes = df[df["Estado"].isin(["En Bodega", "En Camino", "En Reparto", "Solicitud Nueva"])]
    return f"Actualizacion exitosa. {codigo.upper()} ahora esta en estado: {nuevo_estado}", pendientes.values.tolist()

def lista_hoy():
    df = cargar_df()
    pendientes = df[df["Estado"].isin(["En Bodega", "En Camino", "En Reparto", "Solicitud Nueva"])]
    return pendientes.values.tolist()

def login(cedula, clave):
    cedula = cedula.strip()
    clave = clave.strip()
    if cedula == JEFE_CEDULA and clave == JEFE_CLAVE:
        df_actual = cargar_df()
        return ("Bienvenido, Administrador General.", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), cedula, df_actual.values.tolist(), dinero_por_cobrar(), df_actual.values.tolist())
    if cedula in REPARTIDORES and REPARTIDORES[cedula]["clave"] == clave:
        nombre = REPARTIDORES[cedula]["nombre"]
        df_actual = cargar_df()
        pendientes = df_actual[df_actual["Estado"].isin(["En Bodega", "En Camino", "En Reparto", "Solicitud Nueva"])]
        return (f"Bienvenido, {nombre}.", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), cedula, [], "", pendientes.values.tolist())
    return ("Error: Cedula o clave incorrecta. Verifique sus credenciales.", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), "", [], "", [])

CSS = """
body {background:#F2F3F5 !important; font-family: 'Segoe UI', Arial, sans-serif !important;}
.gradio-container {background:#F2F3F5 !important; max-width: 1100px !important; margin: 0 auto !important;}
.header {background: #0A2A4A; color: white; padding: 28px 24px; border-radius: 8px; text-align: left; margin-bottom: 20px;}
.header h1 {color: white !important; font-size: 32px !important; margin: 0 !important; letter-spacing: 2px;}
.header p {color: #C9A227 !important; margin: 6px 0 0 0 !important; font-size: 14px; letter-spacing: 1px; text-transform: uppercase;}
button.primary {background:#0A2A4A !important; border:none !important; color:white !important; font-weight:600 !important; border-radius:6px !important; text-transform: uppercase; letter-spacing: 0.5px;}
label {font-weight: 600 !important; color: #0A2A4A !important; text-transform: uppercase; font-size: 12px !important;}
"""

with gr.Blocks(title="GUZMAN CARGO - Sistema de Gestion Logistica", css=CSS) as demo:
    gr.HTML("""<div class="header"><h1>GUZMAN CARGO</h1><p>Sistema de Gestion Logistica &nbsp;|&nbsp; Cartagena - Colombia &nbsp;|&nbsp; Rapido, Seguro y Confiable</p></div>""")

    with gr.Tabs():
        with gr.Tab("Rastrear Paquete"):
            gr.Markdown("### Consulta Publica de Envios")
            gr.Markdown("Consulte el estado actual de su envio ingresando su codigo de guia.")
            cod_r = gr.Textbox(label="Codigo de Guia", placeholder="Ejemplo: GC-1001")
            btn_r = gr.Button("Consultar Estado", variant="primary")
            res_r = gr.Textbox(label="Resultado de la consulta", lines=8)
            btn_r.click(rastrear, inputs=[cod_r], outputs=[res_r])

        with gr.Tab("Tarifas y Cobertura"):
            gr.Markdown("""
            ### Tarifas Vigentes - Base hasta 5 Kg
            | Destino | Tarifa |
            |---|---|
            | Cartagena - Zona Urbana | $10.000 COP |
            | Turbaco / Arjona | $15.000 COP |
            | Barranquilla | $25.000 COP |
            | Santa Marta | $30.000 COP |
            | Bogota / Medellin | $35.000 COP |
            
            Para paquetes superiores a 5 kg, se realiza cotizacion personalizada. Todos los envios incluyen seguimiento en linea.
            """)

        with gr.Tab("Solicitar Recogida"):
            gr.Markdown("### Solicitud de Servicio a Domicilio")
            p_nombre = gr.Textbox(label="Nombre completo")
            p_tel = gr.Textbox(label="Telefono / WhatsApp")
            p_recoge = gr.Textbox(label="Direccion de recogida")
            p_entrega = gr.Textbox(label="Direccion de entrega")
            p_que = gr.Textbox(label="Descripcion del contenido")
            btn_pedir = gr.Button("Enviar Solicitud", variant="primary")
            res_pedir = gr.Textbox(label="Confirmacion", lines=6)
            btn_pedir.click(pedir_envio, inputs=[p_nombre, p_tel, p_recoge, p_entrega, p_que], outputs=[res_pedir])

    gr.Markdown("---\n### ACCESO AL PERSONAL AUTORIZADO")
    with gr.Column() as login_box:
        cedula_in = gr.Textbox(label="Numero de Cedula", placeholder="Ingrese su cedula sin puntos ni comas")
        pass_in = gr.Textbox(label="Contrasena", type="password", placeholder="Ingrese su contrasena")
        btn_login = gr.Button("Ingresar al Sistema", variant="primary")
        msg_login = gr.Textbox(label="Estado de acceso", interactive=False)
        cedula_actual = gr.State(value="")

    with gr.Tab("Jefe - Crear Guia", visible=False) as tab_jefe:
        gr.Markdown("#### REGISTRO DE NUEVA GUIA")
        with gr.Row():
            remitente = gr.Textbox(label="Remitente")
            destinatario = gr.Textbox(label="Destinatario")
        with gr.Row():
            origen = gr.Textbox(label="Ciudad de Origen", value="Cartagena")
            destino = gr.Textbox(label="Ciudad / Barrio de Destino")
        with gr.Row():
            peso = gr.Number(label="Peso (Kg)", value=1.0)
            valor = gr.Number(label="Valor a Cobrar (COP)", value=10000)
        telefono = gr.Textbox(label="Telefono del Cliente")
        btn_crear = gr.Button("Generar Guia", variant="primary")
        res_crear = gr.Textbox(label="Resultado", interactive=False)
        tabla1 = gr.Dataframe(headers=COLUMNAS, label="Guias Registradas en el Sistema")
        btn_crear.click(crear_guia, inputs=[remitente, destinatario, origen, destino, peso, valor, telefono], outputs=[res_crear, tabla1, remitente, destinatario, destino, telefono])

    with gr.Tab("Jefe - Panel Financiero", visible=False) as tab_dinero:
        gr.Markdown("#### CONTROL FINANCIERO Y ESTADISTICAS")
        dinero_txt = gr.Textbox(label="Resumen Ejecutivo", lines=7)
        btn_dinero = gr.Button("Actualizar Resumen Financiero")
        btn_dinero.click(dinero_por_cobrar, inputs=[], outputs=[dinero_txt])

    with gr.Tab("Repartidor - Entregas Pendientes", visible=False) as tab_repa:
        gr.Markdown("#### RUTA DE ENTREGAS ASIGNADAS")
        btn_hoy = gr.Button("Refrescar Lista Pendientes")
        tabla_hoy = gr.Dataframe(headers=COLUMNAS, label="Envios Activos")
        btn_hoy.click(lista_hoy, inputs=[], outputs=[tabla_hoy])
        gr.Markdown("#### ACTUALIZAR ESTADO DE ENTREGA")
        cod_a = gr.Textbox(label="Codigo de Guia - Ejemplo: GC-1001")
        estado_a = gr.Dropdown(["En Bodega", "En Camino", "En Reparto", "Entregado", "Devuelto"], value="En Reparto", label="Nuevo Estado")
        btn_a = gr.Button("Confirmar Actualizacion", variant="primary")
        res_a = gr.Textbox(label="Resultado Operativo", interactive=False)
        btn_a.click(actualizar, inputs=[cod_a, estado_a, cedula_actual], outputs=[res_a, tabla_hoy])

    with gr.Tab("Jefe - Todas las Guias", visible=False) as tab_todas:
        gr.Markdown("#### HISTORIAL COMPLETO DE OPERACIONES")
        btn_t = gr.Button("Cargar Base de Datos Completa")
        tabla3 = gr.Dataframe(headers=COLUMNAS)
        btn_t.click(lambda: cargar_df().values.tolist(), inputs=[], outputs=[tabla3])

    btn_login.click(login, inputs=[cedula_in, pass_in], outputs=[msg_login, tab_jefe, tab_dinero, tab_repa, tab_todas, login_box, cedula_actual, tabla1, dinero_txt, tabla_hoy])

    gr.Markdown("---\n<center><small>GUZMAN CARGO S.A.S. - Todos los derechos reservados - Sistema interno de gestion logistica</small></center>")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
