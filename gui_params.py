import cv2
import tkinter
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


def draw_cross(img, x, y, line_thick=2, line_color=(255, 0, 0)):
    img_h = img.shape[0]
    img_w = img.shape[1]

    cv2.line(img, (x, 0), (x, img_h), color=line_color, thickness=line_thick)
    cv2.line(img, (0, y), (img_w, y), color=line_color, thickness=line_thick)

    return img


def draw_rectangle(img, x0, x1, y0, y1, line_thick=2, line_color=(255, 0, 0)):
    _img_h = img.shape[0]
    line_thick = int(line_thick *_img_h / 500)

    cv2.rectangle(img, (x0, y0), (x1, y1), color=0, thickness=line_thick + 2)
    cv2.rectangle(img, (x0, y0), (x1, y1), color=line_color, thickness=line_thick)

    return img


class GuiParams:
    def __init__(self):
        self.pix2um = 1
        self.win_size = '1000x700'
        self.img_num_col = 1
        self.img_num_row = 1
        self.img_key = '*.*'

        self.topmost = False

        self.gui_type = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None

        self._set_pos0_flg = False
        self._set_pos1_flg = False

    def reset(self):
        self.gui_type = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None

        self._set_pos0_flg = False
        self._set_pos1_flg = False

    def set_type(self, gui_type):
        self.gui_type = gui_type

    def set_pos0(self, x0, y0):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x0
        self.y1 = y0

        self._set_pos0_flg = True
        self._set_pos1_flg = True

    def set_pos1(self, x1, y1):
        self.x1 = x1
        self.y1 = y1

        self._set_pos1_flg = True

    def draw_img(self, img):
        if self.gui_type is None:
            return img

        elif self.gui_type.lower() == 'cross':
            if self._set_pos0_flg:
                img = draw_cross(img, self.x0, self.y0)
            return img

        elif self.gui_type.lower() == 'rectangle':
            if self._set_pos0_flg and self._set_pos1_flg:
                img = draw_rectangle(img, self.x0, self.x1, self.y0, self.y1)
            return img


if __name__ == '__main__':
    pass
