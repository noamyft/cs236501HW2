# ===============================================================================
# Imports
# ===============================================================================

import abstract
from utils import INFINITY, run_with_limited_time, ExceededTimeError
from Reversi.consts import EM, OPPONENT_COLOR, BOARD_COLS, BOARD_ROWS
import time
import copy
from collections import defaultdict
from utils import MiniMaxWithAlphaBetaPruning
import numpy as np
import random


# ===============================================================================
# Player
# ===============================================================================

class Player(abstract.AbstractPlayer):

    param = {"SCORE_CORNER":random.choice(range(5,50)),\
                "SCORE_PERIMETER_CORNER":random.choice(range(-2,-20)),\
                "SCORE_BORDER":random.choice(range(1,30)),\
                "SCORE_PERIMETER_BORDER":random.choice(range(-15,-1)),\
                "SCORE_ONE_TILE":random.choice(range(2,30)),\
                "SCORE_FRONTIER":random.choice(range(-10,-1))}
    DECAY = 1
    DECAY_INITIAL = 1.2
    DECAY_FACTOR = 250 # 250 outscored 120,200,300,1000



    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.time()

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.
        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        alphaBeta = MiniMaxWithAlphaBetaPruning(self.utilityBetter, player_color, self.no_more_time, False)
        self.search = alphaBeta.search

        # divide the board into 5 categories and score them from best to worst
        cells1Type = [2, 3, 4, 5]
        cells2TypeA = [1, 6]
        cells2TypeB = [2, 3, 4, 5]
        cells3TypeA = [0, 7]
        cells3TypeB = [2, 3, 4, 5]
        cells4Type = [0, 1, 6]
        cells5Type = [0, 7]
        # initiate the scoring matrix
        self.scoreMat = np.zeros((8, 8))
        for i in cells2TypeA:
            for j in cells2TypeB:
                self.scoreMat[i][j] = Player.SCORE_PERIMETER_BORDER
                self.scoreMat[j][i] = Player.SCORE_PERIMETER_BORDER
        for i in cells3TypeA:
            for j in cells3TypeB:
                self.scoreMat[i][j] = Player.SCORE_BORDER
                self.scoreMat[j][i] = Player.SCORE_BORDER
        for i in cells4Type:
            for j in cells4Type:
                self.scoreMat[i][j] = Player.SCORE_PERIMETER_CORNER
        for i in cells5Type:
            for j in cells5Type:
                self.scoreMat[i][j] = Player.SCORE_CORNER

    def get_move(self, game_state, possible_moves):
        self.clock = time.time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        depth = 2
        bestMove = None
        while not (self.no_more_time()):
            # print(" AB-The current depth is:",depth) # TODO remove
            score, currMove = self.search(game_state, depth, -INFINITY, INFINITY, True)
            if not (self.no_more_time()):
                bestMove = currMove
            # print("At ",depth, "depth best move is:", bestMove,"with score of:",score) # TODO remove

            depth += 1

        return bestMove

    def no_more_time(self):
        return (time.time() - self.clock) >= self.time_for_current_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'Decay')

    # *****      simple heuristic        *****#
    def utilitySimple(self, state):
        if len(state.get_possible_moves()) == 0: #TODO trying something new this heuristic looks wrong to me
            return INFINITY if state.curr_player != self.color else -INFINITY

        my_u = 0
        op_u = 0
        for x in range(BOARD_COLS):
            for y in range(BOARD_ROWS):
                if state.board[x][y] == self.color:
                    my_u += 1
                if state.board[x][y] == OPPONENT_COLOR[self.color]:
                    op_u += 1

        if my_u == 0:
            # I have no tools left
            return -INFINITY
        elif op_u == 0:
            # The opponent has no tools left
            return INFINITY
        # elif len(state.get_possible_moves()) == 0:
        #     print("NO MOVES",my_u - op_u) # TODO remove
        #     return INFINITY if (my_u - op_u > 0) else -INFINITY
        else:
            return my_u - op_u

    # *****      better heuristic        *****#
    def utilityBetter(self, state, verbose=False):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY

        my_u = 0
        op_u = 0
        (my_u, op_u) = np.array(self.scoreOfTiles(state)) \
                       + Player.SCORE_FRONTIER * np.array(self.countNumOfEmptyAroundTile(state)) \
                       + np.array(self.countUnemptyColRow(state))
        if verbose:
            (my_u1, op_u1) = self.scoreOfTiles(state)
            print("our score for tiles =", my_u1, "enemy score for tiles:", op_u1)
            (my_u1, op_u1) = self.countNumOfEmptyAroundTile(state)
            print("our empty around =", my_u1, "enemy empty around:", op_u1)
            (my_u1, op_u1) = self.countUnemptyColRow(state)
            print("our row-col =", my_u1, "enemy rowcol:", op_u1)
            print("Total score = ", my_u - op_u)

        """
        if my_u == 0:
            # I have no tools left
            return -INFINITY
        elif op_u == 0:
            # The opponent has no tools left
            return INFINITY

        else:"""
        return my_u - op_u

    def scoreOfTiles(self, state):
        # Uses the initial scoring mat to evaluate the state
        my_u = op_u = 0
        for x in range(BOARD_COLS):
            for y in range(BOARD_ROWS):
                if state.board[x][y] == self.color:
                    my_u += Player.DECAY * self.scoreMat[x][y] + Player.SCORE_ONE_TILE
                if state.board[x][y] == OPPONENT_COLOR[self.color]:
                    op_u += Player.DECAY * self.scoreMat[x][y] + Player.SCORE_ONE_TILE
        Player.DECAY = Player.DECAY_INITIAL - (my_u + op_u) / Player.DECAY_FACTOR  # CHANGE
        return [my_u, op_u]

    def countNumOfEmptyAroundTile(self, state):
        # Return the number of empty tiles
        my_u = op_u = 0
        for x in range(BOARD_COLS):
            for y in range(BOARD_ROWS):
                if state.board[x][y] == self.color:
                    my_u += 1 if self.emptyAroundTiles(state, x, y) else 0
                if state.board[x][y] == OPPONENT_COLOR[self.color]:
                    op_u += 1 if self.emptyAroundTiles(state, x, y) else 0
        return [my_u, op_u]

    def isOnBoard(self, x, y):
        # Returns True if the coordinates are located on the board.
        return x >= 0 and x <= 7 and y >= 0 and y <= 7

    def isEmptyTile(self, state, x, y):
        # Returns True if the coordinates are located on the board and the tile is empty
        return self.isOnBoard(x, y) and state.board[x][y] == EM

    def emptyAroundTiles(self, state, x, y):
        # Sum the legal empty tiles around a given tile
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if self.isEmptyTile(state, x - i, y - j):
                    return True
        return False

    def countUnemptyColRow(self, state):
        # gives a score for successive tiles at the same color
        dic = {self.color: 0, OPPONENT_COLOR[self.color]: 0, EM: 0}
        # iterate over first row
        i = j = 0
        currColor = state.board[i][j]
        while i < 8 and state.board[i][j] == currColor:
            dic[currColor] += 1
            i += 1
        # iterate over first col
        i = j = 0
        currColor = state.board[i][j]
        while j < 8 and state.board[i][j] == currColor:
            dic[currColor] += 1
            j += 1
        # iterate over last row
        i = j = 7
        currColor = state.board[i][j]
        while i >= 0 and state.board[i][j] == currColor:
            dic[currColor] += 1
            i -= 1
        # iterate over last col
        i = j = 7
        currColor = state.board[i][j]
        while j >= 0 and state.board[i][j] == currColor:
            dic[currColor] += 1
            j -= 1

        return [dic[self.color], dic[OPPONENT_COLOR[self.color]]]