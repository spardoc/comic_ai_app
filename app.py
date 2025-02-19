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
os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.route('/')
def home():
    """Sirve la página principal."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_comic():
    """Genera un cómic basado en una historia."""
    data = request.json
    story = data.get('story')

    if not story:
        return jsonify({"error": "Debes proporcionar una historia."}), 400

    # Dividir la historia en 7 partes
    story_parts = [story[i:i + len(story) // 7] for i in range(0, len(story), len(story) // 7)]
    if len(story_parts) > 7:
        story_parts = story_parts[:7]

    image_urls = []
    for i, part in enumerate(story_parts):
        # Llamada a la API de Qwen
        response = Application.call(app_id=app_id, prompt=f"{part} en estilo cómic")

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
            else:
                return jsonify({"error": "No se pudo descargar la imagen"}), 500
        else:
            return jsonify({"error": "No se encontró imagen en la respuesta"}), 500

    return jsonify({"images": image_urls})

if __name__ == '__main__':
    app.run(debug=True)