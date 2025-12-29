import os
import tkinter
from PIL import Image, ImageTk
from typing import List, Optional, Tuple
from tkinter import ttk, messagebox, simpledialog, filedialog

import cv2

from opencv_func import ImageFunc
from image_info import ImageData, ImageInfo
from sub_window import ProfileViewer, HistogramViewer


class CanvasState:
    def __init__(self, scale=None, center_x=None, center_y=None, event_mode=None):
        self.scale: float = scale
        self.center_x: float = center_x
        self.center_y: float = center_y

        self.event_mode = event_mode


class CanvasStateSync:
    def __init__(self):
        self.canvases: List[Canvas] = []
        self._in_update = False

    def register_cvs(self, cvs):
        self.canvases.append(cvs)
        cvs.canvas_state_sync = self

    def apply_view_state_to_all_cvs(self, src_cvs):
        if self._in_update:
            return

        self._in_update = True

        try:
            state = src_cvs.get_view_state()
            for cvs in self.canvases:
                if cvs is src_cvs:
                    continue
                cvs.apply_view_state(state)
        finally:
            self._in_update = False

    def delete_overlay(self):
        for cvs in self.canvases:
            cvs.delete("overlay")
            cvs.x0 = 0
            cvs.y0 = 0
            cvs.x1 = 0
            cvs.y1 = 0

    def add_overlay(self, ix0, iy0, ix1, iy1):
        for cvs in self.canvases:
            cx0, cy0 = cvs.img_to_canvas(ix0, iy0)
            cx1, cy1 = cvs.img_to_canvas(ix1, iy1)

            cvs.rect_id = cvs.create_rectangle(cx0, cy0, cx1, cy1, outline="red", width=2, tags=("overlay",))
            cvs.x0 = cx0
            cvs.y0 = cy0
            cvs.x1 = cx1
            cvs.y1 = cy1


class Canvas(tkinter.Canvas):
    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)

        self.cvs_id = None
        self.cvs_w = None
        self.cvs_h = None

        self.img_data: Optional[ImageData] = None
        self.img_pil = None
        self.img_id = None

        self.cwd = os.getcwd()
        self.right_click_menu = tkinter.Menu(self, tearoff=0)

        # callback
        self.callback = None

        # event mode(pan or draw)
        self.event_mode = "rect"
        self.rect_id = None

        # Zoom
        self.scale = 1.0
        self.scale_ini = 1.0
        self.min_scale = 1.0
        self.max_scale = 5.0

        # Pan
        self.offset_x = 0
        self.offset_y = 0

        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0

        # EventBind
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Button-3>", self.right_click_function)

        self.bind("<MouseWheel>", self.on_mousewheel)

        self.bind("<ButtonPress-1>", self.on_mouse_press)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_release)

    def set_image_data(self, image_data: ImageData, scale=1.0):
        if image_data is None:
            return

        self.img_data = image_data
        self.cvs_w = image_data.win_w
        self.cvs_h = image_data.win_h

        self.scale_ini = scale
        self.scale = scale

        if self.img_data.img_org is not None:
            self.img_data.img_fit(scale=scale)

            self.update_idletasks()
            center_cx = max(1, self.winfo_width()) / 2
            center_cy = max(1, self.winfo_height()) / 2
            center_ix = self.img_data.img_w_org / 2
            center_iy = self.img_data.img_h_org / 2

            self.offset_x = center_cx - center_ix * self.img_data.fit_ratio
            self.offset_y = center_cy - center_iy * self.img_data.fit_ratio

        self._update_image()

    def set_event_mode(self, mode="pan"):
        self.event_mode = mode

    def set_callback(self, callback):
        self.callback = callback

    def _update_image(self, reset_flg=False):
        """scale と offset_x/y をもとに Canvas の画像を更新"""
        if self.img_data.img_org is None:
            return

        # Prepare TK-image
        self.img_pil = self.img_data.img_pil(scale=self.scale)
        self.tk_img = ImageTk.PhotoImage(self.img_pil)

        # Set Display
        if self.img_id is None or reset_flg:
            self.img_id = self.create_image(
                self.offset_x, self.offset_y,
                anchor="nw",
                image=self.tk_img
            )
        else:
            self.itemconfig(self.img_id, image=self.tk_img)
            self.coords(self.img_id, self.offset_x, self.offset_y)

    def check_offset(self):
        if self.img_data.img_org is None:
            return

        self.update_idletasks()
        cw = max(1, self.winfo_width())
        ch = max(1, self.winfo_height())

        iw, ih = self.img_data.img_pil().size

        if iw >= cw:
            min_x = cw - iw
            max_x = 0
            self.offset_x = max(min_x, min(max_x, self.offset_x))
        else:
            self.offset_x = (cw - iw) / 2

        if ih >= ch:
            min_y = ch - ih
            max_y = 0
            self.offset_y = max(min_y, min(max_y, self.offset_y))
        else:
            self.offset_y = (ch - ih) / 2

    # Right Click-----------------------------------------------------------
    def set_right_click_menu(self):
        self.right_click_menu.delete(0, "end")

        def _change_mode(mode):
            self.event_mode = mode
            self.x0 = 0
            self.y0 = 0
            self.x1 = 0
            self.y1 = 0
            if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
                self.canvas_state_sync.apply_view_state_to_all_cvs(self)
                self.canvas_state_sync.delete_overlay()

        if self.event_mode.lower() == "pan":
            self.right_click_menu.add_command(label="pan", state="disable")
            self.right_click_menu.add_command(label="rect", command=lambda: _change_mode("rect"))
        elif self.event_mode.lower() == "rect":
            self.right_click_menu.add_command(label="pan", command=lambda: _change_mode("pan"))
            self.right_click_menu.add_command(label="rect", state="disable")

        self.right_click_menu.add_separator()
        if self.event_mode == "rect":
            _state = "active"
        else:
            _state = "disable"

        self.right_click_menu.add_command(label="profile(hor)", command=lambda: self.show_profile("hor"), state=_state)
        self.right_click_menu.add_command(label="profile(ver)", command=lambda: self.show_profile("ver"), state=_state)
        self.right_click_menu.add_command(label="histogram(rgb)", command=lambda: self.show_histgram(), state=_state)
        # self.right_click_menu.add_command(label="histogram(hsv)", command=None)

        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="save image", command=self.save_image)
        self.right_click_menu.add_command(label="show info", command=self.show_info)
        self.right_click_menu.add_command(label="reset view", command=self.reset_view)

    def right_click_function(self, event):
        self.set_right_click_menu()

        self.right_click_menu.tk_popup(event.x_root, event.y_root)
        self.right_click_menu.grab_release()

    # Mouse Events-----------------------------------------------------------

    def on_mousewheel(self, event):
        if self.img_data.img_org is None:
            return

        if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
            self.canvas_state_sync.delete_overlay()

        cx = self.canvasx(event.x)
        cy = self.canvasy(event.y)
        old_scale = self.scale

        # for Windows
        if hasattr(event, "delta") and event.delta != 0:
            zoom = 1.1 if event.delta > 0 else 0.9
        else:
            return

        new_scale = self.scale * zoom
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        zoom = new_scale / old_scale
        if zoom == 1.0:
            return

        img_x = (cx - self.offset_x) / old_scale
        img_y = (cy - self.offset_y) / old_scale

        self.scale = new_scale

        self.offset_x = cx - img_x * self.scale
        self.offset_y = cy - img_y * self.scale

        self._update_image()
        self.check_offset()
        self._update_image()

        if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
            self.canvas_state_sync.apply_view_state_to_all_cvs(self)

    def on_mouse_press(self, event):

        if self.event_mode == "pan":
            self.x0 = event.x
            self.y0 = event.y

        elif self.event_mode == "rect":
            if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
                self.canvas_state_sync.delete_overlay()

            self.x0 = self.canvasx(event.x)
            self.y0 = self.canvasy(event.y)
            self.x1 = self.x0
            self.y1 = self.y0

            self.rect_id = self.create_rectangle(0, 0, 0, 0, outline="red", width=2, tags=("overlay",))
            self.coords(self.rect_id, self.x0, self.y0, self.x0, self.y0)

    def on_mouse_drag(self, event):

        if self.event_mode == "pan":
            dx = event.x - self.x0
            dy = event.y - self.y0

            self.offset_x += dx
            self.offset_y += dy

            self.x0 = event.x
            self.y0 = event.y

            self.check_offset()
            self._update_image()

            if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
                self.canvas_state_sync.apply_view_state_to_all_cvs(self)
        else:
            self.x1 = self.canvasx(event.x)
            self.y1 = self.canvasy(event.y)

            self.coords(self.rect_id, int(self.x0), int(self.y0), self.x1, self.y1)

    def on_mouse_release(self, event):
        if self.event_mode == "rect":
            self.x1 = self.canvasx(event.x)
            self.y1 = self.canvasy(event.y)

            ix0, iy0 = self.canvas_to_img(self.x0, self.y0)
            ix1, iy1 = self.canvas_to_img(self.x1, self.y1)

            if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
                self.canvas_state_sync.add_overlay(ix0, iy0, ix1, iy1)

    def on_mouse_move(self, event):
        if not self.callback:
            return

        info = ImageInfo()

        img = self.img_data.img_org
        cx = self.canvasx(event.x)
        cy = self.canvasy(event.y)
        x, y = self.canvas_to_img(cx, cy)
        info.calc_vals(img, x, y)

        ix0, iy0 = self.canvas_to_img(self.x0, self.y0)
        ix1, iy1 = self.canvas_to_img(self.x1, self.y1)

        if self.event_mode == 'rect':
            info.calc_rect_vals(x0=ix0, x1=ix1, y0=iy0, y1=iy1)

        self.callback("move", info)

    # Helper-----------------------------------------------------------------------------------------
    def show_profile(self, direction="hor"):
        if self.x0 == 0 or self.y0 == 0 or self.x1 == 0 or self.y1 == 0:
            return

        ix0, iy0 = self.canvas_to_img(self.x0, self.y0)
        ix1, iy1 = self.canvas_to_img(self.x1, self.y1)

        pos, profs = ImageFunc.check_profile(self.img_data.img_org, x0=ix0, y0=iy0, x1=ix1, y1=iy1,
                                             direction=direction)
        ProfileViewer(self, pos, profs)

    def show_histgram(self):
        if self.x0 == 0 or self.y0 == 0 or self.x1 == 0 or self.y1 == 0:
            return

        ix0, iy0 = self.canvas_to_img(self.x0, self.y0)
        ix1, iy1 = self.canvas_to_img(self.x1, self.y1)

        labels = ('Blue', 'Green', 'Red')
        hists = ImageFunc.check_histgram(self.img_data.img_org, x0=int(ix0), x1=int(ix1), y0=int(iy0), y1=int(iy1))

        HistogramViewer(self, hists, labels=labels)

    def save_image(self):
        img_path = filedialog.asksaveasfilename(initialdir=self.cwd)
        if not img_path:
            return
        cv2.imwrite(img_path, self.img_data.img_org)

    def show_info(self):
        path = self.img_data.img_path

        messagebox.showinfo('info',
                            f'path: {path}\n'
                            f'dir: {os.path.dirname(path)}\n'
                            f'file: {os.path.basename(path)}\n'
                            f'img_h: {self.img_data.img_h_org}\n'
                            f'img_w: {self.img_data.img_w_org}\n')

    def reset_view(self):
        self.scale = self.scale_ini
        self.img_data.img_fit(scale=self.scale)

        try:
            self.xview_moveto(0)
            self.yview_moveto(0)
        except Exception:
            pass

        self.update_idletasks()
        center_cx = max(1, self.winfo_width()) / 2
        center_cy = max(1, self.winfo_height()) / 2

        center_ix = self.img_data.img_w_org / 2
        center_iy = self.img_data.img_h_org / 2

        self.offset_x = center_cx - center_ix * self.img_data.fit_ratio
        self.offset_y = center_cy - center_iy * self.img_data.fit_ratio

        self._update_image()

        if hasattr(self, "canvas_state_sync") and self.canvas_state_sync:
            self.canvas_state_sync.delete_overlay()
            self.canvas_state_sync.apply_view_state_to_all_cvs(self)

    # Sync ViewState---------------------------------------------------------------------------------
    def get_view_state(self):
        if self.img_data.img_org is None:
            return CanvasState(self.scale, 0.0, 0.0)

        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())

        cx = self.canvasx(w / 2)
        cy = self.canvasy(h / 2)

        center_img_x = (cx - self.offset_x) / self.scale
        center_img_y = (cy - self.offset_y) / self.scale

        return CanvasState(scale=self.scale,
                           center_x=center_img_x,
                           center_y=center_img_y,
                           event_mode=self.event_mode)

    def apply_view_state(self, state: CanvasState):
        if self.img_data.img_org is None:
            return

        self.scale = max(self.min_scale, min(self.max_scale, state.scale))
        self.event_mode = state.event_mode

        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())

        # canvas_center = img * scale + offset  => offset = canvas_center - img*scale
        canvas_center_x = self.canvasx(w / 2)
        canvas_center_y = self.canvasy(h / 2)

        self.offset_x = canvas_center_x - state.center_x * self.scale
        self.offset_y = canvas_center_y - state.center_y * self.scale

        self._update_image()
        self.check_offset()
        self._update_image()

    def canvas_to_img(self, cx, cy):
        ix = (cx - self.offset_x) / self.img_data.fit_ratio
        iy = (cy - self.offset_y) / self.img_data.fit_ratio
        return ix, iy

    def img_to_canvas(self, ix, iy):
        cx = ix * self.img_data.fit_ratio + self.offset_x
        cy = iy * self.img_data.fit_ratio + self.offset_y
        return cx, cy
