import streamlit as st
from PIL import Image
import numpy as np
import io

# Configuración de la página con diseño ancho
st.set_page_config(
    page_title="Separación CMYK Pro",
    page_icon="🎨",
    layout="wide"
)

# --- ESTILOS CSS PROFESIONALES Y ORIGINALES ---
st.markdown("""
    <style>
    /* Fondo general y tipografía */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Títulos principales con acento de diseño */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Tarjetas contenedoras personalizadas */
    .css-1r6slb0, .stExpander, div.stMarkdown {
        font-family: 'Inter', sans-serif;
    }
    
    .card-container {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    
    /* Estilo personalizado para botones de descarga */
    .stDownloadButton button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        width: 100%;
        transition: background-color 0.2s ease;
    }
    
    .stDownloadButton button:hover {
        background-color: #2ea043;
        color: white;
    }
    
    /* Ajustes en las barras laterales */
    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363D;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA DE LA APP ---
st.markdown("<h1 style='text-align: center; color: #58A6FF;'>⚡ Separación Profesional de Cuatricomía</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E; font-size: 1.1rem;'>Módulo 1: Extracción de canales CMYK planos con precisión de preimpresión.</p>", unsafe_allow_html=True)
st.divider()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🎛️ Panel de Control")
    st.markdown("---")
    archivo_subido = st.file_uploader("Cargar Archivo de Diseño", type=["png", "jpg", "jpeg", "tiff"])
    st.markdown("---")
    st.info("💡 **Consejo:** Utiliza imágenes en alta resolución con perfil sRGB para obtener los canales más limpios.")

# --- CUERPO PRINCIPAL ---
if archivo_subido is not None:
    imagen_original = Image.open(archivo_subido)
    
    # Contenedor para la imagen original y estado
    col_orig, col_info = st.columns([1.2, 1], gap="large")
    
    with col_orig:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("🖼️ Imagen Original")
        st.image(imagen_original, use_container_width=True)
        st.markdown(f"<p style='color: #8B949E; font-size: 0.85rem;'>Dimensiones: {imagen_original.size[0]} x {imagen_original.size[1]} px</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # Procesamiento CMYK
    if imagen_original.mode == "RGBA":
        background = Image.new("RGB", imagen_original.size, (255, 255, 255))
        background.paste(imagen_original, mask=imagen_original.split()[3])
        rgb = np.array(background).astype(float) / 255.0
    else:
        rgb = np.array(imagen_original.convert('RGB')).astype(float) / 255.0

    # Fórmulas de separación CMYK
    k = 1.0 - np.max(rgb, axis=2)
    k_mask = k < 1.0 
    c = np.zeros_like(k)
    m = np.zeros_like(k)
    y = np.zeros_like(k)
    
    c[k_mask] = (1.0 - rgb[:, :, 0][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    m[k_mask] = (1.0 - rgb[:, :, 1][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    y[k_mask] = (1.0 - rgb[:, :, 2][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    
    canales = {
        'Cian': (c * 255).astype(np.uint8),
        'Magenta': (m * 255).astype(np.uint8),
        'Amarillo': (y * 255).astype(np.uint8),
        'Negro': (k * 255).astype(np.uint8)
    }

    with col_info:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("⚙️ Estado del Proceso")
        st.success("✔ Conversión y separación completadas con éxito.")
        st.markdown("Los canales individuales han sido aislados matemáticamente listos para su revisión y exportación en escala de grises de alta fidelidad.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📥 Canales Planos Individuales")
    
    cols = st.columns(4, gap="medium")
    nombres_canales = ['Cian', 'Magenta', 'Amarillo', 'Negro']
    colores_badge = {'Cian': '#00bcd4', 'Magenta': '#e91e63', 'Amarillo': '#ffeb3b', 'Negro': '#9e9e9e'}
    
    for i, nombre in enumerate(nombres_canales):
        with cols[i]:
            st.markdown(f"<div class='card-container' style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color: {colores_badge[nombre]}; margin-bottom: 5px;'>● {nombre}</h4>", unsafe_allow_html=True)
            
            matriz_img = canales[nombre]
            st.image(matriz_img, use_container_width=True, clamp=True)
            
            # Botón de descarga estilizado
            buf = io.BytesIO()
            Image.fromarray(matriz_img).save(buf, format="PNG")
            st.download_button(
                label=f"Descargar {nombre}",
                data=buf.getvalue(),
                file_name=f"canal_{nombre.lower()}.png",
                mime="image/png",
                key=f"btn_{nombre}"
            )
            st.markdown("</div>", unsafe_allow_html=True)
else:
    # Estado vacío con diseño profesional
    st.markdown("""
        <div style='text-align: center; padding: 50px; background-color: #161B22; border-radius: 12px; border: 1px dashed #30363D;'>
            <h3 style='color: #8B949E;'>No hay ninguna imagen cargada</h3>
            <p style='color: #484F58;'>Utiliza el panel de la izquierda para subir un archivo y comenzar la separación.</p>
        </div>
    """, unsafe_allow_html=True)
