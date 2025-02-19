import os
from flask import Flask, request, jsonify, send_from_directory
from dashscope import Application
import dashscope
import requests
import re
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Configuración de la API de Qwen
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
app_id = os.getenv("DASHSCOPE_APP_ID")

app = Flask(__name__)

# Carpeta donde se guardarán las imágenes generadas
IMAGE_FOLDER = 'static'
os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.route('/generate', methods=['POST'])
def generate_comic():
    """Genera una imagen basada en el prompt recibido"""
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "El prompt es requerido"}), 400

    # Llamada a la API de Qwen
    response = Application.call(app_id=app_id, prompt=prompt)

    if response.status_code != 200:
        return jsonify({"error": "Error en la API", "message": response.message}), response.status_code

    # Extraer la URL de la imagen
    output_text = response.output.get('text', '')
    match = re.search(r'!\[.*\]\((https?://[^\)]+)\)', output_text)

    if match:
        image_url = match.group(1)

        # Descargar la imagen
        image_path = os.path.join(IMAGE_FOLDER, 'imagen_generada.png')
        img_response = requests.get(image_url)

        if img_response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(img_response.content)
            return jsonify({"message": "Imagen generada exitosamente", "image_url": f"/static/imagen_generada.png"})
        else:
            return jsonify({"error": "No se pudo descargar la imagen"}), 500
    else:
        return jsonify({"error": "No se encontró imagen en la respuesta"}), 500

@app.route('/static/<filename>')
def serve_image(filename):
    """Sirve imágenes generadas desde la carpeta static"""
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
