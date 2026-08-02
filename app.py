import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from rembg import remove
from sklearn.cluster import KMeans
import stripe
import io
import requests
import base64

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
        .cambio-badge {
            background-color: #f0f2f6;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 4px solid #ff4b4b;
            margin-bottom: 8px;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MONETIZACIÓN ($1.50 USD) - STRIPE Y PAYPAL
# ==========================================
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
        "titulo": "👕 DiseñosApp | Preparador Textil IA Avanzado",
        "subtitulo": "Visualiza los cambios pedidos en tiempo real, verifica tu diseño protegido y descárgalo a **300 DPI reales** por solo **$1.50 USD**.",
        "medidas_header": "📏 Medidas de Impresión HD",
        "unidad": "Unidad de medida",
        "ancho": "Ancho",
        "alto": "Alto",
        "herramientas_ia_extra": "🤖 Ajustes y Cambios Solicitados (IA)",
        "modo_ia": "✨ Recrear/Duplicar con IA (Img2Img)",
        "prompt_ia": "Instrucciones de cambio de la gente",
        "fuerza_ia": "Fuerza de variación",
        "usar_upscale": "🔍 Ampliar Calidad (Estilo Megapixel 4K)",
        "tecnica": "Técnica de Impresión / Processo",
        "dtf": "DTF (Impresión Directa a Film)",
        "sublimacion": "Sublimación",
        "serigrafia_planos": "Serigrafía (Colores Planos)",
        "serigrafia_cmyk": "Serigrafía (Cuatricomía CMYK)",
        "num_tintas": "Número de Tintas",
        "subir_imagen": "Sube tu diseño base",
        "muestra_marca": "1. Vista Previa Interactiva (Con Cambios y Marca de Agua)",
        "resumen": "2. Resumen de Cambios y Confirmación",
        "medida_final": "Medida final de impresión",
        "calidad_salida": "Calidad de Salida",
        "precio_total": "Precio Total a Pagar",
        "elige_pago": "💳 Elige tu método de pago ($1.50 USD)",
        "pagar_tarjeta": "Pagar $1.50 con Tarjeta (Stripe)",
        "pagar_paypal": "Pagar $1.50 con PayPal",
        "pago_exitoso": "✅ ¡Pago de $1.50 USD confirmado! Cambios aplicados guardados.",
        "descargar_hd": "📥 Descarga tu Arte Modificado en Alta Resolución (300 DPI)",
        "descargar_master": "🚀 Descargar Master PNG (Sin Fondo para DTF/Sublimación)",
        "fotolitos": "Fotolitos en Alta Definición para Serigrafía",
        "descargar_tinta": "Descargar Fotolito Tinta",
        "procesar_otro": "🔄 Procesar otro diseño ($1.50 USD)",
        "instrucciones_cmyk": "📌 **Guía CMYK:** Impresión en prensa (Amarillo ➔ Magenta ➔ Cian ➔ Negro)."
    },
    "English": {
        "titulo": "👕 DiseñosApp | Advanced AI Textile Prepress",
        "subtitulo": "See requested changes live, verify protected design preview, and download at **300 real DPI** for just **$1.50 USD**.",
        "medidas_header": "📏 HD Print Dimensions",
        "unidad": "Unit of measurement",
        "ancho": "Width",
        "alto": "Height",
        "herramientas_ia_extra": "🤖 Requested Custom Changes (AI)",
        "modo_ia": "✨ AI Replication/Redraw (Img2Img)",
        "prompt_ia": "Customer change instructions",
        "fuerza_ia": "Variation strength",
        "usar_upscale": "🔍 AI Upscale & Enhance (Megapixel 4K)",
        "tecnica": "Printing Technique / Process",
        "dtf": "DTF (Direct to Film)",
        "sublimacion": "Sublimation",
        "serigrafia_planos": "Screen Printing (Spot Colors)",
        "serigrafia_cmyk": "Screen Printing (CMYK Process)",
        "num_tintas": "Number of Inks",
        "subir_imagen": "Upload your base design",
        "muestra_marca": "1. Interactive Preview (With Changes & Watermark)",
        "resumen": "2. Summary of Changes & Confirmation",
        "medida_final": "Final print size",
        "calidad_salida": "Output Quality",
        "precio_total": "Total Price to Pay",
        "elige_pago": "💳 Choose your payment method ($1.50 USD)",
        "pagar_tarjeta": "Pay $1.50 with Card (Stripe)",
        "pagar_paypal": "Pay $1.50 with PayPal",
        "pago_exitoso": "✅ $1.50 USD Payment confirmed! Applied changes secured.",
        "descargar_hd": "📥 Download High-Resolution Modified Artwork (300 DPI)",
        "descargar_master": "🚀 Download Master PNG (Transparent for DTF/Sublimation)",
        "fotolitos": "High Definition Screen Printing Separations",
        "descargar_tinta": "Download Ink Film",
        "procesar_otro": "🔄 Process another design ($1.50 USD)",
        "instrucciones_cmyk": "📌 **CMYK Guide:** Print order (Yellow ➔ Magenta ➔ Cyan ➔ Black)."
    },
    "Português": {
        "titulo": "👕 DiseñosApp | Pré-impressão Têxtil IA Avançada",
        "subtitulo": "Visualize as alterações solicitadas em tempo real e baixe a **300 DPI reais** por **$1.50 USD**.",
        "medidas_header": "📏 Dimensões de Impressão HD",
        "unidad": "Unidade de medida",
        "ancho": "Largura",
        "alto": "Altura",
        "herramientas_ia_extra": "🤖 Alterações Solicitadas (IA)",
        "modo_ia": "✨ Recriação/Duplicação com IA (Img2Img)",
        "prompt_ia": "Instruções de mudança do cliente",
        "fuerza_ia": "Força de variação",
        "usar_upscale": "🔍 Ampliar Qualidade (Estilo Megapixel 4K)",
        "tecnica": "Técnica de Impressão / Processo",
        "dtf": "DTF (Impressão Direta no Filme)",
        "sublimacion": "Sublimação",
        "serigrafia_planos": "Serigrafia (Cores Planas)",
        "serigrafia_cmyk": "Serigrafia (Quadricromia CMYK)",
        "num_tintas": "Número de Tintas",
        "subir_imagen": "Envie seu design base",
        "muestra_marca": "1. Pré-visualização Interativa (Com Mudanças e Marca d'água)",
        "resumen": "2. Resumo de Mudanças e Confirmação",
        "medida_final": "Tamanho final de impressão",
        "calidad_salida": "Qualidade de Saída",
        "precio_total": "Preço Total a Pagar",
        "elige_pago": "💳 Escolha seu método de pagamento ($1.50 USD)",
        "pagar_tarjeta": "Pagar $1.50 com Cartão (Stripe)",
        "pagar_paypal": "Pagar $1.50 com PayPal",
        "pago_exitoso": "✅ Pagamento confirmado!",
        "descargar_hd": "📥 Baixe sua Arte Modificada em Alta Resolução (300 DPI)",
        "descargar_master": "🚀 Baixar Master PNG (Fundo Transparente para DTF/Sublimação)",
        "fotolitos": "Fotolitos em Alta Definição",
        "descargar_tinta": "Baixar Fotolito Tinta",
        "procesar_otro": "🔄 Processar outro design ($1.50 USD)",
        "instrucciones_cmyk": "📌 **Guia CMYK**"
    },
    "Français": {
        "titulo": "👕 DiseñosApp | Pré-impression Textile IA Avancée",
        "subtitulo": "Visualisez les modifications demandées en direct pour **1,50 $ USD**.",
        "medidas_header": "📏 Dimensions d'impression HD",
        "unidad": "Unité de mesure",
        "ancho": "Largeur",
        "alto": "Hauteur",
        "herramientas_ia_extra": "🤖 Modifications Demandées (IA)",
        "modo_ia": "✨ Recréation/Duplication IA (Img2Img)",
        "prompt_ia": "Instructions de modification du client",
        "fuerza_ia": "Force de variation",
        "usar_upscale": "🔍 Agrandir Qualité (Style Megapixel 4K)",
        "tecnica": "Technique d'impression / Processus",
        "dtf": "DTF",
        "sublimacion": "Sublimation",
        "serigrafia_planos": "Sérigraphie (Plats)",
        "serigrafia_cmyk": "Sérigraphie (CMYK)",
        "num_tintas": "Nombre d'encres",
        "subir_imagen": "Téléchargez votre design",
        "muestra_marca": "1. Aperçu Interactif (Avec Modifications et Filigrane)",
        "resumen": "2. Résumé des Modifications & Confirmation",
        "medida_final": "Taille finale",
        "calidad_salida": "Qualité",
        "precio_total": "Prix total",
        "elige_pago": "💳 Paiement (1,50 $ USD)",
        "pagar_tarjeta": "Payer par Carte",
        "pagar_paypal": "Payer par PayPal",
        "pago_exitoso": "✅ Paiement confirmé!",
        "descargar_hd": "📥 Télécharger",
        "descargar_master": "🚀 Master PNG",
        "fotolitos": "Typons",
        "descargar_tinta": "Télécharger Typon",
        "procesar_otro": "🔄 Autre design",
        "instrucciones_cmyk": "📌 CMYK"
    }
}

# Selector de idioma
idioma_sel = st.sidebar.selectbox("🌐 Language / Idioma", ["Español", "English", "Português", "Français"])
txt = TRADUCCIONES[idioma_sel]

st.title(txt["titulo"])
st.markdown(txt["subtitulo"])

# ==========================================
# 4. FUNCIONES DE PROCESAMIENTO E IA REALES
# ==========================================
def recrear_imagen_con_ia(pil_img, prompt, strength=0.35):
    if STABILITY_API_KEY == "sk-TU_CLAVE_STABILITY_AI" or not STABILITY_API_KEY:
        return pil_img
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)
    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/image-to-image",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "application/json"},
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
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return Image.open(io.BytesIO(image_data))
        return pil_img
    except Exception:
        return pil_img

def ampliar_calidad_megapixel(pil_img):
    if STABILITY_API_KEY == "sk-TU_CLAVE_STABILITY_AI" or not STABILITY_API_KEY:
        w, h = pil_img.size
        return pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)
    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/esrgan-v1-x2plus/image-to-image/upscale",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "application/json"},
            files={"image": buffer}
        )
        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return Image.open(io.BytesIO(image_data))
        w, h = pil_img.size
        return pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    except Exception:
        w, h = pil_img.size
        return pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

def generar_vista_previa_protegida_con_cambios(pil_img, lista_cambios):
    preview = pil_img.copy()
    preview.thumbnail((500, 500))
    draw = ImageDraw.Draw(preview)
    w, h = preview.size
    
    draw.line((0, 0, w, h), fill=(255, 0, 0, 140), width=5)
    draw.line((0, h, w, 0), fill=(255, 0, 0, 140), width=5)
    
    draw.rectangle([10, 10, w - 10, 45], fill=(0, 0, 0, 160))
    draw.text((20, 18), "DISEÑOSAPP - VISTA CON CAMBIOS (PAGO PENDIENTE)", fill=(255, 255, 255))
    return preview

def procesar_alta_calidad(pil_img, target_w, target_h):
    img_sin_fondo = remove(pil_img)
    return img_sin_fondo.resize((target_w, target_h), Image.Resampling.LANCZOS)

def separar_colores_kmeans(pil_image, num_tintas):
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

# Pasarela PayPal
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
# 5. BARRA LATERAL (MEDIDAS, TÉCNICAS E IA)
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

st.sidebar.divider()
st.sidebar.header(txt["tecnica"])
tecnica_opciones = [txt["dtf"], txt["sublimacion"], txt["serigrafia_planos"], txt["serigrafia_cmyk"]]
tecnica = st.sidebar.radio("Selecciona técnica", tecnica_opciones)

num_tintas = 4
if tecnica == txt["serigrafia_planos"]:
    num_tintas = st.sidebar.slider(txt["num_tintas"], 2, 8, 4)

# Panel de Cambios y Peticiones de la Gente (Sin modificación de contenido específico)
st.sidebar.divider()
st.sidebar.header(txt["herramientas_ia_extra"])

cambios_solicitados = []

usar_ia = st.sidebar.checkbox(txt["modo_ia"], value=False)
prompt_ia = ""
fuerza_ia = 0.35
if usar_ia:
    prompt_ia = st.sidebar.text_input(txt["prompt_ia"], "vector illustration style, sharp lines")
    if prompt_ia:
        cambios_solicitados.append(f"Recrear/Estilo: {prompt_ia}")

usar_upscale = st.sidebar.checkbox(txt["usar_upscale"], value=False)
if usar_upscale:
    cambios_solicitados.append("Ampliación Calidad Megapixel 4K")

# ==========================================
# 6. CARGA Y VISUALIZADOR DE CAMBIOS
# ==========================================
uploaded_file = st.file_uploader(txt["subir_imagen"], type=["png", "jpg", "jpeg", "webp"])

if uploaded_file is not None:
    imagen_original = Image.open(uploaded_file).convert("RGB")
    
    # APLICAR MODIFICACIONES
    if usar_upscale:
        with st.spinner("Aplicando ampliación de calidad Megapixel..."):
            imagen_original = ampliar_calidad_megapixel(imagen_original)

    if usar_ia and prompt_ia:
        with st.spinner("Recreando diseño según instrucciones..."):
            imagen_original = recrear_imagen_con_ia(imagen_original, prompt_ia, fuerza_ia)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(txt["muestra_marca"])
        preview_img = generar_vista_previa_protegida_con_cambios(imagen_original, cambios_solicitados)
        st.image(preview_img, use_container_width=True)
        st.info("💡 *Este diseño muestra los cambios aplicados en tiempo real para tu aprobación.*")

    with col2:
        st.subheader(txt["resumen"])
        st.write(f"• **{txt['medida_final']}:** {ancho_deseado} x {alto_deseado}")
        st.write(f"• **{txt['calidad_salida']}:** {px_ancho} x {px_alto} px (300 DPI)")
        st.write(f"• **Proceso seleccionado:** {tecnica}")
        
        if cambios_solicitados:
            st.markdown("📋 **Cambios y peticiones aplicadas en esta versión:**")
            for cambio in cambios_solicitados:
                st.markdown(f'<div class="cambio-badge">✔️ {cambio}</div>', unsafe_allow_html=True)
        else:
            st.info("ℹ️ No se seleccionaron cambios adicionales.")

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
                                    'product_data': {'name': f'DiseñosApp HD Modificado ({ancho_deseado}x{alto_deseado})'},
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

        with st.spinner("Procesando matriz HD final con los cambios aplicados (300 DPI)..."):
            imagen_hd = procesar_alta_calidad(imagen_original, px_ancho, px_alto)

        col_desc1, col_desc2 = st.columns(2)
        
        with col_desc1:
            st.image(imagen_hd, caption=f"DiseñosApp HD Final ({px_ancho}x{px_alto}px)", use_container_width=True)
            
            buf = io.BytesIO()
            imagen_hd.save(buf, format="PNG", dpi=(DPI_SALIDA, DPI_SALIDA), compress_level=1)
            
            st.download_button(
                label=txt["descargar_master"],
                data=buf.getvalue(),
                file_name=f"diseñosapp_HD_modificado_{ancho_deseado}x{alto_deseado}.png",
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
        
        elif tecnica in [txt["dtf"], txt["sublimacion"]]:
            with col_desc2:
                st.success(f"✅ Arte listo y optimizado para {tecnica} a 300 DPI.")

        st.divider()
        if st.button(txt["procesar_otro"]):
            st.session_state.pago_completado = False
            st.query_params.clear()
            st.rerun()
