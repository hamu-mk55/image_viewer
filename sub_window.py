

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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure



# ---- helpers ----
# def cv_to_tk(img_cv):
#     """Convert OpenCV BGR/GRAY numpy image to Tk PhotoImage."""
#     if img_cv is None:
#         return None
#     img = img_cv
#     if img.ndim == 3:
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     pil = Image.fromarray(img)
#     return ImageTk.PhotoImage(pil.convert('RGB'))


# ---- Param windows ----
class ParamsForSingleChannel:
    def __init__(self):
        self.mode = 'single'
        self.lower = 125
        self.upper = 255
        self.inverse = False

    def to_dict(self):
        return {
            "mode": self.mode,
            "value_inverse": self.inverse,
            "value_lower": self.lower,
            "value_upper": self.upper,
        }


class ParamWindow:
    is_exist = False
    root = None

    def __init__(self, parent):
        if ParamWindow.is_exist:
            self.start()
            return

        ParamWindow.root = tkinter.Toplevel(parent)
        ParamWindow.root.title('Params')
        ParamWindow.root.attributes('-topmost', False)
        ParamWindow.root.geometry('220x220')
        ParamWindow.root.protocol('WM_DELETE_WINDOW', self.exit)
        ParamWindow.is_exist = True

        # style (fix: blue/red collision in original)
        self.style_font = ("Arial", 15)
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_blue = {'bg': '#0000ff', 'fg': '#ffffff'}

        # buttons
        self.btn_set = None
        self.btn_unset = None

        # outputs
        self.proc_flg = False
        self.params_dict = {}

        # frame
        self.frame = None
        self.set_frame()

    def set_frame(self):
        for child in ParamWindow.root.winfo_children():
            child.destroy()

        self.frame = tkinter.Frame(ParamWindow.root)
        self.frame.pack()

        self.frame_btn = tkinter.Frame(ParamWindow.root)
        self.frame_btn.pack(pady=20)
        self.set_btn()

    def set_btn(self):
        def _call_set():
            self.proc_flg = True

        def _call_unset():
            self.proc_flg = False

        self.btn_set = tkinter.Button(self.frame_btn, text='Set', width=8, command=_call_set)
        self.btn_set['relief'] = tkinter.RAISED
        self.btn_set.grid(row=0, column=0, sticky=tkinter.W)

        self.btn_unset = tkinter.Button(self.frame_btn, text='Unset', width=8, command=_call_unset)
        self.btn_unset['relief'] = tkinter.RAISED
        self.btn_unset.grid(row=0, column=1, sticky=tkinter.E, padx=2)

    def start(self):
        ParamWindow.root.mainloop()

    def __del__(self):
        self.exit()

    def exit(self):
        try:
            ParamWindow.is_exist = False
            self.proc_flg = False
            ParamWindow.root.destroy()
        except Exception:
            pass


class ParamWindowForSingleChannel(ParamWindow):
    def __init__(self, parent):
        super().__init__(parent)

        ParamWindow.root.geometry('240x200')
        self.param = ParamsForSingleChannel()
        self.params_dict = self.param.to_dict()

        # parts
        self.check_inv = None
        self.entry_lower = None
        self.entry_upper = None

        self.set_entries()

    def set_entries(self, label_width=10, entry_width=5, entry_justify='right'):
        def _apply(mode: str):
            inv = is_inverse.get()
            try:
                up = int(self.entry_upper.get())
            except Exception:
                up = self.param.upper
            try:
                lo = int(self.entry_lower.get())
            except Exception:
                lo = self.param.lower

            if mode == 'lower' and up <= lo:
                up = lo + 1
            elif mode == 'upper' and lo >= up:
                lo = up - 1

            self.param.lower, self.param.upper, self.param.inverse = lo, up, inv
            is_inverse.set(self.param.inverse)
            self.entry_lower.delete(0, tkinter.END); self.entry_lower.insert(tkinter.END, f'{self.param.lower}')
            self.entry_upper.delete(0, tkinter.END); self.entry_upper.insert(tkinter.END, f'{self.param.upper}')
            self.params_dict = self.param.to_dict()

        # Label
        tkinter.Label(self.frame, text='Value').grid(row=0, column=0, sticky=tkinter.W)

        # CheckBOX
        is_inverse = tkinter.BooleanVar(value=self.param.inverse)
        self.check_inv = tkinter.Checkbutton(self.frame, text='inverse', variable=is_inverse,
                                             command=lambda: _apply('inv'))
        self.check_inv.grid(row=1, column=0, padx=20, sticky=tkinter.W)

        # Entry: lower
        tkinter.Label(self.frame, text='lower', width=label_width).grid(row=2, column=0, sticky=tkinter.W)
        self.entry_lower = tkinter.Entry(self.frame, width=entry_width, justify=entry_justify)
        self.entry_lower.grid(row=2, column=1)
        self.entry_lower.insert(tkinter.END, f'{self.param.lower}')
        self.entry_lower.bind('<Return>', lambda e: _apply('lower'))

        # Entry: upper
        tkinter.Label(self.frame, text='upper', width=label_width).grid(row=3, column=0, sticky=tkinter.W)
        self.entry_upper = tkinter.Entry(self.frame, width=entry_width, justify=entry_justify)
        self.entry_upper.grid(row=3, column=1)
        self.entry_upper.insert(tkinter.END, f'{self.param.upper}')
        self.entry_upper.bind('<Return>', lambda e: _apply('upper'))


# ---- viewers ----
class GraphViewer:
    """Matplotlib single-window viewer (singleton by default)."""
    is_exist = False
    root = None

    @classmethod
    def delete(cls):
        try:
            GraphViewer.is_exist = False
            GraphViewer.root.destroy()
        except Exception:
            pass

    def __init__(self, parent, singleton: bool = True):
        self.singleton = singleton

        if singleton and not GraphViewer.is_exist:
            GraphViewer.root = tkinter.Toplevel(parent)
            GraphViewer.root.title('Viewer')
            GraphViewer.root.attributes('-topmost', True)
            GraphViewer.root.protocol('WM_DELETE_WINDOW', self.exit)
            GraphViewer.is_exist = True
            self.container = GraphViewer.root
        elif singleton:
            for child in GraphViewer.root.winfo_children():
                child.destroy()
            self.container = GraphViewer.root
        else:
            self.root = tkinter.Toplevel(parent)
            self.root.title('Viewer')
            self.root.attributes('-topmost', True)
            self.root.protocol('WM_DELETE_WINDOW', self.exit)
            self.container = self.root

        self.frame = tkinter.Frame(self.container)
        self.fig = Figure()
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame)
        self.canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)
        self.frame.pack(fill=tkinter.BOTH, expand=True)

    def __del__(self):
        self.exit()

    def start(self):
        self.canvas.draw()
        if self.singleton:
            GraphViewer.root.mainloop()
        else:
            self.root.mainloop()

    def set_btn(self, command, btn_name='Button'):
        btn = tkinter.Button(self.frame, text=btn_name, command=command)
        btn['relief'] = tkinter.RAISED
        btn.pack(fill=tkinter.BOTH, anchor=tkinter.W, pady=5)

    def exit(self):
        try:
            if self.singleton:
                GraphViewer.is_exist = False
                GraphViewer.root.destroy()
            else:
                self.root.destroy()
        except Exception:
            pass


class ProfileViewer(GraphViewer):
    def __init__(self, parent, pos, profile):
        super().__init__(parent)
        if self.singleton:
            GraphViewer.root.title('ProfileViewer')
        else:
            self.root.title('ProfileViewer')
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(pos, profile)
        self.start()


class HistogramViewer(GraphViewer):
    def __init__(self, parent, hist_list, labels=('Blue', 'Green', 'Red'), singleton=False):
        super().__init__(parent, singleton)
        (GraphViewer.root if self.singleton else self.root).title('HistogramViewer')

        ax = self.fig.add_subplot(1, 1, 1)
        colors = ('b', 'g', 'r')
        linestyles = ('-', ':', '-')
        if len(hist_list) == 1:
            labels = ('value',)

        for i, h in enumerate(hist_list):
            maxv = float(max(h)) if len(h) > 0 else 0.0
            if maxv > 0:
                h = h / maxv
            ax.plot(h, color=colors[i if i < 3 else 0], label=labels[i if i < len(labels) else 0],
                    ls=linestyles[i if i < 3 else 0])
        ax.legend()
        self.start()




if __name__ == '__main__':
    pass
