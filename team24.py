import uuid
import time
import random
import signal
import copy
import sys

class TimedOutExc(Exception):
    pass


def handler(signum, frame):
    # print 'Signal handler called with signal', signum
    raise TimedOutExc()


class Team24:

    def __init__(self):
        self.player_sign = ""
        self.opponent_sign = ""
        self.current_board = [[0] * 16 for i in range(16)]
        self.current_transpose_board = [[0] * 16 for i in range(16)]
        self.current_block = [[0] * 4 for i in range(4)]
        self.current_transpose_block = [[0] * 4 for i in range(4)]
        self.transposition_table = {}
        # print self.transposition_table  
        self.keys = [[[0 for k in range(2)] for j in range(4)] for i in range(4)]
        self.cell_values = [[6, 4, 4, 6], [4, 3, 3, 4], [4, 3, 3, 4], [6, 4, 4, 6]]
        # Hash value of every block
        self.hash_block = [[0 for i in range(4)] for i in range(4)]
        # print self.hash_block
        self.generate_values()
        self.board_center = 0
        self.best_move = 0
        self.level = 3


    def move(self, board, old_move, flag):
        """Called every time our bot has to make a move"""
        if old_move == (-1, -1):  # if chance is first then always play 5,5
            return (5, 5)
        self.current_board = board
        saved = copy.deepcopy(board)
        # self.current_transpose_board = map(list, zip(*self.current_board))
        self.player_sign = flag
        if flag == "x":
            self.opponent_sign = "o"
        else:
            self.opponent_sign = "x"
        self.current_board = board
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(15)
        self.compute_key()
        # for i in range(3, 5):
        #     self.level = i
        # signal.alarm(15)
        try:
            # for i in range(3, 20):
            #     # print "iteration",i
            #     self.level = i
            #     # print "level", self.level
            self.alpha_beta(3, float("-inf"), float("inf"), 1, old_move)
            self.current_board = saved
        except Exception as e:
            pass
            # print 'Exception occurred ', e
            # print 'Traceback printing ', sys.exc_info()
        # print "returning to simulator",type(self.best_move)
        print "best move is", self.best_move
        return self.best_move

    def centre_check(self):
        danger = 0
        for i in range(1,3):
            for j in range(1,3):
                if self.current_board.block_status[i][j] == self.opponent_sign:
                    danger += 2

        if danger > 1:
            return True
        return 0

    def heuristic_cell_weight(self):
        value = 0
        for i in range(4):
            for j in range(4):
                if self.current_board.block_status[i][j] == self.player_sign:
                    value += self.cell_values[i][j] * 100
                elif self.current_board.block_status[i][j] == self.opponent_sign:
                    value -= self.cell_values[i][j] * 100
        return value


    def generate_values(self):
        """This Function fills up the keys matrix with random 32 bit values which will be used to represent states."""
        for i in range(4):
            for j in range(4):
                for k in range(2):
                    # Generating a random number
                    self.keys[i][j][k] = uuid.uuid1().int >> 32

    def compute_key(self):
        """Called every time we need to recompute the hash value"""
        for i in range(16):
            block_row = i // 4
            block_column = i % 4
            hash_value = 0
            for j in range(4):
                for k in range(4):
                    current_sign = self.current_board.board_status[
                        4 * block_row + j][4 * block_column + k]
                    if current_sign == self.player_sign:
                        hash_value ^= self.keys[j][k][0]
                    elif current_sign == self.opponent_sign:
                        hash_value ^= self.keys[j][k][1]

            self.hash_block[block_row][block_column] = hash_value
        return

    def calculate_score_utility(self, array):
        value = 0
        if array[0] == 4:
            value = 1028
        elif array[0] == 3 and array[1] == 0:
            value = 259
        elif array[0] == 2 and array[1] == 0:
            value = 34
        elif array[0] == 1 and array[1] == 0:
            value = 3

        if array[1] == 4:
            value = -1024
        elif array[1] == 3 and array[0] == 0:
            value = -256
        elif array[1] == 2 and array[0] == 0:
            value = -32
        elif array[1] == 1 and array[0] == 0:
            value = -2
        return value

    def calculate_score(self, array):
        array_column = map(list, zip(*array))  # gives transpose of the list , used for columns
        value = 0
        ans = 0
        diamonds = [[] * 4 for z in range(4)]
        diamonds[0].extend(
            (array[0][1], array[1][0], array[1][2], array[2][1]))
        diamonds[1].extend(
            (array[0][2], array[1][1], array[1][3], array[2][2]))
        diamonds[2].extend(
            (array[1][1], array[2][0], array[2][2], array[3][1]))
        diamonds[3].extend(
            (array[1][2], array[2][1], array[2][3], array[3][2]))

        for i in range(4):
            temp1 = [0, 0]
            temp2 = [0, 0]
            temp3 = [0, 0]
            for j in range(4):
                if array[i][j] == self.player_sign:
                    temp1[0] += 1
                if array_column[i][j] == self.player_sign:
                    temp2[0] += 1
                if diamonds[i][j] == self.player_sign:
                    temp3[0] += 1
                if array[i][j] == self.opponent_sign:
                    temp1[1] += 1
                if array_column[i][j] == self.opponent_sign:
                    temp2[1] += 1
                if diamonds[i][j] == self.opponent_sign:
                    temp3[1] += 1
            value += self.calculate_score_utility(temp1)
            value += self.calculate_score_utility(temp2)
            ans += self.calculate_score_utility(temp3)
        return value + ans

    def find_score(self):
        board_score = 0
        blocks_score = 0
        board_score += (self.calculate_score(self.current_board.block_status))/5  # for board
        for i in range(4):
            for j in range(4):
                # if self.hash_block[i][j] in self.transposition_table and self.hash_block[i][j] != 0:
                #     blocks_score += self.transposition_table[self.hash_block[i][j]]  # if state value pre computed
                #     continue
                block_score = 0
                for k in range(4):
                    for l in range(4):
                        self.current_block[k][l] = self.current_board.board_status[4 * i + k][4 * j + l]  # for blocks
                block_score = self.calculate_score(self.current_block)
                blocks_score += block_score
                self.transposition_table[self.hash_block[i][j]] = block_score
        if self.centre_check():
            return 2 * board_score + blocks_score + self.heuristic_cell_weight()
        return 2 * board_score + blocks_score

    def alpha_beta(self, depth, alpha, beta, max_flag, old_move):
        terminal_status = self.current_board.find_terminal_state()
        if depth == 0 or terminal_status[0] != 'CONTINUE':
            return self.find_score()

        elif max_flag:
            best_val = float("-inf")
            valid_moves = self.current_board.find_valid_move_cells(old_move)
            random.shuffle(valid_moves)
            for valid in valid_moves:
                self.current_board.update(old_move, valid, self.player_sign)
                self.hash_block[valid[0] / 4][valid[1] / 4] ^= self.keys[valid[0] % 4][valid[1] % 4][0]
                val = self.alpha_beta(depth - 1, alpha, beta, 0, valid)
                self.current_board.board_status[valid[0]][valid[1]] = '-'
                self.current_board.block_status[valid[0] / 4][valid[1] / 4] = '-'
                self.hash_block[valid[0] / 4][valid[1] / 4] ^= self.keys[valid[0] % 4][valid[1] % 4][0]
                # move removed after returning from recursion
                if val > best_val:
                    if depth == self.level:
                        self.best_move = valid
                    best_val = val
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
            return best_val

        elif max_flag != 1:
            valid_moves = self.current_board.find_valid_move_cells(old_move)
            best_val = float("inf")
            random.shuffle(valid_moves)
            for valid in valid_moves:
                self.current_board.update(old_move, valid, self.opponent_sign)
                self.hash_block[valid[0] / 4][valid[1] / 4] ^= self.keys[valid[0] % 4][valid[1] % 4][1]
                val = self.alpha_beta(depth - 1, alpha, beta, 1, valid)
                self.current_board.board_status[valid[0]][valid[1]] = '-'
                self.current_board.block_status[valid[0] / 4][valid[1] / 4] = '-'
                self.hash_block[valid[0] / 4][valid[1] / 4] ^= self.keys[valid[0] % 4][valid[1] % 4][1]
                # move removed after returning from recursion
                if val < best_val:
                    best_val = val
                beta = min(beta, best_val)
                if beta <= alpha:
                    break
            return best_val


    def signal_handler(self, signum, frame):
        raise Exception('Timed out!')
