import gradio as gr
import pandas as pd
import os, datetime

DATA = "guias.csv"
if not os.path.exists(DATA):
    pd.DataFrame(columns=["Guia","Fecha","Remitente","Destinatario","Origen","Destino","Peso","Valor","Estado","Telefono"]).to_csv(DATA, index=False)

def guardar_guia(rem, dest, origen, destino, peso, valor, tel):
    df = pd.read_csv(DATA)
    guia = f"GC-{len(df)+1001}"
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    nuevo = pd.DataFrame([[guia, fecha, rem, dest, origen, destino, peso, valor, "En Bodega", tel]], columns=df.columns)
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(DATA, index=False)
    return f"GUÍA CREADA: {guia}\nRemitente: {rem}\nDestino: {destino}\nValor: ${valor}", df

def buscar_guia(codigo):
    df = pd.read_csv(DATA)
    r = df[df["Guia"]==codigo.strip().upper()]
    if r.empty:
        return "Guía no encontrada. Verifica el código. Ej: GC-1001"
    fila = r.iloc[0]
    return f"GUÍA {fila['Guia']}\n\nDe: {fila['Remitente']} ({fila['Origen']}) -> Para: {fila['Destinatario']} ({fila['Destino']})\nPeso: {fila['Peso']} kg | Valor: ${fila['Valor']}\nEstado: {fila['Estado']}\nFecha: {fila['Fecha']}"

def actualizar_estado(codigo, nuevo_estado):
    df = pd.read_csv(DATA)
    idx = df[df["Guia"]==codigo.strip().upper()].index
    if len(idx)==0:
        return "Guía no encontrada", df
    df.loc[idx, "Estado"] = nuevo_estado
    df.to_csv(DATA, index=False)
    return f"Guía {codigo} actualizada a: {nuevo_estado}", df

def cargar_tabla():
    return pd.read_csv(DATA)

with gr.Blocks(title="GUZMAN CARGO") as demo:
    gr.Markdown("# GUZMAN CARGO - Sistema de Logística\n### Cartagena | Guias, Tracking y Control")
    with gr.Tab("Nueva Guía"):
        rem = gr.Textbox(label="Remitente")
        dest = gr.Textbox(label="Destinatario")
        origen = gr.Textbox(label="Origen", value="Cartagena")
        destino = gr.Textbox(label="Destino")
        peso = gr.Number(label="Peso (kg)")
        valor = gr.Number(label="Valor a cobrar $")
        tel = gr.Textbox(label="Teléfono cliente")
        btn = gr.Button("Generar Guía", variant="primary")
        out = gr.Textbox(label="Resultado", lines=6)
        tabla = gr.Dataframe(value=cargar_tabla, label="Todas las Guías")
        btn.click(guardar_guia, [rem, dest, origen, destino, peso, valor, tel], [out, tabla])
    with gr.Tab("Rastrear"):
        cod = gr.Textbox(label="Código de Guía Ej: GC-1001", placeholder="GC-1001")
        btn2 = gr.Button("Buscar", variant="primary")
        out2 = gr.Textbox(label="Estado del envío", lines=8)
        btn2.click(buscar_guia, cod, out2)
    with gr.Tab("Actualizar Estado"):
        cod2 = gr.Textbox(label="Código Guía")
        estado = gr.Dropdown(["En Bodega","En Camino","En Reparto","Entregado","Devuelto"], label="Nuevo Estado")
        btn3 = gr.Button("Actualizar", variant="primary")
        out3 = gr.Textbox(label="Resultado")
        tabla2 = gr.Dataframe(value=cargar_tabla)
        btn3.click(actualizar_estado, [cod2, estado], [out3, tabla2])
    with gr.Tab("Todas las Guías"):
        btn4 = gr.Button("Actualizar Tabla")
        tabla3 = gr.Dataframe(value=cargar_tabla)
        btn4.click(cargar_tabla, None, tabla3)

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
