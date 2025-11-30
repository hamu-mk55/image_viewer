import numpy as np
from opencv_func import ImageFunc


def img_proc(img_in: np.ndarray):
    """
    Your real-time processing hook.
    Keep signature unchanged; return processed BGR/GRAY image (same size).
    """
    if img_in is None:
        return None

    try:
        # example: simple intensity gain
        return ImageFunc.convert_intensity(img_in, coeff=1.3)
    except Exception as err:
        print(err)
        # fail safe: return original
        return img_in


def main():
    img = ImageFunc.open_img_file('test.png')
    if img is not None:
        out = img_proc(img)
        ImageFunc.show_img(out)


if __name__ == '__main__':
    main()
