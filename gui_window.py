import cv2
import tkinter
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class ParamsForSingleChannel:
    def __init__(self):
        self.mode = 'single'
        self.val = Param()
        self.val.set_params(lower=125,
                            upper=255,
                            inverse=False)

    def get_result_dict(self):
        res = {"mode": self.mode,
               "value_inverse": self.val.inverse,
               "value_lower": self.val.lower,
               "value_upper": self.val.upper,
               }
        return res


class Param:
    def __init__(self):
        self.lower = None
        self.upper = None
        self.inverse = False

    def set_params(self, lower, upper, inverse):
        self.lower = lower
        self.upper = upper
        self.inverse = inverse


class ParamWindow:
    is_exist = False
    root = None

    def __init__(self, parent):
        if ParamWindow.is_exist:
            self.start()
            return

        print('params..............')
        ParamWindow.root = tkinter.Toplevel(parent)
        ParamWindow.root.title('Params')
        ParamWindow.root.attributes('-topmost', False)
        ParamWindow.root.geometry('200x300')
        ParamWindow.root.protocol('WM_DELETE_WINDOW', self.exit)
        ParamWindow.is_exist = True

        # define style
        self.style_font = ("Arial", 15)
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_red = {'bg': '#0000ff', 'fg': '#ffffff'}

        # btn
        self.btn_set = None
        self.btn_unset = None

        # res
        self.proc_flg = False
        self.params_dict = {}

        # frame
        self.frame = None
        self.set_frame()

    def set_frame(self):
        # delete frames
        children = ParamWindow.root.winfo_children()
        for child in children:
            child.destroy()

        # set frame
        self.frame = tkinter.Frame(ParamWindow.root)
        self.frame.pack()

        self.frame_btn = tkinter.Frame(ParamWindow.root)
        self.frame_btn.pack(pady=20)
        self.set_btn()

    def set_btn(self):
        def _call_set():
            self.proc_flg=True
        def _call_unset():
            self.proc_flg=False

        self.btn_set = tkinter.Button(self.frame_btn,
                                      text='Set',
                                      width=8,
                                      command=_call_set)
        self.btn_set['relief'] = tkinter.RAISED
        self.btn_set.grid(row=0, column=0, sticky=tkinter.W)

        self.btn_unset = tkinter.Button(self.frame_btn,
                                        text='Unset',
                                        width=8,
                                        command=_call_unset)
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
        except:
            pass


class ParamWindowForSingleChannel(ParamWindow):
    def __init__(self, parent):
        super().__init__(parent)

        ParamWindow.root.geometry('200x200')
        self.param = ParamsForSingleChannel()
        self.params_dict = self.param.get_result_dict()

        # parts
        self.check_inv = None
        self.entry_lower = None
        self.entry_upper = None

        self.set_entrys()

    def set_entrys(self, label_width=10,
                   entry_width=5, entry_justify='right'):

        def _call_inv():
            _exec_param(mode='inv')

        def _call_lower(event):
            _exec_param(mode='lower')

        def _call_upper(event):
            _exec_param(mode='upper')

        def _exec_param(mode):
            # get
            _inv = is_inverse.get()
            _upper = self.entry_upper.get()
            _lower = self.entry_lower.get()

            try:
                _upper = int(_upper)
            except:
                _upper = self.param.val.upper
            try:
                _lower = int(_lower)
            except:
                _lower = self.param.val.lower

            if mode == 'lower' and _upper <= _lower:
                _upper = _lower + 1
            elif mode == 'upper' and _lower >= _upper:
                _lower = _upper - 1

            self.param.val.set_params(_lower, _upper, _inv)

            # set
            is_inverse.set(self.param.val.inverse)
            self.entry_lower.delete(0, tkinter.END)
            self.entry_lower.insert(tkinter.END, f'{self.param.val.lower}')
            self.entry_upper.delete(0, tkinter.END)
            self.entry_upper.insert(tkinter.END, f'{self.param.val.upper}')

            self.params_dict = self.param.get_result_dict()

        # Label
        label = tkinter.Label(self.frame, text='Value')
        label.grid(row=0, column=0, sticky=tkinter.W)

        # CheckBOX
        is_inverse = tkinter.BooleanVar()
        is_inverse.set(self.param.val.inverse)
        self.check_inv = tkinter.Checkbutton(self.frame,
                                             text='inverse',
                                             variable=is_inverse,
                                             command=_call_inv)
        self.check_inv.grid(row=1, column=0, padx=20, sticky=tkinter.W)

        # Entry: lower
        label = tkinter.Label(self.frame, text='lower', width=label_width)
        label.grid(row=2, column=0, sticky=tkinter.W)

        self.entry_lower = tkinter.Entry(self.frame,
                                         width=entry_width,
                                         justify=entry_justify)
        self.entry_lower.grid(row=2, column=1)
        self.entry_lower.delete(0, tkinter.END)
        self.entry_lower.insert(tkinter.END, f'{self.param.val.lower}')
        self.entry_lower.bind('<Return>', _call_lower)

        # Entry: upper
        label = tkinter.Label(self.frame, text='upper', width=label_width)
        label.grid(row=3, column=0, sticky=tkinter.W)

        self.entry_upper = tkinter.Entry(self.frame, width=entry_width, justify=entry_justify)
        self.entry_upper.grid(row=3, column=1)
        self.entry_upper.delete(0, tkinter.END)
        self.entry_upper.insert(tkinter.END, f'{self.param.val.upper}')
        self.entry_upper.bind('<Return>', _call_upper)


class GraphViewer:
    """
    matplotlibのグラフを表示する基底クラス。主用途はシングルトン。
    使用する際は、
    ①self.figの中に、axを追加してグラフ表示する。
    ②self.startでGUI表示。
    ③ボタンが必要な場合は、self.set_btnを使用する。
    """
    is_exist = False
    root = None

    @classmethod
    def delete(cls):
        try:
            GraphViewer.is_exist = False
            GraphViewer.root.destroy()
        except Exception as err:
            pass

    def __init__(self, parent, singleton=True):
        self.singleton = singleton

        if singleton and not GraphViewer.is_exist:
            GraphViewer.root = tkinter.Toplevel(parent)
            GraphViewer.root.title('Viewer')
            GraphViewer.root.attributes('-topmost', True)
            GraphViewer.root.protocol('WM_DELETE_WINDOW', self.exit)
            GraphViewer.is_exist = True

        elif singleton:
            children = GraphViewer.root.winfo_children()
            for child in children:
                child.destroy()

        else:
            self.root = tkinter.Toplevel(parent)
            self.root.title('Viewer')
            self.root.attributes('-topmost', True)
            self.root.protocol('WM_DELETE_WINDOW', self.exit)

        if singleton:
            self.frame = tkinter.Frame(GraphViewer.root)
        else:
            self.frame = tkinter.Frame(self.root)

        self.fig = Figure()
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame)
        self.canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)

        self.frame.pack()

    def __del__(self):
        self.exit()

    def start(self):
        self.canvas.draw()

        if self.singleton:
            GraphViewer.root.mainloop()
        else:
            self.root.mainloop()

    def set_btn(self, command, btn_name='Button'):
        btn = tkinter.Button(self.frame,
                             text=btn_name,
                             command=command)
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
    """
    プロファイル表示クラス
    メインウインドウとは別ウインドウとして開く
    """

    def __init__(self,
                 parent,
                 pos,
                 profile):
        super().__init__(parent)
        ProfileViewer.root.title('ProfileViewer')

        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.plot(pos, profile)

        self.start()


class HistogramViewer(GraphViewer):
    """
    ヒストグラム表示クラス
    メインウインドウとは別ウインドウとして開く
    """

    def __init__(self,
                 parent,
                 hist_list,
                 labels=('Blue', 'Green', 'Red'),
                 singleton=False):
        super().__init__(parent, singleton)
        if singleton:
            HistogramViewer.root.title('HistogramViewer')
        else:
            self.root.title('HistogramViewer')

        self.ax = self.fig.add_subplot(1, 1, 1)

        colors = ('b', 'g', 'r')
        linestyles = ('-', ':', '-')
        if len(hist_list) == 1:
            labels = ('value',)
        for _cnt, _hist in enumerate(hist_list):
            _max = max(_hist)
            _hist = _hist / _max

            self.ax.plot(_hist, color=colors[_cnt], label=labels[_cnt], ls=linestyles[_cnt])

        self.ax.legend()
        self.start()


if __name__ == '__main__':
    pass
