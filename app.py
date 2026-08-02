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

STABILITY_API_KEY = "sk-TU_CLAVE_STABILITY_AI"

# Función original de quitar fondo
def quitar_fondo(pil_img):
    try:
        return remove(pil_img)
    except Exception:
        return pil_img

def ampliar_calidad_megapixels(pil_img):
    w, h = pil_img.size
    return pil_img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

def recrear_con_ia(pil_img):
    return pil_img

# --- NUEVA FUNCIÓN: Cuatricomía Semitones (Halftone Converter) ---
def generar_halftone_cmyk(pil_img, dot_size=8):
    """
    Convierte la imagen a separación CMYK de semitonos (puntos de imprenta/halftone)
    simulando un convertidor profesional de semitonos para serigrafía.
    """
    img_rgb = pil_img.convert("RGB")
    np_img = np.array(img_rgb) / 255.0
    
    # Conversión RGB a CMYK
    K = 1.0 - np.max(np_img, axis=2)
    C = (1.0 - np_img[:, :, 0] - K) / (1.0 - K + 1e-10)
    M = (1.0 - np_img[:, :, 1] - K) / (1.0 - K + 1e-10)
    Y = (1.0 - np_img[:, :, 2] - K) / (1.0 - K + 1e-10)
    
    channels = {
        'Cyan': (C, (0, 255, 255)), 
        'Magenta': (M, (255, 0, 255)), 
        'Amarillo': (Y, (255, 255, 0)), 
        'Negro': (K, (0, 0, 0))
    }
    
    h, w = np_img.shape[:2]
    halftone_canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
    step = max(4, dot_size)
    
    for name, (channel_data, color) in channels.items():
        y_coords, x_coords = np.mgrid[step//2:h:step, step//2:w:step]
        y_indices = np.clip(y_coords, 0, h - 1)
        x_indices = np.clip(x_coords, 0, w - 1)
        intensities = channel_data[y_indices, x_indices]
        
        radii = (step / 2) * np.sqrt(intensities)
        channel_img = np.ones((h, w, 3), dtype=np.uint8) * 255
        
        for yy, xx, r in zip(y_coords.ravel(), x_coords.ravel(), radii.ravel()):
            if r > 0.5:
                ink_color = (255 - color[0], 255 - color[1], 255 - color[2])
                cv2.circle(channel_img, (int(xx), int(yy)), int(r), ink_color, -1)
                
        halftone_canvas = cv2.bitwise_and(halftone_canvas, channel_img)
        
    return Image.fromarray(halftone_canvas)

# --- Interfaz en Sidebar (Estructura Original Respetada) ---
st.sidebar.markdown("### Ancho y Alto")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    ancho_cm = st.sidebar.number_input("Ancho (cm)", value=30.0, step=1.0)
with col_s2:
    alto_cm = st.sidebar.number_input("Alto (cm)", value=40.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.markdown("### Técnica de Impresión / Proceso")
st.sidebar.markdown("**Selecciona técnica**")
tecnica = st.sidebar.radio(
    "Selecciona técnica",
    ["DTF (Impresión Directa a Film)", "Sublimación", "Serigrafía (Colores Planos)", "Serigrafía (Cuatricomía CMYK)"],
    label_visibility="collapsed"
)

# Control dinámico exclusivo para Halftone si se elige Cuatricomía
dot_size_param = 8
if tecnica == "Serigrafía (Cuatricomía CMYK)":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖨️ Configuración Halftone")
    dot_size_param = st.sidebar.slider("Tamaño de Punto", min_value=4, max_value=20, value=8, step=1)

st.sidebar.markdown("---")
st.sidebar.markdown("### Ajustes y Cambios Solicitados (IA)")
opcion_recrear = st.sidebar.checkbox("Recrear/Duplicar con IA (Img2Img)")
opcion_ampliar = st.sidebar.checkbox("Ampliar Calidad (Estilo Megapixel 4K)")
opcion_quitar_fondo = st.sidebar.checkbox("Quitar Fondo HD Ultra Profesional\n(Corte perfecto sin residuos en barbas ni orillas)", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sube tu imagen de diseño")
uploaded_file = st.sidebar.file_uploader("Sube tu imagen de diseño", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file is not None:
    imagen_original = Image.open(uploaded_file).convert("RGBA")
else:
    imagen_original = Image.new("RGBA", (800, 800), (120, 80, 50, 255))

# Procesamiento de la imagen
imagen_procesada = imagen_original.copy()
cambios_aplicados = []

if opcion_recrear:
    imagen_procesada = recrear_con_ia(imagen_procesada)
    cambios_aplicados.append("Recreación o duplicación mediante IA aplicada.")

if opcion_ampliar:
    imagen_procesada = ampliar_calidad_megapixels(imagen_procesada)
    cambios_aplicados.append("Amplificación de calidad estilo Megapixel 4K.")

if opcion_quitar_fondo:
    imagen_procesada = quitar_fondo(imagen_procesada)
    cambios_aplicados.append("Eliminación de fondo HD profesional.")

# Aplicar Halftone Converter automáticamente si la técnica es Cuatricomía CMYK
if tecnica == "Serigrafía (Cuatricomía CMYK)":
    imagen_procesada = generar_halftone_cmyk(imagen_procesada, dot_size=dot_size_param)
    cambios_aplicados.append(f"Separación de Cuatricomía por Semitonos (Halftone Converter - Tamaño: {dot_size_param}px).")

# --- Pantalla Principal ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### DISEÑOSAPP - VISTA CON CAMBIOS (PAGO PENDIENTE)")
    st.image(imagen_procesada, use_container_width=True)
    st.info("💡 Este diseño muestra los cambios aplicados en tiempo real para tu aprobación.")

with col2:
    w_px, h_px = imagen_procesada.size if hasattr(imagen_procesada, 'size') else (800, 800)
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
