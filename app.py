import os
import re
import requests
from flask import Flask, request, jsonify, send_from_directory, render_template
from dotenv import load_dotenv
import dashscope
from dashscope import Application

# Cargar variables del archivo .env
load_dotenv()

# Configuración de la API de Qwen
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
app_id = os.getenv("DASHSCOPE_APP_ID")

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Carpeta donde se guardarán las imágenes generadas
IMAGE_FOLDER = 'static'
LAST_IMAGE_FOLDER = 'last_image'
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(LAST_IMAGE_FOLDER, exist_ok=True)

@app.route('/')
def home():
    """Sirve la página principal."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_comic():
    """Genera un cómic basado en 7 prompts."""
    data = request.json
    prompts = data.get('prompts')

    if not prompts or len(prompts) != 7:
        return jsonify({"error": "Debes proporcionar exactamente 7 prompts."}), 400

    image_urls = []
    last_image_path = None

    for i, prompt in enumerate(prompts):
        # Verificar si hay una última imagen para usar como referencia
        reference_image = None
        if last_image_path and os.path.exists(last_image_path):
            reference_image = last_image_path

        # Llamada a la API de Qwen
        response = Application.call(
            app_id=app_id,
            prompt=f"En estilo de cómic genera la siguiente escena: {prompt}",
            reference_image=reference_image,  # Proporcionar la última imagen como referencia
            seed=42
        )

        if response.status_code != 200:
            return jsonify({"error": "Error en la API", "message": response.message}), response.status_code

        # Extraer la URL de la imagen
        output_text = response.output.get('text', '')
        match = re.search(r'!\[.*\]\((https?://[^\)]+)\)', output_text)
        if match:
            image_url = match.group(1)
            image_path = os.path.join(IMAGE_FOLDER, f'comic_panel_{i + 1}.png')
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                image_urls.append(f"/static/comic_panel_{i + 1}.png")

                # Guardar esta imagen como la última generada
                last_image_path = os.path.join(LAST_IMAGE_FOLDER, 'last_image.png')
                with open(last_image_path, 'wb') as f:
                    f.write(img_response.content)
            else:
                return jsonify({"error": "No se pudo descargar la imagen"}), 500
        else:
            return jsonify({"error": "No se encontró imagen en la respuesta"}), 500

    return jsonify({"images": image_urls})

if __name__ == '__main__':
    app.run(debug=True)