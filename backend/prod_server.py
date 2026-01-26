from waitress import serve
import logging
from config.wsgi import application

logging.basicConfig(level=logging.INFO)

serve(application, host='127.0.0.1', port=8000, )
