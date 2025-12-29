import os
from logging import getLogger, Logger, NullHandler
from typing import Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk


class ImageFunc:
    """
    OpenCV utility collection.
    All methods are classmethods so you can call them without instantiation.
    """

    logger: Logger = getLogger(__name__)
    logger.addHandler(NullHandler())

    # ----- infra -----
    @classmethod
    def set_logger(cls, logger: Logger) -> None:
        if logger is not None:
            cls.logger = logger

    # ----- IO / display -----
    @classmethod
    def open_img_file(cls, img_file: str, gray_flg: bool = False, unchanged_flg: bool = False) -> Optional[np.ndarray]:
        if not os.path.isfile(img_file):
            cls.logger.warning(f'No file: {img_file}')
            return None

        if unchanged_flg:
            return cv2.imread(img_file, cv2.IMREAD_UNCHANGED)
        if gray_flg:
            return cv2.imread(img_file, cv2.IMREAD_GRAYSCALE)
        return cv2.imread(img_file, cv2.IMREAD_COLOR)

    @classmethod
    def save_img_file(cls, img: Optional[np.ndarray], img_file: str) -> None:
        if img is None:
            cls.logger.warning(f'No Image: {img_file}')
            return

        cv2.imwrite(img_file, img)

    @classmethod
    def show_img(cls, img: np.ndarray, winname: str = 'window', delay_msec: int = 0) -> None:
        cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
        cv2.imshow(winname, img)
        cv2.waitKey(delay_msec)
        cv2.destroyAllWindows()

    @classmethod
    def show_img_by_plt(cls, img: np.ndarray) -> None:
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img)
        plt.show()
        plt.close()

    # ----- tkinter transforms -----
    @classmethod
    def cv2tk(cls, img_cv: np.ndarray):
        """Convert OpenCV BGR/GRAY numpy image to Tk PhotoImage."""
        if img_cv is None:
            return None

        img = img_cv
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(img)
        return ImageTk.PhotoImage(pil.convert('RGB'))

    @classmethod
    def cv2pil(cls, img_cv: np.ndarray):
        """Convert OpenCV BGR/GRAY numpy image to PIL."""
        if img_cv is None:
            return None

        img = img_cv
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img)

    # ----- basic transforms -----
    @classmethod
    def crop(cls, img: Optional[np.ndarray],
             h0: Optional[int] = None, h1: Optional[int] = None,
             w0: Optional[int] = None, w1: Optional[int] = None) -> Optional[np.ndarray]:
        if img is None:
            cls.logger.warning('No Image')
            return None

        img_h, img_w = img.shape[:2]
        h0 = 0 if h0 is None else h0
        h1 = img_h if h1 is None else h1
        w0 = 0 if w0 is None else w0
        w1 = img_w if w1 is None else w1
        if h0 < 0 or h1 > img_h or h0 > h1:
            cls.logger.warning('Illegal crop range')
            return None
        if w0 < 0 or w1 > img_w or w0 > w1:
            cls.logger.warning('Illegal crop range')
            return None

        return img[h0:h1, w0:w1] if img.ndim != 3 else img[h0:h1, w0:w1, :]

    @classmethod
    def crop_by_ratio(cls, img: Optional[np.ndarray],
                      h0_ratio: float = 0.0, h1_ratio: float = 1.0,
                      w0_ratio: float = 0.0, w1_ratio: float = 1.0) -> Optional[np.ndarray]:
        if img is None:
            cls.logger.warning('No Image')
            return None
        if not (0 <= h0_ratio <= 1 and 0 <= h1_ratio <= 1 and 0 <= w0_ratio <= 1 and 0 <= w1_ratio <= 1):
            cls.logger.warning('Illegal ratio')
            return None
        if h0_ratio > h1_ratio or w0_ratio > w1_ratio:
            cls.logger.warning('Illegal ratio order')
            return None

        img_h, img_w = img.shape[:2]
        h0 = int(img_h * h0_ratio)
        h1 = int(img_h * h1_ratio)
        w0 = int(img_w * w0_ratio)
        w1 = int(img_w * w1_ratio)
        return img[h0:h1, w0:w1] if img.ndim != 3 else img[h0:h1, w0:w1, :]

    @classmethod
    def convert_color(cls, img_bgr: Optional[np.ndarray], type: str = 'gray') -> Optional[np.ndarray]:
        """Convert BGR image to GRAY/HSV or single channel (b,g,r)."""
        if img_bgr is None:
            cls.logger.warning('No Image')
            return None

        if img_bgr.ndim == 3:
            t = type.lower()
            if t == 'gray':
                return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            if t == 'hsv':
                return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            if t == 'blue':
                return img_bgr[:, :, 0]
            if t == 'green':
                return img_bgr[:, :, 1]
            if t == 'red':
                return img_bgr[:, :, 2]

            cls.logger.warning(f'Illegal type: {type}')
            return None
        return img_bgr

    @classmethod
    def convert_intensity(cls, img: Optional[np.ndarray], coeff: float = 1.0, offset: float = 0.0) -> Optional[np.ndarray]:
        if img is None:
            cls.logger.warning('No Image')
            return None
        out = coeff * img + offset
        return np.clip(out, 0, 255).astype(np.uint8)

    # ----- threshold / morphology -----
    @classmethod
    def threshold_gray(cls, img_bgr: np.ndarray, thres: int = 0, type: str = 'gray', inverse: bool = False) -> np.ndarray:
        """Binary threshold on a single channel derived from BGR (not HSV)."""
        if type == 'hsv':
            raise ValueError('illegal type')
        ch = cls.convert_color(img_bgr, type=type)
        if ch is None:
            raise ValueError('No image')
        thresh_type = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
        _, out = cv2.threshold(ch, thres, 255, thresh_type)
        return out

    @classmethod
    def threshold_gray2(cls, img_bgr: np.ndarray, thres_min: int = 0, thres_max: int = 255, type: str = 'gray') -> np.ndarray:
        if type == 'hsv':
            raise ValueError('illegal type')
        ch = cls.convert_color(img_bgr, type=type)
        if ch is None:
            raise ValueError('No image')
        return cv2.inRange(ch, np.array(thres_min), np.array(thres_max))

    @classmethod
    def threshold_hsv(cls, img_bgr: np.ndarray, low: Sequence[int], high: Sequence[int]) -> np.ndarray:
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, np.array(low), np.array(high))

    @classmethod
    def threshold_bgr(cls, img_bgr: np.ndarray, low: Sequence[int], high: Sequence[int]) -> np.ndarray:
        return cv2.inRange(img_bgr, np.array(low), np.array(high))

    @classmethod
    def erode(cls, img_bin: np.ndarray, kernel: int = 3, iter: int = 2) -> np.ndarray:
        return cv2.erode(img_bin, np.ones((kernel, kernel), np.uint8), iterations=iter)

    @classmethod
    def dilate(cls, img_bin: np.ndarray, kernel: int = 3, iter: int = 2) -> np.ndarray:
        return cv2.dilate(img_bin, np.ones((kernel, kernel), np.uint8), iterations=iter)

    # ----- drawing -----
    @classmethod
    def draw_contours(cls, img_out: np.ndarray, img_bin: np.ndarray, fill: bool = False,
                      thickness: int = 2, color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
        contours, _ = cv2.findContours(img_bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        t = -1 if fill else thickness
        return cv2.drawContours(img_out, contours, -1, color=color, thickness=t)

    @classmethod
    def draw_cross(cls, img: np.ndarray, x: int, y: int, line_thick: int = 2,
                   line_color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
        h, w = img.shape[:2]
        cv2.line(img, (x, 0), (x, h), color=line_color, thickness=line_thick)
        cv2.line(img, (0, y), (w, y), color=line_color, thickness=line_thick)
        return img

    @classmethod
    def draw_rectangle(cls, img: np.ndarray, x0: int, x1: int, y0: int, y1: int,
                       line_thick: int = 2, line_color: Tuple[int, int, int] = (255, 0, 0),
                       use_white_outline:bool=False) -> np.ndarray:

        if use_white_outline:
            cv2.rectangle(img, (x0, y0), (x1, y1), color=(0,0,0), thickness=line_thick + 2)

        cv2.rectangle(img, (x0, y0), (x1, y1), color=line_color, thickness=line_thick)
        return img

    # ----- analysis -----
    @classmethod
    def check_profile(cls, img: np.ndarray, x0: int, y0: int, x1:int, y1:int,
                      direction: str = 'hor', ch_type: str = 'all'):
        pos = None
        profiles = []
        try:
            if img is None:
                return None, None

            img_h, img_w = img.shape[:2]

            x0 = max(int(x0), 0)
            x1 = min(int(x1), img_w)
            y0 = max(int(y0), 0)
            y1 = min(int(y1), img_h)

            if ch_type == 'all':
                ch = None
            else:
                ch = {'blue': 0, 'green': 1, 'red': 2}.get(ch_type, 0)

            if direction == 'hor':
                pos = np.arange(x0, x1)

                if img.ndim != 3:
                    profile = np.mean(img[y0:y1, x0:x1], axis=0)
                    profiles.append(profile)
                elif ch_type != 'all':
                    profile = np.mean(img[y0:y1, x0:x1, ch], axis=0)
                    profiles.append(profile)
                else:
                    for ch in range(3):
                        profile = np.mean(img[y0:y1, x0:x1, ch], axis=0)
                        profiles.append(profile)
            else:
                pos = np.arange(y0, y1)

                if img.ndim != 3:
                    profile = np.mean(img[y0:y1, x0:x1], axis=1)
                    profiles.append(profile)
                elif ch_type != 'all':
                    profile = np.mean(img[y0:y1, x0:x1, ch], axis=1)
                    profiles.append(profile)
                else:
                    for ch in range(3):
                        profile = np.mean(img[y0:y1, x0:x1, ch], axis=1)
                        profiles.append(profile)

        except Exception as err:
            print(err)
        return pos, profiles

    @classmethod
    def check_histgram(cls, img: np.ndarray, x0: int, x1: int, y0: int, y1: int):
        """Return list of histograms (1 or 3)."""
        try:
            if img is None:
                return []

            h, w = img.shape[:2]
            _x0, _x1 = max(min(x0, x1), 0), min(max(x0, x1), w)
            _y0, _y1 = max(min(y0, y1), 0), min(max(y0, y1), h)
            roi = img[_y0:_y1, _x0:_x1]

            hists = []
            if roi.size == 0:
                return []
            if roi.ndim == 3:
                for ch in range(3):
                    hist = cv2.calcHist([roi], [ch], None, [256], [0, 256])
                    hists.append(hist)
            else:
                hist = cv2.calcHist([roi], [0], None, [256], [0, 256])
                hists.append(hist)
            return hists
        except Exception as err:
            print(err)
            return []


def main():
    img = ImageFunc.open_img_file('test.png')
    if img is not None:
        ImageFunc.show_img(img)


if __name__ == '__main__':
    main()
