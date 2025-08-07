from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
import matplotlib.pyplot as plt
import re

# Configuración inicial
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
st.set_page_config(page_title="Nutriólogo Virtual", page_icon="🍽️")

# Funciones GEMINI y visuales
def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input, image[0], prompt])
    return response.text

def input_image_setup(uploaded_file):
    if uploaded_file:
        bytes_data = uploaded_file.getvalue()
        return [{"mime_type": uploaded_file.type, "data": bytes_data}]
    raise FileNotFoundError("No se subió archivo")

def mostrar_grafico_platometro(carbs, proteins, fats):
    labels = ['Carbohidratos', 'Proteínas', 'Grasas']
    sizes = [carbs, proteins, fats]
    colors = ['#F4D03F', '#58D68D', '#EC7063']
    explode = (0.05, 0.05, 0.05)
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

def extraer_macros(texto):
    carbs = proteins = fats = 0
    patterns = {
        "carbs": r"(carbohidratos|carbohydrates).*?(\d{1,3})\s?%",
        "proteins": r"(proteínas|proteins).*?(\d{1,3})\s?%",
        "fats": r"(grasas|fats).*?(\d{1,3})\s?%",
    }
    for macro, pattern in patterns.items():
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            value = int(match.group(2))
            if macro == "carbs": carbs = value
            elif macro == "proteins": proteins = value
            elif macro == "fats": fats = value
    total = carbs + proteins + fats
    return (carbs, proteins, fats) if total > 0 else (50, 30, 20)

def calcular_calorias_recomendadas(sexo, edad, peso, altura, actividad):
    if sexo == "Hombre":
        bmr = 10 * peso + 6.25 * altura - 5 * edad + 5
    else:
        bmr = 10 * peso + 6.25 * altura - 5 * edad - 161
    factores = {
        "Sedentario": 1.2, "Actividad ligera": 1.375,
        "Moderado": 1.55, "Activo": 1.725, "Muy activo": 1.9
    }
    return int(bmr * factores[actividad])

def clasificar_imc(imc):
    if imc < 18.5: return "Bajo peso"
    elif imc < 25: return "Normal"
    elif imc < 30: return "Sobrepeso"
    else: return "Obesidad"

# Prompts
input_prompt1 = """Analiza la imagen cargada del platillo:
1. Nombre del platillo y su esencia culinaria.
2. Origen cultural o histórico.
3. Ingredientes principales."""
input_prompt2 = """Como chef experto, proporciona receta paso a paso:
1. Selección de ingredientes.
2. Preparación (lavado, corte).
3. Cocción detallada.
4. Consejos del chef."""
input_prompt3 = """Como asesor nutricional:
1. Muestra una tabla con calorías, proteínas, grasas y carbohidratos.
2. Otra tabla por ingrediente.
3. Indica porcentajes de carbohidratos, proteínas y grasas."""
input_prompt4 = """Sugiere:
1. 2 platillos vegetarianos con valor nutricional similar.
2. 2 platillos no vegetarianos equivalentes."""

# Estado de navegación
if 'page' not in st.session_state:
    st.session_state.page = 'menu'

def boton_volver():
    if st.button("🏠 Volver al menú principal"):
        st.session_state.page = 'menu'

# Páginas
def menu_principal():
    st.title("🍽️ Nutriólogo Virtual")
    st.subheader("Selecciona una opción:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🍽 Escanear platillo"):
            st.session_state.page = 'escanear'
    with col2:
        if st.button("🧮 Calculadora de salud"):
            st.session_state.page = 'calculadora'
    with col3:
        if st.button("🍳 Crear receta"):
            st.session_state.page = 'crear_receta'

def pagina_escanear():
    st.title("🍽 Escanear Platillo")
    uploaded_file = st.file_uploader("Sube una imagen del platillo", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(Image.open(uploaded_file), caption="Imagen cargada", use_column_width=True)
        user_input = st.text_input("Instrucción personalizada (opcional):", key="input_escanear")

        col1, col2 = st.columns(2)
        if col1.button("📛 Nombre e Ingredientes"):
            content = input_image_setup(uploaded_file)
            st.write(get_gemini_response(input_prompt1, content, user_input))
        if col2.button("👨‍🍳 Cómo cocinarlo"):
            content = input_image_setup(uploaded_file)
            st.write(get_gemini_response(input_prompt2, content, user_input))
        if col1.button("🍽 Platómetro"):
            content = input_image_setup(uploaded_file)
            response = get_gemini_response(input_prompt3, content, "")
            st.write(response)
        if col2.button("🥗 Alternativas similares"):
            content = input_image_setup(uploaded_file)
            st.write(get_gemini_response(input_prompt4, content, user_input))
    else:
        st.warning("🔺 Por favor, sube una imagen para comenzar.")
    boton_volver()

def pagina_calculadora():
    st.title("🧮 Calculadora de Salud")
    sexo = st.radio("Sexo:", ["Hombre", "Mujer"])
    edad = st.number_input("Edad (años):", min_value=10, max_value=100, value=25)
    altura = st.number_input("Altura (cm):", min_value=100, max_value=250, value=170)
    peso = st.number_input("Peso (kg):", min_value=30, max_value=200, value=70)
    actividad = st.selectbox("Nivel de actividad física:", [
        "Sedentario", "Actividad ligera", "Moderado", "Activo", "Muy activo"
    ])
    if st.button("Calcular"):
        imc = peso / ((altura / 100) ** 2)
        estado = clasificar_imc(imc)
        calorias = calcular_calorias_recomendadas(sexo, edad, peso, altura, actividad)
        st.success(f"✅ Tu IMC es: {imc:.2f} → Estado: **{estado}**")
        st.info(f"🔥 Calorías recomendadas por día: **{calorias} kcal**")
    boton_volver()

def pagina_crear_receta():
    st.title("🍳 Crear receta con tus ingredientes")
    ingredientes = st.text_area("📋 Escribe los ingredientes que tienes (separados por comas)")
    if st.button("Crear receta"):
        prompt = f"""Actúa como chef creativo. Tienes los siguientes ingredientes: {ingredientes}.
        Crea una receta completa, indicando:
        1. Nombre del platillo.
        2. Preparación paso a paso.
        3. Tiempo aproximado.
        4. Tips adicionales."""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.write(response.text)
    boton_volver()

# Controlador de navegación
if st.session_state.page == 'menu':
    menu_principal()
elif st.session_state.page == 'escanear':
    pagina_escanear()
elif st.session_state.page == 'calculadora':
    pagina_calculadora()
elif st.session_state.page == 'crear_receta':
    pagina_crear_receta()
