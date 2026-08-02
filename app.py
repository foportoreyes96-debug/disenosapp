import streamlit as st
from PIL import Image
import numpy as np
import io

# Configuración inicial de la app
st.set_page_config(
    page_title="Separación CMYK por Partes",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 Parte 1: Separación de Cuatricomía (CMYK)")
st.markdown("Sube tu diseño para obtener los canales individuales de Cian, Magenta, Amarillo y Negro.")

# Subida de imagen
archivo_subido = st.file_uploader("Sube tu imagen de diseño", type=["png", "jpg", "jpeg"])

if archivo_subido is not None:
    imagen_original = Image.open(archivo_subido)
    
    # Mostrar original
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Imagen Original")
        st.image(imagen_original, use_container_width=True)
        
    # Procesar conversión a CMYK plano
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

    with col2:
        st.subheader("Estado")
        st.success("¡Canales CMYK separados correctamente!")

    st.divider()
    st.subheader("📥 Canales Planos Individuales")
    
    cols = st.columns(4)
    nombres_canales = ['Cian', 'Magenta', 'Amarillo', 'Negro']
    
    for i, nombre in enumerate(nombres_canales):
        with cols[i]:
            st.markdown(f"**Canal {nombre}**")
            matriz_img = canales[nombre]
            # Invertimos visualmente para que se vea como negativo/positivo impreso si se prefiere, 
            # o se muestra directo. Aquí lo mostramos en escala de grises directa:
            st.image(matriz_img, use_container_width=True, clamp=True)
            
            # Botón de descarga
            buf = io.BytesIO()
            Image.fromarray(matriz_img).save(buf, format="PNG")
            st.download_button(
                label=f"Descargar {nombre}",
                data=buf.getvalue(),
                file_name=f"canal_{nombre.lower()}.png",
                mime="image/png",
                key=f"btn_{nombre}"
            )
else:
    st.info("Sube una imagen para probar esta primera parte.")
