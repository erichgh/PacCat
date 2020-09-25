"""
    Modelos de datos utilizados a lo largo de la aplicación de PACCAT.
        - Game
        - Move
        - Counter

    Author
    -------
        Andrés Mena
        Eric Morales
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from enum import IntEnum

from datamodel import constants

# Posiciones iniciales.
CAT1POS = 0
CAT2POS = 2
CAT3POS = 4
CAT4POS = 6
MOUSEPOS = 59


def validate_position(value):
    """
        Función que comprueba si una posición en el tablero se encuentra dentro
        de las casillas blancas, es decir las casillas a las que pueden moverse
        los jugadores.

        Parameters
        ----------
        value : int
            Posición del tablero

        Returns
        -------
        void : void

        Raises
        -------
        ValidationError
            Si la posición no es correcta.

        Author
        -------
            Andrés Mena
            Eric Morales
    """
    if value < Game.MIN_CELL or value > Game.MAX_CELL:
        raise ValidationError(constants.MSG_ERROR_INVALID_CELL)

    if (value // 8) % 2 == 0:
        if value % 2 != 0:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)
    else:
        if value % 2 == 0:
            raise ValidationError(constants.MSG_ERROR_INVALID_CELL)


def valid_move(game, origin, target):
    """
        Función que comprueba si un movimiento es valido, teniendo en
        cuenta la posición del resto de jugadores.

        Parameters
        ----------
        game : Game
            Juego actual
        origin : int
            Posición del tablero origen
        target : int
            Posición del tablero destino

        Returns
        -------
        boolean : True si el movimiento es correcto

        Raises
        -------
        ValidationError
            Si el movimiento no es correcto

        Author
        -------
            Andrés Mena
            Eric Morales
    """

    # Si la casilla está ocupada
    if target in [game.cat1, game.cat2, game.cat3, game.cat4, game.mouse]:
        raise ValidationError(constants.MSG_ERROR_MOVE)

    x_ori = origin // 8 + 1
    y_ori = origin % 8 + 1

    x_tar = target // 8 + 1
    y_tar = target % 8 + 1

    if game.cat_turn:
        if x_tar != x_ori + 1:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        elif y_tar != y_ori + 1 and y_tar != y_ori - 1:
            raise ValidationError(constants.MSG_ERROR_MOVE)
    else:
        if x_tar != x_ori + 1 and x_tar != x_ori - 1:
            raise ValidationError(constants.MSG_ERROR_MOVE)
        elif y_tar != y_ori + 1 and y_tar != y_ori - 1:
            raise ValidationError(constants.MSG_ERROR_MOVE)

    # Comprobamos que no estemos intentando realizar justo un movimiento de
    # los extremos
    if (y_ori == 8 and y_tar == 9) or (y_ori == 1 and y_tar == 0) or \
            (x_ori == 1 and x_tar == 0) or (x_ori == 8 and x_tar == 9):
        raise ValidationError(constants.MSG_ERROR_MOVE)

    elif not (Game.MIN_CELL <= target <= Game.MAX_CELL):
        raise ValidationError(constants.MSG_ERROR_INVALID_CELL)

    # Si el movimiento es valido, y llego hasta aqui, devuelvo true
    return True


def check_winner(game):
    """
        Funcion que comprueba si hay ganador.

        Parameters
        ----------
        game : Game
            Partida correspondiente

        Returns
        -------
        int : función que indica cual ha sido el ganador de una partida,
              los posibles resultados son los siguientes:
                - 0 == NO WINNER
                - 1 == CAT_WINNER
                - 2 == MOUSE_WINNER

        Author
        -------
            Andrés Mena
    """

    if game is not None:
        # Compruebo si PAC ha llegado al otro extremo
        if game.mouse in [0, 2, 4, 6]:
            return 2

        if not game.cat_turn:
            mouse = game.mouse
            # El otro caso, es que el raton se vea rodeado
            # Probamos el movimiento a todas las posibles casillas del gato
            flag = 0
            for i in range(Game.MIN_CELL, Game.MAX_CELL):
                try:
                    if valid_move(game, mouse, i):
                        # Si tengo un movimiento valido, todavia no he perdido
                        flag = 1
                except ValidationError:
                    pass

            if flag == 0:
                # El raton pierde porque no puede hacer ningun movimiento
                return 1

            # Si llegamos aqui, es porque no hay ganador
        return 0


def valid_game_status(value):
    """
        Funcion que nos especifica el rango válido de estados que puede tener
        un juego. Relacion directa con GameStatus

        Parameters
        ----------
        value : int
            Entero que identifica el tipo de estado que se esta intentando
            crear

        Raises
        -------
        ValidationError
            Si el tipo de estado no es valido
    """
    if not 0 <= value <= 2:
        raise ValidationError(constants.MSG_ERROR_GAMESTATUS)


class GameStatus(IntEnum):
    """
        Enumeracion que almacena los estados en los que se puede encontrar
        juego.
    """

    CREATED = 0
    ACTIVE = 1
    FINISHED = 2

    @classmethod
    def get_values(cls):
        return (
            (cls.CREATED, 'Created'),
            (cls.ACTIVE, 'Active'),
            (cls.FINISHED, 'Finished')
        )


class Game(models.Model):
    """
        Modelo que almacena toda la informacion relativa a un juego

        Attributes
        ----------
        cat_user : ForeignKey
        mouse_user : ForeignKey
        cat1 : IntegerField
        cat2 : IntegerField
        cat3 : IntegerField
        cat4 : IntegerField
        mouse : IntegerField
        cat_turn : BooleanField
        status : IntegerField

        Methods
        -------
        save(self, *args, **kwargs)
            Almacena el juego en la base de datos.
        __str__(self)
            Devuelve una cadena con toda la información necesaria de un objeto
            de esta clase.
    """

    MIN_CELL = 0
    MAX_CELL = 63

    cat_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name="games_as_cat")
    mouse_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                   blank=True, related_name="games_as_mouse")

    cat1 = models.IntegerField(default=CAT1POS, blank=False, null=False,
                               validators=[validate_position])
    cat2 = models.IntegerField(default=CAT2POS, blank=False, null=False,
                               validators=[validate_position])
    cat3 = models.IntegerField(default=CAT3POS, blank=False, null=False,
                               validators=[validate_position])
    cat4 = models.IntegerField(default=CAT4POS, blank=False, null=False,
                               validators=[validate_position])
    mouse = models.IntegerField(default=MOUSEPOS, blank=False, null=False,
                                validators=[validate_position])
    cat_turn = models.BooleanField(default=True, blank=False, null=False)

    status = models.IntegerField(default=0, validators=[valid_game_status])

    def save(self, *args, **kwargs):
        """
            Almacena el juego en la base de datos.

            Parameters
            ----------
            *args : array
                Argumentos para llamar a la funcion save de models.Model
            **kwargs : array
                Argumentos para llamar a la funcion save de models.Model

            Returns
            -------
            void : void

            Author
            -------
                Andrés Mena
                Eric Morales
        """

        # Antes de guardar, comprobamos si la partida ya ha terminado
        if check_winner(self) != 0:
            self.status = GameStatus.FINISHED
        validate_position(self.cat1)
        validate_position(self.cat2)
        validate_position(self.cat3)
        validate_position(self.cat4)
        validate_position(self.mouse)

        if self.status == GameStatus.CREATED:
            self.cat1 = CAT1POS
            self.cat2 = CAT2POS
            self.cat3 = CAT3POS
            self.cat4 = CAT4POS
            self.mouse = MOUSEPOS
            self.cat_turn = True

        # Cuando nos metan al mouse, pasamos a estado activo
        if self.mouse_user and self.status == GameStatus.CREATED:
            self.status = GameStatus.ACTIVE

        super(Game, self).save(*args, **kwargs)

    def __str__(self):
        """
            Devuelve una cadena con toda la información necesaria de un objeto
            de esta clase.

            Parameters
            ----------
            void : void

            Returns
            -------
                string : cadena formateada

            Author
            -------
                Andrés Mena
       """

        response = "(" + str(self.id) + ", "
        if self.status == GameStatus.ACTIVE:
            response += "Active)\t"
        elif self.status == GameStatus.FINISHED:
            response += "Finished)\t"

        elif self.status == GameStatus.CREATED:
            response += "Created)\t"

        response += "Cat [X] " if self.cat_turn else "Cat [ ] "

        response += str(self.cat_user) + "(" + str(self.cat1) + ", "
        response += str(self.cat2) + ", " + str(self.cat3)
        response += ", " + str(self.cat4) + ")"

        if self.mouse_user:
            response += " --- Mouse "
            response += "[X] " if not self.cat_turn else "[ ] "
            response += str(self.mouse_user) + "(" + str(self.mouse) + ")"

        return response

    class Meta:
        ordering = ['id']


class Move(models.Model):
    """
        Modelo que almacena toda la informacion relativa a un movimiento

        Attributes
        ----------
        origin : IntegerField
        target : IntegerField
        game : ForeignKey
        player : ForeignKey
        date : DateTimeField

        Methods
        -------
        save(self, *args, **kwargs)
            Almacena el juego en la base de datos.
        __str__(self)
            Devuelve una cadena con toda la información necesaria de un objeto
            de esta clase.

    """

    origin = models.IntegerField(blank=False, null=False)
    target = models.IntegerField(blank=False, null=False)
    game = models.ForeignKey(Game,
                             on_delete=models.CASCADE,
                             related_name='moves')
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, blank=False, null=False)

    def __str__(self):
        """
            Devuelve una cadena con toda la información necesaria de un objeto
            de esta clase.

            Parameters
            ----------
            void : void

            Returns
            -------
                string : cadena formateada

            Author
            -------
                Andrés Mena
        """
        return "Game: " + str(self.game.id) + " player: " \
               + str(self.player) + " origin: " + str(self.origin) \
               + " target: " + str(self.target)

    def save(self, *args, **kwargs):
        """
            Almacena el movimiento en la base de datos.

            Parameters
            ----------
            *args : array
                Argumentos para llamar a la funcion save de models.Model
            **kwargs : array
                Argumentos para llamar a la funcion save de models.Model

            Returns
            -------
            void : void

            Raises
            -------
            ValidationError
                Si el movimiento no es correcto

            Author
            -------
                Andrés Mena
        """

        if self.game.status == GameStatus.CREATED \
                or self.game.status == GameStatus.FINISHED:
            raise ValidationError(constants.MSG_ERROR_MOVE)

        valid_move(self.game, self.origin, self.target)

        if self.player == self.game.cat_user:

            if self.game.cat_turn:
                if self.game.cat1 == self.origin:
                    self.game.cat1 = self.target
                    self.game.cat_turn = False

                elif self.game.cat2 == self.origin:
                    self.game.cat2 = self.target
                    self.game.cat_turn = False

                elif self.game.cat3 == self.origin:
                    self.game.cat3 = self.target
                    self.game.cat_turn = False

                elif self.game.cat4 == self.origin:
                    self.game.cat4 = self.target
                    self.game.cat_turn = False
                else:
                    raise ValidationError(constants.MSG_ERROR_MOVE)
            else:
                raise ValidationError(constants.MSG_ERROR_MOVE)
        elif self.player == self.game.mouse_user:
            if not self.game.cat_turn:
                if self.game.mouse == self.origin:
                    self.game.mouse = self.target
                    self.game.cat_turn = True
                else:
                    raise ValidationError(constants.MSG_ERROR_MOVE)
            else:
                raise ValidationError(constants.MSG_ERROR_MOVE)
        else:
            raise ValidationError(constants.MSG_ERROR_MOVE)

        super(Move, self).save(*args, **kwargs)
        self.game.save()

    class Meta:
        ordering = ['id']


class SingletonModel(models.Model):
    """
        Modelo abstracto del cual heredan todos los modelos que deban
        utilizar la estructura Singleton

        Attributes
        ----------
        none

        Methods
        -------
        save(self, *args, **kwargs)
            Almacena el objeto en la base de datos (borrando el resto)
        load(cls)
            Devuelve de la base de datos el objeto único del tipo
            Singleton.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
            Almacena el objeto en la base de datos, eliminando el resto de
            entradas de este tipo.

            Parameters
            ----------
            *args : array
                Argumentos para llamar a la funcion save de models.Model
            **kwargs : array
                Argumentos para llamar a la funcion save de models.Model

            Returns
            -------
            void : void

            Author
            -------
                Eric Morales
        """

        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
            Devuelve de la base de datos el objeto único del tipo
            Singleton. Si este no existe crea uno nuevo.

            Parameters
            ----------
            none

            Returns
            -------
            SingletonModel : objeto recuperado/creado.

            Author
            -------
                Eric Morales
        """

        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class CounterManager(models.Manager):
    """
        Clase que representa al manager de los objetos de tipo Counter,
        es decir declara las funciones que llamamos utilizando la sentencia
        Counter.objects.

        Attributes
        ----------
        none

        Methods
        -------
        get_current_value(self)
            Devuelve el valor de contador que se encuentra en la base de datos.
        inc(self)
            Incrementa el valor del contador y lo almacena en la base de datos.
        create(self, *args, **kwargs)
            Sobreescribimos el método create para evitar su uso.
    """

    def get_current_value(self):
        """
            Devuelve el valor de contador que se encuentra en la base de datos.

            Parameters
            ----------
                none

            Returns
            -------
            int : value

            Author
            -------
                Eric Morales
        """

        return Counter.load().value

    def inc(self):
        """
            Incrementa el valor del contador y lo almacena en la base de datos.

            Parameters
            ----------
                none

            Returns
            -------
            int : value

            Author
            -------
                Eric Morales
        """

        counter = Counter.load()
        counter.value += 1
        super(Counter, counter).save()
        return self.get_current_value()

    def create(self, *args, **kwargs):
        """
            Sobreescribimos el método create para evitar su uso.

            Parameters
            ----------
            *args : array
                Para sobreescribir a la funcion create de models.Manager
            **kwargs : array
                Para sobreescribir a la funcion create de models.Manager

            Returns
            -------
            void : void

            Raises
            -------
            ValidationError
                Si intentamos crear una instancia nueva del objeto, no lo
                permitimos lanzando esta excepción.

            Author
            -------
                Eric Morales
        """

        raise ValidationError(constants.MSG_ERROR_NEW_COUNTER)


class Counter(SingletonModel):
    """
        Modelo que almacena toda la información relativa al contador.
        Hereda del modelo SingletonModel, para evitar que exista mas de una
        instancia de este objeto.

        Attributes
        ----------
        value : IntegerField
        objects : CounterManager()
            Sobreescribimos el Manager por defecto.

        Methods
        -------
        save(self, *args, **kwargs)
            Sobreescribimos el método save para evitar su uso.
    """

    value = models.IntegerField(default=0, blank=False, null=False)
    objects = CounterManager()

    def save(self, *args, **kwargs):
        """
            Sobreescribimos el método save para evitar su uso.

            Parameters
            ----------
            *args : array
                Para sobreescribir a la funcion save de models.Model
            **kwargs : array
                Para sobreescribir a la funcion save de models.Model

            Returns
            -------
            void : void

            Raises
            -------
            ValidationError
                Si intentamos crear una instancia nueva del objeto, no lo
                permitimos lanzando esta excepción.

            Author
            -------
                Eric Morales
        """

        raise ValidationError(constants.MSG_ERROR_NEW_COUNTER)
