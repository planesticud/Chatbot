# Chatbot Planestic

Este proyecto es un chatbot RAG desarrollado con Django que utiliza Cohere para generar respuestas basadas en documentos específicos proporcionados por el usuario.

## Estructura del Proyecto

```
.
├── chatbot
│   ├── docs
│   │   └── *.pdf
│   ├── migrations
│   ├── RAG
│   │   ├── __init__.py
│   │   ├── LLM.py
│   │   └── QAHandler.py
│   ├── static
│   ├── templates
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── db.sqlite3
├── manage.py
├── README.md
└── requirements.txt
```

## Comenzando

### Prerrequisitos
1. **Python 3.10+**: Asegúrate de tener Python 3.10 o superior instalado.

2. **Cohere API Key**: Necesitas una cuenta en [Cohere](https://cohere.com/ "Click para acceder") para obtener una clave API.

3. **Entorno virtual**: Se recomienda usar un entorno virtual para gestionar las dependencias del proyecto.

4. **Keys**: El proyecto utiliza un archivo `.env` para gestionar variables sensibles como la clave API de Cohere y la clave secreta de Django. Este archivo debe contener:
    ```
    COHERE_API_KEY=tu_clave_cohere
    DJANGO_SECRET_KEY=tu_clave_secreta_django
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
    ```

5. Realiza las migraciones de la base de datos:
    ```
    python manage.py migrate
    ```

### Configuración
Para entornos de producción, asegúrate de cambiar la variable `DEBUG` a `False` en el archivo `settings.py` dentro del directorio `project`. Esta configuración evita mostrar información sensible en caso de errores en producción.
```
DEBUG = False  # Cambia a False en producción
```

## Ejecutar la aplicación
1. Inicia el servidor de desarrollo de Django:
    ```
    python manage.py runserver
    ```
2. Accede a la aplicación en tu navegador: [http://127.0.0.1:8000/](http://127.0.0.1:8000/ "Click para acceder")

3. Para interactuar con el chatbot, asegúrate de haber cargado correctamente los documentos PDF en la carpeta `docs/`.

## Contribuciones
Si deseas contribuir al proyecto, por favor sigue los siguientes pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Añadir nueva funcionalidad'`).
4. Envía tus cambios a la rama principal (`git push origin feature/nueva-funcionalidad`).
5. Crea un Pull Request.

¡Las contribuciones son bienvenidas!