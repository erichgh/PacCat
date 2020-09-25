"""
    URLs correspondientes a toda la aplicación de PACGato.

    Author
    -------
        Andrés Mena
"""

from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from logic import views

urlpatterns = [
    url(r'', include(('logic.urls', 'logic'), namespace='logic')),
    path('admin/', admin.site.urls),
    path('mouse_cat/', include('logic.urls')),
    url(r'^(?P<url>.*)/$', views.error404, name='error404'),
]
