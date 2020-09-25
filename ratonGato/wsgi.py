"""
    Configuración WSGI de la aplicación de PACGato

    Author
    -------
        Eric Morales
"""

import os

from dj_static import Cling
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ratonGato.settings')

application = Cling(get_wsgi_application())
