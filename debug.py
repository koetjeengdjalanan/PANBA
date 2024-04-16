import customtkinter as ctk


class CustomLabelFrame(ctk.CTkFrame):
    def __init__(self, master=None, label="", **kwargs):
        super().__init__(master, **kwargs)
        self.label = label
        self.label_frame = ctk.CTkFrame(self)
        self.label_widget = ctk.CTkLabel(self.label_frame, text=self.label)
        self.label_widget.pack(side="top", fill="x", pady=5)
        self.label_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def add_widget(self, widget, **kwargs):
        widget.pack(**kwargs, padx=5, pady=5)
        widget.master = self.label_frame


# Example usage:
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("300x200")

    custom_frame = CustomLabelFrame(root, label="My LabelFrame")
    custom_frame.pack(fill="both", expand=True)

    button1 = ctk.CTkButton(custom_frame.label_frame, text="Button 1")
    button2 = ctk.CTkButton(custom_frame.label_frame, text="Button 2")

    custom_frame.add_widget(button1, side="left")
    custom_frame.add_widget(button2, side="right")

    root.mainloop()
