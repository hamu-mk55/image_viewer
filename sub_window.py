import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


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
