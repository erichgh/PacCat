"""
    Vistas utilizadas a lo largo de la aplicación de PACCAT.

    Author
    -------
        Andrés Mena
        Eric Morales
"""
import json
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from itertools import chain

from datamodel import constants
from datamodel.models import Counter, Game, GameStatus, Move, check_winner
from logic.forms import SignupForm, UserForm


def countErr(request):
    """
        Servicio de contador de errores. Se invoca una vez cada vez que la
        pagina nos devuelve un error

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http
        Returns
        -------
        void

        Author
        -------
            Eric Morales
    """
    # Si el contador ya esta definido en la sesion, lo incrementamos en 1
    if "counter" in request.session:
        request.session["counter"] += 1

    # En caso de no tener todavia contador en la sesion, lo inicializamos a 1
    else:
        counter_session = 1
        request.session["counter"] = counter_session

    # Incrementamos el contador global
    Counter.objects.inc()


def anonymous_required(f):
    """
        Decorador para limitar funciones a usuarios anonimos.

        Parameters
        ----------
        f : funcion
            Funcion a ejecutar

        Returns
        -------
        HttpResponse : error o la respuesta de la funcion.

        Author
        -------
            Profesores PSI
    """

    def wrapped(request):
        if request.user.is_authenticated:
            return HttpResponseForbidden(
                errorHTTP(request,
                          exception=constants.ERROR_RESTRICTED_ANONYMOUS))
        else:
            return f(request)

    return wrapped


def login_required(f):
    """
        Decorador para limitar funciones a usuarios logeados.

        Parameters
        ----------
        f : funcion
            Funcion a ejecutar

        Returns
        -------
        HttpResponse : error o la respuesta de la funcion.

        Author
        -------
            Andres Mena
    """

    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            countErr(request)

            return redirect(reverse('login'))
        else:
            return f(request, *args, **kwargs)

    return wrapped


def error404(request, url=None, err=None):

    context_dict = {}
    if err is not None:
        context_dict = {'msg_error': "ERROR 404. PAGE NOT FOUND. " + err}
    elif url is not None:
        context_dict = {'msg_error': "ERROR 404. PAGE NOT FOUND. No se ha "
                                     "encontrado la pagina " + str(url)}

    countErr(request)

    return render(request, "mouse_cat/error.html", context_dict, status=404)


def errorHTTP(request, exception=None):
    """
        Crea un error http basado en una solicitud y lo devuelve

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http
        exception : string
            Almacena el error a mostrar.

        Returns
        -------
        HttpResponse : error o la respuesta de la funcion.

        Author
        -------
            Profesores PSI
    """
    countErr(request)
    return render(request, "mouse_cat/error.html", {'msg_error': exception})


def end_game(request, game):
    """
        Funcion que imprime el tablero una vez ha finalizado la partida,
        mostrando el mensaje de ganador o perdedor en funcion del usuario que
        hace la solicitud

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http
        game : Game
            Juego del que mostrar la partida

        Returns
        -------
        Html : archivo html con el resumen de final de partida.

        Author
        -------
            Andrés Mena
    """

    # La partida ha terminado. Imprimiremos una ultima vez el
    # tablero
    board = create_board_from_game(game)

    # Borramos de la sesion la partida, porque ya ha terminado
    if constants.GAME_SELECTED_SESSION_ID in request.session:
        del request.session[constants.GAME_SELECTED_SESSION_ID]

    # Devolvemos un página con un mensaje de ganador y el tablero final de la
    # partida
    context_dict = {}

    # Felicitamos al usuario que ha ganado
    insert_winner_message(request, game, context_dict)

    context_dict['board'] = board
    return render(request, "mouse_cat/end_game.html", context_dict)


def index(request):
    """
        Funcion que genera la pagina html inicial.

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con la página incial

        Author
        -------
            Eric Morales
    """
    return render(request, 'mouse_cat/index.html')


@anonymous_required
def login_service(request):
    """
        Funcion que genera la pagina html con los formularios para inciar
        sesión (método GET) y de recibir estos formularios (método POST).

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con el formulario de login.

        Author
        -------
            Andrés Mena
    """

    # Si alguien esta intentando iniciar sesion, es metodo post
    if request.method == 'POST':
        form = UserForm(request.POST)

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                # Inicia sesion en la aplicaion
                login(request, user)

                # Reseteo el contador
                request.session["counter"] = 0

                return redirect(reverse('logic:index'))
            else:
                return errorHTTP(request, constants.EEROR_ACCOUNT_DISABLED)
        else:
            # Borramos los errores del formulario en caso de que los hubiera
            form.errors.pop('username', None)

            # Añadimos el error de autentificacion invalida
            form.add_error('username', constants.ERROR_CREDENTIALS)
            return render(request, 'mouse_cat/login.html',
                          {'user_form': form})

    # Metodo get implica que alguien está intentando ver la pagina de login
    else:
        return render(request, 'mouse_cat/login.html',
                      {'user_form': UserForm()})


@login_required
def logout_service(request):
    """
        Funcion que se encarga de cerrar la sesión de los usuarios y
        genera la pagina html informando de que el cierre se ha realizado
        correctamente.

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con el resultado del logout.

        Author
        -------
            Eric Morales
    """

    # Obtenemos que usuario esta conectado, y procedemos a cerrar sesion
    user = request.user
    logout(request)

    # Eliminamos la informacion de la sesion
    for key in request.session.keys():
        del request.session[key]

    return render(request, 'mouse_cat/logout.html', {'user': user})


@anonymous_required
def signup_service(request):
    """
        Funcion que genera la pagina html con los formularios para registrarse
        (método GET) y de recibir estos formularios (método POST).

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con el formulario de registro.

        Author
        -------
            Andrés Mena
    """

    # Si el metodo es post, significa que nos estan mandando un formulario con
    # informacion de inicio de sesion
    if request.method == 'POST':
        form = SignupForm(request.POST)

        # Esto llamara a la funcion clean para hacer la comprobacion del
        # formulario
        if form.is_valid():
            new_user = form.save()

            # Sacamos el valor de la contraseña, y se lo asignamos al usuario
            # antes de guardar
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()

            # Procedemos a iniciar sesion del usuario en la pagina
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password'])
            login(request, new_user)

            # Devolvemos una pagina que indica que se ha registrado
            # correctamente
            return render(request,
                          'mouse_cat/signup.html', {'user_form': None})

        else:
            # Formulario invalido, devolvemos los errores
            return render(request,
                          'mouse_cat/signup.html', {'user_form': form})

    # Si el metodo es get, devolvemos la pagina para que se registre
    else:
        return render(request,
                      'mouse_cat/signup.html', {'user_form': SignupForm()})


def counter_service(request):
    """
        Funcion que genera la pagina html para mostrar el valor del counter
        e inicializarlo en caso de que no estuviese definido en la sesion

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con el estado del counter.

        Author
        -------
            Eric Morales
    """

    # En caso de no tener todavia contador en la sesion, lo inicializamos a 0
    # Ya que aun no ha habido errores.
    if "counter" not in request.session:
        counter_session = 0
        request.session["counter"] = counter_session

    context_dict = {'counter_session': request.session["counter"],
                    'counter_global': Counter.objects.get_current_value()}
    return render(request, 'mouse_cat/counter.html', context=context_dict)


@login_required
def create_game_service(request):
    """
        Funcion que crea una partida nueva y muestra una pagina avisando
        de ello.

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con el resultado de la creación de la partida.

        Author
        -------
            Andrés Mena
    """

    # Creamos una partida asignandosela al usuario que esta dentro del sistema
    new_game = Game(cat_user=request.user)
    new_game.save()
    return render(request, 'mouse_cat/new_game.html', {'game': new_game})


@login_required
def select_game_service(request, tipo=-1, filter=-1, game_id=-1):
    """
        Funcion que maneja las partdias y la seleccion de ellas: Unirse a
        partidas, mostrar partidas en las que estoy participando para seleccion
         de juego y ver que partidas se pueden reproducir

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http
        tipo : int (default -1)
            Tipo de servicio que queremos usar:
                1: Mostrar partidas que estamos jugando
                2: Mostrar partidas a las que nos podemos unir
                3: Mostrar partidas para reproducir

        filter: int (default -1)
            Nos dice si tenemos que aplicar algun filtro a los resutlados
            que devolvemos
                1: Partidas como gato
                2: Partidas como PAC
                3: Partidas en las que es mi turno
                4: Partidas que he ganado (solo para finished)

        game_id : int (default -1)
            Id de la partida seleccionada

        Returns
        -------
        Html : archivo html con una lista de partidas o con el tablero
               listo para jugar o reproducir

        Author
        -------
            Eric Morales
    """
    # Esto significa que quiero ver las partidas que estoy jugando
    if request.method == 'GET' and int(tipo) == 1 and int(game_id) == -1:
        # Tengo que añadir un campo id a cada partida, para luego poder hacer
        # bien el template

        # Filtro los juegos que estan activos, en los que el usuario que
        # hace la solicitud es el gato o el PAC
        mis_juegos_cat = Game.objects.filter(status=GameStatus.ACTIVE,
                                             cat_user=request.user)
        mis_juegos_mouse = Game.objects.filter(status=GameStatus.ACTIVE,
                                               mouse_user=request.user)

        games_list = []
        if int(filter) == -1:
            games_list = list(chain(mis_juegos_cat, mis_juegos_mouse))

        elif int(filter) == 1:
            games_list = mis_juegos_cat

        elif int(filter) == 2:
            games_list = mis_juegos_mouse

        elif int(filter) == 3:
            mis_juegos_cat = mis_juegos_cat.filter(cat_turn=True)
            mis_juegos_mouse = mis_juegos_mouse.filter(cat_turn=False)
            games_list = list(chain(mis_juegos_cat, mis_juegos_mouse))

        # Show 5 games per page
        paginator = Paginator(games_list, 5)
        page = request.GET.get('page')
        games = paginator.get_page(page)
        return render(request, 'mouse_cat/select_game.html', {'games': games})

    # En este caso, significa que quiero jugar la partida
    elif request.method == 'GET' and int(tipo) == 1 and int(game_id) != -1:
        # Confirmo que no me esten dando un id que no es valido. En caso de
        # ser válido, intento devuelver el estado de la partida llamando a
        # show game service
        game = Game.objects.filter(id=game_id)
        if len(game) > 0:
            game = game[0]
            if game.status == GameStatus.CREATED:
                # Error porque el juego seleccionado no esta en estado activo
                return errorHTTP(request, constants.
                                 ERROR_SELECTED_GAME_NOT_AVAILABLE)

            # Si la partida a terminado, nos muestra el ultimo estado de la
            # partida
            if game.status == GameStatus.FINISHED and \
                    (game.cat_user == request.user or
                     game.mouse_user == request.user):
                return end_game(request, game)

            if game.cat_user != request.user \
                    and game.mouse_user != request.user:
                # Error porque el jugador que solicita el juego no es ni el
                # gato ni el PAC
                return errorHTTP(request,
                                 constants.ERROR_SELECTED_GAME_NOT_YOURS)

            request.session[constants.GAME_SELECTED_SESSION_ID] = game_id
            return show_game_service(request)

        # Error porque no se ha encontrado un juego con el id solicitado
        else:
            return errorHTTP(request,
                             constants.ERROR_SELECTED_GAME_NOT_EXISTS)

    # Quiero ver las partidas a las que me quiero unir
    elif request.method == 'GET' and int(tipo) == 2 and int(game_id) == -1:
        # Entre todas las partidas, miro las que solo tienen un jugador

        # En funcion de si tenemos aplicado o no el filtro, devuelve unas
        # partidas de un jugador u otras
        if int(filter) == -1:
            one_player = Game.objects.filter(mouse_user=None,
                                             status=GameStatus.CREATED)

        elif int(filter) == 1:
            one_player = Game.objects.filter(mouse_user=None,
                                             status=GameStatus.CREATED)

        # En la seleccion de partidas a las que unirte, no hay partidas como
        # PAC
        # Nunca es nuestro turno tampoco
        elif int(filter) == 2 or int(filter) == 3:
            one_player = []

        # Tengo que dejar en las que el jugador no sea el propio mouse_user,
        # ya que un jugador no puede jugar contra si mismo
        games_list = []
        if len(one_player) > 0:
            for partida in one_player.order_by('id'):
                if partida.cat_user != request.user:
                    games_list.append(partida)

        # Show 5 games per page
        paginator = Paginator(games_list, 5)
        page = request.GET.get('page')
        games = paginator.get_page(page)
        return render(request, 'mouse_cat/join_game.html', {'games': games})

    # Este caso significa que el usuario ya me ha dicho a que partida se
    # quiere unir
    elif request.method == 'GET' and int(tipo) == 2 and int(game_id) != -1:
        # Compruebo que la partida siga estando disponible (la puede haber
        # cogido otro jugador mientras yo esperaba a seleccionarla)
        game = Game.objects.filter(id=game_id)
        if len(game) > 0:
            game = game[0]
            if game.status != GameStatus.CREATED or \
                    game.mouse_user is not None:
                return render(request, 'mouse_cat/join_game.html', {
                    'msg_error': constants.ERROR_SELECTED_GAME_NOT_AVAILABLE})

            # Le meto en la partida y empieza el juego
            else:
                request.session[constants.GAME_SELECTED_SESSION_ID] = game_id
                game.mouse_user = request.user
                game.save()
                print("Le reenvio a la misma pagina")
                return redirect('select_game', tipo=1, game_id=game_id)

        else:
            return render(request, 'mouse_cat/join_game.html', {
                'msg_error': constants.ERROR_SELECTED_GAME_NOT_EXISTS})

    # Muestro todas las partidas finalizadas en las que yo era alguno de los
    # participantes
    elif request.method == 'GET' and int(tipo) == 3 and int(game_id) == -1:
        finished_as_cat = Game.objects.filter(
            status=GameStatus.FINISHED, cat_user=request.user).order_by('id')
        finished_as_mouse = Game.objects.filter(
            status=GameStatus.FINISHED, mouse_user=request.user).order_by('id')

        games_list = []
        if int(filter) == -1:
            games_list = list(chain(finished_as_cat, finished_as_mouse))

        elif int(filter) == 1:
            games_list = finished_as_cat

        elif int(filter) == 2:
            games_list = finished_as_mouse

        # Tengo que ver qué partidas he ganado yo
        elif int(filter) == 4:
            winner_cat = []
            winner_mouse = []
            for game in finished_as_cat:
                if check_winner(game) == 1:
                    winner_cat.append(game)
            for game in finished_as_mouse:
                if check_winner(game) == 2:
                    winner_mouse.append(game)

            games_list = list(chain(winner_cat, winner_mouse))

        # Show 5 games per page
        paginator = Paginator(games_list, 5)
        page = request.GET.get('page')
        games = paginator.get_page(page)
        return render(request, 'mouse_cat/finished_games.html',
                      {'games': games})

    # Entrar en modo reproduccion
    elif request.method == 'GET' and int(tipo) == 3 and int(game_id) != -1:
        # Almacenamos en la sesion el juego que se está reproduciendo
        request.session[constants.GAME_SELECTED_SESSION_ID] = game_id
        return reproduce_game_service(request)

    # Si nos intentan meter una url que no es ninguna de las opciones
    else:
        return error404(request, constants.ACCESO_URL_INVALIDO)


@login_required
def show_game_service(request):
    """
        Funcion que nos muestra el juego seleccionado listo para jugar.

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con con el tablero listo para jugar o error en
        caso de que el juego no este disponible

        Author
        -------
            Andrés Mena
    """

    # Muestra el estado de la partida que se encuentra en la sesion. En caso
    # de que no se haya ninguna partida en la sesion, devuelve un mensaje de
    # error
    try:
        game = Game.objects.filter(id=request.session[
            constants.GAME_SELECTED_SESSION_ID])[0]

        # Compruebo si la partida ha terminado ya, porque el otro jugador haya
        # ganado, en cuyo caso afirmativo tendré que llamar a la función de
        # partida finalizada
        if game.status == GameStatus.FINISHED:
            return end_game(request, game)

        # Devolvemos la partida con tablero
        return render(request, 'mouse_cat/game.html',
                      {'game': game, 'board': create_board_from_game(game)})
    except KeyError:
        return errorHTTP(request, constants.ERROR_NO_SELECTED_GAME)


@csrf_exempt
def move_service(request):
    """
        Funcion que realiza un movimiento en la partida que se esta jugando
        (via POST), o da error si se llama via GET

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        HttpResponse : json con el status del movimiento, que puede ser:
            -2: Error en el movimiento
            -1: Error en el movimiento
            0: Movimiento ok
            2: Hay ganador, finalizar partida

        Author
        -------
            Eric Morales
    """

    if request.method == 'POST':
        # Nos mandan un post que contiene el movimento que se quiere
        # realizar.

        try:
            origin = int(request.POST.get('origin'))
            target = int(request.POST.get('target'))
        except ValueError:
            return HttpResponse(json.dumps({'status': -2}),
                                content_type="application/json")

        try:
            # Sacamos la partida que se esta jugando de la sesión
            game = Game.objects.filter(id=request.session[
                constants.GAME_SELECTED_SESSION_ID])[0]

            # Intentamos hacer el movimiento. En caso de que nos de una
            # excepcion, significa que el moviemiento no estaba permitido
            try:
                if game.cat_turn:
                    Move.objects.create(
                        game=game, player=game.cat_user,
                        origin=origin,
                        target=target)
                else:
                    Move.objects.create(
                        game=game, player=game.mouse_user,
                        origin=origin,
                        target=target)

                # Si hay un ganador, devolvemos un status code a interpretar
                # por el que ha hecho la solicutd, para que finalice la partida
                if check_winner(game) != 0:
                    return HttpResponse(json.dumps({'status': 2}),
                                        content_type="application/json")
            except ValidationError:
                return HttpResponse(json.dumps({'status': -1}),
                                    content_type="application/json")

            return HttpResponse(json.dumps({'status': 0}),
                                content_type="application/json")

        except KeyError:
            return HttpResponse(json.dumps({'status': -2}),
                                content_type="application/json")

    # GET: Tiene que dar error. No se puede llamar a este servicio en modo get
    else:
        return HttpResponse(json.dumps({'status': -2}),
                            content_type="application/json")


@login_required
def reproduce_game_service(request):
    """
        Funcion que pinta el tablero para comenzar la reproduccion de una
        partida, inicializando las variables necesarias para la reproduccion de
        la misma

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        Html : archivo html con con el tablero listo o error en caso de que se
        produzca algun comportamiento inesperado

        Author
        -------
            Andrés Mena
    """

    if constants.GAME_SELECTED_SESSION_ID not in request.session:
        return errorHTTP(request, constants.ERROR_REPRODUCE_NOT_IN_SESSION)

    game_id = request.session[constants.GAME_SELECTED_SESSION_ID]
    game = Game.objects.filter(id=game_id)

    # No hay ninguna partida con el id
    if len(game) == 0:
        return errorHTTP(request,
                         constants.ERROR_SELECTED_GAME_NOT_EXISTS)

    game = game[0]

    # La partida no ha finalizado todavia
    if game.status != GameStatus.FINISHED:
        return errorHTTP(request,
                         constants.ERROR_NOT_FINISHED_YET)

    # Si no somos ni el PAC ni el gato, no podemos visualizar la partida
    if not (game.cat_user == request.user or game.mouse_user == request.user):
        return errorHTTP(request,
                         constants.ERROR_NOT_ALLOWED_TO_REPRODUCE)

    # Coloco el tablero en la posicion inicial
    if request.method == "GET":
        # Ponemos a 0 el movimiento por que vamos a colocar en pos inicial
        request.session[constants.GAME_SELECTED_MOVE_NUMBER] = 0

        # Creo un tablero con los gatos en las posiciones iniciales
        board = create_initial_board()
        context_dict = {'game': game, 'board': board}

        # Dejamos un mensaje de quien es el ganador por si reproduce la partida
        # entera
        insert_winner_message(request, game, context_dict)

        return render(request, 'mouse_cat/reproduce_game.html', context_dict)


def insert_winner_message(request, game, context_dict):
    """
        Rellena el contenido del diccionario (context_dict) con el mensaje de
        victoria personalizado para el usuario

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        game: Game
            Partida sobre la que hay que mostrar quien ha ganado

        context_dict: Dictionary
            Diccionario que se le devolvera a la pagina con los mensajes
            personalizados

        Returns
        -------
        Void

        Author
        -------
            Andrés Mena
    """

    winner = check_winner(game)
    if winner == 1:
        if request.user == game.cat_user:
            msg = constants.CAT_WINNER + ". Enhorabuena " + str(
                request.user)
            context_dict['winner'] = msg
        else:
            msg = constants.CAT_WINNER + ". Sigue practicando " + str(
                request.user)
            context_dict['winner'] = msg
    if winner == 2:
        if request.user == game.mouse_user:
            msg = constants.MOUSE_WINNER + ". Enhorabuena " + str(
                request.user)
            context_dict['winner'] = msg
        else:
            msg = constants.MOUSE_WINNER + ". Sigue practicando " + str(
                request.user)
            context_dict['winner'] = msg


def create_only_board(request, game_id=-1):
    """
        Funcion que devuelve el tablero de la partida pasada como parámetro,
        devolviendo además los errores correspondientes, si los hay

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http
        game_id : int
            Id del juego del que se crea el tablero

        Returns
        -------
        Html : archivo html con la situacion del tablero de la partida

        Author
        -------
        Eric Morales
    """

    game = Game.objects.filter(id=game_id)

    # No hay ninguna partida con el id
    if len(game) == 0:
        return error404(request,
                        constants.ERROR_SELECTED_GAME_NOT_EXISTS)

    game = game[0]

    # Creamos el array que representa el tablero
    if game is not None:
        # Creamos el tablero
        board = create_board_from_game(game)
        return render(request, 'mouse_cat/board.html',
                      {'board': board})


@csrf_exempt
def turn(request, game_id=-1):
    """
        Funcion que comprueba si ya es mi turno, para refrescar la partida

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        game_id : int
            Id del juego del que se crea el tablero

        Returns
        -------
        HttpResponse : json con parametros variables, entre los siguientes
            turn:
                -1: No es mi turno
                1: Es mi turno

            origin: Origen del movimiento
            target: Destino del movimiento
            winner:
                0: No hay ganador
                1: Hay ganador

        Author
        -------
            Eric Morales
    """
    game = Game.objects.filter(id=game_id)

    # No hay ninguna partida con el id
    if len(game) == 0:
        return HttpResponse(json.dumps({'turn': -1}),
                            content_type="application/json")
    game = game[0]

    if game is not None:
        if check_winner(game) != 0:
            return HttpResponse(json.dumps({'winner': 1}),
                                content_type="application/json")

        moves = Move.objects.filter(game=game).order_by('-date')
        if len(moves) != 0:
            last_move = moves[0]
            return HttpResponse(json.dumps({'turn': game.cat_turn,
                                            'origin': last_move.origin,
                                            'target': last_move.target,
                                            'winner': 0}),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps({'turn': game.cat_turn,
                                            'origin': -1,
                                            'target': -1,
                                            'winner': 0}),
                                content_type="application/json")

    return HttpResponse(json.dumps({'turn': -1}),
                        content_type="application/json")


def create_board_from_game(game):
    """
        Funcion que devuelve el tablero con las posiciones de los jugadores

        Parameters
        ----------
        game: Game
            Partida sobre la que hay que mostrar quien ha ganado

        Returns
        -------
        int []: Array con el tablero y sus jugadores

        Author
        -------
            Eric Morales
    """
    # Primero colocamos todas las casillas a 0, y luego donde estén los
    # gatos lo ponemos a 1, y donde esté el PAC a -1
    board = [0] * 64
    board[game.cat1] = 1
    board[game.cat2] = 2
    board[game.cat3] = 3
    board[game.cat4] = 4
    board[game.mouse] = -1

    newBoard = []
    for c in range(0, 64, 8):
        newBoard.append(board[c: c + 8])
    return newBoard


def create_initial_board():
    """
        Funcion que devuelve un tablero con los jugadores en la posicion
        inicial

        Returns
        -------
        int []: Array con el tablero y sus jugadores

        Author
        -------
            Andres Mena
    """
    board = [0] * 64
    board[0] = 1
    board[2] = 2
    board[4] = 3
    board[6] = 4
    board[59] = -1

    newBoard = []
    for c in range(0, 64, 8):
        newBoard.append(board[c: c + 8])
    return newBoard


@csrf_exempt
def get_move_service(request):
    """
        Funcion que devuelve el json con la información que debe realizar la
        partida reproduciendose

        Parameters
        ----------
        request : HttpRequest
            Solicitud Http

        Returns
        -------
        HttpResponse : json con información del movimiento
            origin: Origen del movimiento
            target: Destino del movimiento
            previous: Flag que indica si hay movimientos previos
            next: Flag que indica si hay movimientos siguientes

        Author
        -------
            Andres Mena
    """
    if request.method == 'GET':
        return error404(request, err=constants.GET_NOT_ALLOWED)

    game = Game.objects.filter(id=request.session[constants.
                               GAME_SELECTED_SESSION_ID])
    if len(game) == 0:
        return HttpResponse("ERROR")

    game = game[0]

    # Sacamos el parametro recibido por metodo post
    shift = int(request.POST.get('shift'))

    moves = Move.objects.filter(game=game).order_by('id')

    # Si todavia no se ha hecho ningun movimiento, inicializamos a 0
    if constants.GAME_SELECTED_MOVE_NUMBER not in request.session:
        request.session[constants.GAME_SELECTED_MOVE_NUMBER] = 0

    move_number = request.session[constants.GAME_SELECTED_MOVE_NUMBER]
    if shift == -1:
        move_number -= 1

    json_dict = {}

    # Tengo que devolver un json con previous a 0 si move_number < 0 (resto de
    # campos irrelevantes, no se van a usar)
    if move_number < 0:
        json_dict['origin'] = 0
        json_dict['target'] = 0
        json_dict['previous'] = 0
        json_dict['next'] = 1

    else:
        if move_number < len(moves):
            real_move = moves[move_number]

            # En funcion de si vamos hacia delante o atras, tendremos un target
            # y un origin
            if shift == 1:
                json_dict['origin'] = real_move.origin
                json_dict['target'] = real_move.target
            else:
                json_dict['origin'] = real_move.target
                json_dict['target'] = real_move.origin

            # En el diccionario, los campos previous y next se identifican con
            # 1 (true) y 0 (false)
            json_dict['previous'] = 1 if move_number > 0 or shift == 1 else 0
            json_dict['next'] = \
                1 if move_number < len(moves) - 1 or shift == -1 else 0

        else:
            json_dict['origin'] = 0
            json_dict['target'] = 0
            json_dict['previous'] = 0
            json_dict['next'] = 0

    # Actualizamos por qué movimiento vamos en la sesion
    if shift == 1:
        request.session[constants.GAME_SELECTED_MOVE_NUMBER] += 1
    elif shift == -1:
        request.session[constants.GAME_SELECTED_MOVE_NUMBER] -= 1
        if request.session[constants.GAME_SELECTED_MOVE_NUMBER] < 0:
            request.session[constants.GAME_SELECTED_MOVE_NUMBER] = 0

    return HttpResponse(json.dumps(json_dict),
                        content_type="application/json")
