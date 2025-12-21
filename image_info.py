from typing import List, Optional, Tuple
from PIL import Image, ImageTk

import cv2
import numpy as np

from opencv_func import ImageFunc


class ImageInfo:
    def __init__(self):
        self.x = None
        self.y = None
        self.val = None
        self.hsv = None

        self.rect_w = None
        self.rect_h = None

    def calc_vals(self, img: np.ndarray, x, y):
        if img is None:
            return

        img_h, img_w = img.shape[:2]

        self.x = max(0, min(int(x), img_w - 1))
        self.y = max(0, min(int(y), img_h - 1))

        try:
            self.val = img[self.y, self.x]
        except Exception:
            self.val = None

        try:
            _hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            self.hsv = _hsv[self.y, self.x]
        except Exception:
            self.hsv = None

    def calc_rect_vals(self, x0, y0, x1, y1):
        if x0 is not None and x1 is not None:
            self.rect_w = int(abs(x1 - x0))

        if y0 is not None and y1 is not None:
            self.rect_h = int(abs(y1 - y0))


class ImageData:
    def __init__(self, img_org, win_h, win_w, scale=1.0, img_path=None):
        self.img_org: np.ndarray = img_org
        self.win_h: int = win_h
        self.win_w: int = win_w

        self.scale: float = scale
        self.img_path = img_path

        self.fit_ratio: Optional[float] = None

        self.img_w_org = None
        self.img_h_org = None
        self.img_w_fit = None
        self.img_h_fit = None

        self._img_fit: Optional[np.ndarray] = None
        self._img_pil: Optional[Image] = None

        if img_org is not None:
            self.img_h_org, self.img_w_org = img_org.shape[:2]

        self._fit_window()

    def _fit_window(self):
        if self.img_org is None:
            return

        h_ratio = self.win_h / self.img_h_org
        w_ratio = self.win_w / self.img_w_org
        ratio = min(h_ratio, w_ratio) * self.scale

        self.fit_ratio = ratio
        self.img_h_fit = int(self.img_h_org * ratio)
        self.img_w_fit = int(self.img_w_org * ratio)
        self._img_fit = cv2.resize(self.img_org, (self.img_w_fit, self.img_h_fit))
        self._img_pil = ImageFunc.cv2pil(self._img_fit)

    def img_fit(self, scale=None):
        if self.img_org is None:
            return None

        if scale is None:
            return self._img_fit

        if self.scale * 0.99 < scale < self.scale * 1.01:
            return self._img_fit

        self.scale = scale
        self._fit_window()
        return self._img_fit

    def img_pil(self, scale=None):
        if self.img_org is None:
            return None

        if scale is None:
            return self._img_pil

        if self.scale * 0.99 < scale < self.scale * 1.01:
            return self._img_pil

        self.scale = scale
        self._fit_window()
        return self._img_pil


if __name__ == '__main__':
    pass
