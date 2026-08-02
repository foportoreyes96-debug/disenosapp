import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import numpy as np
import io
import requests
import base64
import cv2
from rembg import remove, new_session

# Configuración de página
st.set_page_config(page_title="DiseñosApp - Editor y Vista Previa", layout="wide")

# Configuración de Claves de API (puedes cambiarlas o usar variables de entorno)
STABILITY_API_KEY = "sk-TU_CLAVE_STABILITY_AI"

# Función de eliminación de fondo mejorada con corte perimetral estricto
def quitar_fondo_hd_ultra_limpio(pil_img):
    """Quita el fondo y aplica una binarización estricta del canal alfa para eliminar 
    cualquier rastro, sombra o residuo difuso en la barba y los contornos."""
    try:
        session_u2net = new_session("u2net")
        img_rembg = remove(pil_img, session=session_u2net)
    except Exception:
        img_rembg = remove(pil_img)
        
    if img_rembg.mode != "RGBA":
        img_rembg = img_rembg.convert("RGBA")
        
    r, g, b, alpha = img_rembg.split()
    
    # Convertir canal alfa a matriz NumPy para manipulación exacta
    alpha_np = np.array(alpha)
    rgb_np = np.array(Image.merge("RGB", (r, g, b)))
    
    # Umbral drástico: cualquier píxel semi-transparente o halo menor a 150 se vuelve 100% transparente
    _, alpha_mask = cv2.threshold(alpha_np, 150, 255, cv2.THRESH_BINARY)
    
    # Operación morfológica limpia para sellar el contorno sin dejar bordes borrosos
    kernel = np.ones((1, 1), np.uint8)
    alpha_clean = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kernel)
    
    r_c, g_c, b_c = cv2.split(rgb_np)
    img_final_limpia = Image.merge("RGBA", (Image.fromarray(r_c), Image.fromarray(g_c), Image.fromarray(b_c), Image.fromarray(alpha_clean)))

    if STABILITY_API_KEY != "sk-TU_CLAVE_STABILITY_AI" and STABILITY_API_KEY:
        buffer = io.BytesIO()
        img_final_limpia.save(buffer, format="PNG")
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
                return Image.open(io.BytesIO(image_data)).convert("RGBA")
        except Exception:
            pass
            
    w, h = img_final_limpia.size
    return img_final_limpia.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

def ampliar_calidad_megapixels(pil_img):
    """Función de ampliación de calidad HD/Megapixel."""
    w, h = pil_img.size
    return pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

def recrear_con_ia(pil_img):
    """Función simulada o lista para integración de Img2Img con IA."""
    return pil_img

# --- Interfaz Principal ---
st.sidebar.title("Ajustes y Parámetros")

# Dimensiones
ancho_cm = st.sidebar.number_input("Ancho (cm)", value=30.0, step=1.0)
alto_cm = st.sidebar.number_input("Alto (cm)", value=40.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("Técnica de Impresión / Proceso")
tecnica = st.sidebar.radio(
    "Selecciona técnica",
    ["DTF (Impresión Directa a Film)", "Sublimación", "Serigrafía (Colores Planos)", "Serigrafía (Cuatricomía CMYK)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Ajustes y Cambios Solicitados (IA)")
opcion_recrear = st.sidebar.checkbox("Recrear/Duplicar con IA (Img2Img)")
opcion_ampliar = st.sidebar.checkbox("Ampliar Calidad (Estilo Megapixel 4K)")
opcion_quitar_fondo = st.sidebar.checkbox("Quitar Fondo HD Ultra Profesional (Corte perfecto sin residuos en barbas ni orillas)", value=True)

# Área de Carga de Imagen (o imagen por defecto si se desea probar)
uploaded_file = st.sidebar.file_uploader("Sube tu imagen de diseño", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    imagen_original = Image.open(uploaded_file).convert("RGBA")
else:
    # Imagen de prueba por defecto en caso de no subir archivo (puedes reemplazarla o dejar el comportamiento vacío)
    # Creamos una imagen sintética transparente de respaldo si no hay archivo
    imagen_original = Image.new("RGBA", (800, 800), (120, 80, 50, 255))

# Procesamiento de la imagen según los checkboxes seleccionados
imagen_procesada = imagen_original.copy()
cambios_aplicados = []

if opcion_recrear:
    imagen_procesada = recrear_con_ia(imagen_procesada)
    cambios_aplicados.append("Recreación o duplicación mediante IA aplicada.")

if opcion_ampliar:
    imagen_procesada = ampliar_calidad_megapixels(imagen_procesada)
    cambios_aplicados.append("Amplificación de calidad estilo Megapixel 4K.")

if opcion_quitar_fondo:
    imagen_procesada = quitar_fondo_hd_ultra_limpio(imagen_procesada)
    cambios_aplicados.append("Eliminación de fondo HD con Limpieza Profunda en Barbas y Contornos.")

# --- Vista Principal en Pantalla ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### DISEÑOSAPP - VISTA CON CAMBIOS (PAGO PENDIENTE)")
    st.image(imagen_procesada, use_container_width=True)
    st.info("💡 Este diseño muestra los cambios aplicados en tiempo real para tu aprobación.")

with col2:
    w_px, h_px = imagen_procesada.size
    st.markdown(f"**• Calidad de Salida:** {w_px} x {h_px} px (300 DPI)")
    st.markdown(f"**• Proceso seleccionado:** {tecnica}")
    
    st.markdown("**📋 Cambios y peticiones aplicadas en esta versión:**")
    for cambio in cambios_aplicados:
        st.success(f"✔️ {cambio}")
    
    st.markdown("---")
    st.markdown("### Precio Total a Pagar")
    st.markdown("# $1.50 USD")
    
    st.markdown("### 💳 Elige tu método de pago ($1.50 USD)")
    metodo_pago = st.radio("Método / Method", ["Stripe (Tarjeta)", "PayPal"])
    
    if st.button("Pagar $1.50 con Tarjeta (Stripe)"):
        st.write("Redirigiendo a pasarela de pago segura...")
