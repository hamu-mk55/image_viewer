import cv2
import tkinter
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class Params1Ch:
    def __init__(self):
        self.mode = 'single'
        self.val = Param()


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
    def __init__(self, parent, color_mode='1ch'):
        self.root = tkinter.Toplevel(parent)
        self.root.title('Parameters')
        self.root.attributes('-topmost', True)
        self.root.geometry('200x300')
        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        # define style
        self.style_font = ("Arial", 15)
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_red = {'bg': '#0000ff', 'fg': '#ffffff'}

        # frame
        self.frame = None

        # results
        self.param = Params1Ch()

        # start
        self.set_frame()
        self.root.mainloop()

    def set_frame(self):
        # delete frames
        children = self.root.winfo_children()
        for child in children:
            child.destroy()

        # set frame
        self.frame = tkinter.Frame(self.root)
        self.frame.pack()

        self.set_entrys_1ch()

        pass

    def set_entrys_1ch(self,
                       label_width=10,
                       entry_width=5, entry_justify='right'):

        def _set_param(mode='lower'):
            ret = entry.get()
            entry.delete(0, tkinter.END)
            entry.insert(tkinter.END, 'ss')

        label = tkinter.Label(self.frame, text='value')
        label.grid(row=0, column=0)

        label = tkinter.Label(self.frame, text='lower', width=label_width)
        label.grid(row=1, column=0, padx=10)

        entry_lower = tkinter.Entry(self.frame,
                              width=entry_width,
                              justify=entry_justify)
        entry_lower.grid(row=1, column=1)

        label = tkinter.Label(self.frame, text='lower', width=label_width)
        label.grid(row=2, column=0, padx=10)

        entry_upper = tkinter.Entry(self.frame, width=entry_width,justify=entry_justify)
        entry_upper.grid(row=2, column=1)

    def __del__(self):
        self.exit()

    def exit(self):
        self.root.destroy()


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
            self.ax.plot(_hist, color=colors[_cnt], label=labels[_cnt], ls=linestyles[_cnt])

        self.ax.legend()
        self.start()


if __name__ == '__main__':
    pass
