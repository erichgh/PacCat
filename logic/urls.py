"""
    URLs correspondientes a las vistas de la aplicación de PACCAT.

    Author
    -------
        Andrés Mena
        Eric Morales
"""
from django.conf.urls import url
from django.urls import path

from logic import views

urlpatterns = [
    path('', views.index, name='landing'),
    path('index/', views.index, name='index'),
    path('login/', views.login_service, name='login'),
    path('logout/', views.logout_service, name='logout'),
    path('signup/', views.signup_service, name='signup'),
    path('counter/', views.counter_service, name='counter'),
    path('create_game/', views.create_game_service, name='create_game'),
    url(r'^select_game/(?P<tipo>\d+)/$', views.select_game_service,
        name='select_game'),
    url(r'^select_game/(?P<tipo>\d+)/(?P<filter>\d+)$',
        views.select_game_service, name='select_game'),
    url(r'^select_game/(?P<tipo>\d+)/(?P<game_id>\d+)/$',
        views.select_game_service, name='select_game'),
    url(r'^select_game/(?P<tipo>\d+)/(?P<join>\d+)/$',
        views.select_game_service, name='select_game'),
    url(r'^select_game/', views.select_game_service, name='select_game'),
    path('play/', views.show_game_service, name='show_game'),

    path('move/', views.move_service, name='move'),
    path('get_move/', views.get_move_service, name='get_move'),

    url(r'^reproduce_game_service/(?P<game_id>\d+)/$',
        views.reproduce_game_service, name='reproduce_game'),
    url(r'^create_only_board/(?P<game_id>\d+)/$', views.create_only_board,
        name='create_only_board'),
    url(r'^turn/(?P<game_id>\d+)/$', views.turn,
        name='turn'),
    path('reproduce_game/', views.reproduce_game_service,
         name='reproduce_game'),
]
