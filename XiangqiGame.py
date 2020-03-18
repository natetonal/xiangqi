# Author: Nate Kimball
# Date: 2/24/2020
# Description: A program that implements the Chinese board game of Xiangqi. This implementation controls turns,
#              allows players to make legal moves, capture pieces, reports the game status, and determines a winning
#              game situation.


class XiangqiGame:
    """ A class that defines a game of Xiangqi, to include a Board, Players, and Pieces. """

    def __init__(self):
        """ Initializes a new Xiangqi game with a new board, piece set, game state, and player definitions. """

        self._board = Board()
        self._pieces = Pieces(self._board)
        self._players = (self._board.red(), self._board.black())
        self._game_states = ('UNFINISHED', 'RED_WON', 'BLACK_WON')
        self._current_game_state = self._game_states[0]
        self._current_player = self._players[0]

        # Maps all initial attack ranges for each piece on the board.
        self._pieces.map_all_attack_ranges(self._board, self._pieces)

    def print_board(self):
        """ Prints the current board layout. """

        self._board.print_board()

    def get_game_state(self):
        """ Returns the current game state. """

        return self._current_game_state

    def is_in_check(self, color):
        """ Determines whether or not the given General is in check by checking the opponent's attack map. """

        return self._pieces.is_in_check(color)

    def make_move(self, pos1, pos2, test=False):
        """ Attempts the move inputted by the user. Returns true or false depending on whether or not the move is valid.
        If test is set to True, the method will set the board back to the previous move after completing this move. """

        # If the game is over, then the user cannot make a move.
        if self._current_game_state != self._game_states[0]:
            # print("ERROR: The game has ended.")
            return False

        # If the user makes a valid move, make the move, update the board layout, and remap all attacked squares.
        if self._pieces.is_valid_move(pos1, pos2, self._board, self._pieces, self._current_player) is True:
            self._pieces._remove_captured_piece(pos2, self._current_player)
            self._pieces.get_piece_by_pos(pos1).update_pos(pos2)
            self._board.update_layout(self._pieces)
            self._pieces.map_all_attack_ranges(self._board, self._pieces)

            # If this move caused the General to be in check, undo it and return False.
            if self.is_in_check(self._current_player) is True:
                # print("ERROR: Move cannot leave General in check.")
                self._undo_move(pos1, pos2)
                return False

            # If this was a test move, return the board to its original position and mark move as valid.
            # Otherwise, switch the player and check if the game has ended.
            else:
                # print(f"Valid Move Made: {pos1} - {pos2}.")
                if test is True:
                    self._undo_move(pos1, pos2)
                else:
                    self._switch_player()
                    self._update_game_state()
            return True

        # print(f"Invalid Move Made: {pos1} - {pos2}.")
        return False

    def _undo_move(self, pos1, pos2):
        """ Helper method that resets the board to its state before the most recent attempted move. """

        # Set move to previous move, restore any captured pieces, and update layout/attack ranges.
        self._pieces.get_piece_by_pos(pos2).update_pos(pos1)
        self._pieces._restore_captured_piece()
        self._board.update_layout(self._pieces)
        self._pieces.map_all_attack_ranges(self._board, self._pieces)

    def _switch_player(self):
        """ Helper method that toggles the current player. """

        if self._current_player == self._players[0]:
            self._current_player = self._players[1]
        else:
            self._current_player = self._players[0]

    def _update_game_state(self):
        """ Checks the current game state for a checkmate or stalemate situation for either color and updates state. """

        # Check if the game is over, and if so, update the game state to reflect the winner.
        if self._is_game_over():
            if self._current_player == self._players[0]:
                self._current_game_state = self._game_states[2]
            else:
                self._current_game_state = self._game_states[1]

    def _is_game_over(self):
        """ Checks the board for a checkmate or stalemate position for current player. """

        # Retrieve all possible moves for the current player from their attack map.
        all_moves = self._pieces.get_all_possible_moves(self._current_player)

        # If there are any valid moves in the moves list, the game is still unfinished.
        for move in all_moves:
            if self.make_move(move[0], move[1], True) is True:
                return False

        # Otherwise, the game is over.
        return True


class Pieces:
    """ A collection of Piece objects. Pieces performs iterative operations on the current collection of pieces,
    including retrieving a Piece by its current position, mapping/updating the attack ranges for each player, and
    performing basic validation that would be true or false for any type of piece. """

    def __init__(self, board):
        """ Initializes a set of pieces from the starting board layout. """

        # A collection of Piece objects, initialized from the board layout.
        self._pieces = {}

        # Quick definitions for the player colors.
        self._red = board.red()
        self._black = board.black()

        # Maps of points on the board that pieces are currently attacking, separated by color.
        # Attack maps have positions as keys, and a list of the labels of attacking pieces for that position as a value.
        self._red_attack_map = {}
        self._black_attack_map = {}

        # Store the most recently captured piece for undo operation.
        self._captured_piece = None

        # Initialize all pieces from the starting board position and store to self._pieces.
        self._initialize_pieces(board)

    def get_all_pieces(self):
        """ Gets a dictionary of all the pieces keyed by label. """

        return self._pieces

    def get_all_possible_moves(self, color):
        """ Gets a list of tuples representing a move. List represents all possible moves for a given color. """

        all_moves = []
        attack_map = self.get_attack_map(color)

        # Iterate through all pieces in all destinations in this color's attack map, pushing a tuple of the
        # piece's current position and attack map destination.
        for pos2, pieces in attack_map.items():
            for label in pieces:
                piece = self.get_piece_by_label(label)
                all_moves.append((piece.get_current_pos(), pos2))

        return all_moves

    def get_pieces_by_pos(self):
        """ Returns the pieces collection with the current pos as key. """

        pieces_by_pos = {}

        for piece in self._pieces.values():
            pieces_by_pos[piece.get_current_pos()] = piece

        return pieces_by_pos

    def get_piece_by_label(self, label):
        """ Gets a piece by its label. If it doesn't exist, returns None. """

        if label in self._pieces:
            return self._pieces[label]

        return None

    def get_piece_by_pos(self, pos):
        """ Returns the piece at a given position, or None if the position is unoccupied or invalid. """

        for piece in self._pieces.values():
            if piece.get_current_pos() == pos:
                return piece

        return None

    def get_attack_map(self, color):
        """ Returns the attack map for a given color. """

        if color is self._red:
            return self._red_attack_map

        return self._black_attack_map

    def is_in_check(self, color):
        """ Determines whether or not a player is currently in check by checking if their General's position is
        listed as a key in their opponent's attack map. """

        # If checking black General, see if any piece on red's attack map is attacking the General's position.
        if color.lower() == 'black' or color == self._black:
            attack_map = self._red_attack_map
            general_pos = self.get_piece_by_label('GB1').get_current_pos()

        # If checking red General, see if any piece on black's attack map is attacking the General's position.
        elif color.lower() == 'red' or color == self._red:
            attack_map = self._black_attack_map
            general_pos = self.get_piece_by_label('GR1').get_current_pos()

        # If something other than 'black' or 'red' was entered, return None.
        else:
            # print("ERROR: Invalid color entered. Please enter 'red' or 'black'.")
            return None

        # Otherwise, return whether or not this General is in the opponent's attack map.
        return general_pos in attack_map

    def is_valid_move(self, pos1, pos2, board, pieces, current_player):
        """ Runs a series of validations on all piece types as well as the piece's own validation. """

        # If one of the moves is not a valid position, the move is invalid.
        if board.is_valid_pos(pos1) is False or board.is_valid_pos(pos2) is False:
            # print("ERROR: Invalid position entered.")
            return False

        # If the two positions entered are the same, the move is invalid.
        if pos1 == pos2:
            # print("ERROR: Must move to a position other than current.")
            return False

        # Get the piece at pos1.
        pos1_piece = self.get_piece_by_pos(pos1)

        # If there's no piece there, this move is invalid.
        if pos1_piece is None:
            # print("ERROR: No piece at given square.")
            return False

        # If the piece is not the color of the current player, the move is invalid.
        if pos1_piece.get_color() != current_player:
            # print("ERROR: Wrong color.")
            return False

        # Get the piece at pos2.
        pos2_piece = self.get_piece_by_pos(pos2)

        # If the piece at pos2 is the same color as the piece at pos1, the move is invalid.
        if pos2_piece is not None and pos2_piece.get_color() == current_player:
            # print("ERROR: Same color piece at destination.")
            return False

        # Return True if this is a valid move for this specific piece type. Otherwise, False.
        return pos1_piece.is_valid_move(pos1, pos2, board, pieces, current_player)

    def map_all_attack_ranges(self, board, pieces):
        """ Maps all possible attack squares (valid moves) for each piece to its attack_range data member. """

        for piece in self._pieces.values():
            piece.map_attack_range(board, pieces, self.is_valid_move)

        self._update_attack_ranges()

    def _remove_captured_piece(self, pos, current_player):
        """ Removes a captured piece from the Pieces collection.  """

        # If an enemy piece was on the destination square, delete it from the collection.
        # Store the removed piece for one move length in case the move needs to be undone.
        piece_at_dest = self.get_piece_by_pos(pos)
        if piece_at_dest is not None and piece_at_dest.get_color() != current_player:
            self._captured_piece = self._pieces[piece_at_dest.get_label()]
            del self._pieces[piece_at_dest.get_label()]
            return

        self._captured_piece = None

    def _restore_captured_piece(self):
        """ Restores a piece that was captured last move, if any. Used only for undoing the last move. """

        if self._captured_piece is not None:
            self._pieces[self._captured_piece.get_label()] = self._captured_piece
            self._captured_piece = None

    def _update_attack_ranges(self):
        """ Updates the attack ranges for each player by iterating over each Piece in the collection and
         mapping its valid moves to the appropriate dictionary. """

        red_attack_map = {}
        black_attack_map = {}

        for piece in self._pieces.values():
            attack_range = piece.get_attack_range()

            if len(attack_range) > 0:
                for attacked_sq in attack_range:
                    if piece.get_color() == 'R' and attacked_sq not in red_attack_map:
                        red_attack_map[attacked_sq] = [piece.get_label()]
                    elif piece.get_color() == 'R' and attacked_sq in red_attack_map:
                        red_attack_map[attacked_sq].append(piece.get_label())
                    elif piece.get_color() == 'B' and attacked_sq not in black_attack_map:
                        black_attack_map[attacked_sq] = [piece.get_label()]
                    elif piece.get_color() == 'B' and attacked_sq in black_attack_map:
                        black_attack_map[attacked_sq].append(piece.get_label())

        self._red_attack_map = red_attack_map
        self._black_attack_map = black_attack_map

    def _initialize_pieces(self, board):
        """ Static helper method that initializes a set of Piece objects using the starting board layout. """

        pieces = {}
        layout = board.get_layout()

        # Determine which piece to create from its board label, initialize it, and store it to the Pieces collection.
        for i, row in enumerate(layout):
            for j, square in enumerate(row):
                if square[0] == 'C':
                    pieces[square] = Chariot(square, board.get_pos_from_coordinates(i, j), board)
                elif square[0] == 'N':
                    pieces[square] = Cannon(square, board.get_pos_from_coordinates(i, j), board)
                elif square[0] == 'H':
                    pieces[square] = Horse(square, board.get_pos_from_coordinates(i, j))
                elif square[0] == 'E':
                    pieces[square] = Elephant(square, board.get_pos_from_coordinates(i, j))
                elif square[0] == 'A':
                    pieces[square] = Advisor(square, board.get_pos_from_coordinates(i, j))
                elif square[0] == 'G':
                    pieces[square] = General(square, board.get_pos_from_coordinates(i, j))
                elif square[0] == 'S':
                    pieces[square] = Soldier(square, board.get_pos_from_coordinates(i, j))

        self._pieces = pieces


class Piece:
    """ A class that defines a Piece in a Xiangqi Game. All piece types are subclassed from Piece. """

    def __init__(self, label, pos):
        """ Initializes a Piece with a label, type, color, count, current position, and attack range. """

        self._label = label
        self._type = label[0]
        self._color = label[1]
        self._count = label[2]
        self._current_pos = pos
        self._range = []
        self._attack_range = []

    def get_type(self):
        """ Gets the type of piece this is as a single upper-case character. """

        return self._type

    def get_color(self):
        """ Returns the piece's color. 'R' for Red, and 'B' for Black. """

        return self._color

    def get_label(self):
        """ Gets the unique label for this piece, a 3 character sequence with type, color, and count. """

        return self._label

    def get_current_pos(self):
        """ Returns the current cardinal position for this piece. """

        return self._current_pos

    def get_attack_range(self):
        """ Returns a list of positions that this piece can legally move to. """

        return self._attack_range

    def update_pos(self, pos):
        """ Updates the current position of the piece. """

        self._current_pos = pos

    def map_attack_range(self, board, pieces, is_valid_move):
        """ Determines all attacking points (valid moves) for a piece.  """

        self._map_attack_range_from_offsets(board, pieces, is_valid_move)

    def _map_attack_range_from_offsets(self, board, pieces, is_valid_move, offsets=None):
        """ Determines all attacking points (valid moves) for this piece by mapping from a list of offsets. """

        # Container for all possible attack ranges.
        attack_range = []

        # Attack range is derived either from the piece's self._range or a passed 'offsets' list.
        offsets = self._range if offsets is None else offsets

        # Get the current position for this piece to use in testing its offsets.
        current_pos = self.get_current_pos()

        # Test each point in this piece's range. If this piece can legally move there, add point to its attack range.
        for offset in offsets:
            offset_col = chr(ord(current_pos[0]) + offset[0])
            offset_row = str(int(current_pos[1:]) + offset[1])
            dest_pos = offset_col + offset_row

            if is_valid_move(current_pos, dest_pos, board, pieces, self.get_color()):
                attack_range.append(dest_pos)

        # Set resulting attack range for this piece.
        self._attack_range = attack_range


class General(Piece):
    """ A subclass that defines a General Piece. """

    def __init__(self, label, pos):
        """ Initializes a General piece with its own movement, capture, and validation style. """

        super().__init__(label, pos)

        # Establish a collection of offsets as a range of motion for the General for validating moves.
        self._range = [(-1, 0), (0, -1), (0, 1), (1, 0)]

    def is_valid_move(self, pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for a General. """

        # If the move is not inside this player's palace, then return False.
        if board.is_in_palace(pos2, current_player) is not True:
            # print("ERROR: Move is outside of the palace.")
            return False

        # If the move is farther than one point orthogonally, return False.
        if not (
                abs(ord(pos1[0]) - ord(pos2[0])) == 0 and abs(int(pos1[1:]) - int(pos2[1:])) == 1 or
                abs(ord(pos1[0]) - ord(pos2[0])) == 1 and abs(int(pos1[1:]) - int(pos2[1:])) == 0
        ):
            # print("ERROR: Generals can only move 1 point orthogonally.")
            return False

        # Locate the enemy general if it exists. If 'None', then the move is valid.
        enemy_general = pieces.get_piece_by_label('GB1' if current_player == board.red() else 'GR1')

        if enemy_general is None:
            return True

        # If the generals will be in the same column by this move, we need to check if they "see" each other.
        enemy_pos = enemy_general.get_current_pos()
        if enemy_pos[0] == pos2[0]:

            # Get the column where the two generals are located and fill in the move this general will make with a 'G'.
            column = board.get_column(pos2[0])
            column[int(pos2[1:]) - 1] = self.get_type()

            # Slice the column to focus on the position of these two generals and what is between them.
            column_lo = min(int(pos2[1:]) - 1, int(enemy_pos[1:]) - 1)
            column_hi = max(int(pos2[1:]), int(enemy_pos[1:]))
            column = [point for point in column[column_lo:column_hi] if point != '---']

            # If it's only empty space, then this move is invalid.
            if all(point[0] == self.get_type() for point in column):
                # print("ERROR: Generals cannot see each other.")
                return False

        return True


class Advisor(Piece):
    """ A subclass that defines a Advisor Piece. """

    def __init__(self, label, pos):
        """ Initializes an Advisor piece with its own movement, capture, and validation style. """

        super().__init__(label, pos)

        # Establish a collection of offsets as a range of motion for the Advisor for validating moves.
        self._range = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    @staticmethod
    def is_valid_move(pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for the Advisor. """

        # If the move is not inside this player's palace, then it is invalid.
        if board.is_in_palace(pos2, current_player) is not True:
            # print("ERROR: Move is outside of the palace.")
            return False

        # If the move is not exactly one point away diagonally, return False.
        if abs(ord(pos1[0]) - ord(pos2[0])) is not 1 or abs(int(pos1[1:]) - int(pos2[1:])) is not 1:
            # print("ERROR: Advisors can only move 1 point diagonally.")
            return False

        return True


class Elephant(Piece):
    """ A subclass that defines a Elephant Piece. """

    def __init__(self, label, pos):
        """ Initializes an Elephant piece with its own movement, capture, and validation style. """

        super().__init__(label, pos)

        # Establish a collection of offsets as a range of motion for the Elephant for validating moves.
        self._range = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

    @staticmethod
    def is_valid_move(pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for the Elephant. """

        # If the move is not inside this player's river, then return False.
        if board.is_behind_river(pos2, current_player) is not True:
            # print("ERROR: Move is outside of the palace.")
            return False

        # If pos2 is not exactly two diagonal points away from pos1, then the move is not valid.
        if abs(ord(pos1[0]) - ord(pos2[0])) is not 2 or abs(int(pos1[1:]) - int(pos2[1:])) is not 2:
            # print("ERROR: Piece must move exactly two diagonal points.")
            return False

        # If there is a piece blocking the diagonal between pos1 and pos2, then this move cannot be made.
        middle_pos = chr(ord(max(pos1[0], pos2[0])) - 1) + str(max(int(pos1[1:]), int(pos2[1:])) - 1)
        if pieces.get_piece_by_pos(middle_pos) is not None:
            # print("ERROR: Cannot jump over a piece.")
            return False

        return True


class Horse(Piece):
    """ A subclass that defines a Horse Piece. """

    def __init__(self, label, pos):
        """ Initializes a Horse piece with its own movement, capture, and validation style. """

        super().__init__(label, pos)

        # Establish a collection of offsets as a range of motion for the Horse for validating moves.
        self._range = [(2, 1), (2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]

    def is_valid_move(self, pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for the Horse. """

        # If pos2 is not one orthogonal + one diagonal point away from pos1, then this move is invalid.
        if (ord(pos1[0]) - ord(pos2[0]), int(pos1[1:]) - int(pos2[1:])) not in self._range:
            # print("ERROR: Piece must move one orthogonal + one diagonal point away.")
            return False

        # If there's a piece one space orthogonally in the direction this piece is moving, then the move is invalid.
        # First check if a piece is blocking on the immediate left or right.
        if (
                abs(ord(pos1[0]) - ord(pos2[0])) == 2 and
                pieces.get_piece_by_pos(chr(max(ord(pos1[0]) - 1, ord(pos2[0]) - 1)) + pos1[1:]) is not None
        ):
            # print("ERROR: Cannot leap over a blocking piece (row).")
            return False

        # Then check if a piece is blocking above or below.
        if (
                abs(int(pos1[1:]) - int(pos2[1:])) == 2 and
                pieces.get_piece_by_pos(pos1[0] + str(min(int(pos1[1:]) + 1, int(pos2[1:]) + 1))) is not None
        ):
            # print("ERROR: Cannot leap over a blocking piece (col).")
            return False

        return True


class Chariot(Piece):
    """ A subclass that defines a Chariot Piece. """

    def __init__(self, label, pos, board):
        """ Initializes a Chariot piece with its own movement, capture, and validation style. Positional ranges
        for the Chariot are also calculated upon initialization. """

        super().__init__(label, pos)

        self._horizontal_range = []
        self._vertical_range = []
        self._pos_range = []

        # Determine all valid moves for the Chariot by analyzing its entire rank and file for the next closest piece
        # in any orthogonal direction.
        self._update_ranges(pos, board)

    def map_attack_range(self, board, pieces, is_valid_move):
        """ Overrides Piece's map_attack_range to update all ranges before calling the mapping method. """

        self._update_ranges(self.get_current_pos(), board)
        self._map_attack_range_from_offsets(board, pieces, is_valid_move)

    def is_valid_move(self, pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for the Chariot. """

        # If the move is not within the Chariot's movement range, then the move is invalid.
        # Validation for Chariot is already done by update_range, so simply check if pos2 is in pos_range.
        if pos2 not in self._pos_range:
            # print("ERROR: That position is outside the Chariot's range.")
            return False

        return True

    def _update_ranges(self, pos, board):
        """ Updates the horizontal range, vertical range, and total range of the Chariot. """

        def _get_offsets_from_positions(target_pos, pos_list):
            """ Returns a list of numeric offsets from a target position from a list of positions. """

            # Returns a new list of (i, j) tuple offsets from the given position.
            return [(ord(move[0]) - ord(target_pos[0]), int(move[1:]) - int(target_pos[1:])) for move in pos_list]

        # Solve & store range of Chariot to closest pieces on its rank and file.
        row = self._filter_range_by_closest_pieces(pos, board.get_row_positions(pos[1:]), board)
        col = self._filter_range_by_closest_pieces(pos, board.get_column_positions(pos[0]), board)
        self._pos_range = row + col

        # The chariot's valid range will be determined by all points of its current row and column.
        self._horizontal_range = _get_offsets_from_positions(pos, row)
        self._vertical_range = _get_offsets_from_positions(pos, col)

        # Convert between set & list to clear the duplicate cross-section point.
        self._range = list(set(self._horizontal_range + self._vertical_range))

    def _filter_range_by_closest_pieces(self, pos, pos_arr, board):
        """ Takes a row/column and returns the list reduced to the closest pieces from pos on either side, if any.  """

        # Filter left and right sides of current position to the next closest piece.
        # Make sure to flip the left side to keep the origin point the same.
        left_of_pos = self._filter_side_of_piece(pos_arr[:pos_arr.index(pos)][::-1], board)
        right_of_pos = self._filter_side_of_piece(pos_arr[pos_arr.index(pos) + 1:], board)

        # Return concatenated list with newly filtered left and right sides.
        return left_of_pos[::-1] + [pos] + right_of_pos

    def _filter_side_of_piece(self, side_arr, board):
        """ A helper method that returns a list of valid moves in a given orthogonal direction from the Chariot. """

        # The valid filtered positions to be returned to the calling method.
        filtered = []

        # Moves are valid in this direction until a non-empty square is reached.
        for point in side_arr:
            label = board.get_value_at_pos(point)
            if label is not board.empty():
                filtered.append(point)
                break
            else:
                filtered.append(point)

        return filtered


class Cannon(Chariot):
    """ A subclass of a Chariot that defines a Cannon Piece. """

    def __init__(self, label, pos, board):
        """ Initializes a Cannon piece with same set of properties as a Chariot, since the only difference is which
        points are considered valid movement for a Cannon vs. a Chariot. """

        super().__init__(label, pos, board)

    def _filter_side_of_piece(self, side_arr, board):
        """ A helper method that returns a list of valid moves in a given orthogonal direction from the Cannon. """

        # The valid filtered positions to be returned to the calling method.
        filtered = []

        # A boolean that returns whether or not a piece has been leaped over in the given orthogonal direction.
        piece_leaped = False

        # Examine all positions in this direction until last valid position is reached.
        for point in side_arr:
            label = board.get_value_at_pos(point)

            # If there is a piece at this point:
            if label is not board.empty():
                # If the piece is the same color, add it to the 'valid' moves since the main validator will catch it.
                # Flip the piece_leaped to True.
                if not piece_leaped:
                    if label[1] == self.get_color():
                        filtered.append(point)
                    piece_leaped = True

                # If we've already leaped over a piece and this piece is an opponent piece, add it. Either way, break.
                else:
                    if label[1] != self.get_color():
                        filtered.append(point)
                        break
                    break

            # If the square is empty and we haven't leaped over a piece, add it in.
            else:
                if not piece_leaped:
                    filtered.append(point)

        return filtered


class Soldier(Piece):
    """ A subclass that defines a Soldier Piece. """

    def __init__(self, label, pos):
        super().__init__(label, pos)

        # Range offsets for behind and ahead of the river, for red and black respectively.
        self._range_lo = {
            'R': [(0, 1)],
            'B': [(0, -1)]
        }
        self._range_hi = {
            'R': [(0, 1), (-1, 1), (1, 1)],
            'B': [(0, -1), (-1, -1), (1, -1)]
        }

    def map_attack_range(self, board, pieces, is_valid_move):
        """ Overrides Piece's map_attack_range method to send the correct offsets depending on what color piece
        it is and whether or not the Solider is past the river. """

        if board.is_behind_river(self.get_current_pos(), self.get_color()) is not True:
            return self._map_attack_range_from_offsets(board, pieces, is_valid_move, self._range_hi[self.get_color()])

        self._map_attack_range_from_offsets(board, pieces, is_valid_move, self._range_lo[self.get_color()])

    def is_valid_move(self, pos1, pos2, board, pieces, current_player):
        """ Determines whether or not the current move is legal for the Soldier. """

        is_behind_river = board.is_behind_river(pos2, current_player)

        # If the soldier is behind the river and did not move exactly one point forward, the move is invalid.
        if is_behind_river is True:
            range_lo = self._range_lo[self.get_color()]
            if pos1[0] != pos2[0] or int(pos2[1:]) - int(pos1[1:]) != range_lo[0][1]:
                return False

        # If the soldier is beyond the river and did not move one point forward, left, or right, the move is invalid.
        if is_behind_river is False:
            range_hi = self._range_hi[self.get_color()]

            if not (
                    abs(ord(pos1[0]) - ord(pos2[0])) == 1 and int(pos2[1:]) - int(pos1[1:]) == 0 or
                    abs(ord(pos1[0]) - ord(pos2[0])) == 0 and int(pos2[1:]) - int(pos1[1:]) == range_hi[0][1]
            ):
                return False

        return True


class Board:
    """ A class that initializes, updates, and displays a Xiangqi board. """

    def __init__(self):

        # The starting position for the board. Used to initialize Pieces in the "Pieces" class.
        self._layout = [
            ["CR1", "HR1", "ER1", "AR1", "GR1", "AR2", "ER2", "HR2", "CR2"],
            ["---", "---", "---", "---", "---", "---", "---", "---", "---"],
            ["---", "NR1", "---", "---", "---", "---", "---", "NR2", "---"],
            ["SR1", "---", "SR2", "---", "SR3", "---", "SR4", "---", "SR5"],
            ["---", "---", "---", "---", "---", "---", "---", "---", "---"],
            ["---", "---", "---", "---", "---", "---", "---", "---", "---"],
            ["SB1", "---", "SB2", "---", "SB3", "---", "SB4", "---", "SB5"],
            ["---", "NB1", "---", "---", "---", "---", "---", "NB2", "---"],
            ["---", "---", "---", "---", "---", "---", "---", "---", "---"],
            ["CB1", "HB1", "EB1", "AB1", "GB1", "AB2", "EB2", "HB2", "CB2"]
        ]

        # A list of helpful attributes defining a board.
        self._red = 'R'
        self._black = 'B'
        self._empty = '---'
        self._width = 9
        self._height = 10
        self._columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self._rows = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        self._red_palace = ['d1', 'e1', 'f1', 'd2', 'e2', 'f2', 'd3', 'e3', 'f3']
        self._black_palace = ['d8', 'e8', 'f8', 'd9', 'e9', 'f9', 'd10', 'e10', 'f10']
        self._palaces = self._red_palace + self._black_palace

    def empty(self):
        """ Returns the string value of an empty point on the board. """

        return self._empty

    def red(self):
        """ Returns the string value for a red player or piece. """

        return self._red

    def black(self):
        """ Returns the string value for a black player or piece. """

        return self._black

    def get_layout(self):
        """ Returns the current board layout as a list of lists. """

        return self._layout

    def get_row(self, row, pos1='a', pos2='i'):
        """ Returns all contents of this row with optional start & end points. None if invalid. """

        if row not in self._rows or pos1 not in self._columns or pos2 not in self._columns:
            return None

        return self._layout[int(row) - 1][ord(pos1) - ord('a'): ord(pos2) - ord('a') + 1]

    def get_row_positions(self, row, pos1='a', pos2='i'):
        """ Returns all cardinal positions for this row with optional start & end points. None if invalid. """

        if row not in self._rows or pos1 not in self._columns or pos2 not in self._columns:
            return None

        return [col + row for col in self._columns[ord(pos1) - ord('a'): ord(pos2) - ord('a') + 1]]

    def get_column(self, col, pos1='1', pos2='10'):
        """ Returns all contents in this column with optional start & end points from low to high. None if invalid. """

        if col not in self._columns or pos1 not in self._rows or pos2 not in self._rows:
            return None

        column = []

        pos_lo = self.get_coordinates_from_pos(col + str(min(int(pos1), int(pos2))))
        pos_hi = self.get_coordinates_from_pos(col + str(max(int(pos1), int(pos2))))

        for i in range(self._height):
            for j in range(self._width):
                if j == pos_lo[1] and pos_lo[0] <= i <= pos_hi[0]:
                    column.append(self._layout[i][j])

        return column.reverse() if int(pos1) > int(pos2) else column

    def get_column_positions(self, col, pos1='1', pos2='10'):
        """ Returns all cardinal positions for this row with optional start & end points. None if invalid. """

        if col not in self._columns or pos1 not in self._rows or pos2 not in self._rows:
            return None

        return [col + row for row in self._rows[int(pos1) - 1: int(pos2)]]

    def get_pos_from_coordinates(self, row, col):
        """ Converts a row, col coordinates (i, j) to a position. Returns None if invalid.  """

        try:
            return self._columns[col] + self._rows[row] if int(row) >= 0 and int(col) >= 0 else None
        except IndexError:
            return None

    def get_value_at_coordinate(self, row, col):
        """ Returns the value on the board at coordinates (i, j). Returns None if invalid. """

        try:
            return self._layout[row][col] if int(row) >= 0 and int(col) >= 0 else None
        except IndexError:
            return None

    def get_value_at_pos(self, pos):
        """ Returns the value at a given position. None if invalid. """

        coords = self.get_coordinates_from_pos(pos)
        if coords is None:
            return None

        try:
            return self._layout[coords[0]][coords[1]] if int(coords[0]) >= 0 and int(coords[1]) >= 0 else None
        except IndexError:
            return None

    def get_coordinates_from_pos(self, pos):
        """ Converts a position to row, col coordinates (i, j). Returns None if invalid. """

        try:
            return self._rows.index(pos[1:]), self._columns.index(pos[0])
        except:
            return None

    def is_valid_pos(self, pos):
        """ Returns True/False depending on whether or not the position is valid. """

        return self.get_coordinates_from_pos(pos) is not None

    def is_in_palace(self, pos, color):
        """ Returns True/False depending on whether or not the position is in its color's palace. """

        if color == self._red:
            return pos in self._red_palace

        return pos in self._black_palace

    def is_behind_river(self, pos, color):
        """ Returns True/False depending on whether or not the position is behind the river on its own side. """

        if color == self._red and int(pos[1:]) <= 5:
            return True

        if color == self._black and int(pos[1:]) >= 6:
            return True

        return False

    def update_layout(self, pieces):
        """ Updates the layout of the board from a set of Pieces. """

        pieces_by_pos = pieces.get_pieces_by_pos()

        for i, row in enumerate(self._layout):
            for j, point in enumerate(row):
                pos = self.get_pos_from_coordinates(i, j)
                if pos in pieces_by_pos:
                    self._layout[i][j] = pieces_by_pos[pos].get_label()
                else:
                    self._layout[i][j] = self._empty

    def print_board(self):
        """ Prints the current board layout to console. """

        def _print_row_label():
            """ Print helper method to print column labels (a-i). """

            print("\x1b[1;5;30;47m   ", end='')
            for ltr in self._columns:
                print(f"  {ltr}  ", end='')
            print("\x1b[1;5;30;47m   \x1b[0;30;48m")

        def _print_col_label(idx, left=True, river=True):
            """ Print helper to print row labels (1-10) & river """

            lspace = '' if left is True else ' '
            rspace = '' if left is False else ' '

            if idx == 9:
                print(f"\x1b[1;5;30;47m{lspace}{i+1}{rspace}\x1b[0;30;48m", end='')
            else:
                if idx == 5 and river is True:
                    print("\x1b[0;34;44m" + "=" * 51 + "\x1b[0;30;48m")
                print(f"\x1b[1;5;30;47m {i+1} \x1b[0;30;48m", end='')

        _print_row_label()

        # Loop through board layout, printing pieces with appropriate color and position.
        for i, row in enumerate(self._layout):
            _print_col_label(i)
            for j, point in enumerate(row):
                bracket_l = '['
                bracket_r = ']'
                if self.get_pos_from_coordinates(i, j) in self._palaces:
                    bracket_l = '\x1b[1;33;48m<\x1b[0;30;48m'
                    bracket_r = '\x1b[1;33;48m>\x1b[0;30;48m'
                if point[1] == self._red:
                    print(f"{bracket_l}\x1b[1;31;48m {point[0]} \x1b[0;30;48m{bracket_r}", end='')
                elif point[1] == self._black:
                    print(f"{bracket_l}\x1b[1;36;48m {point[0]} \x1b[0;30;48m{bracket_r}", end='')
                elif point == self._empty:
                    print(f"{bracket_l}\x1b[0;37;48m   \x1b[0;30;48m{bracket_r}", end='')
                else:
                    print(f"{bracket_l}\x1b[0;37;48m {point} \x1b[0;30;48m{bracket_r}", end='')
            _print_col_label(i, False, False)
            print()

        _print_row_label()
        print()


