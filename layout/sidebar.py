import customtkinter as ctk


class SideBar(ctk.CTkFrame):
    def __init__(self, master, start_pos, end_pos):
        super().__init__(master=master, corner_radius=None)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = abs(start_pos - end_pos)

        ### Positioning ###
        self.place(relx=self.start_pos, rely=0, relwidth=self.width, relheight=1)

        ### window Menu List ###
        ctk.CTkLabel(master=self, text="PANBA (V 1.2.5)").pack(fill="x", pady=(2, 15))
