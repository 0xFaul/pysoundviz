#!/usr/bin/env python3
import curses


class Graphics:
    __scrn = None
    __height = 0
    __width = 0

    ERR = curses.ERR
    KEY_RESIZE = curses.KEY_RESIZE
    KEY_UP = curses.KEY_UP
    KEY_DOWN = curses.KEY_DOWN
    KEY_RIGHT = curses.KEY_RIGHT
    KEY_LEFT = curses.KEY_LEFT
    KEY_ESC = 27



    def __init__(self):
        self.__scrn = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.use_default_colors()

    def refresh(self):
        self.__scrn.refresh()

    def nodelay(self, i):
        self.__scrn.nodelay(i)

    def noecho(self):
        curses.noecho()

    def cbreak(self):
        curses.cbreak()

    def keypad(self, i):
        self.__scrn.keypad(i)

    def __updateScrnSize(self):
        w = 0
        try:
            while True:
                self.__scrn.addstr(0, w, " ")
                w = w + 1
        except:
            self.__width = w - 1
        h = 0
        try:
            while True:
                self.__scrn.addstr(h, 0, " ")
                h = h + 1
        except:
            self.__height = h - 1

    def get_width(self):
        return self.__width

    def get_height(self):
        return self.__height

    def update(self):
        self.__scrn = curses.initscr()
        self.__updateScrnSize()

    def write(self, *args):
        if len(args) == 1 :
            self.__scrn.addstr(str(args[0]))
        elif len(args) == 3:
            self.__scrn.addstr(int(args[0]), int(args[1]), str(args[2]))
        else:
            raise TypeError("invalid number of arguments")

    def input(self, *promt):
        if promt:
            self.write(str(promt[0]))
        return self.__scrn.getch()

    def exit(self):
        curses.endwin()

    def clear(self):
        self.__scrn.clear()

    def write_footer(self, text):
        self.__scrn.addstr(self.__height, 0, str(text[:self.__width].ljust(self.__width, " ")), curses.color_pair(1))
        curses.use_default_colors()
