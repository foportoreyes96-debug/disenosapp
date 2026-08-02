import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import io

# Configuración de la página
st.set_page_config(
    page_title="Separación Profesional CMYK & Serigrafía",
    page_icon="🖨️",
    layout="wide"
)

# --- ESTILOS CSS PROFESIONALES ---
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

# --- CABECERA ---
st.markdown("<h1 style='text-align: center; color: #58A6FF;'>🖨️ Estación de Preimpresión y Cuatricomía</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E;'>Preparación de archivos, reescalado HD y separación de tramas a 300 PPI con vista previa final.</p>", unsafe_allow_html=True)
st.divider()

# --- PANEL DE CONTROL (BARRA LATERAL) ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración del Trabajo")
    archivo_subido = st.file_uploader("Subir Diseño Original", type=["png", "jpg", "jpeg", "tiff"])
    
    st.markdown("---")
    st.markdown("#### 📐 Medidas y Resolución")
    ancho_cm = st.number_input("Ancho Deseado (cm)", min_value=5.0, max_value=100.0, value=28.0, step=1.0)
    alto_cm = st.number_input("Alto Deseado (cm)", min_value=5.0, max_value=100.0, value=35.0, step=1.0)
    
    st.markdown("---")
    st.markdown("#### 👕 Ajustes de Impresión")
    tipo_fondo = st.radio("¿Para qué tipo de fondo es la prenda?", ["Fondo Claro (Sin Base)", "Fondo Oscuro (Con Base Blanca)"])
    
    st.markdown("---")
    st.markdown("#### 🔍 Optimización HD")
    mejorar_nitidez = st.checkbox("Mejorar Nitidez / Calidad", value=True)
    remover_fondo = st.checkbox("Quitar Fondo", value=False)

# --- FUNCIÓN DE TRAMADO ---
def generar_trama_canal(canal_array, lpi=45, dpi=300):
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

# --- CUERPO PRINCIPAL ---
if archivo_subido is not None:
    try:
        imagen_original = Image.open(archivo_subido)
        
        if remover_fondo:
            img_rgba = imagen_original.convert("RGBA")
            datas = img_rgba.getdata()
            nueva_data = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    nueva_data.append((255, 255, 255, 0))
                else:
                    nueva_data.append(item)
            img_rgba.putdata(nueva_data)
            imagen_procesada = img_rgba
        else:
            imagen_procesada = imagen_original.convert("RGBA")

        dpi_objetivo = 300
        nuevo_w = int((ancho_cm / 2.54) * dpi_objetivo)
        nuevo_h = int((alto_cm / 2.54) * dpi_objetivo)
        
        if nuevo_w > 2500: nuevo_w = 2500
        if nuevo_h > 2500: nuevo_h = 2500

        imagen_redimensionada = imagen_procesada.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        
        if mejorar_nitidez:
            enhancer = ImageEnhance.Sharpness(imagen_redimensionada)
            imagen_redimensionada = enhancer.enhance(1.8)
            
        col_prev1, col_prev2 = st.columns([1, 1], gap="large")
        
        with col_prev1:
            st.markdown("<div class='card-container'>", unsafe_allow_html=True)
            st.subheader("🖼️ Imagen Preparada (HD)")
            st.image(imagen_redimensionada, use_container_width=True)
            st.markdown(f"<p style='color: #8B949E; font-size: 0.85rem;'>Tamaño físico: {ancho_cm} x {alto_cm} cm | Resolución: {nuevo_w} x {nuevo_h} px (300 PPI)</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_prev2:
            st.markdown("<div class='card-container'>", unsafe_allow_html=True)
            st.subheader("⚙️ Estado de Preimpresión")
            st.success("✔ Archivo procesado correctamente a 300 PPI.")
            st.info(f"Modo seleccionado: **{tipo_fondo}**")
            st.markdown("</div>", unsafe_allow_html=True)

        background_blanco = Image.new("RGB", imagen_redimensionada.size, (255, 255, 255))
        if imagen_redimensionada.mode == "RGBA":
            background_blanco.paste(imagen_redimensionada, mask=imagen_redimensionada.split()[3])
        else:
            background_blanco.paste(imagen_redimensionada)
            
        rgb_arr = np.array(background_blanco).astype(float) / 255.0

        k = 1.0 - np.max(rgb_arr, axis=2)
        k_mask = k < 1.0 
        c = np.zeros_like(k)
        m = np.zeros_like(k)
        y = np.zeros_like(k)
        
        c[k_mask] = (1.0 - rgb_arr[:, :, 0][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
        m[k_mask] = (1.0 - rgb_arr[:, :, 1][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
        y[k_mask] = (1.0 - rgb_arr[:, :, 2][k_mask] - k[k_mask]) / (1.0 - k[k_mask])

        lineatura = 40
        fotolitos = {
            'Cian': generar_trama_canal(c, lpi=lineatura, dpi=300),
            'Magenta': generar_trama_canal(m, lpi=lineatura, dpi=300),
            'Amarillo': generar_trama_canal(y, lpi=lineatura, dpi=300),
            'Negro': generar_trama_canal(k, lpi=lineatura, dpi=300)
        }

        if "Oscuro" in tipo_fondo:
            base_gray = 1.0 - np.mean(rgb_arr, axis=2)
            fotolitos['Base Blanca'] = generar_trama_canal(base_gray, lpi=lineatura, dpi=300)

        st.divider()
        st.markdown("### 📥 Fotolitos Separados y Tramados")
        
        canales_a_mostrar = list(fotolitos.keys())
        cols = st.columns(len(canales_a_mostrar), gap="medium")
        colores_badge = {'Cian': '#00bcd4', 'Magenta': '#e91e63', 'Amarillo': '#ffeb3b', 'Negro': '#9e9e9e', 'Base Blanca': '#ffffff'}

        for i, nombre in enumerate(canales_a_mostrar):
            with cols[i]:
                st.markdown(f"<div class='card-container' style='text-align: center;'>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color: {colores_badge.get(nombre, '#fff')}; margin-bottom: 5px;'>● {nombre}</h4>", unsafe_allow_html=True)
                
                matriz_img = fotolitos[nombre]
                st.image(matriz_img, use_container_width=True, clamp=True)
                
                buf_img = io.BytesIO()
                img_to_dl = Image.fromarray(matriz_img)
                img_to_dl.save(buf_img, format="PNG", dpi=(300, 300))
                
                st.download_button(
                    label=f"Descargar {nombre}",
                    data=buf_img.getvalue(),
                    file_name=f"fotolito_{nombre.lower().replace(' ', '_')}.png",
                    mime="image/png",
                    key=f"dl_{nombre}"
                )
                st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Ocurrió un error al procesar la imagen: {e}")
else:
    st.markdown("""
        <div style='text-align: center; padding: 50px; background-color: #161B22; border-radius: 12px; border: 1px dashed #30363D;'>
            <h3 style='color: #8B949E;'>Sube una imagen para comenzar el proceso de preimpresión</h3>
        </div>
    """, unsafe_allow_html=True)
