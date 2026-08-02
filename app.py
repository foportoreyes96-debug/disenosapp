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
                
                # Conversión segura a RGB para evitar errores de canales
                bg = Image.new("RGB", img_resized.size, (255, 255, 255))
                if img_resized.mode == 'RGBA':
                    bg.paste(img_resized, mask=img_resized.split()[3])
                else:
                    bg.paste(img_resized)
                
                rgb_arr = np.array(bg).astype(float) / 255.0
                
                # Cálculo CMYK seguro
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
