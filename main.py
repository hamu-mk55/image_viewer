import glob
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import tkinter
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk

from image_info import ImageData, ImageInfo
from opencv_func import ImageFunc
from sub_window import ProfileViewer, GraphViewer, HistogramViewer
from ini_file import ViewerIniFile
from image_proc import img_proc


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
        self.canvases: List[tkinter.Canvas] = []
        self.img_cnt = 0

        # image overlay
        self.gui_type = None
        self.rect_id = 1
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None

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
        self.click_func = 'show_info'

        # frame-related
        self.root.update_idletasks()
        self.root_h = self.root.winfo_height()
        self.root_w = self.root.winfo_width()

        self.frame1 = None
        self.frame2 = None
        self.img_h = None
        self.img_w = None

        self.entry_file_key = None
        self.entry_file_no = None

        self.msg_file_num = tkinter.StringVar()
        self.msg_path = tkinter.StringVar()
        self.msg_pos = tkinter.StringVar()
        self.msg_img = tkinter.StringVar()
        self.msg_hsv = tkinter.StringVar()
        self.msg_size = tkinter.StringVar()
        self.msg_shortcut_func = tkinter.StringVar()


        self.shortcut_func_list = ['None', 'Profile(Hor)', 'Profile(Ver)', 'Cross', 'Histogram', 'Histogram(HSV)']
        self.shortcut_func = self.shortcut_func_list[0]

        self.right_click_menu = None

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
        self.img_h = int(f2_h / self.img_num_row * 0.95)
        self.img_w = int(f2_w / self.img_num_col * 0.95)
        self.set_frame2()

        self.set_menu()
        self.set_right_click_menu()

    def set_frame1(self, frame_width=20):

        def _label(text=None, textvariable=None, pady=1, **kwargs):
            params = {}
            if text is not None: params['text'] = text
            if textvariable is not None: params['textvariable'] = textvariable

            _lbl = tkinter.Label(self.frame1, width=frame_width, anchor=tkinter.W, **params, **kwargs)
            _lbl.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=pady)
            return _lbl

        def _button(text, command, pady=10, **kwargs):
            _btn = tkinter.Button(self.frame1, width=frame_width, text=text, command=command, **kwargs)
            _btn['relief'] = tkinter.RAISED
            _btn.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=pady)
            return _btn

        def _sub_frame_entry(entry_name, entry_width,
                             label1_text,
                             btn1_text, btn1_command,
                             label2_text=None, label2_textvar=None,
                             btn2_text=None, btn2_command=None):
            _frame =tkinter.Frame(self.frame1)
            _frame.pack(anchor=tkinter.W, pady=1)

            _label = tkinter.Label(_frame, text=label1_text)
            _label.grid(row=0, column=0, padx=1, pady=1, sticky='w')

            entry = tkinter.Entry(_frame, width=entry_width, justify='center')
            entry.grid(row=0, column=1, columnspan=2, padx=1, pady=1, sticky='w')

            if label2_text is not None:
                _label = tkinter.Label(_frame, text=label2_text)
                _label.grid(row=0, column=3, padx=1, pady=1, sticky='w')
            elif label2_textvar is not None:
                _label = tkinter.Label(_frame, textvariable=label2_textvar)
                _label.grid(row=0, column=3, padx=1, pady=1, sticky='w')

            _buttun = tkinter.Button(_frame, text=btn1_text, command=btn1_command)
            _buttun.grid(row=1, column=0, padx=(0,0), pady=1, sticky='w')

            if btn2_text is not None:
                _buttun = tkinter.Button(_frame, text=btn2_text, command=btn2_command)
                _buttun.grid(row=1, column=1, padx=(0,0), pady=1, sticky='w')

            setattr(self, entry_name, entry)

        # info/control
        _label(text='file-------------------------------------------')

        self.msg_file_num.set(' / 564')
        _sub_frame_entry(entry_name='entry_file_no', entry_width=10,
                         label1_text='file-no:   ', label2_textvar=self.msg_file_num,
                         btn1_text='move', btn1_command=None,
                         btn2_text=None, btn2_command=None)

        _sub_frame_entry(entry_name='entry_file_key',entry_width=20,
                         label1_text='filter-key: ', label2_text=None,
                         btn1_text='filter', btn1_command=None,
                         btn2_text='reset', btn2_command=None)

        _label(text='image info--------------------------------------', pady=(10,1))
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

        # select function
        _label(text='Select shortcut-function')
        self.msg_shortcut_func.set(self.shortcut_func)
        combobox = ttk.Combobox(self.frame1, textvariable=self.msg_shortcut_func,
                                value=self.shortcut_func_list, state='readonly', **self.style_font)
        combobox.pack(fill=tkinter.X, anchor=tkinter.W, pady=0)

        def _combo(event):
            GraphViewer.delete()
            self.shortcut_func = self.msg_shortcut_func.get()
            self.set_frames()

        combobox.bind('<<ComboboxSelected>>', _combo)

    def set_frame2(self):

        cnt = 0
        self.imgs = []
        self.canvases = []

        self.show_img_path(self.img_cnt)

        for row in range(self.img_num_row):
            for col in range(self.img_num_col):
                # load img
                img_org = self.load_img_with_preprocess(self.img_cnt + cnt)
                self.imgs.append(ImageData(img_org, self.img_h, self.img_w))

                img = self.imgs[cnt].img_pil

                cell = tkinter.Frame(self.frame2, width=self.img_w, height=self.img_h)
                cell.grid(row=row, column=col, padx=4, pady=4)
                cell.grid_propagate(False)

                cvs = tkinter.Canvas(cell, width=self.img_w, height=self.img_h, highlightthickness=0)
                cvs.grid()

                cvs.cell_id = self.img_cnt + cnt
                cvs.create_image(0, 0, anchor="nw", image=img)

                self.canvases.append(cvs)

                cnt += 1

                # set shortcuts if img is not None
                if img is not None:
                    self.set_shortcut2cvs(cvs)

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

        # zoom_menu = tkinter.Menu(menubar)
        # zoom_menu.add_command(label='set zoom', command=self.set_zoom)
        # zoom_menu.add_command(label='unset zoom', command=self.unset_zoom)
        # menubar.add_cascade(label='Zoom', menu=zoom_menu)

        def _set_click_function(mode='show_info'):
            self.click_func = mode
            self.set_frame2()

        func_menu = tkinter.Menu(menubar)
        func_menu.add_command(label='show info', command=lambda: _set_click_function('show_info'))
        func_menu.add_command(label='save image', command=lambda: _set_click_function('save_image'))
        menubar.add_cascade(label='ClickFunc', menu=func_menu)

        self.root.config(menu=menubar)

    def set_right_click_menu(self):
        self.right_click_menu = tkinter.Menu(self.root, tearoff=0)
        self.right_click_menu.add_command(label="Zoom In", command=None)
        self.right_click_menu.add_command(label="Zoom Out", command=None)
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="Reset View", command=None)

    def set_shortcut(self):
        self.root.bind("<Down>", lambda e: self.next_img())
        self.root.bind("<Up>", lambda e: self.return_img())

    def set_shortcut2cvs(self, cvs):
        sf = self.shortcut_func.lower()
        if 'profile' in sf:
            cvs.bind("<Button>", self.show_profile)
        elif sf == 'cross':
            cvs.bind("<Button>", self.mouse_press)
        elif 'histogram' in sf:
            cvs.bind("<ButtonPress-1>", self.mouse_press)
            cvs.bind("<Button1-Motion>", self.mouse_drag)
            cvs.bind("<ButtonRelease-1>", self.mouse_release)
        else:
            cvs.bind("<ButtonPress-1>", self.mouse_press)
            cvs.bind("<Button1-Motion>", self.mouse_drag)
            cvs.bind("<ButtonRelease-1>", self.mouse_release)

        cvs.bind("<Button-3>", self.right_click_function)
        cvs.bind("<Motion>", self.show_info_mouse)

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

    # ---- event helpers ---------------------------------
    def _get_image_info(self, event, use_org_img=False):
        info = ImageInfo(use_org_img)

        info.cnt = int(event.widget.cell_id)
        info.full_path = self.img_paths[info.cnt]
        info.dir = os.path.basename(os.path.dirname(info.full_path))
        info.file = os.path.basename(info.full_path)
        info.gui_x = int(event.x)
        info.gui_y = int(event.y)

        imgdata = self.imgs[info.cnt - self.img_cnt]
        info.img = imgdata.img_org if use_org_img else imgdata.img_fit
        info.fit_ratio = imgdata.fit_ratio

        info.calc_params()
        return info

    def click_function(self, event):
        if self.click_func == 'save_image':
            self.save_image(event)
        else:
            self.show_info(event)

    def right_click_function(self, event):
        self.right_click_menu.tk_popup(event.x_root, event.y_root)
        self.right_click_menu.grab_release()

    def save_image(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)
        img_path = filedialog.asksaveasfilename(initialdir=self.cwd, initialfile=f'{info.file}')
        if not img_path:
            return
        cv2.imwrite(img_path, info.img)

    def show_info(self, event):
        info: ImageInfo = self._get_image_info(event)
        messagebox.showinfo('info',
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

        t = (self.gui_type or '').lower()
        if t == 'cross':
            cx, cy = self.x0, self.y0
            w = int(abs(info.x - cx) / info.fit_ratio * self.config.pix2um)
            h = int(abs(info.y - cy) / info.fit_ratio * self.config.pix2um)
            self.msg_size.set(f'W: {w}, H: {h}')
        else:
            self.msg_size.set('')

    def show_profile(self, event):
        info: ImageInfo = self._get_image_info(event, use_org_img=True)
        direction = 'ver' if self.shortcut_func == 'Profile(Ver)' else 'hor'
        pos, prof = ImageFunc.check_profile(info.img, x=info.x, y=info.y, direction=direction)
        ProfileViewer(self.root, pos, prof)

    # Mouse Event---------------------------------------------------------------------------------------
    def overlay_all_delete(self):
        for cvs in self.canvases:
            cvs.delete("overlay")

    def overlay_all_add(self, x0, y0, x1=None, y1=None):
        sf = self.shortcut_func.lower()
        if sf == 'cross':
            for cvs in self.canvases:
                cvs.create_line(0, y0, self.img_w, y0, fill="red", width=2, tags=("overlay",))
                cvs.create_line(x0, 0, x0, self.img_h, fill="red", width=2, tags=("overlay",))
        else:
            for cvs in self.canvases:
                cvs.create_rectangle(x0, y0, x1, y1, outline="red", width=2, tags=("overlay",))

    def mouse_press(self, event):
        cvs = event.widget
        self.x0 = event.x
        self.y0 = event.y

        self.overlay_all_delete()

        sf = self.shortcut_func.lower()
        if sf == 'cross':
            cvs.create_line(0, self.y0, self.img_w, self.y0, fill="red", width=2, tags=("overlay",))
            cvs.create_line(self.x0, 0, self.x0, self.img_h, fill="red", width=2, tags=("overlay",))
            self.overlay_all_add(self.x0, self.y0)
        else:
            self.rect_id = cvs.create_rectangle(0, 0, 0, 0, outline="red", width=2, tags=("overlay",))
            cvs.coords(self.rect_id, self.x0, self.y0, self.x0, self.y0)

    def mouse_drag(self, event):
        cvs = event.widget
        x = event.x
        y = event.y

        cvs.coords(self.rect_id, int(self.x0), int(self.y0), x, y)

    def mouse_release(self, event):
        self.x1 = event.x
        self.y1 = event.y

        self.overlay_all_add(int(self.x0), int(self.y0), int(self.x1), int(self.y1))

    # Image Pipeline ----------------------------------------------------------------------------------------
    def load_img_with_preprocess(self, img_cnt: int):
        if 0 <= img_cnt < len(self.img_paths):
            path = self.img_paths[img_cnt]
            if not os.path.isfile(path):
                return None
            img = cv2.imread(path, cv2.IMREAD_COLOR)

            # external processing hook
            if self.func_proc is not None:
                img = self.func_proc(img)

            return img
        return None

    def show_img_path(self, img_cnt):
        if 0 <= img_cnt < len(self.img_paths):
            self.msg_path.set(os.path.basename(self.img_paths[img_cnt]))
        else:
            self.msg_path.set('')

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

        self.shortcut_func = self.shortcut_func_list[0]
        self.msg_shortcut_func.set(self.shortcut_func)
        self.set_frames()


if __name__ == '__main__':
    ImageViewer()
