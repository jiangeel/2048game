# -*-coding=utf-8-*-

import curses
from random import randrange, choice
from collections import defaultdict

actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
actions_dict = dict(zip(letter_codes, actions * 2))


# 处理用户输入
# keyboard是后面传入的stdscr
def get_user_action(keyboard):
    char = "N"
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]


# 矩阵转制和矩阵逆转
def transpose(field):  # 转制
    return [list(row) for row in zip(*field)]


def invert(field):  # 逆转
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win_value = win
        self.score = 0
        self.highscore = 0  # 最高分
        self.reset()

    # 棋盘操作
    # 随机生成一个2或者4
    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.width) for j in range \
            (self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    # 重置棋盘
    def reset(self):
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i+1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row
            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    # 判断输赢
    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    # 绘制游戏界面
    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'

        def cast(string):
            screen.addstr(string + '\n')

        # 绘制水平分割线
        def draw_hor_separator():
            line = ('+-----' * self.width) + '+'
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5}'.format(num) if num > 0 else '|     ' for num in row) + '|')

        screen.clear()

        cast('SCORE:' + str(self.score))
        cast('HIGHSCORE:' + str(self.highscore))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def change(i): # true if there'll be change in i-th tile
                if row[i] == 0 and row[i + 1] != 0: # Move
                    return True
                if row[i] != 0 and row[i + 1] == row[i]: # Merge
                    return True
                return False
            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left']  = lambda field:                              \
                any(row_is_left_movable(row) for row in field)

        check['Right'] = lambda field:                              \
                 check['Left'](invert(field))

        check['Up']    = lambda field:                              \
                check['Left'](transpose(field))

        check['Down']  = lambda field:                              \
                check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False


# 游戏循环的主逻辑
def main(stdscr):
    game_field = GameField(win=64)

    # 以下三个都是动作函数，用于改变状态机状态，返回的是做完后的状态
    def init():
        # 重置游戏棋盘，然后进入游戏状态
        game_field.reset()
        return 'Game'

    # state可以是 胜利或失败
    def not_game(state):
        game_field.draw(stdscr)
        # 读取用户输入得到的action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        # 默认是当前状态，没有行为就会一直在当前界面循环
        response = defaultdict(lambda: state)
        # 对应不同的行为转换到不同的状态
        response['Restart'], response['Exit'] = 'Init', 'Exit'
        # 返回重新开始或者退出的状态
        return response[action]

    def game():
        # 画棋盘状态
        game_field.draw(stdscr)
        # 读取用户输入
        action = get_user_action(stdscr)
        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'  # 没有失败或胜利或退出，继续游戏

    # key是状态，value是动作函数
    state_actions = {
        # 都是函数名不带括号
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }

    state = 'Init'
    # 状态机开始循环
    while state != 'Exit':
        # 执行改变状态的函数，并返回改变后的状态
        state = state_actions[state]()


curses.wrapper(main)
