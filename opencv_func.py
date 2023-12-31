import os
from logging import getLogger, Logger

import cv2
import numpy as np
import matplotlib.pyplot as plt


class ImageFunc:
    """
    OpenCVの関数を纏めたクラス。インスタンスを生成せずに使用する。
    入力画像に対して、各種画像処理を実施し、処理後の画像を返す。
    """

    logger: Logger = getLogger(__name__)
    debug: bool = False

    @classmethod
    def set_logger(cls, logger=None):
        if logger is not None:
            cls.logger = logger
        else:
            cls.logger = getLogger(__name__)
        cls.debug = True

    @classmethod
    def open_img_file(cls, img_file: str,
                      gray_flg: bool = False,
                      unchanged_flg: bool = False) -> np.array:
        if not os.path.isfile(img_file):
            if cls.debug:
                cls.logger.warning(f'No file: {img_file}')
            return None

        if unchanged_flg:
            img = cv2.imread(img_file, cv2.IMREAD_UNCHANGED)
        elif gray_flg:
            img = cv2.imread(img_file, cv2.IMREAD_GRAYSCALE)
        else:
            img = cv2.imread(img_file, cv2.IMREAD_COLOR)

        return img

    @classmethod
    def save_img_file(cls, img: np.array, img_file: str) -> None:
        if img is not None:
            cv2.imwrite(img_file, img)
        else:
            if cls.debug:
                cls.logger.warning(f'No Image: {img_file}')

    @classmethod
    def show_img(cls, img: np.array, winname: str = 'window', delay_msec: int = 0) -> None:
        cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
        cv2.imshow(winname, img)
        cv2.waitKey(delay_msec)
        cv2.destroyAllWindows()

    @classmethod
    def show_img_by_plt(cls, img: np.array) -> None:
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img)
        plt.show()
        plt.close()

    @classmethod
    def crop(cls, img: np.array,
                      h0: int = None, h1: int = None,
                      w0: int = None, w1: int = None):

        # check image
        if img is None:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None

        img_h = img.shape[0]
        img_w = img.shape[1]

        # check if params are illegal
        if h0 is None:
            h0 = 0
        if h1 is None:
            h1 = img_h
        if w0 is None:
            w0 = 0
        if w1 is None:
            w1 = img_w
        if h0 < 0 or h1 > img_h or h0 > h1:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None
        if w0 < 0 or w1 > img_w or w0 > w1:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None

        # main
        if img.ndim == 3:
            img = img[h0:h1, w0:w1, :]
        else:
            img = img[h0:h1, w0:w1]

        return img

    @classmethod
    def crop_by_ratio(cls, img: np.array,
                      h0_ratio: float = 0.0, h1_ratio: float = 1.0,
                      w0_ratio: float = 0.0, w1_ratio: float = 1.0):

        # check if params are illegal
        if img is None:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None
        if h0_ratio < 0 or h1_ratio > 1 or h0_ratio > h1_ratio:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None
        if w0_ratio < 0 or w1_ratio > 1 or w0_ratio > w1_ratio:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None

        # main
        img_h = img.shape[0]
        img_w = img.shape[1]

        _h0 = int(img_h * h0_ratio)
        _h1 = int(img_h * h1_ratio)
        _w0 = int(img_w * w0_ratio)
        _w1 = int(img_w * w1_ratio)

        if img.ndim == 3:
            img = img[_h0:_h1, _w0:_w1, :]
        else:
            img = img[_h0:_h1, _w0:_w1]

        return img

    @classmethod
    def convert_color(cls, img_bgr:np.array, type:str='gray'):
        """
        BGR画像をモノクロ画像やHSV画像へ変換

        :param img_bgr: 入力画像
        :param type: 変換タイプ: gray, blue, green, red, hsv
        :return:
        """

        # check image
        if img_bgr is None:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None

        if img_bgr.ndim == 3:
            if type.lower() == 'gray':
                img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            elif type.lower() == 'hsv':
                img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            elif type.lower() == 'blue':
                img = img_bgr[:, :, 0]
            elif type.lower() == 'green':
                img = img_bgr[:, :, 1]
            elif type.lower() == 'red':
                img = img_bgr[:, :, 2]
            else:
                if cls.debug:
                    cls.logger.warning(f'No Image')
                return None
        else:
            img = img_bgr

        return img

    @classmethod
    def convert_intensity(cls, img:np.array, coeff:float=1.0, offset:float=0.0):
        # check image
        if img is None:
            if cls.debug:
                cls.logger.warning(f'No Image')
            return None

        img = coeff * img + offset
        img = np.clip(img, 0, 255).astype(np.uint8)

        return img

    @classmethod
    def threshold_gray(cls, img_bgr, thres=0, type='gray', inverse=False):
        """
        二値化(モノクロ, 1つの閾値)

        :param img_bgr:
        :param thres:
        :param type: 変換タイプ: gray, blue, green, red
        :param inverse:
        :return:
        """
        if type != 'hsv':
            _img = cls.trans(img_bgr)
        else:
            raise ValueError('illegal type')

        if not inverse:
            _, _img = cv2.threshold(_img, thres, 255, cv2.THRESH_BINARY)
        else:
            _, _img = cv2.threshold(_img, thres, 255, cv2.THRESH_BINARY_INV)

        return _img

    @classmethod
    def threshold_gray2(cls, img_bgr, thres_min=0, thres_max=255, type='gray'):
        """
        二値化(モノクロ, ２つの閾値)

        :param img_bgr:
        :param thres_min:
        :param thres_max:
        :param type: 変換タイプ: gray, blue, green, red
        :return:
        """
        if type != 'hsv':
            _img = cls.convert_color(img_bgr, type=type)
        else:
            raise ValueError('illegal type')

        mask_low = np.array(thres_min)
        mask_high = np.array(thres_max)
        _img = cv2.inRange(_img, mask_low, mask_high)

        return _img

    @classmethod
    def threshold_hsv(cls, img_bgr, low, high):
        """
        二値化(HSV)

        :param img_bgr:
        :param low:
        :param high:
        :return:
        """

        # caution: Hue-range is [0:180] in open-cv, [0:255] in image-J
        mask_low = np.array(low)
        mask_high = np.array(high)

        _img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        _img = cv2.inRange(_img, mask_low, mask_high)
        return _img

    @classmethod
    def threshold_bgr(cls, img_bgr, low, high):
        """
        二値化(BGR)

        :param img_bgr:
        :param low:
        :param high:
        :return:
        """

        mask_low = np.array(low)
        mask_high = np.array(high)

        _img = cv2.inRange(img_bgr, mask_low, mask_high)
        return _img

    @classmethod
    def erode(cls, img_bin, kernel=3, iter=2):
        """
        収縮処理

        :param img_bin:
        :param kernel:
        :param iter:
        :return:
        """
        _kernel = np.ones((kernel, kernel), np.uint8)
        _img = cv2.erode(img_bin, _kernel, iterations=iter)
        return _img

    @classmethod
    def dilate(cls, img_bin, kernel=3, iter=2):
        """
        膨張処理

        :param img_bin:
        :param kernel:
        :param iter:
        :return:
        """
        _kernel = np.ones((kernel, kernel), np.uint8)
        _img = cv2.dilate(img_bin, _kernel, iterations=iter)
        return _img

    @classmethod
    def draw_contours(cls, img_out, img_bin, fill=False, thickness=2, color=(255, 0, 0)):
        """
        輪郭追加

        :param img_out:
        :param img_bin:
        :param fill:
        :param thickness:
        :param color:
        :return:
        """

        # For OpenCV 4.8, ret-num is 2
        # _, contours, _ = cv2.findContours(img_bin, 1, 2)
        contours, _ = cv2.findContours(img_bin, 1, 2)

        if fill:
            _thickness = -1
        else:
            _thickness = thickness

        img_out = cv2.drawContours(img_out, contours, -1,
                                   color=color,
                                   thickness=_thickness)

        return img_out

    @classmethod
    def draw_cross(cls, img, x, y, line_thick=2, line_color=(255, 0, 0)):
        """
        十字線表示

        :param img:
        :param x:
        :param y:
        :param line_thick:
        :param line_color:
        :return:
        """
        img_h = img.shape[0]
        img_w = img.shape[1]

        cv2.line(img, (x, 0), (x, img_h), color=line_color, thickness=line_thick)
        cv2.line(img, (0, y), (img_w, y), color=line_color, thickness=line_thick)

        return img

    @classmethod
    def draw_rectangle(cls, img, x0, x1, y0, y1, line_thick=2, line_color=(255, 0, 0)):
        """
        矩形表示

        :param img:
        :param x0:
        :param x1:
        :param y0:
        :param y1:
        :param line_thick:
        :param line_color:
        :return:
        """

        cv2.rectangle(img, (x0, y0), (x1, y1), color=line_color, thickness=line_thick)

        return img

    @classmethod
    def check_profile(cls, img, x, y, direction='hor',
                      width=20, average=True, ch_type='all'):
        """
        プロファイル算出

        :param img:
        :param x:
        :param y:
        :param direction:
        :param width:
        :param average:
        :param ch_type:
        :return:
        """
        _pos = None
        _profile = None

        try:
            if img is None:
                return
            else:
                img_h = img.shape[0]
                img_w = img.shape[1]

            if ch_type == 'blue':
                ch = 0
            elif ch_type == 'green':
                ch = 1
            elif ch_type == 'red':
                ch = 2
            else:
                ch = 0

            if direction == 'hor':
                y0 = max(y - (width - 1) / 2, 0)
                y1 = min(y + (width - 1) / 2, img_h - 5)

                _pos = np.arange(0, img_w)

                if average:
                    if ch_type == 'all' or img.ndim < 3:
                        _profile = np.mean(img[int(y0):int(y1), :], axis=0)
                    else:
                        _profile = np.mean(img[int(y0):int(y1), :, ch], axis=0)
                else:
                    if img.ndim != 3:
                        _profile = img[int(y0):int(y1), :]
                    else:
                        _profile = img[int(y0):int(y1), :, ch]
                    _profile = _profile.T

            else:
                x0 = max(x - (width - 1) / 2, 0)
                x1 = min(x + (width - 1) / 2, img_w - 5)

                _pos = np.arange(0, img_h)

                if average:
                    if ch_type == 'all' or img.ndim < 3:
                        _profile = np.mean(img[:, int(x0):int(x1)], axis=1)
                    else:
                        _profile = np.mean(img[:, int(x0):int(x1), ch], axis=1)
                else:
                    if img.ndim != 3:
                        _profile = img[:, int(x0):int(x1), :]
                    else:
                        _profile = img[:, int(x0):int(x1), ch]
                    _profile = _profile.T

            # viewer = ProfileViewer(_pos, _profile)

        except Exception as err:
            print(err)

        return _pos, _profile

    @classmethod
    def check_histgram(cls, img, x0, x1, y0, y1):

        _hist_list = []

        try:
            if img is None:
                return

            img_h = img.shape[0]
            img_w = img.shape[1]

            _x0 = min(x0, x1)
            _x1 = max(x0, x1)
            _y0 = min(y0, y1)
            _y1 = max(y0, y1)
            _x0 = int(max(_x0, 0))
            _x1 = int(min(_x1, img_w))
            _y0 = int(max(_y0, 0))
            _y1 = int(min(_y1, img_h))

            img = img[_y0:_y1, _x0:_x1]

            if img.ndim==3:
                for ch_cnt in range(3):
                    _hist = cv2.calcHist([img], [ch_cnt], None, [256], [0, 256])
                    _hist_list.append(_hist)
            else:
                _hist = cv2.calcHist([img], [0], None, [256], [0, 256])
                _hist_list.append(_hist)

        except Exception as err:
            print(err)
            return []

        return _hist_list


def main():
    img = ImageFunc.open_img_file('test.png')
    ImageFunc.show_img(img)


if __name__ == '__main__':
    main()
