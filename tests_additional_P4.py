"""
    Tests que comprueban la funcionalidad del sistema de victorias.

    Author
    -------
        Andrés Mena
        Eric Morales
"""
import re
from django.urls import reverse
from logic.tests_services import PlayGameBaseServiceTests, SHOW_GAME_SERVICE
from datamodel import constants
from datamodel.models import Game, GameStatus, Move


class GameEndTests(PlayGameBaseServiceTests):
    """Este test comprueba si ha ganado un gato o un PAC"""

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test1(self):
        """Se realiza una secuencia de movimientos. En cada movimiento,
        se comprueba que el estado de la partida siga siendo activo, y que la
        respuesta de la página no sea la victoria ni de gato ni de PAC. En el
        último movimiento, hacemos que ganen los gatos porque encierran a
        PAC, y comprobamos que la partida pasa a estado finalizada, y que
        la pagina nos devuelve la respuesta de gato gana. Comprobamos tambien
        que el juego ya no está en la sesión"""

        # Generamos una secuencia de movimientos que encierra al PAC
        # (excepto el ultimo movimiento)
        moves = [
            {"player": self.user1, "origin": 0, "target": 9},
            {"player": self.user2, "origin": 59, "target": 50},
            {"player": self.user1, "origin": 9, "target": 16},
            {"player": self.user2, "origin": 50, "target": 57},
            {"player": self.user1, "origin": 16, "target": 25},
            {"player": self.user2, "origin": 57, "target": 48},
            {"player": self.user1, "origin": 25, "target": 32},
            {"player": self.user2, "origin": 48, "target": 57},
            {"player": self.user1, "origin": 32, "target": 41},
            {"player": self.user2, "origin": 57, "target": 48},
            {"player": self.user1, "origin": 2, "target": 11},
            {"player": self.user2, "origin": 48, "target": 57},
            {"player": self.user1, "origin": 11, "target": 18},
            {"player": self.user2, "origin": 57, "target": 48},
            {"player": self.user1, "origin": 18, "target": 27},
            {"player": self.user2, "origin": 48, "target": 57},
            {"player": self.user1, "origin": 27, "target": 34},
            {"player": self.user2, "origin": 57, "target": 48},
            {"player": self.user1, "origin": 34, "target": 43},
            {"player": self.user2, "origin": 48, "target": 57},
            {"player": self.user1, "origin": 43, "target": 50},
            {"player": self.user2, "origin": 57, "target": 48},
        ]

        game = Game.objects.create(cat_user=self.user1, mouse_user=self.user2)
        game.save()
        self.set_game_in_session(self.client1, self.user1, game.id)

        # Todos estos movimientos tienen que dejar la partida como activa,
        # y no nos pueden llevar a la página de victoria ni de gato ni de PAC
        for move in moves:
            Move.objects.create(game=game, player=move["player"],
                                origin=move["origin"], target=move["target"])
            self.assertEqual(game.status, GameStatus.ACTIVE)
            response = self.client1.get(reverse(SHOW_GAME_SERVICE),
                                        follow=True)

            m = re.search(constants.CAT_WINNER, self.decode(response.content))
            self.assertFalse(m)
            m = re.search(constants.MOUSE_WINNER,
                          self.decode(response.content))
            self.assertFalse(m)

        # Este ultimo movimiento en el que encierran a pac
        Move.objects.create(
            game=game, player=self.user1, origin=50, target=57)
        # Comprobamos que el juego pasa a estado finalizado
        self.assertEqual(game.status, GameStatus.FINISHED)

        # Comprobamos que nos ha llevado a la pagina de victoria del gato
        response = self.client1.get(reverse(SHOW_GAME_SERVICE), follow=True)
        m = re.search(constants.CAT_WINNER, self.decode(response.content))
        self.assertTrue(m)

        # Comprobamos que el juego ya no esta en la sesion, porque ha
        # finalizado
        self.assertFalse(self.client1.session.get(
            constants.GAME_SELECTED_SESSION_ID, False))

    def test2(self):
        """Igual que el test1, se realiza una secuencia de movimentos, pero
        en este caso el que gana es PAC, porque llega al otro extremo del
        tablero"""

        # Generamos una secuencia de movimientos que hace ganar al PAC
        # (excepto el ultimo movimiento)
        moves = [
            {"player": self.user1, "origin": 0, "target": 9},
            {"player": self.user2, "origin": 59, "target": 50},
            {"player": self.user1, "origin": 2, "target": 11},
            {"player": self.user2, "origin": 50, "target": 43},
            {"player": self.user1, "origin": 4, "target": 13},
            {"player": self.user2, "origin": 43, "target": 34},
            {"player": self.user1, "origin": 6, "target": 15},
            {"player": self.user2, "origin": 34, "target": 27},
            {"player": self.user1, "origin": 9, "target": 16},
            {"player": self.user2, "origin": 27, "target": 18},
            {"player": self.user1, "origin": 11, "target": 20},
            {"player": self.user2, "origin": 18, "target": 9},
            {"player": self.user1, "origin": 20, "target": 27},
        ]

        game = Game.objects.create(cat_user=self.user1, mouse_user=self.user2)
        game.save()
        self.set_game_in_session(self.client1, self.user1, game.id)

        # Todos estos movimientos tienen que dejar la partida como activa,
        # y no nos pueden llevar a la página de victoria ni de gato ni de PAC
        for move in moves:
            Move.objects.create(game=game, player=move["player"],
                                origin=move["origin"], target=move["target"])
            self.assertEqual(game.status, GameStatus.ACTIVE)
            response = self.client1.get(reverse(SHOW_GAME_SERVICE),
                                        follow=True)
            m = re.search(constants.CAT_WINNER, self.decode(response.content))
            self.assertFalse(m)
            m = re.search(constants.MOUSE_WINNER,
                          self.decode(response.content))
            self.assertFalse(m)

        # Este ultimo movimiento hace que el PAC llegue al otro extremo
        # por lo que gana la partida
        Move.objects.create(
            game=game, player=self.user2, origin=9, target=2)

        self.assertEqual(game.status, GameStatus.FINISHED)

        # Comprobamos que nos ha llevado a la pagina de victoria del PAC
        response = self.client1.get(reverse(SHOW_GAME_SERVICE), follow=True)
        m = re.search(constants.MOUSE_WINNER, self.decode(response.content))
        self.assertTrue(m)

        self.assertFalse(self.client1.session.get(
            constants.GAME_SELECTED_SESSION_ID, False))
