import cv2
import numpy as np

from opencv_func import ImageFunc


def img_proc(img_in: np.array):
    if img_in is None: return None

    img = img_in.copy()
    img_out = img_in.copy()

    try:
        img = ImageFunc.convert_intensity(img, coeff=1.3)

    except Exception as err:
        print(err)
        return img_in

    return img


def main():
    img = ImageFunc.open_img_file('test.png')
    ImageFunc.show_img(img)


if __name__ == '__main__':
    main()
