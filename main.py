import glob
import os
import sys
from typing import List, Optional, Tuple

import cv2
import tkinter
from tkinter import ttk, messagebox, simpledialog, filedialog


from image_info import ImageData, ImageInfo
from ini_file import ViewerIniFile
from image_proc import img_proc
from canvas import Canvas, CanvasStateSync


class ImageViewer:
    """
    Image viewer performing real-time processing via image_proc.img_proc().
    Functionality preserved; structure cleaned up.
    """

    def __init__(self, config_file: str = 'config.ini'):
        self.root = tkinter.Tk()
        self.root.title('ImageViewer')
        self.root.attributes('-topmost', True)
        self.root.protocol('WM_DELETE_WINDOW', self.close_window)

        # styles
        self.style_font = {'font': ("Arial", 15)}
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_blue = {'bg': '#0000ff', 'fg': '#ffffff'}

        # image params
        self.img_paths: List[str] = []
        self.imgs: List[ImageData] = []
        self.img_cnt = 0

        # image processing hook
        self.func_proc = None

        # config
        self.config_file = config_file
        self.config = ViewerIniFile(filename=self.config_file)
        self.config.load_inifile()

        # GUI params
        self.img_num_col = 1
        self.img_num_row = 1
        self.topmost = True

        # misc
        self.cwd = os.getcwd()
        self.img_dir = None
        # self.click_func = 'show_info'

        # frame-related
        self.root.update_idletasks()
        self.root_h = self.root.winfo_height()
        self.root_w = self.root.winfo_width()

        self.frame1 = None
        self.frame2 = None
        self.cvs_h = None
        self.cvs_w = None

        self.entry_file_key = None
        self.entry_file_no = None

        self.msg_file_num = tkinter.StringVar()
        self.msg_path = tkinter.StringVar()
        self.msg_pos = tkinter.StringVar()
        self.msg_img = tkinter.StringVar()
        self.msg_hsv = tkinter.StringVar()
        self.msg_size = tkinter.StringVar()

        # build UI
        self.reset_params()
        self.set_frames()
        self.set_shortcut()
        self.root.mainloop()

    def exit(self):
        self.root.destroy()

    def close_window(self):
        if messagebox.askokcancel("title", "close window?"):
            self.exit()

    # ---- UI build ---------------------------------------
    def set_frames(self):
        for child in self.root.winfo_children():
            child.destroy()

        # left: info/control
        self.frame1 = tkinter.Frame(self.root, width=300, height=self.root_h, borderwidth=10)
        self.frame1.pack(side='left', fill=tkinter.X)

        # right: images
        self.frame2 = tkinter.Frame(self.root, width=1700, height=self.root_h, bg='#fffffa', borderwidth=10)
        self.frame2.pack(side='right', fill=tkinter.X)

        self.set_frame1()

        self.root.update_idletasks()
        f2_h = self.frame2.winfo_height()
        f2_w = self.frame2.winfo_width()
        self.cvs_h = int(f2_h / self.img_num_row * 0.95)
        self.cvs_w = int(f2_w / self.img_num_col * 0.95)
        self.set_frame2()

        self.set_menu()

    def set_frame1(self, frame_width=20):

        def _label(text=None, textvariable=None, pady=1, **kwargs):
            params = {}
            if text is not None: params['text'] = text
            if textvariable is not None: params['textvariable'] = textvariable

            _lbl = tkinter.Label(self.frame1, width=frame_width, anchor=tkinter.W, **params, **kwargs)
            _lbl.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=pady)

        def _button(text, command, pady=10, **kwargs):
            _btn = tkinter.Button(self.frame1, width=frame_width, text=text, command=command, **kwargs)
            _btn['relief'] = tkinter.RAISED
            _btn.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=pady)

        def _horiontal_buttons(buttons, padx=5, button_width=7):
            _frame = tkinter.Frame(self.frame1)
            _frame.pack(anchor=tkinter.W, pady=1)

            for text, cmd in buttons:
                _btn = tkinter.Button(_frame, width=button_width, text=text, command=cmd)
                _btn.pack(side="left", padx=padx)

        def _entry(entry_name, entry_width,
                   pre_text=None, pre_textvar=None,
                   post_text=None, post_textvar=None):

            _frame = tkinter.Frame(self.frame1)
            _frame.pack(anchor=tkinter.W, pady=1)

            if pre_text is not None:
                _label = tkinter.Label(_frame, text=pre_text)
                _label.pack(side="left")
            elif pre_textvar is not None:
                _label = tkinter.Label(_frame, textvariable=pre_textvar)
                _label.pack(side="left")

            entry = tkinter.Entry(_frame, width=entry_width, justify='center')
            entry.pack(side="left")

            if post_text is not None:
                _label = tkinter.Label(_frame, text=post_text)
                _label.pack(side="left")
            elif post_textvar is not None:
                _label = tkinter.Label(_frame, textvariable=post_textvar)
                _label.pack(side="left")

            setattr(self, entry_name, entry)

        # info/control
        _label(text='file-------------------------------------------')

        self.msg_file_num.set('')
        _entry(entry_name='entry_file_no', entry_width=15,
               pre_text='file-no: ',
               post_textvar=self.msg_file_num)
        _horiontal_buttons([("move", self.jump_img)])

        _entry(entry_name='entry_file_key', entry_width=15,
               pre_text='file-key: ')
        _horiontal_buttons([("filter", self.filter_key), ("reset", self.reset_key)])
        self.entry_file_key.insert(0, self.config.img_key)

        _label(text='image info--------------------------------------', pady=(10, 1))
        self.msg_path.set('')
        _label(textvariable=self.msg_path, **self.style_color, **self.style_font)

        self.msg_pos.set('')
        _label(textvariable=self.msg_pos, **self.style_color, **self.style_font)

        self.msg_img.set('')
        _label(textvariable=self.msg_img, **self.style_color, **self.style_font)

        self.msg_hsv.set('')
        _label(textvariable=self.msg_hsv, **self.style_color, **self.style_font)

        self.msg_size.set('')
        _label(textvariable=self.msg_size, **self.style_color, **self.style_font)

        _button(text='Open Dir', command=self.load_img_list, **self.style_color_blue, **self.style_font)
        _button(text='Set ImageProcess', command=self.set_img_process, **self.style_color_red, **self.style_font)
        _button(text='Unset ImageProcess', command=self.reset_img_process, **self.style_color_red, **self.style_font)
        _button(text='Reset Layout', command=self.reset_params, **self.style_color_red, **self.style_font)

    def set_frame2(self):

        cnt = 0
        self.imgs = []

        self.show_info(self.img_cnt)
        sync = CanvasStateSync()

        for row in range(self.img_num_row):
            for col in range(self.img_num_col):
                # load img
                img_org, img_path = self.load_img_with_preprocess(self.img_cnt + cnt)

                _data = ImageData(img_org, self.cvs_h, self.cvs_w, img_path=img_path)
                self.imgs.append(_data)

                cell = tkinter.Frame(self.frame2, width=self.cvs_w, height=self.cvs_h)
                cell.grid(row=row, column=col, padx=4, pady=4)
                cell.grid_propagate(False)

                cvs = Canvas(cell, width=self.cvs_w, height=self.cvs_h, highlightthickness=0)
                cvs.grid()

                cvs.cvs_id = self.img_cnt + cnt
                cvs.set_image_data(image_data=_data, scale=self.config.zoom)

                sync.register_cvs(cvs)

                cnt += 1

                # set shortcuts if img is not None
                if img_org is not None:
                    cvs.set_callback(self.cvs_callback)

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
        for i in range(1, 5):
            col_menu.add_command(label=f'x{i}', command=lambda v=i: _set_images_num(col=v))
        menubar.add_cascade(label='Cols', menu=col_menu)

        row_menu = tkinter.Menu(menubar)
        for i in range(1, 5):
            row_menu.add_command(label=f'x{i}', command=lambda v=i: _set_images_num(row=v))
        menubar.add_cascade(label='Rows', menu=row_menu)

        self.root.config(menu=menubar)

    def set_shortcut(self):
        self.root.bind("<Down>", lambda e: self.next_img())
        self.root.bind("<Up>", lambda e: self.return_img())

    # ---- navigation -----------------------------------
    def start(self):
        if not self.img_paths:
            return 0
        self.img_cnt = 0
        self.set_frame2()

    def next_img(self):
        n = self.img_num_row * self.img_num_col
        if self.img_cnt + n < len(self.img_paths):
            self.img_cnt += n
            self.set_frame2()
        else:
            messagebox.showinfo('info', 'END of Images')

    def return_img(self):
        self.img_cnt -= self.img_num_row * self.img_num_col
        if self.img_cnt < 0:
            messagebox.showinfo('info', 'First Image')
            self.img_cnt = 0
        self.set_frame2()

    def jump_img(self):
        img_cnt = self.entry_file_no.get()

        try:
            img_cnt = int(img_cnt)

            if img_cnt < 0 or img_cnt >= len(self.img_paths):
                messagebox.showinfo('info', 'OUT-RANGE for file-no')
                self.entry_file_no.delete(0, tkinter.END)
                self.entry_file_no.insert(0, self.img_cnt)
            else:
                self.img_cnt = img_cnt
                self.set_frame2()
        except:
            self.entry_file_no.delete(0, tkinter.END)
            self.entry_file_no.insert(0, self.img_cnt)

    def filter_key(self):
        key = self.entry_file_key.get()
        self.img_paths = glob.glob(f'{self.img_dir}/**/{key}', recursive=True)

        self.img_cnt = 0
        self.set_frame2()

    def reset_key(self):
        key = self.config.img_key
        self.img_paths = glob.glob(f'{self.img_dir}/**/{key}', recursive=True)

        self.entry_file_key.delete(0, tkinter.END)
        self.entry_file_key.insert(0, key)

        self.img_cnt = 0
        self.set_frame2()

    # Mouse Event---------------------------------------------------------------------------------------
    def cvs_callback(self, mode, info:ImageInfo):
        if mode == "move":
            self.msg_pos.set(f'X: {info.x} Y: {info.y}')

            if info.val is not None:
                self.msg_img.set(f'vals: {info.val}')

            if info.hsv is not None:
                self.msg_hsv.set(f'hsv: {info.hsv}')

            if info.rect_h is not None:
                self.msg_size.set(f'w: {info.rect_w} h: {info.rect_h}')
            else:
                self.msg_size.set('')

    # Image Pipeline ----------------------------------------------------------------------------------------
    def load_img_with_preprocess(self, img_cnt: int):
        if 0 <= img_cnt < len(self.img_paths):
            path = self.img_paths[img_cnt]
            if not os.path.isfile(path):
                return None, None
            img = cv2.imread(path, cv2.IMREAD_COLOR)

            # external processing hook
            if self.func_proc is not None:
                img = self.func_proc(img)

            return img, path
        return None, None

    def show_info(self, img_cnt):
        if 0 <= img_cnt < len(self.img_paths):
            self.msg_path.set(os.path.basename(self.img_paths[img_cnt]))
        else:
            self.msg_path.set('')

        if len(self.img_paths) > 0:
            self.msg_file_num.set(f' /{len(self.img_paths)}')
            self.entry_file_no.delete(0, tkinter.END)
            self.entry_file_no.insert(0, img_cnt)
        else:
            self.msg_file_num.set('')
            self.entry_file_no.delete(0, tkinter.END)

    def load_img_list(self, img_dir: Optional[str] = None, ask_input: bool = True):
        if self.topmost:
            self.root.attributes('-topmost', False)

        if img_dir is None:
            img_dir = filedialog.askdirectory(initialdir=self.cwd)
        else:
            img_dir = os.path.join(self.cwd, img_dir)

        key = self.config.img_key
        if ask_input:
            ret = simpledialog.askstring("input",
                                         "探索したい画像ファイル名を入力してください\n"
                                         "空白orキャンセルの場合は初期値を使用\n"
                                         f"初期値：{key}")
            if ret:
                key = ret

        if self.topmost:
            self.root.attributes('-topmost', True)

        img_dir = os.path.relpath(img_dir) if img_dir else self.cwd

        self.img_dir = img_dir
        self.img_paths = glob.glob(f'{img_dir}/**/{key}', recursive=True)

        self.entry_file_key.delete(0, tkinter.END)
        self.entry_file_key.insert(0, key)

        self.start()

    # Setup params/functions-----------------------------------------------------------------------------------
    def set_img_process(self):
        try:
            del sys.modules['image_proc']
        except Exception as err:
            print(f'Error in delete module: {err}')

        from image_proc import img_proc  # reimport
        self.func_proc = img_proc
        self.set_frame2()

    def reset_img_process(self):
        self.func_proc = None
        self.set_frame2()

    def reset_params(self):
        self.func_proc = None
        self.config.load_inifile()

        self.img_num_col = self.config.img_num_col
        self.img_num_row = self.config.img_num_row

        self.root.geometry(self.config.win_size)
        self.topmost = True if 'y' in self.config.topmost.lower() else False
        self.root.attributes('-topmost', bool(self.topmost))

        self.root.update_idletasks()
        self.root_h = self.root.winfo_height()
        self.root_w = self.root.winfo_width()

        self.set_frames()


if __name__ == '__main__':
    ImageViewer()
