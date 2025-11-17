import tkinter as tk
from textwrap import fill


class Tooltip:
    """Tooltip hiển thị thông tin chi tiết khi hover chuột vào widget."""

    def __init__(self, widget, text, wrap_length=40, delay=400, bg="#ffffe0", fg="#000000"):
        """
        :param widget: Widget cần gán tooltip
        :param text: Nội dung tooltip
        :param wrap_length: Số ký tự tối đa mỗi dòng (tự xuống dòng)
        :param delay: Thời gian (ms) trễ trước khi hiển thị tooltip
        :param bg: Màu nền tooltip
        :param fg: Màu chữ tooltip
        """
        self.widget = widget
        self.text = text
        self.wrap_length = wrap_length
        self.delay = delay
        self.bg = bg
        self.fg = fg
        self.tooltip_window = None
        self.after_id = None
        self.hovering = False  # Theo dõi trạng thái hover thật sự

        # Bind sự kiện hover
        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.on_leave, add="+")

    def on_enter(self, event=None):
        """Khi chuột đi vào widget"""
        self.hovering = True
        # Nếu đang đợi tooltip cũ thì hủy
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        # Bắt đầu đếm delay
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event=None):
        """Khi chuột rời widget"""
        self.hovering = False
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self.hide_tooltip()

    def show_tooltip(self):
        """Tạo cửa sổ tooltip"""
        # Nếu không còn hover thì không hiển thị
        if not self.hovering or not self.text:
            return

        # Nếu đã có tooltip thì bỏ qua
        if self.tooltip_window:
            return

        # Lấy vị trí hiển thị
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Tạo cửa sổ nổi
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # không có viền
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        wrapped_text = fill(self.text, self.wrap_length)

        label = tk.Label(
            tw,
            text=wrapped_text,
            justify="left",
            background=self.bg,
            foreground=self.fg,
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=3,
        )
        label.pack(ipadx=1)

        # Giữ tooltip trong màn hình
        tw.update_idletasks()
        screen_width = tw.winfo_screenwidth()
        screen_height = tw.winfo_screenheight()
        tw_width = tw.winfo_reqwidth()
        tw_height = tw.winfo_reqheight()

        if x + tw_width > screen_width:
            x = screen_width - tw_width - 10
        if y + tw_height > screen_height:
            y = self.widget.winfo_rooty() - tw_height - 5
        tw.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        """Ẩn tooltip nếu chuột rời widget"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
