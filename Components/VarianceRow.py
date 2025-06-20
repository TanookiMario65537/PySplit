import tkinter as tk


class VarianceRow(tk.Frame):
    # number = None
    # name = None
    # variance = None
    def __init__(self, parent, row):
        super().__init__(parent)
        for i in range(12):
            self.columnconfigure(i, weight=1)
        self.number = tk.Label(self, text=f'{row[0]}:', fg="white", bg="black")
        self.name = tk.Label(self, text=row[1], fg="white", bg="black")
        self.variance = tk.Label(
            self,
            text=f'{row[2]:.2%}',
            fg="white",
            bg="black"
        )

        self.number.grid(row=0, column=0, columnspan=1, sticky='W')
        self.name.grid(row=0, column=1, columnspan=6)
        self.variance.grid(row=0, column=7, columnspan=5, sticky='E')

    def remove(self):
        self.number.grid_forget()
        self.number.destroy()
        self.name.grid_forget()
        self.name.destroy()
        self.variance.grid_forget()
        self.variance.destroy()
        self.grid_forget()
        self.destroy()
