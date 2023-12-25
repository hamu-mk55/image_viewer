import cv2
import tkinter
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class ParamWindow:
    # TODO: 二値化->膨張収縮->輪郭描画を実施。
    # TODO: 二値化および膨張収縮について、パラメータ変更が出来るようにする

    def __init__(self, parent):
        self.root = tkinter.Toplevel(parent)
        self.root.title('Parameters')
        self.root.attributes('-topmost', True)
        self.root.geometry('300x300')
        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        # フォントの設定
        self.style_font = ("Arial", 15)
        self.style_color = {'bg': '#ffffff', 'fg': '#000000'}
        self.style_color_red = {'bg': '#ff0000', 'fg': '#ffffff'}
        self.style_color_red = {'bg': '#0000ff', 'fg': '#ffffff'}

        # フレーム関係
        self.frame = None

        self.color_ch_list = ['blue', 'green', 'red', 'gray']
        self.color_ch = self.color_ch_list[0]
        self.msg_color = tkinter.StringVar()
        self.combobox = None

        self.msg_scale = tkinter.IntVar()
        self.scale = None

        self.set_frame()

    def set_frame(self):
        # delete frames
        children = self.root.winfo_children()
        for child in children:
            child.destroy()

        # set frame
        self.frame = tkinter.Frame(self.root)
        self.frame.pack()

        self.msg_color.set(self.color_ch)
        self.combobox = ttk.Combobox(self.frame,
                                     textvariable=self.msg_color,
                                     value=self.color_ch_list,
                                     state='readonly')
        self.combobox.pack(pady=10)

        self.scale = tkinter.Scale(self.frame,
                                   label=self.color_ch,
                                   orient=tkinter.HORIZONTAL,
                                   variable=self.msg_scale,
                                   from_=0,
                                   to=255)
        self.scale.pack()

        pass

    def __del__(self):
        self.exit()

    def start(self):
        self.root.mainloop()

    def command(self):
        pass

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
        if len(hist_list)==1:
            labels = ('value',)
        for _cnt, _hist in enumerate(hist_list):
            self.ax.plot(_hist, color=colors[_cnt], label=labels[_cnt], ls=linestyles[_cnt])

        self.ax.legend()
        self.start()


if __name__ == '__main__':
    pass
