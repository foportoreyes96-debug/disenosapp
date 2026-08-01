import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import cv2
from rembg import remove
from sklearn.cluster import KMeans
import stripe
import io
import requests

# Dependencias de PayPal
from paypalcheckoutsdk.core import SandboxEnvironment, PayPalHttpClient
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest

# ==========================================
# 1. CONFIGURACIÓN RESPONSIVE (CELULAR / PC)
# ==========================================
st.set_page_config(
    page_title="DiseñosApp - Preprensa Textil IA",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS adaptativos para pantallas táctiles y móviles
st.markdown("""
    <style>
        .stButton>button, .stDownloadButton>button {
            width: 100% !important;
            height: 3.2em !important;
            font-size: 18px !important;
            border-radius: 10px !important;
            margin-top: 5px !important;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        img {
            max-width: 100% !important;
            height: auto !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MONETIZACIÓN ($1.50 USD) - STRIPE Y PAYPAL
# ==========================================
# Lectura segura desde Streamlit Secrets (o valores por defecto si estás en prueba local)
STRIPE_KEY = st.secrets.get("STRIPE_KEY", "sk_test_TU_CLAVE_STRIPE")
PAYPAL_CLIENT_ID = st.secrets.get("PAYPAL_CLIENT_ID", "TU_PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = st.secrets.get("PAYPAL_CLIENT_SECRET", "TU_PAYPAL_CLIENT_SECRET")
STABILITY_API_KEY = st.secrets.get("STABILITY_API_KEY", "sk-TU_CLAVE_STABILITY_AI")

stripe.api_key = STRIPE_KEY

paypal_env = SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_CLIENT_SECRET)
paypal_client = PayPalHttpClient(paypal_env)

PRECIO_USD = "1.50"

# ==========================================
# 3. SOPORTE MULTI-IDIOMA (I18N)
# ==========================================
TRADUCCIONES = {
    "Español": {
        "titulo": "👕 DiseñosApp | Preparador Textil IA",
        "subtitulo": "Duplica con IA, escala y prepara tus archivos a **300 DPI reales** por solo **$1.50 USD**.",
        "medidas_header": "📏 Medidas de Impresión HD",
        "unidad": "Unidad de medida",
        "ancho": "Ancho",
        "alto": "Alto",
        "modo_ia": "✨ Recreación/Duplicado con IA (Img2Img)",
        "prompt_ia": "Instrucciones para la IA (ej: 'estilo ilustración vectorial, alta resolución')",
        "fuerza_ia": "Fuerza de variación de la IA",
        "tecnica": "Técnica de Impresión",
        "serigrafia_planos": "Serigrafía (Colores Planos)",
        "serigrafia_cmyk": "Serigrafía (Cuatricomía CMYK)",
        "num_tintas": "Número de Tintas",
        "subir_imagen": "Sube tu diseño para procesar",
        "muestra_marca": "1. Muestra con Marca de Agua (Protección)",
        "resumen": "2. Resumen y Confirmación",
        "medida_final": "Medida final de impresión",
        "calidad_salida": "Calidad de Salida",
        "precio_total": "Precio Total a Pagar",
        "elige_pago": "💳 Elige tu método de pago ($1.50 USD)",
        "pagar_tarjeta": "Pagar $1.50 con Tarjeta (Stripe)",
        "pagar_paypal": "Pagar $1.50 con PayPal",
        "pago_exitoso": "✅ ¡Pago de $1.50 USD confirmado exitosamente!",
        "descargar_hd": "📥 Descarga tu Arte en Alta Resolución (300 DPI)",
        "descargar_master": "🚀 Descargar Master PNG (300 DPI Sin Fondo)",
        "fotolitos": "Fotolitos en Alta Definición para Serigrafía",
        "descargar_tinta": "Descargar Fotolito Tinta",
        "procesar_otro": "🔄 Procesar otro diseño ($1.50 USD)",
        "instrucciones_cmyk": "📌 **Guía CMYK:** Impresión en prensa (Amarillo ➔ Magenta ➔ Cian ➔ Negro). Estampado húmedo sobre húmedo."
    },
    "English": {
        "titulo": "👕 DiseñosApp | AI Textile Prepress",
        "subtitulo": "Duplicate with AI, scale, and prepare files at **300 real DPI** for just **$1.50 USD**.",
        "medidas_header": "📏 HD Print Dimensions",
        "unidad": "Unit of measurement",
        "ancho": "Width",
        "alto": "Height",
        "modo_ia": "✨ AI Replication/Redraw (Img2Img)",
        "prompt_ia": "AI prompt (e.g., 'vector illustration style, sharp clean lines')",
        "fuerza_ia": "AI Variation Strength",
        "tecnica": "Printing Technique",
        "serigrafia_planos": "Screen Printing (Spot Colors)",
        "serigrafia_cmyk": "Screen Printing (CMYK Process)",
        "num_tintas": "Number of Inks",
        "subir_imagen": "Upload your design to process",
        "muestra_marca": "1. Watermarked Preview (Protected)",
        "resumen": "2. Summary & Confirmation",
        "medida_final": "Final print size",
        "calidad_salida": "Output Quality",
        "precio_total": "Total Price to Pay",
        "elige_pago": "💳 Choose your payment method ($1.50 USD)",
        "pagar_tarjeta": "Pay $1.50 with Card (Stripe)",
        "pagar_paypal": "Pay $1.50 with PayPal",
        "pago_exitoso": "✅ $1.50 USD Payment successfully confirmed!",
        "descargar_hd": "📥 Download High-Resolution Artwork (300 DPI)",
        "descargar_master": "🚀 Download Master PNG (300 DPI Transparent)",
        "fotolitos": "High Definition Screen Printing Separations",
        "descargar_tinta": "Download Ink Film",
        "procesar_otro": "🔄 Process another design ($1.50 USD)",
        "instrucciones_cmyk": "📌 **CMYK Guide:** Print order (Yellow ➔ Magenta ➔ Cyan ➔ Black)."
    },
    "Português": {
        "titulo": "👕 DiseñosApp | Pré-impressão Têxtil IA",
        "subtitulo": "Duplique com IA, dimensione e prepare arquivos a **300 DPI reais** por **$1.50 USD**.",
        "medidas_header": "📏 Dimensões de Impressão HD",
        "unidad": "Unidade de medida",
        "ancho": "Largura",
        "alto": "Altura",
        "modo_ia": "✨ Recriação/Duplicação com IA (Img2Img)",
        "prompt_ia": "Instruções para a IA",
        "fuerza_ia": "Força de variação da IA",
        "tecnica": "Técnica de Impressão",
        "serigrafia_planos": "Serigrafia (Cores Planas)",
        "serigrafia_cmyk": "Serigrafia (Quadricromia CMYK)",
        "num_tintas": "Número de Tintas",
        "subir_imagen": "Envie seu design para processar",
        "muestra_marca": "1. Pré-visualização com Marca d'água (Protegido)",
        "resumen": "2. Resumo e Confirmação",
        "medida_final": "Tamanho final de impressão",
        "calidad_salida": "Qualidade de Saída",
        "precio_total": "Preço Total a Pagar",
        "elige_pago": "💳 Escolha seu método de pagamento ($1.50 USD)",
        "pagar_tarjeta": "Pagar $1.50 com Cartão (Stripe)",
        "pagar_paypal": "Pagar $1.50 com PayPal",
        "pago_exitoso": "✅ Pagamento de $1.50 USD confirmado com sucesso!",
        "descargar_hd": "📥 Baixe sua Arte em Alta Resolução (300 DPI)",
        "descargar_master": "🚀 Baixar Master PNG (300 DPI Fundo Transparente)",
        "fotolitos": "Fotolitos em Alta Definição",
        "descargar_tinta": "Baixar Fotolito Tinta",
        "procesar_otro": "🔄 Processar outro design ($1.50 USD)",
        "instrucciones_cmyk": "📌 **Guia CMYK:** Ordem de impressão (Amarelo ➔ Magenta ➔ Ciano ➔ Preto)."
    },
    "Français": {
        "titulo": "👕 DiseñosApp | Pré-impression Textile IA",
        "subtitulo": "Dupliquez avec IA, mettez à l'échelle et préparez vos fichiers à **300 DPI réels** pour **1,50 $ USD**.",
        "medidas_header": "📏 Dimensions d'impression HD",
        "unidad": "Unité de mesure",
        "ancho": "Largeur",
        "alto": "Hauteur",
        "modo_ia": "✨ Recréation/Duplication IA (Img2Img)",
        "prompt_ia": "Instructions pour l'IA",
        "fuerza_ia": "Force de variation de l'IA",
        "tecnica": "Technique d'impression",
        "serigrafia_planos": "Sérigraphie (Couleurs Plats)",
        "serigrafia_cmyk": "Sérigraphie (Quadrichromie CMYK)",
        "num_tintas": "Nombre d'encres",
        "subir_imagen": "Téléchargez votre design à traiter",
        "muestra_marca": "1. Aperçu avec filigrane (Protégé)",
        "resumen": "2. Résumé et Confirmation",
        "medida_final": "Taille d'impression finale",
        "calidad_salida": "Qualité de sortie",
        "precio_total": "Prix total à payer",
        "elige_pago": "💳 Choisissez votre mode de paiement (1,50 $ USD)",
        "pagar_tarjeta": "Payer 1,50 $ par Carte (Stripe)",
        "pagar_paypal": "Payer 1,50 $ avec PayPal",
        "pago_exitoso": "✅ Paiement de 1,50 $ USD confirmé avec succès!",
        "descargar_hd": "📥 Téléchargez votre fichier Haute Résolution (300 DPI)",
        "descargar_master": "🚀 Télécharger le Master PNG (300 DPI Sans Fond)",
        "fotolitos": "Typons en Haute Définition",
        "descargar_tinta": "Télécharger le Typon Encre",
        "procesar_otro": "🔄 Traiter un autre design (1,50 $ USD)",
        "instrucciones_cmyk": "📌 **Guide CMYK:** Ordre d'impression (Jaune ➔ Magenta ➔ Cyan ➔ Noir)."
    }
}

# Selector de idioma
idioma_sel = st.sidebar.selectbox("🌐 Language / Idioma", ["Español", "English", "Português", "Français"])
txt = TRADUCCIONES[idioma_sel]

st.title(txt["titulo"])
st.markdown(txt["subtitulo"])

# ==========================================
# 4. FUNCIONES DE PROCESAMIENTO E IA (IMG2IMG)
# ==========================================
def recrear_imagen_con_ia(pil_img, prompt, strength=0.35):
    """Duplica y regenera la imagen de referencia mediante la API Img2Img de Stability AI"""
    if STABILITY_API_KEY == "sk-TU_CLAVE_STABILITY_AI":
        return pil_img

    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)

    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/image-to-image",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json"
            },
            files={"init_image": buffer},
            data={
                "init_image_mode": "IMAGE_STRENGTH",
                "image_strength": 1.0 - strength,
                "text_prompts[0][text]": prompt,
                "text_prompts[0][weight]": 1,
                "cfg_scale": 7,
                "samples": 1,
                "steps": 30,
            }
        )

        if response.status_code == 200:
            data = response.json()
            import base64
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return Image.open(io.BytesIO(image_data))
        else:
            return pil_img
    except Exception:
        return pil_img

def generar_vista_previa_protegida(pil_img):
    """Muestra de baja resolución con marca de agua para proteger el arte"""
    preview = pil_img.copy()
    preview.thumbnail((500, 500))
    draw = ImageDraw.Draw(preview)
    w, h = preview.size
    draw.line((0, 0, w, h), fill=(255, 0, 0, 128), width=4)
    draw.line((0, h, w, 0), fill=(255, 0, 0, 128), width=4)
    draw.text((w // 4, h // 2), "DISEÑOSAPP - $1.50 USD", fill=(255, 255, 255))
    return preview

def procesar_alta_calidad(pil_img, target_w, target_h):
    """Remueve el fondo y escala a medidas exactas a 300 DPI reales (LANCZOS)"""
    img_sin_fondo = remove(pil_img)
    return img_sin_fondo.resize((target_w, target_h), Image.Resampling.LANCZOS)

def separar_colores_kmeans(pil_image, num_tintas):
    """Separación de colores planos para serigrafía mediante K-Means"""
    img_np = np.array(pil_image)
    rgb = img_np[:, :, :3]
    alpha = img_np[:, :, 3]
    mask_pixels = alpha > 100
    pixels_validos = rgb[mask_pixels]

    pixels_lab = cv2.cvtColor(pixels_validos.reshape(-1, 1, 3), cv2.COLOR_RGB2Lab).reshape(-1, 3)
    kmeans = KMeans(n_clusters=num_tintas, random_state=42, n_init=5)
    labels = kmeans.fit_predict(pixels_lab)

    h, w, _ = rgb.shape
    full_labels = np.zeros((h, w), dtype=int) - 1
    full_labels[mask_pixels] = labels

    capas = []
    for i in range(num_tintas):
        mascara = np.zeros((h, w), dtype=np.uint8)
        mascara[full_labels == i] = 255
        capas.append(mascara)
    return capas

def generar_fotolitos_cuatricomia_cmyk(pil_image_hd, lpi=55, dpi=300):
    """Genera 4 fotolitos CMYK tramados con angulación anti-Moiré y corrección de Dot Gain"""
    rgb = np.array(pil_image_hd.convert('RGB')).astype(float) / 255.0
    
    k = 1.0 - np.max(rgb, axis=2)
    k_mask = k < 1.0 
    c = np.zeros_like(k)
    m = np.zeros_like(k)
    y = np.zeros_like(k)
    
    c[k_mask] = (1.0 - rgb[:, :, 0][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    m[k_mask] = (1.0 - rgb[:, :, 1][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    y[k_mask] = (1.0 - rgb[:, :, 2][k_mask] - k[k_mask]) / (1.0 - k[k_mask])

    canales = {'Cian': c, 'Magenta': m, 'Amarillo': y, 'Negro': k}
    angulos = {'Cian': 15, 'Magenta': 75, 'Amarillo': 0, 'Negro': 45}

    fotolitos_cmyk = {}

    for nombre, canal in canales.items():
        canal_compensado = np.power(canal, 1.4) 
        canal_gray = (canal_compensado * 255).astype(np.uint8)
        
        angle_rad = np.radians(angulos[nombre])
        grid_size = dpi / lpi
        
        h, w = canal_gray.shape
        y_coords, x_coords = np.ogrid[:h, :w]
        
        x_rot = x_coords * np.cos(angle_rad) - y_coords * np.sin(angle_rad)
        y_rot = x_coords * np.sin(angle_rad) + y_coords * np.cos(angle_rad)
        
        trama_matriz = (np.sin(2 * np.pi * x_rot / grid_size) + np.sin(2 * np.pi * y_rot / grid_size)) / 4.0 + 0.5
        trama_matriz = (trama_matriz * 255).astype(np.uint8)
        
        fotolito_binario = np.where(canal_gray > trama_matriz, 0, 255).astype(np.uint8)
        fotolitos_cmyk[nombre] = fotolito_binario

    return fotolitos_cmyk

# Lógica de Pagos con PayPal
def crear_orden_paypal():
    try:
        request = OrdersCreateRequest()
        request.prefer('return=representation')
        request.request_body({
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "USD", "value": PRECIO_USD}}],
            "application_context": {
                "return_url": st.config.get_option("browser.serverAddress") + "/?paypal_success=true",
                "cancel_url": st.config.get_option("browser.serverAddress") + "/"
            }
        })
        response = paypal_client.execute(request)
        for link in response.result.links:
            if link.rel == "approve":
                return link.href, response.result.id
    except Exception:
        pass
    return None, None

def capturar_pago_paypal(order_id):
    try:
        request = OrdersCaptureRequest(order_id)
        response = paypal_client.execute(request)
        return response.result.status == "COMPLETED"
    except Exception:
        return False

# Detección de Estado de Pago
if "pago_completado" not in st.session_state:
    st.session_state.pago_completado = False

query_params = st.query_params
if query_params.get("session_id"):
    try:
        session = stripe.checkout.Session.retrieve(query_params.get("session_id"))
        if session.payment_status == "paid":
            st.session_state.pago_completado = True
    except Exception:
        pass

if query_params.get("paypal_success") and "paypal_order_id" in st.session_state:
    if capturar_pago_paypal(st.session_state.paypal_order_id):
        st.session_state.pago_completado = True

# ==========================================
# 5. BARRA LATERAL (OPCIONES Y MEDIDAS)
# ==========================================
st.sidebar.header(txt["medidas_header"])
unidad_opciones = ["Centímetros (cm)", "Pulgadas (in)"] if idioma_sel == "Español" else ["Centimeters (cm)", "Inches (in)"]
unidad = st.sidebar.selectbox(txt["unidad"], unidad_opciones)
col_w, col_h = st.sidebar.columns(2)

if "cm" in unidad.lower():
    ancho_deseado = col_w.number_input(f"{txt['ancho']} (cm)", min_value=5.0, max_value=100.0, value=30.0, step=0.5)
    alto_deseado = col_h.number_input(f"{txt['alto']} (cm)", min_value=5.0, max_value=100.0, value=40.0, step=0.5)
    ancho_in = ancho_deseado / 2.54
    alto_in = alto_deseado / 2.54
else:
    ancho_in = col_w.number_input(f"{txt['ancho']} (in)", min_value=2.0, max_value=40.0, value=12.0, step=0.5)
    alto_in = col_h.number_input(f"{txt['alto']} (in)", min_value=2.0, max_value=40.0, value=16.0, step=0.5)

DPI_SALIDA = 300
px_ancho = int(ancho_in * DPI_SALIDA)
px_alto = int(alto_in * DPI_SALIDA)

# Módulo IA Img2Img
usar_ia = st.sidebar.checkbox(txt["modo_ia"], value=False)
prompt_ia = ""
fuerza_ia = 0.35
if usar_ia:
    prompt_ia = st.sidebar.text_input(txt["prompt_ia"], "vector illustration style, high definition, sharp lines")
    fuerza_ia = st.sidebar.slider(txt["fuerza_ia"], 0.1, 0.8, 0.35, 0.05)

tecnica_opciones = ["DTF / Sublimación", txt["serigrafia_planos"], txt["serigrafia_cmyk"]]
tecnica = st.sidebar.radio(txt["tecnica"], tecnica_opciones)

num_tintas = 4
if tecnica == txt["serigrafia_planos"]:
    num_tintas = st.sidebar.slider(txt["num_tintas"], 2, 8, 4)

# ==========================================
# 6. CARGA Y MUESTRA PROTEGIDA
# ==========================================
uploaded_file = st.file_uploader(txt["subir_imagen"], type=["png", "jpg", "jpeg", "webp"])

if uploaded_file is not None:
    imagen_original = Image.open(uploaded_file).convert("RGB")
    
    # Aplicar duplicado/recreación por IA si está activo
    if usar_ia and prompt_ia:
        with st.spinner("Recreando arte con IA (Img2Img)..."):
            imagen_original = recrear_imagen_con_ia(imagen_original, prompt_ia, fuerza_ia)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(txt["muestra_marca"])
        preview_img = generar_vista_previa_protegida(imagen_original)
        st.image(preview_img, use_container_width=True)

    with col2:
        st.subheader(txt["resumen"])
        st.write(f"• **{txt['medida_final']}:** {ancho_deseado} x {alto_deseado}")
        st.write(f"• **{txt['calidad_salida']}:** {px_ancho} x {px_alto} px (300 DPI)")
        st.write(f"• **{txt['tecnica']}:** {tecnica}")
        if usar_ia:
            st.write("• **Recreación IA:** Activa")
        st.divider()
        st.metric(label=txt["precio_total"], value="$1.50 USD")

        if not st.session_state.pago_completado:
            st.subheader(txt["elige_pago"])
            metodo = st.radio("Método / Method", ["Stripe (Tarjeta)", "PayPal"], horizontal=True)

            if metodo == "Stripe (Tarjeta)":
                if st.button(txt["pagar_tarjeta"], type="primary"):
                    try:
                        checkout_session = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{
                                'price_data': {
                                    'currency': 'usd',
                                    'product_data': {'name': f'DiseñosApp HD ({ancho_deseado}x{alto_deseado})'},
                                    'unit_amount': 150,
                                },
                                'quantity': 1,
                            }],
                            mode='payment',
                            success_url=st.config.get_option("browser.serverAddress") + "/?session_id={CHECKOUT_SESSION_ID}",
                            cancel_url=st.config.get_option("browser.serverAddress") + "/",
                        )
                        st.link_button("Checkout Stripe ➔", checkout_session.url)
                    except Exception as e:
                        st.error(f"Error al iniciar Stripe: {e}")

            elif metodo == "PayPal":
                if st.button(txt["pagar_paypal"], type="primary"):
                    url_aprobacion, order_id = crear_orden_paypal()
                    if url_aprobacion:
                        st.session_state.paypal_order_id = order_id
                        st.link_button("Checkout PayPal ➔", url_aprobacion)
                    else:
                        st.error("Error al conectar con PayPal. Revisa las credenciales.")
        else:
            st.success(txt["pago_exitoso"])

    # ==========================================
    # 7. DESCARGA HD POST-PAGO (300 DPI)
    # ==========================================
    if st.session_state.pago_completado:
        st.divider()
        st.header(txt["descargar_hd"])

        with st.spinner("Procesando matriz HD a 300 DPI..."):
            imagen_hd = procesar_alta_calidad(imagen_original, px_ancho, px_alto)

        col_desc1, col_desc2 = st.columns(2)
        
        with col_desc1:
            st.image(imagen_hd, caption=f"DiseñosApp HD Master ({px_ancho}x{px_alto}px)", use_container_width=True)
            
            buf = io.BytesIO()
            imagen_hd.save(buf, format="PNG", dpi=(DPI_SALIDA, DPI_SALIDA), compress_level=1)
            
            st.download_button(
                label=txt["descargar_master"],
                data=buf.getvalue(),
                file_name=f"diseñosapp_HD_{ancho_deseado}x{alto_deseado}.png",
                mime="image/png",
                type="primary"
            )

        if tecnica == txt["serigrafia_planos"]:
            with col_desc2:
                st.subheader(txt["fotolitos"])
                capas_hd = separar_colores_kmeans(imagen_hd, num_tintas)
                
                for idx, mascara in enumerate(capas_hd):
                    buf_tinta = io.BytesIO()
                    Image.fromarray(mascara).save(buf_tinta, format="PNG", dpi=(DPI_SALIDA, DPI_SALIDA))
                    
                    st.download_button(
                        label=f"{txt['descargar_tinta']} #{idx+1} (300 DPI)",
                        data=buf_tinta.getvalue(),
                        file_name=f"diseñosapp_fotolito_tinta_{idx+1}.png",
                        mime="image/png"
                    )

        elif tecnica == txt["serigrafia_cmyk"]:
            with col_desc2:
                st.subheader("Fotolitos CMYK Tramados (55 LPI - 300 DPI)")
                st.info(txt["instrucciones_cmyk"])
                
                fotolitos_cmyk = generar_fotolitos_cuatricomia_cmyk(imagen_hd, lpi=55, dpi=300)
                grid_cmyk = st.columns(2)
                
                for idx, (nombre_canal, mascara) in enumerate(fotolitos_cmyk.items()):
                    with grid_cmyk[idx % 2]:
                        st.text(f"Canal {nombre_canal}")
                        st.image(mascara, use_container_width=True)
                        
                        buf_cmyk = io.BytesIO()
                        Image.fromarray(mascara).save(buf_cmyk, format="PNG", dpi=(DPI_SALIDA, DPI_SALIDA))
                        
                        st.download_button(
                            label=f"Descargar {nombre_canal}",
                            data=buf_cmyk.getvalue(),
                            file_name=f"diseñosapp_fotolito_CMYK_{nombre_canal}.png",
                            mime="image/png"
                        )

        st.divider()
        if st.button(txt["procesar_otro"]):
            st.session_state.pago_completado = False
            st.query_params.clear()
            st.rerun()
