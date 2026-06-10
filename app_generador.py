import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os
import re
import json
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Generador SEO Pro - Flux 2 Pro", 
    page_icon="🎨", 
    layout="wide"
)

# Inicializar historial en sesión
if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🎨 Generador SEO Pro - Flux 2 Pro")
st.markdown("""
Crea imágenes **profesionales, únicas y optimizadas** para Google SEO y AdSense.
Con prompts inteligentes, estilos personalizados y código HTML listo para WordPress.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("🔑 API Keys")
    
    # Replicate API Key
    try:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ Replicate API cargada")
    except Exception:
        replicate_api_key = st.text_input("Replicate API Token", type="password")
    
    if replicate_api_key:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    # Groq API Key (OPCIONAL - para prompts inteligentes)
    try:
        groq_api_key = st.secrets["GROQ_API_TOKEN"]
        st.success("✅ Groq API cargada (prompts IA)")
        use_groq = True
    except Exception:
        groq_api_key = st.text_input(
            "Groq API Token (opcional)", 
            type="password",
            help="Gratis en console.groq.com - Mejora la calidad de los prompts"
        )
        use_groq = bool(groq_api_key)
    
    st.markdown("---")
    st.header("🎛️ Parámetros")
    
    aspect_ratio = st.selectbox(
        "📐 Proporción:",
        options=["3:2", "16:9", "1:1", "4:3", "2:3", "9:16"],
        index=0
    )
    
    guidance_scale = st.slider("🎯 Fidelidad:", 2.0, 7.0, 3.5, 0.5)
    num_steps = st.slider("⚡ Pasos:", 14, 50, 28, 2)
    output_quality = st.slider("🖼️ Calidad WebP:", 70, 100, 90, 5)
    num_variants = st.selectbox("🎲 Variantes a generar:", [1, 2, 4], index=0)
    
    st.markdown("---")
    st.header("🎨 Estilo Visual")
    
    estilo = st.selectbox(
        "Estilo:",
        options=[
            "📸 Fotografía Profesional",
            "🎭 Ilustración 3D Moderna",
            "⚪ Minimalista / Flat",
            "📻 Vintage / Retro",
            "🎨 Acuarela Artística",
            "🤖 Tech / Futurista"
        ],
        index=0
    )
    
    # Mapeo de estilos a modificadores de prompt
    estilos_map = {
        "📸 Fotografía Profesional": "professional photography, DSLR, natural lighting, photorealistic, editorial style, sharp focus, high detail",
        "🎭 Ilustración 3D Moderna": "3D render, modern illustration, Pixar style, vibrant colors, soft shadows, clean shapes, trending on ArtStation",
        "⚪ Minimalista / Flat": "minimalist flat design, simple shapes, clean lines, vector art, soft pastel colors, negative space, modern",
        "📻 Vintage / Retro": "vintage photography, retro aesthetic, film grain, warm tones, nostalgic, 1970s style, analog film, faded colors",
        "🎨 Acuarela Artística": "watercolor painting, artistic, soft brushstrokes, delicate colors, hand-painted, elegant, fine art",
        "🤖 Tech / Futurista": "futuristic, cyberpunk aesthetic, neon lights, high-tech, sleek design, digital art, sci-fi concept"
    }
    
    estilo_prompt = estilos_map[estilo]
    
    # Estimación de coste
    coste_estimado = 0.05 * num_variants
    st.info(f"💰 Coste estimado: **${coste_estimado:.2f}** ({num_variants} imágenes)")

# --- Funciones ---

def generar_prompt_con_groq(titulo, estilo, api_key):
    """Usa Groq (LLM gratuito) para crear un prompt único y profesional"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"""Eres un experto en dirección de arte y SEO. 
Crea un prompt en INGLÉS para generar una imagen de blog profesional.

Título del artículo: {titulo}
Estilo visual deseado: {estilo}

Reglas:
- Máximo 150 palabras
- Solo el prompt, sin explicaciones
- Debe ser visual, descriptivo y profesional
- Evita texto, logos o marcas
- Añade detalles de iluminación, composición y atmósfera
"""
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Crea el prompt para: {titulo}"}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        return None
    except Exception as e:
        st.warning(f"⚠️ Error con Groq, usando prompt base: {str(e)}")
        return None

def crear_prompt_seo(titulo, estilo_prompt, use_groq, groq_api_key):
    """Crea prompt base o inteligente con Groq"""
    
    if use_groq and groq_api_key:
        prompt_inteligente = generar_prompt_con_groq(titulo, estilo, groq_api_key)
        if prompt_inteligente:
            prompt = f"{prompt_inteligente}. {estilo_prompt}, 8k resolution, clean composition, no text, no watermarks"
            negative_prompt = (
                "text, watermark, signature, logo, blurry, deformed, distorted, "
                "low quality, ugly, bad anatomy, oversaturated, messy background, "
                "extra limbs, amateur, grainy, words, letters, writing"
            )
            return prompt, negative_prompt, True  # True = usó Groq
    
    # Prompt base (si no hay Groq)
    prompt = (
        f"Professional blog header image about: {titulo}. "
        f"{estilo_prompt}. "
        "Ultra high quality, cinematic lighting, 8k resolution, highly detailed, "
        "sharp focus, modern aesthetic, clean composition, no text, no watermarks"
    )
    negative_prompt = (
        "text, watermark, signature, logo, blurry, deformed, distorted, "
        "low quality, ugly, bad anatomy, oversaturated, cartoonish, messy background"
    )
    return prompt, negative_prompt, False

def generar_imagen(prompt, negative_prompt, aspect_ratio, guidance_scale, 
                   num_steps, output_quality, output_format, num_variants):
    """Genera una o varias imágenes"""
    try:
        output = replicate.run(
            "black-forest-labs/flux-2-pro",
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": aspect_ratio,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_steps,
                "output_quality": output_quality,
                "output_format": output_format,
                "num_outputs": num_variants
            }
        )
        
        # Manejar FileOutput o lista
        urls = []
        if isinstance(output, list):
            for item in output:
                if hasattr(item, 'url'):
                    urls.append(item.url)
                else:
                    urls.append(str(item))
        elif hasattr(output, 'url'):
            urls.append(output.url)
        else:
            urls.append(str(output))
        
        return urls
    except Exception as e:
        st.error(f"❌ Error al generar: {str(e)}")
        return None

def optimizar_imagen(image_url, titulo, output_format):
    """Descarga y optimiza"""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        format_map = {"webp": "WEBP", "jpg": "JPEG", "png": "PNG"}
        mime_map = {"webp": "image/webp", "jpg": "image/jpeg", "png": "image/png"}
        
        img_byte_arr = io.BytesIO()
        save_kwargs = {"format": format_map[output_format], "optimize": True}
        if output_format != "png":
            save_kwargs["quality"] = 85
        
        img.save(img_byte_arr, **save_kwargs)
        img_byte_arr.seek(0)
        
        slug = re.sub(r'[^\w\s-]', '', titulo.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        filename = f"{slug[:50]}.{output_format}"
        alt_text = f"Imagen profesional sobre {titulo.lower()}"
        size_kb = len(img_byte_arr.getvalue()) / 1024
        
        return img_byte_arr.getvalue(), filename, alt_text, mime_map[output_format], size_kb
    except Exception as e:
        st.error(f"❌ Error optimizando: {str(e)}")
        return None, None, None, None, 0

def generar_html_wordpress(filename, alt_text, titulo, width=1200):
    """Genera código HTML optimizado para WordPress"""
    html = f'''<figure class="wp-block-image size-full">
    <img src="/wp-content/uploads/{filename}" 
         alt="{alt_text}" 
         title="{titulo}"
         width="{width}"
         loading="lazy"
         decoding="async"
         class="wp-image-XXXXX"/>
    <figcaption class="wp-element-caption">{titulo}</figcaption>
</figure>'''
    return html

# --- Interfaz Principal ---
titulo_articulo = st.text_input(
    "📝 Título del artículo:", 
    placeholder="Ej: Las 10 mejores estrategias de marketing digital para 2024",
    help="Un título descriptivo genera mejores imágenes"
)

if st.button("🚀 Generar Imágenes", type="primary", use_container_width=True):
    if not replicate_api_key:
        st.error("❌ Introduce tu API Key de Replicate")
        st.stop()
    
    if not titulo_articulo.strip():
        st.warning("⚠️ Escribe un título")
        st.stop()
    
    with st.spinner(f"🎨 Generando {num_variants} imagen(es)..."):
        prompt, negative_prompt, uso_groq = crear_prompt_seo(
            titulo_articulo, estilo_prompt, use_groq, groq_api_key
        )
        
        if uso_groq:
            st.info(f"🧠 **Prompt generado con IA (Groq):** {prompt[:200]}...")
        
        image_urls = generar_imagen(
            prompt, negative_prompt, aspect_ratio, guidance_scale,
            num_steps, output_quality, "webp", num_variants
        )
        
        if not image_urls:
            st.error("❌ No se generaron imágenes")
            st.stop()
        
        st.success(f"✅ ¡{len(image_urls)} imagen(es) generada(s)!")
        
        # Mostrar resultados
        cols = st.columns(len(image_urls))
        resultados = []
        
        for idx, (col, url) in enumerate(zip(cols, image_urls)):
            with col:
                st.image(url, caption=f"🖼️ Variante {idx+1}", use_container_width=True)
                
                img_bytes, filename, alt_text, mime_type, size_kb = optimizar_imagen(
                    url, titulo_articulo, "webp"
                )
                
                if img_bytes:
                    resultados.append({
                        'url': url,
                        'bytes': img_bytes,
                        'filename': filename,
                        'alt_text': alt_text,
                        'size_kb': size_kb,
                        'mime_type': mime_type
                    })
                    
                    st.download_button(
                        label=f"📥 Descargar v{idx+1}",
                        data=img_bytes,
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True,
                        key=f"download_{idx}_{datetime.now().timestamp()}"
                    )
        
        # Panel de metadatos SEO (para la primera variante)
        if resultados:
            st.markdown("---")
            st.subheader("📊 Metadatos SEO (Variant 1)")
            
            res = resultados[0]
            
            tab1, tab2, tab3 = st.tabs(["📁 Archivo", "🏷️ Alt Text", "💻 HTML WordPress"])
            
            with tab1:
                st.code(res['filename'], language="text")
                st.info(f"⚖️ Peso: **{res['size_kb']:.2f} KB**")
            
            with tab2:
                st.code(res['alt_text'], language="text")
            
            with tab3:
                html_code = generar_html_wordpress(res['filename'], res['alt_text'], titulo_articulo)
                st.code(html_code, language="html")
                st.caption("📋 Copia y pega directamente en WordPress (editor HTML)")
            
            # Guardar en historial
            st.session_state.history.append({
                'titulo': titulo_articulo,
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'estilo': estilo,
                'variantes': len(resultados),
                'resultados': resultados
            })

# --- Historial ---
if st.session_state.history:
    st.markdown("---")
    with st.expander(f"📚 Historial de generaciones ({len(st.session_state.history)} entradas)", expanded=False):
        for idx, entry in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**{entry['fecha']}** - *{entry['titulo']}*")
            st.caption(f"Estilo: {entry['estilo']} | Variantes: {entry['variantes']}")
            st.markdown("---")
        
        if st.button("🗑️ Limpiar historial"):
            st.session_state.history = []
            st.rerun()
