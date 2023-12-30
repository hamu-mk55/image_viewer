import os
import sys
import glob
import time

import cv2
import tkinter
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk

from gui_window import HistogramViewer, ProfileViewer, GraphViewer, ParamWindow
from opencv_func import ImageFunc
from gui_params import GuiParams
from image_proc import img_proc

def img_cv2tk(img_cv):
    """
    OpenCV->PIL
    :param img_cv: OpenCV-image
    :return:
    """

    if img_cv is None:
        return None

    if img_cv.ndim == 3:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

    img_pil = Image.fromarray(img_cv)
    img = ImageTk.PhotoImage(img_pil.convert('RGB'))
    return img


class ImageViewer:
    """
    TODO: 面積測定機能(モノクロ限定？)
    TODO: 二値化機能
    TODO: 二値化条件の自動抽出??クラスタリング、ヒストグラム
    """

    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title('ImageViewer')

        # define GUI
        self.root.attributes('-topmost', True)
        self.root.protocol('WM_DELETE_WINDOW', self.close_window)

        # define font/fg/bg
        self.style_font = {'font': ("Arial", 15)}
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_blue = {'bg': '#0000ff', 'fg': '#ffffff'}

        # parameters: images
        self.img_paths: list[str] = []
        self.imgs_cv: list[ImageCvData] = []
        self.imgs_pil: list[ImageTk.PhotoImage] = []
        self.img_cnt = 0

        self.func_proc = None

        self.preproc_zoom = False
        self.preproc_zoom_draw = False
        self.preproc_pos0 = None
        self.preproc_pos1 = None
        self.preproc_color = 'color'

        # parameters: GUI-Params
        self.param_gui = GuiParams()
        self.img_key = self.param_gui.img_key

        self.root.geometry(self.param_gui.win_size)
        self.img_num_col = self.param_gui.img_num_col
        self.img_num_row = self.param_gui.img_num_row
        self.topmost = self.param_gui.topmost
        if not self.topmost:
            self.root.attributes('-topmost', False)

        # parameters: etc
        self.cwd = os.getcwd()
        self.gui_timer = time.time()
        self.gui_response_sec = 0.1

        self.click_func = 'show_info'

        # parameters: frame
        self.root.update_idletasks()
        self.root_h = self.root.winfo_height()
        self.root_w = self.root.winfo_width()

        self.frame1 = None
        self.frame2 = None
        self.img_h = None
        self.img_w = None
        self.msg_path = tkinter.StringVar()
        self.msg_pos = tkinter.StringVar()
        self.msg_img = tkinter.StringVar()
        self.msg_hsv = tkinter.StringVar()
        self.msg_size = tkinter.StringVar()
        self.msg_shortcut_func = tkinter.StringVar()

        self.shortcut_func_list = ['None', 'Profile(Hor)', 'Profile(Ver)', 'Cross', 'Histogram', 'Histogram(HSV)']
        self.shortcut_func = self.shortcut_func_list[0]

        # start
        self.set_frames()
        self.set_shortcut()

        self.open_param_window()

        self.root.mainloop()

    def set_frames(self):
        # Delete Frames
        children = self.root.winfo_children()
        for child in children:
            child.destroy()

        # Define Frames
        # frame1: user-interface
        self.frame1 = tkinter.Frame(self.root,
                                    width=300,
                                    height=self.root_h,
                                    borderwidth=10,
                                    )
        self.frame1.pack(side='left', fill=tkinter.X)

        # frame2: image-viewer
        self.frame2 = tkinter.Frame(self.root,
                                    width=1700,
                                    height=self.root_h,
                                    # relief='groove',
                                    bg='#fffffa',
                                    borderwidth=10
                                    )
        self.frame2.pack(side='right', fill=tkinter.X)

        # Set Frames
        self.set_frame1()

        self.root.update_idletasks()
        _frame2_h = self.frame2.winfo_height()
        _frame2_w = self.frame2.winfo_width()
        self.img_h = int(_frame2_h / self.img_num_row * 0.95)
        self.img_w = int(_frame2_w / self.img_num_col * 0.95)
        self.set_frame2()

        # Set Menu
        self.set_menu()

    def set_frame1(self):
        _frame1_w = 20

        def _set_label(text=None, textvariable=None, **kwargs):
            _params = {}
            if text is not None: _params['text'] = text
            if textvariable is not None: _params['textvariable'] = textvariable

            _label = tkinter.Label(self.frame1,
                                   width=_frame1_w,
                                   anchor=tkinter.W,
                                   **_params,
                                   **kwargs
                                   )
            _label.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=1)
            return _label

        def _set_button(text, command, **kwargs):
            _button = tkinter.Button(self.frame1,
                                     width=_frame1_w,
                                     text=text,
                                     command=command,
                                     **kwargs
                                     )
            _button['relief'] = tkinter.RAISED
            _button.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=10)
            return _button

        # title
        _set_label(text='image info')

        # show img_path
        self.msg_path.set('')
        _set_label(textvariable=self.msg_path, **self.style_color, **self.style_font)

        # show pos_info
        self.msg_pos.set('')
        _set_label(textvariable=self.msg_pos, **self.style_color, **self.style_font)

        # show img_info
        self.msg_img.set('')
        _set_label(textvariable=self.msg_img, **self.style_color, **self.style_font)

        # show hsv_info
        self.msg_hsv.set('')
        _set_label(textvariable=self.msg_hsv, **self.style_color, **self.style_font)

        # show size_info
        self.msg_size.set('')
        _set_label(textvariable=self.msg_size, **self.style_color, **self.style_font)

        # button: open_dir
        _set_button(text='Open Dir', command=self.load_img_list,
                    **self.style_color_blue, **self.style_font)

        # button: set_image-process
        _set_button(text='Set ImageProcess', command=self.set_img_process,
                    **self.style_color_red, **self.style_font)

        # button: unset image-process
        _set_button(text='Unset ImageProcess', command=self.reset_img_process,
                    **self.style_color_red, **self.style_font)

        # button: update layout-parameters
        _set_button(text='Reset Layout', command=self.update_params,
                    **self.style_color_red, **self.style_font)

        # commbo: select shortcut-function
        _set_label(text='Select shortcut-function')

        self.msg_shortcut_func.set(self.shortcut_func)
        combobox = ttk.Combobox(self.frame1,
                                textvariable=self.msg_shortcut_func,
                                value=self.shortcut_func_list,
                                state='readonly',
                                **self.style_font)
        combobox.pack(fill=tkinter.X, anchor=tkinter.W, pady=0)

        def _combo(event):
            GraphViewer.delete()
            self.param_gui.reset()
            self.shortcut_func = self.msg_shortcut_func.get()
            self.set_frames()

        combobox.bind('<<ComboboxSelected>>', _combo)

    def set_frame2(self, update_cv=True):
        # initialize
        _cnt = 0
        if update_cv:
            self.imgs_cv = []
        self.imgs_pil = []

        # show info for gui
        self.show_img_path(self.img_cnt)

        # main
        for _row in range(self.img_num_row):
            for _col in range(self.img_num_col):
                # OpenCV->Image Process
                if update_cv:
                    _img_org = self.load_img_with_preprocess(self.img_cnt + _cnt)
                    self.imgs_cv.append(ImageCvData(_img_org, self.img_h, self.img_w))

                # Fit Window
                img = self.imgs_cv[_cnt].img_fit

                # Draw Shape->PIL
                img = self.img_cv2viewer(img)
                self.imgs_pil.append(img)

                # Set frame->image
                _frame = tkinter.Frame(self.frame2,
                                       width=self.img_w, height=self.img_h)
                _frame.grid(row=_row, column=_col, padx=4, pady=4)
                _frame.grid_propagate(False)

                _label = tkinter.Label(_frame,
                                       text=str(self.img_cnt + _cnt),
                                       image=self.imgs_pil[_cnt],
                                       compound='none',
                                       **self.style_color, **self.style_font
                                       )
                _label.grid()

                # Set shortcut
                if 'profile' in self.shortcut_func.lower():
                    _label.bind("<Button>", self.show_profile)
                elif self.shortcut_func.lower() == 'cross':
                    _label.bind("<Button>", self.set_cross)
                elif 'histogram' in self.shortcut_func.lower():
                    _label.bind("<ButtonPress-1>", self.show_histogram_press)
                    _label.bind("<Button1-Motion>", self.show_histogram_drag)
                    _label.bind("<ButtonRelease-1>", self.show_histogram_release)
                else:
                    _label.bind("<ButtonPress-1>", self.set_zoom_press)
                    _label.bind("<Button1-Motion>", self.set_zoom_drag)
                    _label.bind("<ButtonRelease-1>", self.set_zoom_release)

                _label.bind("<Button-3>", self.click_function)
                _label.bind("<Motion>", self.show_info_mouse)

                _cnt += 1
        pass

    def set_menu(self):
        menubar = tkinter.Menu(self.root)

        file_menu = tkinter.Menu(menubar)
        file_menu.add_command(label='exit', command=self.exit)
        menubar.add_cascade(label='File', menu=file_menu)

        def _set_images_num(col=None, row=None):
            if col is not None: self.img_num_col = col
            if row is not None: self.img_num_row = row
            self.set_frames()

        col_menu = tkinter.Menu(menubar)
        col_menu.add_command(label='x1', command=lambda: _set_images_num(col=1))
        col_menu.add_command(label='x2', command=lambda: _set_images_num(col=2))
        col_menu.add_command(label='x3', command=lambda: _set_images_num(col=3))
        col_menu.add_command(label='x4', command=lambda: _set_images_num(col=4))
        menubar.add_cascade(label='Cols', menu=col_menu)

        row_menu = tkinter.Menu(menubar)
        row_menu.add_command(label='x1', command=lambda: _set_images_num(row=1))
        row_menu.add_command(label='x2', command=lambda: _set_images_num(row=2))
        row_menu.add_command(label='x3', command=lambda: _set_images_num(row=3))
        row_menu.add_command(label='x4', command=lambda: _set_images_num(row=4))
        menubar.add_cascade(label='Rows', menu=row_menu)

        def _set_preproc_color(mode='color'):
            self.preproc_color = mode
            self.set_frame2()

        color_menu = tkinter.Menu(menubar)
        color_menu.add_command(label='color', command=lambda: _set_preproc_color('color'))
        color_menu.add_command(label='gray', command=lambda: _set_preproc_color('gray'))
        color_menu.add_command(label='red', command=lambda: _set_preproc_color('red'))
        color_menu.add_command(label='green', command=lambda: _set_preproc_color('green'))
        color_menu.add_command(label='blue', command=lambda: _set_preproc_color('blue'))
        color_menu.add_command(label='hue', command=lambda: _set_preproc_color('h'))
        color_menu.add_command(label='saturation', command=lambda: _set_preproc_color('s'))
        color_menu.add_command(label='value', command=lambda: _set_preproc_color('v'))
        menubar.add_cascade(label='Color', menu=color_menu)

        zoom_menu = tkinter.Menu(menubar)
        zoom_menu.add_command(label='set zoom', command=self.set_zoom)
        zoom_menu.add_command(label='unset zoom', command=self.unset_zoom)
        menubar.add_cascade(label='Zoom', menu=zoom_menu)

        def _set_click_function(mode='show_info'):
            self.click_func = mode
            self.set_frame2()

        func_menu = tkinter.Menu(menubar)
        func_menu.add_command(label='show info', command=lambda: _set_click_function('show_info'))
        func_menu.add_command(label='save image', command=lambda: _set_click_function('save_image'))
        menubar.add_cascade(label='ClickFunc', menu=func_menu)

        self.root.config(menu=menubar)

    def set_shortcut(self):
        def _next(event):
            self.next_img()

        def _return(event):
            self.return_img()

        def _example(event):
            print('widget: ', event.widget)
            print('keysym: ', event.keysym)
            print('type: ', event.type)

        self.root.bind("<Down>", _next)
        self.root.bind("<Up>", _return)

    def start(self):
        if len(self.img_paths) == 0:
            return 0

        self.img_cnt = 0
        self.set_frame2()

    def next_img(self):
        _img_num = self.img_num_row * self.img_num_col

        if self.img_cnt + _img_num < len(self.img_paths):
            self.img_cnt += _img_num
            self.set_frame2()
        else:
            tkinter.messagebox.showinfo('info', 'END of Images')
            pass

    def return_img(self):
        self.img_cnt -= self.img_num_row * self.img_num_col

        if self.img_cnt < 0:
            tkinter.messagebox.showinfo('info', 'First Image')
            self.img_cnt = 0

        self.set_frame2()

    def _get_image_info(self, event, use_org_img=False):
        info = ImageInfo(use_org_img)

        info.cnt = int(event.widget['text'])
        info.full_path = self.img_paths[info.cnt]
        info.dir = os.path.basename(os.path.dirname(info.full_path))
        info.file = os.path.basename(info.full_path)
        info.gui_x = int(event.x)
        info.gui_y = int(event.y)

        if use_org_img:
            info.img = self.imgs_cv[info.cnt - self.img_cnt].img_org
        else:
            info.img = self.imgs_cv[info.cnt - self.img_cnt].img_fit

        info.fit_ratio = self.imgs_cv[info.cnt - self.img_cnt].fit_ratio

        info.calc_params()

        return info

    def click_function(self, event):
        if self.click_func=='save_image':
            self.save_image(event)
        else:
            self.show_info(event)

    def save_image(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)

        img_path = tkinter.filedialog.asksaveasfilename(initialdir=self.cwd,
                                                        initialfile=f'{info.file}')
        if img_path is None: return
        if len(img_path)<1: return

        cv2.imwrite(img_path, info.img)

    def show_info(self, event):
        info: ImageInfo = self._get_image_info(event)

        tkinter.messagebox.showinfo('info',
                                    f'path: {info.full_path}\n'
                                    f'dir: {info.dir}\n'
                                    f'file: {info.file}\n'
                                    f'img_h: {info.img_h_org}\n'
                                    f'img_w: {info.img_w_org}\n')

    def show_info_mouse(self, event):
        info: ImageInfo = self._get_image_info(event)

        self.msg_path.set(info.file)
        self.msg_pos.set(f'X: {info.x_org} Y: {info.y_org}')
        self.msg_img.set(f'BGR: {info.val}')
        self.msg_hsv.set(f'HSV: {info.hsv}')

        _type = self.param_gui.gui_type
        if _type is not None and _type.lower() == 'cross':
            _cross_x0 = self.param_gui.x0
            _cross_y0 = self.param_gui.y0
            _w = int(abs(info.x - _cross_x0) / info.fit_ratio * self.param_gui.pix2um)
            _h = int(abs(info.y - _cross_y0) / info.fit_ratio * self.param_gui.pix2um)
            self.msg_size.set(f'W: {_w}, H: {_h}')
        else:
            self.msg_size.set('')

    def show_profile(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)

        if self.shortcut_func == 'Profile(Ver)':
            _direction = 'ver'
        else:
            _direction = 'hor'

        _pos, _profile = ImageFunc.check_profile(info.img, x=info.x, y=info.y, direction=_direction)
        _viewer = ProfileViewer(self.root, _pos, _profile)

    def show_histogram_press(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)

        self.param_gui.reset()
        self.param_gui.set_type('Rectangle')
        self.param_gui.set_pos0(info.x_fit, info.y_fit)
        self.gui_timer = time.time()

    def show_histogram_drag(self, event):
        if time.time() - self.gui_timer < self.gui_response_sec:
            return
        else:
            self.gui_timer = time.time()

        info: ImageInfo = self._get_image_info(event, use_org_img=True)

        self.param_gui.set_pos1(info.x_fit, info.y_fit)
        self.set_frame2(update_cv=False)

    def show_histogram_release(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)

        self.param_gui.set_pos1(info.x_fit, info.y_fit)

        if self.shortcut_func == 'Histogram(HSV)':
            _img = cv2.cvtColor(info.img, cv2.COLOR_BGR2HSV)
            labels = ('Hue', 'Saturation', 'Bright')
        else:
            _img = info.img
            labels = ('Blue', 'Green', 'Red')

        x0 = int(self.param_gui.x0 / info.fit_ratio)
        x1 = int(self.param_gui.x1 / info.fit_ratio)
        y0 = int(self.param_gui.y0 / info.fit_ratio)
        y1 = int(self.param_gui.y1 / info.fit_ratio)
        _hist_list = ImageFunc.check_histgram(_img,
                                              x0=x0, x1=x1,
                                              y0=y0, y1=y1)
        _viewer = HistogramViewer(self.root, _hist_list, labels=labels)

        self.set_frame2(update_cv=False)

    def set_cross(self, event):
        info: ImageInfo = self._get_image_info(event)

        self.param_gui.set_type('Cross')
        self.param_gui.set_pos0(x0=info.x, y0=info.y)

        self.set_frame2(update_cv=False)

    def set_zoom_press(self, event):
        if self.preproc_zoom: return

        info: ImageInfo = self._get_image_info(event)

        self.preproc_pos0 = (info.x_org, info.y_org)
        self.gui_timer = time.time()

    def set_zoom_drag(self, event):
        if self.preproc_zoom: return

        if time.time() - self.gui_timer < self.gui_response_sec:
            return
        else:
            self.gui_timer = time.time()

        info: ImageInfo = self._get_image_info(event)
        self.preproc_pos1 = (info.x_org, info.y_org)

        self.preproc_zoom_draw = True
        self.set_frame2()

    def set_zoom_release(self, event):
        if self.preproc_zoom: return

        info: ImageInfo = self._get_image_info(event)

        _x0 = self.preproc_pos0[0] * info.fit_ratio
        _y0 = self.preproc_pos0[1] * info.fit_ratio
        if abs(info.x - _x0) < 5 or abs(info.y - _y0) < 5:
            self.preproc_pos0 = None
            self.preproc_pos1 = None
            self.preproc_zoom = False
            self.preproc_zoom_draw = False
            self.set_frame2()
            return

        self.preproc_pos1 = (info.x_org, info.y_org)
        self.preproc_zoom = True
        self.preproc_zoom_draw = False
        self.set_frame2()

    def set_zoom(self):
        if self.preproc_pos0 is None: return
        if self.preproc_pos1 is None: return
        self.preproc_zoom = True
        self.set_frame2()

    def unset_zoom(self):
        self.preproc_zoom = False
        self.set_frame2()

    def load_img_with_preprocess(self, img_cnt):
        if 0 <= img_cnt < len(self.img_paths):
            _img_path = self.img_paths[img_cnt]

            if not os.path.isfile(_img_path):
                return None

            _img = cv2.imread(_img_path, cv2.IMREAD_COLOR)

            # image process---------------
            _img = self.img_preproc(_img)

            if self.func_proc is not None:
                _img = self.func_proc(_img)

            return _img
        else:
            return None

    def img_preproc(self, img_cv):
        if img_cv is None: return None

        img = img_cv.copy()

        if img.ndim == 3:
            if self.preproc_color == 'gray':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            elif self.preproc_color == 'blue':
                img = img[:, :, 0]
            elif self.preproc_color == 'green':
                img = img[:, :, 1]
            elif self.preproc_color == 'red':
                img = img[:, :, 2]
            elif self.preproc_color == 'h':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                img = img[:, :, 0]
            elif self.preproc_color == 's':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                img = img[:, :, 1]
            elif self.preproc_color == 'v':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                img = img[:, :, 2]

        img_out = img.copy()
        if self.preproc_pos1 is not None:
            x0 = self.preproc_pos0[0]
            y0 = self.preproc_pos0[1]
            x1 = self.preproc_pos1[0]
            y1 = self.preproc_pos1[1]

            if self.preproc_zoom_draw:
                img_out = draw_rectangle(img_out, x0, x1, y0, y1)
            if self.preproc_zoom:
                img_out = img_out[min(y0, y1):max(y0, y1), min(x0, x1):max(x0, x1)]

        return img_out

    def img_cv2viewer(self, img_cv):
        if img_cv is None: return None

        img = img_cv.copy()
        img = self.param_gui.draw_img(img)
        img = img_cv2tk(img)

        return img

    def show_img_path(self, img_cnt):
        if 0 <= img_cnt < len(self.img_paths):
            _img_path = self.img_paths[img_cnt]
            _img_path = os.path.basename(_img_path)

            self.msg_path.set(_img_path)
        else:
            self.msg_path.set('')

    def load_img_list(self, dir=None, input=True):
        if self.topmost:
            self.root.attributes('-topmost', False)

        if dir is None:
            dir = tkinter.filedialog.askdirectory(initialdir=self.cwd)
        else:
            dir = os.path.join(self.cwd, dir)

        _img_key = self.img_key
        if input:
            ret = tkinter.simpledialog.askstring("input",
                                                 "探索したい画像ファイル名を入力してください\n"
                                                 "空白orキャンセルの場合は初期値を使用\n"
                                                 f"初期値：{self.img_key}")
            if ret is not None and len(ret) > 0:
                _img_key = ret

        if self.topmost:
            self.root.attributes('-topmost', True)

        # self.img_path_list = glob.glob(os.path.join(_dir, '*.png'))

        dir = os.path.relpath(dir)
        self.img_paths = glob.glob(f'{dir}/**/{_img_key}', recursive=True)

        self.start()

    def set_img_process(self):
        try:
            del sys.modules['image_proc']
        except Exception as err:
            print(err)

        from image_proc import img_proc
        self.func_proc = img_proc

        self.set_frame2()

        self.root.after(100, self.img_preproc)

    def reset_img_process(self):
        self.func_proc = None
        self.set_frame2()

    def update_params(self):
        try:
            del sys.modules['gui_params']
        except Exception as ee:
            print(ee)

        from gui_params import GuiParams
        self.func_proc = None
        self.param_gui = GuiParams()

        self.root.geometry(self.param_gui.win_size)
        self.img_num_col = self.param_gui.img_num_col
        self.img_num_row = self.param_gui.img_num_row
        self.topmost = self.param_gui.topmost
        if self.topmost:
            self.root.attributes('-topmost', True)
        else:
            self.root.attributes('-topmost', False)

        self.root.update_idletasks()
        self.root_h = self.root.winfo_height()
        self.root_w = self.root.winfo_width()

        self.shortcut_func = self.msg_shortcut_func.get()

        self.set_frames()

    def open_param_window(self):
        def _print(event):
            pass
            # print(app.msg_color.get())
            # print(app.msg_scale.get())

        app = ParamWindow(self.root)
        # app.combobox.bind('<<ComboboxSelected>>', _print)

    def exit(self):
        self.root.destroy()

    def close_window(self):
        _ret = tkinter.messagebox.askokcancel("title", "close window?")
        if _ret: self.exit()


class ImageCvData:
    def __init__(self, img_cv, img_win_h, img_win_w):
        self.img_org = img_cv
        self.img_fit = None
        self.fit_ratio = None

        self._img_win_h = img_win_h
        self._img_win_w = img_win_w

        self._fit_window()

    def _fit_window(self):
        if self.img_org is None: return

        try:
            img_h = self.img_org.shape[0]
            img_w = self.img_org.shape[1]

            _h_ratio = self._img_win_h / img_h
            _w_ratio = self._img_win_w / img_w
            _ratio = min(_h_ratio, _w_ratio)

            self.img_fit = cv2.resize(self.img_org,
                                  (int(img_w * _ratio), int(img_h * _ratio)))
            self.fit_ratio = _ratio
        except:
            self.img_fit = None
            self.fit_ratio = None


class ImageInfo:
    def __init__(self, use_org_img=False):
        self.use_org_img = use_org_img

        # params: need to be defined
        self.cnt = None
        self.full_path = None
        self.dir = None
        self.file = None

        self.img = None
        self.fit_ratio = None
        self.gui_x = None
        self.gui_y = None

        # params: calculate
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
        if self.img is None: return

        # img shape
        self.img_h = self.img.shape[0]
        self.img_w = self.img.shape[1]
        if not self.use_org_img:
            self.img_h_org = int(self.img_h / self.fit_ratio)
            self.img_w_org = int(self.img_w / self.fit_ratio)

        # x/y position
        if self.use_org_img:
            _x = int(self.gui_x / self.fit_ratio)
            _y = int(self.gui_y / self.fit_ratio)
            self.x_fit = int(_x * self.fit_ratio)
            self.y_fit = int(_y * self.fit_ratio)
        else:
            _x = self.gui_x
            _y = self.gui_y
            self.x_org = int(_x / self.fit_ratio)
            self.y_org = int(_y / self.fit_ratio)

        self.x = min(_x, self.img_w - 5)
        self.y = min(_y, self.img_h - 5)

        # image value
        self.val = self.img[self.y, self.x]

        try:
            _img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
            self.hsv = _img_hsv[self.y, self.x]
        except:
            self.hsv = ''


def draw_rectangle(img, x0, x1, y0, y1, line_thick=2, line_color=(255, 0, 0)):
    _img_h = img.shape[0]
    line_thick = int(line_thick * _img_h / 500)

    cv2.rectangle(img, (x0, y0), (x1, y1), color=0, thickness=line_thick + 2)
    cv2.rectangle(img, (x0, y0), (x1, y1), color=line_color, thickness=line_thick)
    return img


def main():
    app = ImageViewer()


if __name__ == '__main__':
    main()
