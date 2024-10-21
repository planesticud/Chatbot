# Chatbot Planestic

Este proyecto es un chatbot RAG desarrollado con Django que utiliza Cohere para generar respuestas basadas en documentos específicos proporcionados por el usuario.

## Estructura del Proyecto

```
.
├── chatbot
│   ├── docs
│   │   └── *.pdf
│   ├── migrations
│   ├── rag
│   │   ├── clients
│   │   │   ├── __init__.py
│   │   │   └── aws_client.py
│   │   ├── config
│   │   │   └── config.json
│   │   ├── database
│   │   │   ├── info.txt
│   │   │   └── log_message_interaction.csv
│   │   ├── handlers
│   │   │   ├── __init__.py
│   │   │   ├── aws_bedrock_handler.py
│   │   │   ├── cohere_handler.py
│   │   │   ├── base_handler.py
│   │   │   └── factory.py
│   │   ├── utils
│   │   │   ├── __init__.py
│   │   │   ├── patterns.py
│   │   │   ├── singleton_meta.py
│   │   │   └── utils.py
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   ├── js
│   │   │   └── scripts.js
│   ├── templates
│   │   └── index.html
│   ├── views.py
├── project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── Dockerfile
├── README.md
└── requirements.txt
```

## Comenzando

### Prerrequisitos
1. **Python 3.10+**: Asegúrate de tener Python 3.10 o superior instalado.

2. **Cohere API Key**: Necesitas una cuenta en [Cohere](https://cohere.com/ "Click para acceder") para obtener una clave API.

3. **AWS Bedrock**: Asegúrate de tener acceso a AWS Bedrock si vas a utilizar este proveedor.

4. **Entorno virtual**: Se recomienda usar un entorno virtual para gestionar las dependencias del proyecto.

5. **Keys**: El proyecto utiliza un archivo `.env` para gestionar variables sensibles como la clave API de Cohere, la clave secreta de Django y los orígenes permitidos para iframes (CSP). Este archivo debe contener:
    ```
    COHERE_API_KEY=tu_clave_cohere
    DJANGO_SECRET_KEY=tu_clave_secreta_django
    ALLOWED_IFRAME_ORIGINS=dominio1.com,dominio2.com
    ```

### Instalación

1. Clona el repositorio:
    ```
    git clone https://github.com/dalzoj/chatbot.git
    cd chatbot
    ```

2. Crea y activa un entorno virtual:
    ```
    python -m venv venv
    source venv/bin/activate  # En Windows usa: venv\Scripts\activate
    ```

3. Instala las dependencias:
    ```
    pip install -r requirements.txt
    ```

4. Configura el archivo .env:

    Crea un archivo .env en la raíz del proyecto con las siguientes variables:
    ```
    COHERE_API_KEY=tu_clave_cohere
    DJANGO_SECRET_KEY=tu_clave_secreta_django
    ALLOWED_IFRAME_ORIGINS=dominio1.com,dominio2.com
    ```

5. Realiza las migraciones de la base de datos:
    ```
    python manage.py migrate
    ```

### Configuración en Producción
Para entornos de producción, asegúrate de cambiar la variable `DEBUG` a `False` en el archivo `settings.py` dentro del directorio `project`. Esta configuración evita mostrar información sensible en caso de errores en producción.
```
DEBUG = False  # Cambia a False en producción
```
### Configuración de Seguridad
Para asegurar que solo los orígenes permitidos puedan cargar el chatbot en un iframe, se utiliza la variable `ALLOWED_IFRAME_ORIGINS` en el archivo `.env`. Esta variable se utiliza en la configuración `CSP_FRAME_ANCESTORS` dentro de `settings.py`.
Además, se configura el uso de la política de seguridad de contenido (CSP) para los scripts mediante:
```
CSP_SCRIPT_SRC_ELEM = [
    "'self'",  
    'https://cdn.jsdelivr.net'
]
```
### Configuración del Logging
El archivo `settings.py` también contiene una configuración de logging para mostrar mensajes en la consola durante el desarrollo y depuración. Este es un ejemplo de la configuración de logging:
```
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'chatbot': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Configuración del Chatbot
El archivo `config.json` permite configurar el chatbot para utilizar Cohere o AWS Bedrock. Aquí tienes un ejemplo del contenido de este archivo:
```
{
    "bot_type": "cohere",
    "bot_config": {
        "aws_bedrock": {
            "model": "cohere.command-r-v1:0",
            "temperature": 0.2,
            "max_tokens": 50,
            "docs_directory": "./chatbot/docs/"
        },
        "cohere": {
            "model": "command-nightly",
            "temperature": 0.2,
            "max_tokens": 100,
            "docs_directory": "./chatbot/docs/"
        }
    }
}
```


## Ejecutar la aplicación
1. Inicia el servidor de desarrollo de Django:
    ```
    python manage.py runserver 0.0.0.0:8000
    ```
2. Accede a la aplicación en tu navegador: [http://127.0.0.1:8000/](http://127.0.0.1:8000/ "Click para acceder")

3. Para interactuar con el chatbot, asegúrate de haber cargado correctamente los documentos PDF en la carpeta `docs/`.

## Parte Visual
El chatbot utiliza HTML, CSS y JavaScript para su interfaz. Los archivos relevantes se encuentran en `templates/index.html`, `static/css/styles.css`, y `static/js/scripts.js`.
1. `index.html` define la estructura básica del chat, incluyendo el campo de entrada y el botón de envío.
2. `styles.css` contiene el estilo visual del chatbot, adaptado con los colores de la Universidad Distrital Francisco José de Caldas.
3. `scripts.js` gestiona la interacción entre el usuario y el chatbot, enviando los mensajes y manejando la respuesta.

## Contribuciones
Si deseas contribuir al proyecto, por favor sigue los siguientes pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Añadir nueva funcionalidad'`).
4. Envía tus cambios a la rama principal (`git push origin feature/nueva-funcionalidad`).
5. Crea un Pull Request.

¡Las contribuciones son bienvenidas!