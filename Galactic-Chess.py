# Author: Aaron Fuller
# Description: Galactic Chess: A one-player chess game that uses the stockfish chess
# API for the opponent's logic, Chessnut for move validation, and Pygame for the GUI.

import pygame
import os
from pygame.locals import *
import pygame.mixer
from Chessnut import Game
import chess
import chess.engine

pygame.init()
pygame.mixer.init()

mouse_sound = pygame.mixer.Sound('assets/sounds/mouse_click.mp3')
mouse_sound.set_volume(0.5)


class Chess:
    """"""
    def __init__(self):
        self._board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]

        self._turn = "white"
        self._game_state = 'UNFINISHED'
        self.chessgame = Game()
        self.selected_square = None
        self.animation_duration = 15  # 0.5 seconds
        self.animation_progress = 0.0
        self.animation_start = None
        self.animation_end = None
        image_dir = 'assets/images/'

        self.piece_mapping = {
            'K': os.path.join(image_dir, 'white_king.png'),
            'k': os.path.join(image_dir, 'black_king.png'),
            'Q': os.path.join(image_dir, 'white_queen.png'),
            'q': os.path.join(image_dir, 'black_queen.png'),
            'R': os.path.join(image_dir, 'white_rook.png'),
            'r': os.path.join(image_dir, 'black_rook.png'),
            'B': os.path.join(image_dir, 'white_bishop.png'),
            'b': os.path.join(image_dir, 'black_bishop.png'),
            'P': os.path.join(image_dir, 'white_pawn.png'),
            'p': os.path.join(image_dir, 'black_pawn.png'),
            'N': os.path.join(image_dir, 'white_knight.png'),
            'n': os.path.join(image_dir, 'black_knight.png')
        }

    def draw_board(self, screen):
        colors = [(4,13,52), (74,151,215)]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                pygame.draw.rect(screen, color, (col * 75, row * 75, 75, 75))

    def highlight_square(self, screen, row, col):
        """used when a piece is selected"""
        square_size = 75
        highlight_color = (255, 255, 0)  # Yellow

        pygame.draw.rect(screen, highlight_color, (
        col * square_size, row * square_size, square_size, square_size), 4)

    def fen_to_2d_array(self):
        """Translates between the FEN style board representation and the game's 2d
        array"""
        board = chess.Board(str(self.chessgame))

        board_2d = []

        for rank in board.board_fen().split()[0].split('/'):
            row = []
            for char in rank:
                if char.isdigit():
                    # If it's a number, add empty squares
                    for _ in range(int(char)):
                        row.append(None)
                else:
                    # If it's a piece, add the piece
                    row.append(char)
            board_2d.append(row)
        print(f"board_2d is now {board_2d}")
        self._board = board_2d

    def draw_pieces(self, screen):
        """get images for chess pieces and draw onto the board"""
        square_size = 75  # Assuming each square is 75x75 pixels

        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece:
                    piece = self.piece_mapping.get(piece, None)

                    if piece:
                        image = pygame.image.load(piece)
                        transparent_color = (255,255,255)
                        image.set_colorkey(transparent_color)
                    if image:
                        # Scale the image to fit the square size
                        image = pygame.transform.scale(image,
                                                       (square_size, square_size))
                        screen.blit(image, (col * square_size, row * square_size))

    def calculate_clicked_square(self, mouse_x, mouse_y):

        square_size = 75
        clicked_row = mouse_y // square_size
        clicked_col = mouse_x // square_size

        if clicked_row < 0 or clicked_row >= 8 or clicked_col < 0 or clicked_col >= 8:
            return None

        # Set the selected square
        self.selected_square = (clicked_row, clicked_col)

        return clicked_row, clicked_col

    def get_game_state(self):
        """Returns the game state, which is either UNFINISHED, WHITE_WINS, BLACK_WINS
        or TIE"""
        return self._game_state


    def switch_turn(self):
        """switches the player's turn, after each player's move"""
        if self._game_state == "UNFINISHED":
            if self._turn == "white":
                 self._turn = "black"
            elif self._turn == "black":
                 self._turn = "white"

    def get_turn(self):
        """returns the player whose turn it currently is"""
        return self._turn


    def numeric_string_to_half_fen(self, numeric_string):
        # if len(numeric_string) != 2:
        #     raise ValueError("Input must be a numeric string of length 2.")
        if numeric_string[0] not in ['0', '1', '2', '3', '4', '5', '6', '7']:
            return numeric_string
        rank = 8 - int(numeric_string[0])  # FEN doesn't use zero indexing
        file = int(numeric_string[1])

        # Convert to chess coordinates
        file_letter = chr(ord('a') + file)
        half_fen = f"{file_letter}{rank}"

        return half_fen


    def make_move(self, move_from, move_to):
        """takes two parameters - strings that represent
        the square moved from and the square moved to. For example, make_move('b3',
        'c4'). If the square being moved from does not contain a piece belonging to the
        player whose turn it is, or if the indicated move is not legal, or if the game
         has already been won, then it returns False. Otherwise it
         makes the indicated move, removes any captured piece, updates the game state,
         updates whose turn it is, and returns True."""

        if move_from == move_to:
            print("Invalid move. There must be a different starting and ending square.")
            return False

        move = self.numeric_string_to_half_fen(move_from) + \
               self.numeric_string_to_half_fen(move_to)

        possible_moves = self.chessgame.get_moves()
        print(f"possible moves are: {possible_moves}")
        print(f"{self.get_turn()}'s move is {move}")

        if not possible_moves:
            self.switch_turn()
            print(f"CHECKMATE! {self.get_turn()} wins!")
            pygame.time.delay(2000)

            self._game_state = "FINISHED"

        if move in possible_moves:
            self.chessgame.apply_move(move)
            self.fen_to_2d_array()
            self.animation_progress = 0.0
            start_row, start_col = int(move_from[1]) - 1, ord(move_from[0]) - ord('a')
            end_row, end_col = int(move_to[1]) - 1, ord(move_to[0]) - ord('a')
            self.animation_start = (start_row, start_col)
            self.animation_end = (end_row, end_col)

            # Switch turns after the move
            self.switch_turn()

            print(f" move {move} just now made, current turn is now {self._turn}")



        else:
            print(f"move {move} not in possible_moves")

            return False

        return True


    def check_for_win(self):
        """refactor for checkmate"""
        if self._game_state != "UNFINISHED":
            print(self._game_state)

    def animate_move(self, screen):
        if self.animation_progress < 1.0 and self.animation_start is not None and self.animation_end is not None:
            # Interpolate the current position based on the animation progress
            current_row = int(self.animation_start[0] + (
                    self.animation_end[0] - self.animation_start[
                0]) * self.animation_progress)
            current_col = int(self.animation_start[1] + (
                    self.animation_end[1] - self.animation_start[
                1]) * self.animation_progress)

            # Check if the current position is within the valid range
            if 0 <= current_row < 8 and 0 <= current_col < 8:
                # Draw the board and pieces as usual
                self.draw_board(screen)
                self.draw_pieces(screen)

                # Draw the moving piece at the interpolated position
                square_size = 75
                piece = self._board[current_row][current_col]
                if piece:
                    piece_path = self.piece_mapping.get(piece, None)
                    if piece_path:
                        image = pygame.image.load(piece_path)
                        transparent_color = (255, 255, 255)
                        image.set_colorkey(transparent_color)
                        image = pygame.transform.scale(image,
                                                       (square_size, square_size))
                        screen.blit(image,
                                    (current_col * square_size,
                                     current_row * square_size))

            # Update the animation progress
            self.animation_progress += pygame.time.get_ticks() / (
                    1000.0 * self.animation_duration)
            pygame.display.flip()
        else:
            # Animation complete, reset animation parameters
            self.animation_progress = 0.0
            self.animation_start = None
            self.animation_end = None

    def get_mouse_move(self, event):
        if event.type == MOUSEBUTTONDOWN:
            mouse_sound.play()
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = pygame.mouse.get_pos()
                clicked_square = self.calculate_clicked_square(mouse_x, mouse_y)
                # pygame.time.set_timer(pygame.USEREVENT, 100)

                if clicked_square is not None:
                    # The player clicked a valid square; you can now process the click.
                    col, row = clicked_square
                    # Perform actions based on the clicked square.
                    # print(f"Clicked square: Row {row}, Column {col}")
            return str(col) + str(row)


    def run_stockfish(self, fen_position):
        stockfish_path = '/opt/homebrew/bin/stockfish'
        board = chess.Board(fen_position)

        # Initialize the Stockfish engine
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            result = engine.play(board, chess.engine.Limit(
                time=2.0))  # Example: 2 seconds per move

        return result.move

def main():

    chess = Chess()
    pygame.display.set_caption("Galactic Chess")

    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()

    pygame.display.flip()
    from_move = None  # Initialize from_move and to_move as None
    to_move = None

    while chess.get_game_state() == "UNFINISHED":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:

            if chess._turn == "white":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                    mouse_sound.play()
                    if from_move is None:
                        from_move = chess.get_mouse_move(event)
                    elif to_move is None:
                        to_move = chess.get_mouse_move(event)

                    if from_move and to_move:
                        chess.make_move(from_move, to_move)
                        from_move = None
                        to_move = None
                        # You should call animate_move after processing user input
                        # to allow for gradual animation over multiple frames.
                        chess.animate_move(screen)

            else:
                best_move = chess.run_stockfish(str(chess.chessgame))
                best_move = str(best_move)
                print("Best move:", best_move)
                from_move = best_move[:2]
                to_move = best_move[2:4]
                chess.make_move(from_move, to_move)
                from_move = None
                to_move = None

        chess.draw_board(screen)
        chess.draw_pieces(screen)

        # Highlight the selected square
        if chess.selected_square:
            row, col = chess.selected_square
            chess.highlight_square(screen, row, col)

        # Check if an animation is in progress and perform it
        chess.animate_move(screen)

        pygame.display.set_caption(chess.get_turn() + "'s turn:")

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()

