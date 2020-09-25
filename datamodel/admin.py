"""
    Administración de los modelos desde la interfaz de administrador

    Author
    -------
        Andrés Mena
        Eric Morales
"""

from django.contrib import admin

from datamodel.models import Game, Move

admin.site.register(Game)
admin.site.register(Move)
