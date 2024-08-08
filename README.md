# Chatbot Planestic

Chatbot Planestic es un asistente impulsado por IA diseñado para responder preguntas basadas en documentos. El chatbot está construido usando Flask para el servidor web y LangChain para el sistema de preguntas y respuestas.

## Estructura del Proyecto

```
PLANESTIC-CHATBOT/
├── venv/
├── .env
├── app.py
├── QAHandler.py
├── README.md
├── requirements.txt
```

## Comenzando

### Prerrequisitos

- Python 3.8 o superior
- Virtualenv
- Docker (opcional, para despliegue en contenedor)

### Instalación

1. Clona el repositorio:

```
git clone https://github.com/dalzoj/planestic-chatbot.git
cd chatbot
```

2. Instala los paquetes requeridos
```
pip install -r requirements.txt
```

3. Configura las variables de enotrno. Crea un archivo `.env` en el directorio raíz del proyecto  añade las siguientes variables:
```
COHERE_API_KEY = tu_api_key_de_cohere
DOCS_PATH = ruta_a_tu_directorio_de_documentos
```


## Ejecutando la aplicación

1. Iniciar el servidor Flask
```
python app.py
```

2. La aplicación estará corriendo en `http://0.0.0.0:5000`.



## Endpoints de la API
* `GET /`: Ruta principal para verificar si la API está funcionando.
* `POST /ask`: Endpoint para hacer preguntas.
    * Cuerpo de la solicitud (JSON)
    ```
    {
        "question": "Tu pregunta aquí"
    }
    ```
    * Cuerpo de la respuesta (JSON)
    ```
    {
        "answer": "Respuesta a tu pregunta"
    }
    ```



## DEspliegue con Docker

1. Contruir la imagen de docker
```
docker build -t chatbot .
```

2. Ejecutar el contenedor de Docker
```
docker run -p 5000:5000 --env-file .env chatbot
```


## Contribuir
¡Las contribuciones son bienvenidas! Por favor, abre un issue o envía un pull request para cualquier mejora o corrección de errores.


