"""Generic utility functions
"""
# from __future__ import print_function
from threading import Thread
from multiprocessing import Queue
import time
import copy
from Reversi.board import GameState



INFINITY = float(6000)
MAX_DEPTH = 100


class ExceededTimeError(RuntimeError):
    """Thrown when the given function exceeded its runtime.
    """
    pass


def function_wrapper(func, args, kwargs, result_queue):
    """Runs the given function and measures its runtime.

    :param func: The function to run.
    :param args: The function arguments as tuple.
    :param kwargs: The function kwargs as dict.
    :param result_queue: The inter-process queue to communicate with the parent.
    :return: A tuple: The function return value, and its runtime.
    """
    start = time.time()
    try:
        result = func(*args, **kwargs)
    except MemoryError as e:
        result_queue.put(e)
        return

    runtime = time.time() - start
    result_queue.put((result, runtime))


def run_with_limited_time(func, args, kwargs, time_limit):
    """Runs a function with time limit

    :param func: The function to run.
    :param args: The functions args, given as tuple.
    :param kwargs: The functions keywords, given as dict.
    :param time_limit: The time limit in seconds (can be float).
    :return: A tuple: The function's return value unchanged, and the running time for the function.
    :raises PlayerExceededTimeError: If player exceeded its given time.
    """
    q = Queue()
    t = Thread(target=function_wrapper, args=(func, args, kwargs, q))
    t.start()

    # This is just for limiting the runtime of the other thread, so we stop eventually.
    # It doesn't really measure the runtime.
    t.join(time_limit)

    if t.is_alive():
        raise ExceededTimeError

    q_get = q.get()
    if isinstance(q_get, MemoryError):
        raise q_get
    return q_get


class MiniMaxAlgorithm:

    def __init__(self, utility, my_color, no_more_time, selective_deepening):
        """Initialize a MiniMax algorithms without alpha-beta pruning.

        :param utility: The utility function. Should have state as parameter.
        :param my_color: The color of the player who runs this MiniMax search.
        :param no_more_time: A function that returns true if there is no more time to run this search, or false if
                             there is still time left.
        :param selective_deepening: A functions that gets the current state, and
                        returns True when the algorithm should continue the search
                        for the minimax value recursivly from this state.
                        optional
        """

        self.utility = utility
        self.my_color = my_color
        self.no_more_time = no_more_time
        self.selective_deepening = selective_deepening

    def search(self, state, depth, maximizing_player):
        """Start the MiniMax algorithm.

        :param state: The state to start from.
        :param depth: The maximum allowed depth for the algorithm.
        :param maximizing_player: Whether this is a max node (True) or a min node (False).
        :return: A tuple: (The min max algorithm value, The move in case of max node or None in min mode)
        """
        # print("The current depth is:",depth)
        if depth == 0:
            score = self.utility(state)  # TODO remove
            # print("at",maximizing_player, "score = ", score) # TODO remove
            return score, None
        moves = state.get_possible_moves()
        if len(moves) == 0: # no more moves from this state
            return self.utility(state), None
        if maximizing_player: # our turn lets MAX # TODO change this with corrlation to state or agent
            currMax = -INFINITY
            bestMove = moves[0]
            i = 0
            while not(self.no_more_time()) and i < len(moves):
                next_state = copy.deepcopy(state)
                next_state.perform_move(moves[i][0], moves[i][1])
                v,_ = self.search(next_state,depth-1,False)
                # print("At", depth, "depth best move is:", moves[i], "with score of:", v) # TODO remove
                if currMax < v:
                    currMax = v
                    bestMove = moves[i]
                i += 1
                # print("At", depth, "depth best move is:", bestMove, "with score of:", currMax) # TODO remove
            return currMax, bestMove
        else:              # not our turn lets MIN
            currMin = INFINITY
            i = 0
            while not (self.no_more_time()) and i < len(moves):
                next_state = copy.deepcopy(state)
                next_state.perform_move(moves[i][0], moves[i][1])
                v,_ = self.search(next_state, depth - 1, True)
                # if currMax < v:
                #     currMax = v
                #     bestMove = moves[i]
                currMin = min(v,currMin)
                i += 1
            return currMin, None



class MiniMaxWithAlphaBetaPruning:

    def __init__(self, utility, my_color, no_more_time, selective_deepening):
        """Initialize a MiniMax algorithms with alpha-beta pruning.

        :param utility: The utility function. Should have state as parameter.
        :param my_color: The color of the player who runs this MiniMax search.
        :param no_more_time: A function that returns true if there is no more time to run this search, or false if
                             there is still time left.
        :param selective_deepening: A functions that gets the current state, and
                        returns True when the algorithm should continue the search
                        for the minimax value recursivly from this state.
        """
        self.utility = utility
        self.my_color = my_color
        self.no_more_time = no_more_time
        self.selective_deepening = selective_deepening

    def search(self, state, depth, alpha, beta, maximizing_player):
        """Start the MiniMax algorithm.

        :param state: The state to start from.
        :param depth: The maximum allowed depth for the algorithm.
        :param alpha: The alpha of the alpha-beta pruning.
        :param beta: The beta of the alpha-beta pruning.
        :param maximizing_player: Whether this is a max node (True) or a min node (False).
        :return: A tuple: (The alpha-beta algorithm value, The move in case of max node or None in min mode)
        """
        # print("The current depth is:",depth)
        if depth == 0:
            score = self.utility(state)  # TODO remove
            # print("at",maximizing_player, "score = ", score) # TODO remove
            return score, None
        moves = state.get_possible_moves()
        if len(moves) == 0:  # no more moves from this state
            return self.utility(state), None
        if maximizing_player:  # our turn lets MAX # TODO change this with corrlation to state or agent
            currMax = -INFINITY
            bestMove = moves[0]
            i = 0
            while not(self.no_more_time()) and i < len(moves):
                next_state = copy.deepcopy(state)
                next_state.perform_move(moves[i][0], moves[i][1])
                v, _ = self.search(next_state, depth - 1, alpha, beta, False)
                # print("At", depth, "depth best move is:", moves[i], "with score of:", v) # TODO remove
                if currMax < v: # should update max and best move
                    currMax = v
                    bestMove = moves[i]
                alpha = max(currMax,alpha)
                if currMax >= beta:
                    return INFINITY, bestMove
                i += 1
                # print("At", depth, "depth best move is:", bestMove, "with score of:", currMax) # TODO remove
            return currMax, bestMove
        else:  # not our turn lets MIN
            currMin = INFINITY
            i = 0
            while not (self.no_more_time()) and i < len(moves):
                next_state = copy.deepcopy(state)
                next_state.perform_move(moves[i][0], moves[i][1])
                v, _ = self.search(next_state, depth - 1, alpha, beta, True)
                # if currMax < v:
                #     currMax = v
                #     bestMove = moves[i]
                currMin = min(v, currMin)
                beta = min(currMin,beta)
                if currMin <= alpha:
                    return -INFINITY, None
                i += 1
            return currMin, None


class Book:
    openingBook = {'': [3, 5], '35252445362646': [1, 4], '35252445361454': [2, 6], '3525244536264614': [5, 5],
                   '354554255364': [5, 5], '3525244554234653': [5, 2], '3523524525': [5, 3], '3525244536231415': [5, 4],
                   '35252445542322': [3, 2], '352524455423': [4, 6], '3523': [5, 2], '35455425536455': [6, 5],
                   '3545': [5, 4], '35252445542342': [5, 5], '3525244536145455': [5, 3], '35235253424532': [5, 1],
                   '3523425352452536': [2, 4], '3523525342453251': [6, 2], '3525': [2, 4], '35234253524532': [5, 1],
                   '3525244536231546': [5, 5], '35252445362313': [1, 4], '352342': [5, 3], '3545542553': [6, 4],
                   '35455425': [5, 3], '3525244536141323': [5, 5], '3525244536261423': [3, 2], '352332455422': [5, 3],
                   '3523425352452555': [2, 4], '352524': [4, 5], '3525244536231426': [3, 2], '35235245': [2, 5],
                   '35235245255342': [5, 5], '35234253524525': [5, 5], '3523524525534236': [2, 4],
                   '3525244554324214': [2, 2], '354554': [2, 5], '3525244554234264': [1, 5], '3523324554222425': [4, 6],
                   '3525244554323656': [2, 2], '352524455432': [4, 2], '3525244536235354': [3, 2],
                   '3523525342452555': [2, 4], '35234253': [5, 2], '35233245542224': [2, 5], '35252445': [3, 6],
                   '35252445362614': [2, 3], '3525244536261437': [5, 4], '352524453623': [1, 5], '3523324554': [2, 2],
                   '3523324554225325': [2, 4], '3525244554234255': [5, 6], '35': [2, 3], '352352534245': [2, 5],
                   '352342535245': [2, 5], '35252445543242': [1, 4], '35252445542346': [5, 3], '352352452553': [4, 2],
                   '35252445361413': [2, 3], '3525244554322223': [1, 4], '352332': [4, 5], '352524453626': [1, 4],
                   '352352': [4, 5], '3523524525534255': [2, 4], '3525244554324213': [2, 2], '3523425352453251': [6, 2],
                   '35252445543236': [5, 6], '3525244526235455': [4, 6], '35235253': [4, 2], '35233245': [5, 4],
                   '3525244536231314': [5, 5], '352524452623': [5, 4], '3525244536145426': [2, 3],
                   '35233245542253': [2, 5], '3523425352': [4, 5], '3523525342': [4, 5], '35252445362353': [5, 4],
                   '3525244536': [2, 3], '35252445362314': [2, 6], '3525244554232232': [1, 4], '3525244526': [2, 3],
                   '3545542553645565': [2, 4], '35252445362315': [4, 6], '3523525342452536': [2, 4],
                   '35252445262354': [5, 5], '35235253424525': [5, 5], '35252445543222': [2, 3], '352524453614': [1, 3],
                   '3525244554': [3, 2]}