from typing import List, Optional, Tuple
from PIL import Image, ImageTk

import cv2
import numpy as np

from opencv_func import ImageFunc

class ImageData:
    def __init__(self, img_org, win_h, win_w):
        self.img_org: np.ndarray = img_org
        self.win_h: int = win_h
        self.win_w: int = win_w

        self.img_fit: Optional[np.ndarray] = None
        self.fit_ratio: Optional[float] = None

        self.img_pil : Optional[ImageTk.PhotoImage] = None

        self._fit_window()
        self._cvt2pil()

    def _fit_window(self):
        if self.img_org is None:
            return

        try:
            img_h, img_w = self.img_org.shape[:2]
            h_ratio = self.win_h / img_h
            w_ratio = self.win_w / img_w
            ratio = min(h_ratio, w_ratio)

            self.img_fit = cv2.resize(self.img_org, (int(img_w * ratio), int(img_h * ratio)))
            self.fit_ratio = ratio

        except Exception:
            self.img_fit = None
            self.fit_ratio = None

    def _cvt2pil(self):
        if self.img_fit is None:
            return

        try:
            self.img_pil = ImageFunc.cv2tk(self.img_fit)
        except Exception:
            self.img_pil = None


class ImageInfo:
    def __init__(self, use_org_img=False):
        self.use_org_img = use_org_img

        self.cnt = None
        self.full_path = None
        self.dir = None
        self.file = None

        self.img = None
        self.fit_ratio = None
        self.gui_x = None
        self.gui_y = None

        # calculated
        self.x = None
        self.y = None
        self.val = None
        self.hsv = None
        self.img_h = None
        self.img_w = None

        self.img_h_org = None
        self.img_w_org = None
        self.x_org = None
        self.y_org = None
        self.x_fit = None
        self.y_fit = None

    def calc_params(self):
        if self.img is None:
            return
        self.img_h, self.img_w = self.img.shape[:2]

        if not self.use_org_img:
            self.img_h_org = int(self.img_h / self.fit_ratio)
            self.img_w_org = int(self.img_w / self.fit_ratio)

        if self.use_org_img:
            x = int(self.gui_x / self.fit_ratio)
            y = int(self.gui_y / self.fit_ratio)
            self.x_fit = int(x * self.fit_ratio)
            self.y_fit = int(y * self.fit_ratio)
        else:
            x = self.gui_x
            y = self.gui_y
            self.x_org = int(x / self.fit_ratio)
            self.y_org = int(y / self.fit_ratio)

        self.x = min(x, self.img_w - 1)
        self.y = min(y, self.img_h - 1)

        self.val = self.img[self.y, self.x]
        try:
            _hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
            self.hsv = _hsv[self.y, self.x]
        except Exception:
            self.hsv = ''


if __name__ == '__main__':
    pass
