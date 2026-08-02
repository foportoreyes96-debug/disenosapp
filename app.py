import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
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
st.markdown("<p style='text-align: center; color: #8B949E;'>Preparación de archivos, reescalado HD, remoción de fondo y separación de tramas a 300 PPI.</p>", unsafe_allow_html=True)
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
    mejorar_nitidez = st.checkbox("Mejorar Nitidez / Calidad (Estilo Megapíxel)", value=True)
    remover_fondo = st.checkbox("Quitar Fondo Automático (Hacer PNG Transparente)", value=True)

# --- FUNCIÓN PARA GENERAR TRAMAS DE SEMITONOS (HALFTONE) ---
def generar_trama_canal(canal_array, lpi=45, dpi=300, angulo=0):
    h, w = canal_array.shape
    grid_size = dpi / lpi
    
    y_coords, x_coords = np.mgrid[:h, :w]
    angle_rad = np.radians(angulo)
    
    x_rot = x_coords * np.cos(angle_rad) - y_coords * np.sin(angle_rad)
    y_rot = x_coords * np.sin(angle_rad) + y_coords * np.cos(angle_rad)
    
    # Matriz de semitonos basada en senos
    trama_matriz = (np.sin(2 * np.pi * x_rot / grid_size) + np.sin(2 * np.pi * y_rot / grid_size)) / 4.0 + 0.5
    trama_matriz = (trama_matriz * 255).astype(np.uint8)
    
    canal_gray = (canal_array * 255).astype(np.uint8)
    fotolito_binario = np.where(canal_gray > trama_matriz, 0, 255).astype(np.uint8)
    return fotolito_binario

# --- CUERPO PRINCIPAL ---
if archivo_subido is not None:
    imagen_original = Image.open(archivo_subido)
    
    # 1. Remoción de fondo básica (umbral de blancos)
    if remover_fondo:
        img_rgba = imagen_original.convert("RGBA")
        datas = img_rgba.getdata()
        nueva_data = []
        for item in datas:
            # Si el píxel es muy blanco, lo volvemos transparente
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                nueva_data.append((255, 255, 255, 0))
            else:
                nueva_data.append(item)
        img_rgba.putdata(nueva_data)
        imagen_procesada = img_rgba
    else:
        imagen_procesada = imagen_original.convert("RGBA")

    # 2. Reescalado a 300 PPI según medidas en cm (1 pulgada = 2.54 cm)
    dpi_objetivo = 300
    nuevo_w = int((ancho_cm / 2.54) * dpi_objetivo)
    nuevo_h = int((alto_cm / 2.54) * dpi_objetivo)
    
    # Redimensionar con alta calidad de interpolación (Simulando mejora de resolución)
    imagen_redimensionada = imagen_procesada.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
    
    if mejorar_nitidez:
        enhancer = ImageEnhance.Sharpness(imagen_redimensionada)
        imagen_redimensionada = enhancer.enhance(1.8)
        
    # Mostrar vista previa e información
    col_prev1, col_prev2 = st.columns([1, 1], gap="large")
    
    with col_prev1:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("🖼️ Imagen Preparada (HD)")
        st.image(imagen_redimensionada, use_container_width=True)
        st.markdown(f"<p style='color: #8B949E; font-size: 0.85rem;'>Tamaño físico configurado: {ancho_cm} x {alto_cm} cm | Resolución: {nuevo_w} x {nuevo_h} px (300 PPI)</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Botón para descargar el diseño limpio sin fondo en PNG
        buf_png = io.BytesIO()
        imagen_redimensionada.save(buf_png, format="PNG")
        st.download_button(
            label="📥 Descargar Diseño Limpio (PNG Sin Fondo)",
            data=buf_png.getvalue(),
            file_name="diseno_limpio_hd.png",
            mime="image/png"
        )

    with col_prev2:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.subheader("⚙️ Estado de Preimpresión")
        st.success("✔ Imagen escalada a 300 PPI correctamente.")
        st.info(f"Modo seleccionado: **{tipo_fondo}**")
        st.markdown("Los ángulos de trama aplicados están configurados bajo norma serigráfica:")
        st.markdown("- **Cian:** 15°\n- **Magenta:** 75°\n- **Amarillo:** 0°\n- **Negro:** 45°")
        if "Oscuro" in tipo_fondo:
            st.markdown("- **Base Blanca:** 22.5°")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- PROCESO DE SEPARACIÓN CMYK Y TRAMADO ---
    # Convertir a RGB sobre fondo blanco para la separación matemática
    background_blanco = Image.new("RGB", imagen_redimensionada.size, (255, 255, 255))
    background_blanco.paste(imagen_redimensionada, mask=imagen_redimensionada.split()[3])
    rgb_arr = np.array(background_blanco).astype(float) / 255.0

    # Fórmulas CMYK
    k = 1.0 - np.max(rgb_arr, axis=2)
    k_mask = k < 1.0 
    c = np.zeros_like(k)
    m = np.zeros_like(k)
    y = np.zeros_like(k)
    
    c[k_mask] = (1.0 - rgb_arr[:, :, 0][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    m[k_mask] = (1.0 - rgb_arr[:, :, 1][k_mask] - k[k_mask]) / (1.0 - k[k_mask])
    y[k_mask] = (1.0 - rgb_arr[:, :, 2][k_mask] - k[k_mask]) / (1.0 - k[k_mask])

    # Generar tramas (Halftone) con los ángulos solicitados a 45 LPI y 300 PPI
    lineatura = 45
    fotolitos = {
        'Cian': generar_trama_canal(c, lpi=lineatura, dpi=300, angulo=15),
        'Magenta': generar_trama_canal(m, lpi=lineatura, dpi=300, angulo=75),
        'Amarillo': generar_trama_canal(y, lpi=lineatura, dpi=300, angulo=0),
        'Negro': generar_trama_canal(k, lpi=lineatura, dpi=300, angulo=45)
    }

    if "Oscuro" in tipo_fondo:
        # Generar base blanca basada en la luminosidad general invertida
        base_gray = 1.0 - np.mean(rgb_arr, axis=2)
        fotolitos['Base Blanca'] = generar_trama_canal(base_gray, lpi=lineatura, dpi=300, angulo=22.5)

    st.divider()
    st.markdown("### 📥 Fotolitos Separados y Tramados (Listos para Impresión)")
    
    # Mostrar columnas dinámicamente según si hay base o no
    canales_a_mostrar = list(fotolitos.keys())
    cols = st.columns(len(canales_a_mostrar), gap="medium")
    colores_badge = {'Cian': '#00bcd4', 'Magenta': '#e91e63', 'Amarillo': '#ffeb3b', 'Negro': '#9e9e9e', 'Base Blanca': '#ffffff'}

    for i, nombre in enumerate(canales_a_mostrar):
        with cols[i]:
            st.markdown(f"<div class='card-container' style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color: {colores_badge.get(nombre, '#fff')}; margin-bottom: 5px;'>● {nombre}</h4>", unsafe_allow_html=True)
            
            matriz_img = fotolitos[nombre]
            st.image(matriz_img, use_container_width=True, clamp=True)
            
            # Botón de descarga en PNG con 300 DPI incrustados
            buf_img = io.BytesIO()
            img_to_dl = Image.fromarray(matriz_img)
            img_to_dl.save(buf_img, format="PNG", dpi=(300, 300))
            
            st.download_button(
                label=f"Descargar {nombre} (PNG)",
                data=buf_img.getvalue(),
                file_name=f"fotolito_{nombre.lower().replace(' ', '_')}.png",
                mime="image/png",
                key=f"dl_{nombre}"
            )
            
            # Botón de descarga en PDF para cada fotolito
            buf_pdf = io.BytesIO()
            img_to_dl.save(buf_pdf, format="PDF", resolution=300)
            st.download_button(
                label=f"Descargar {nombre} (PDF)",
                data=buf_pdf.getvalue(),
                file_name=f"fotolito_{nombre.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                key=f"dl_pdf_{nombre}"
            )
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; padding: 50px; background-color: #161B22; border-radius: 12px; border: 1px dashed #30363D;'>
            <h3 style='color: #8B949E;'>Sube una imagen para comenzar el proceso de preimpresión</h3>
            <p style='color: #484F58;'>Usa el panel izquierdo para cargar tu diseño, definir las medidas en cm y seleccionar el tipo de fondo.</p>
        </div>
    """, unsafe_allow_html=True)
