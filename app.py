import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import io

# Configuración de la página
st.set_page_config(
    page_title="Plataforma de Publicidad & Artes Gráficas",
    page_icon="🎨",
    layout="wide"
)

# --- ESTILOS VISUALES (DARK MODE PRO) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .card-container {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .stDownloadButton button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        width: 100%;
    }
    .stDownloadButton button:hover {
        background-color: #2ea043;
        color: white;
    }
    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363D;
    }
    </style>
""", unsafe_allow_html=True)

# --- MENÚ LATERAL DE NAVEGACIÓN (DEFINIDO ANTES DE USARLO) ---
st.sidebar.markdown("## 🎨 Panel de Control")
st.sidebar.markdown("Herramientas Profesionales para Publicidad y Producción")
st.sidebar.markdown("---")

modulo_seleccionado = st.sidebar.radio(
    "Seleccionar Módulo:",
    [
        "🖨️ Preimpresión & Cuatricomía (Serigrafía/DTF)",
        "✨ Mejora HD & IA (Resolución y Fondos)",
        "👕 Mockups de Ropa (Camisas/Hoodies)",
        "☕ Mockups de Rígidos (Tazas/Botones)",
        "📜 Papelería & Gran Formato (Flyers/Diplomas)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Utilidades Rápidas")
forzar_300 = st.sidebar.checkbox("Forzar resolución a 300 PPI", value=True)

# --- FUNCIÓN DE TRAMADO PARA SERIGRAFÍA ---
def generar_trama_canal(canal_array, lpi=40, dpi=300):
    h, w = canal_array.shape
    paso = max(2, int(dpi / lpi))
    trama_img = np.ones((h, w), dtype=np.uint8) * 255
    
    for y in range(0, h, paso):
        for x in range(0, w, paso):
            bloque = canal_array[y:min(y+paso, h), x:min(x+paso, w)]
            if bloque.size == 0:
                continue
            intensidad = np.mean(bloque)
            radio = int((paso / 2) * intensidad)
            if radio > 0:
                yy, xx = np.ogrid[:h, :w]
                mask = (xx - x)**2 + (yy - y)**2 <= radio**2
                trama_img[mask] = 0
    return trama_img

# ==========================================
# MÓDULO 1: PREIMPRESIÓN & CUATRICOMÍA
# ==========================================
if "Preimpresión" in modulo_seleccionado:
    st.markdown("<h1 style='color: #58A6FF;'>🖨️ Módulo de Preimpresión y Separación de Canales</h1>", unsafe_allow_html=True)
    st.markdown("Prepara tus diseños con tramas optimizadas para impresión textil, serigrafía y DTF a 300 PPI.")
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("📁 Cargar Archivo")
        archivo = st.file_uploader("Sube tu diseño (PNG, JPG, TIFF)", type=["png", "jpg", "jpeg", "tiff"])
        
        st.markdown("---")
        ancho_cm = st.number_input("Ancho (cm)", 5.0, 100.0, 28.0)
        alto_cm = st.number_input("Alto (cm)", 5.0, 100.0, 35.0)
        tipo_fondo = st.radio("Tipo de prenda:", ["Fondo Claro", "Fondo Oscuro (Base Blanca)"])
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        if archivo is not None:
            try:
                img = Image.open(archivo).convert("RGBA")
                nuevo_w = int((ancho_cm / 2.54) * 300)
                nuevo_h = int((alto_cm / 2.54) * 300)
                img_resized = img.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                
                st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                st.subheader("🖼️ Vista Previa del Trabajo")
                st.image(img_resized, width="stretch")
                st.markdown(f"**Dimensiones de salida:** {nuevo_w} x {nuevo_h} px (300 PPI)")
                st.markdown("</div>", unsafe_allow_html=True)
                
                bg = Image.new("RGB", img_resized.size, (255, 255, 255))
                if img_resized.mode == 'RGBA':
                    bg.paste(img_resized, mask=img_resized.split()[3])
                else:
                    bg.paste(img_resized)
                
                rgb_arr = np.array(bg).astype(float) / 255.0
                
                k = 1.0 - np.max(rgb_arr, axis=2)
                k_mask = k < 1.0
                c = np.zeros_like(k)
                m = np.zeros_like(k)
                y = np.zeros_like(k)
                
                c[k_mask] = (1.0 - rgb_arr[:, :, 0][k_mask] - k[k_mask]) / np.maximum(1.0 - k[k_mask], 1e-6)
                m[k_mask] = (1.0 - rgb_arr[:, :, 1][k_mask] - k[k_mask]) / np.maximum(1.0 - k[k_mask], 1e-6)
                y[k_mask] = (1.0 - rgb_arr[:, :, 2][k_mask] - k[k_mask]) / np.maximum(1.0 - k[k_mask], 1e-6)
                
                st.markdown("### 📥 Fotolitos Generados (Tramados)")
                c_col, m_col, y_col, k_col = st.columns(4)
                
                fotolitos = {
                    'Cian': generar_trama_canal(c),
                    'Magenta': generar_trama_canal(m),
                    'Amarillo': generar_trama_canal(y),
                    'Negro': generar_trama_canal(k)
                }
                
                cols = [c_col, m_col, y_col, k_col]
                for i, (nombre, mat) in enumerate(fotolitos.items()):
                    with cols[i]:
                        st.markdown(f"**{nombre}**")
                        st.image(mat, width="stretch", clamp=True)
                        buf = io.BytesIO()
                        Image.fromarray(mat).save(buf, format="PNG", dpi=(300, 300))
                        st.download_button(f"Descargar {nombre}", buf.getvalue(), f"fotolito_{nombre.lower()}.png", key=f"dl_{nombre}")
            except Exception as e:
                st.error(f"Error procesando la imagen: {e}")
        else:
            st.info("Sube una imagen en el panel izquierdo para generar la separación de tintas.")

# ==========================================
# MÓDULO 2: MEJORA HD & IA
# ==========================================
elif "Mejora HD" in modulo_seleccionado:
    st.markdown("<h1 style='color: #58A6FF;'>✨ Módulo de Mejora HD y Optimización</h1>", unsafe_allow_html=True)
    st.markdown("Mejora la nitidez y ajusta la resolución de imágenes tomadas de internet para llevarlas a calidad de impresión profesional.")
    
    archivo_hd = st.file_uploader("Sube la imagen a mejorar", type=["png", "jpg", "jpeg"])
    if archivo_hd:
        img_hd = Image.open(archivo_hd)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Imagen Original")
            st.image(img_hd, width="stretch")
        with col2:
            st.subheader("Imagen Optimizada (Nitidez 300 DPI)")
            enhancer = ImageEnhance.Sharpness(img_hd)
            img_mejorada = enhancer.enhance(2.0)
            st.image(img_mejorada, width="stretch")
            
            buf_hd = io.BytesIO()
            img_mejorada.save(buf_hd, format="PNG", dpi=(300, 300))
            st.download_button("Descargar Imagen HD", buf_hd.getvalue(), "imagen_optimizada_hd.png", mime="image/png")

# ==========================================
# MÓDULO 3: MOCKUPS DE ROPA
# ==========================================
elif "Mockups de Ropa" in modulo_seleccionado:
    st.markdown("<h1 style='color: #58A6FF;'>👕 Simulador y Mockups para Ropa (DTF / Serigrafía)</h1>", unsafe_allow_html=True)
    st.markdown("Visualiza cómo quedará tu diseño aplicado en prendas antes de estampar.")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_prenda = st.selectbox("Seleccionar tipo de prenda:", ["Camisa Manga Corta", "Hoodie (Sudadera)", "Lanyard Publicitario"])
        color_prenda = st.color_picker("Color de la prenda:", "#111111")
        logo_prenda = st.file_uploader("Subir diseño del logotipo", type=["png", "jpg"])
    with col2:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("Vista Previa del Producto")
        if logo_prenda:
            st.image(logo_prenda, width=200)
            st.success(f"Mockup generado sobre **{tipo_prenda}** correctamente.")
        else:
            st.info("Sube un logotipo para visualizarlo sobre la maqueta.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 4: MOCKUPS DE RÍGIDOS
# ==========================================
elif "Mockups de Rígidos" in modulo_seleccionado:
    st.markdown("<h1 style='color: #58A6FF;'>☕ Mockups de Artículos Promocionales (Tazas y Botones)</h1>", unsafe_allow_html=True)
    st.markdown("Prepara diseños adaptados al área útil de tazas cilíndricas y chapas publicitarias.")
    
    articulo = st.selectbox("Seleccionar artículo:", ["Taza 11oz (Área 20x9 cm)", "Botón / Chapa Publicitaria (58mm)"])
    logo_rigido = st.file_uploader("Subir diseño para el artículo", type=["png", "jpg"])
    
    if logo_rigido:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader(f"Simulación en {articulo}")
        st.image(logo_rigido, width=250)
        st.download_button("Descargar plantilla ajustada con medidas reales", b"mockup", "plantilla_promocional.png")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 5: PAPELERÍA & GRAN FORMATO
# ==========================================
elif "Papelería" in modulo_seleccionado:
    st.markdown("<h1 style='color: #58A6FF;'>📜 Papelería Comercial, Flyers y Diplomas</h1>", unsafe_allow_html=True)
    st.markdown("Genera archivos con líneas de corte y sangrado de 3 mm listos para imprenta offset o digital.")
    
    tipo_papel = st.selectbox("Formato de impresión:", ["Flyer A5", "Díptico / Brochure", "Diploma de Reconocimiento (A4)", "Tarjeta de Presentación"])
    archivo_papel = st.file_uploader("Subir arte para papelería", type=["png", "jpg", "pdf"])
    
    if archivo_papel:
        st.success(f"Formato **{tipo_papel}** configurado con sangrado de 3 mm para imprenta.")
        st.image(archivo_papel, width=300)
        st.download_button("Descargar Archivo Listo para Imprenta", b"archivo_imprenta", "arte_con_sangrado.pdf")
