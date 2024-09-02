import tkinter as tk
from util import timeHelpers as timeh
from Widgets import WidgetBase

class Widget(WidgetBase.WidgetBase):
    # game = None
    # category = None
    # sessions = None
    # completion = None

    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        # bg = config["colours"]["bg"]
        # font = config["font"]
        # textColour = config["colours"]["text"]

        # self.configure(bg=bg)
        # self.game = tk.Label(self, bg=bg, font=font, fg=textColour)
        # self.category = tk.Label(self, bg=bg, font=font, fg=textColour)
        # self.sessions = tk.Label(self, bg=bg, font=font, fg=textColour)
        # self.completion = tk.Label(self, bg=bg, font=font, fg=textColour)

        # self.game.grid(row=0,column=0,columnspan=12,sticky='WE')
        # self.category.grid(row=1,column=0,columnspan=12,sticky='WE')
        # self.completion.grid(row=1,column=10,columnspan=2,sticky='E',ipadx=10)
        # self.sessions.grid(row=0,column=10,columnspan=2,sticky='E',ipadx=10)

        # self.resetUI()

        # self.points = [(-10, -5), (-5, -2), (0, 0), (5, 3), (10, 7)]
        self.points = []
        self.configure(height=config["height"])
        self.canvas = tk.Canvas(self, bg="green", height=config["height"])
        self.canvas.pack(fill=tk.X, expand=True)
        self.bind("<Configure>", self.doResize)
        self.isResizing = False
        self.after(100, self.drawGraph)

    def doResize(self):
        if not self.isResizing:
            self.isResizing = True
            self.drawGraph()
            self.isResizing = False

    def generatePoints(self):
        comparisons = [i for i, diff in
                       enumerate(self.state.currentComparison.diffs.totals) if
                       not timeh.isBlank(diff)]
        self.points = ([] if not len(comparisons) else [(0, 0)]) + [
            (self.state.currentRun.totals[index], self.state.currentComparison.diffs.totals[index])
            for index in comparisons
        ]

    def initGraph(self):
        self.canvas.create_rectangle(0, 0, self.width, 0.5 * self.height, fill='red')
        self.canvas.create_rectangle(0, 0.5 * self.height, self.width, self.height, fill='green')
        self.canvas.create_line(0, 0.5 * self.height, self.width, 0.5 * self.height, fill='white', width=2)

    def drawGraph(self):
        # Clear the canvas before redrawing
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.canvas.delete("all")
        self.generatePoints()

        if not self.points:
            self.initGraph()
            return

        x_values = [x for x, y in self.points]
        y_values = [y for x, y in self.points]

        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        if min_x == max_x:
            min_x, max_x = min_x - 1, max_x + 1
        if min_y == max_y:
            min_y, max_y = min_y - 1, max_y + 1

        x_scale = self.width / (max_x - min_x)
        y_scale = self.height / (max_y - min_y)

        if max_y > 0:
            self.canvas.create_rectangle(0, 0, self.width, (max_y / (max_y - min_y)) * self.height, fill='red')
        if min_y < 0:
            self.canvas.create_rectangle(0, (max_y / (max_y - min_y)) * self.height, self.width, self.height, fill='green')

        x_axis_y = (max_y / (max_y - min_y)) * self.height
        self.canvas.create_line(0, x_axis_y, self.width, x_axis_y, fill='white', width=2)

        scaled_points = [
            (
                (x - min_x) * x_scale,
                self.height - (y - min_y) * y_scale
            ) for x, y in self.points
        ]
        self.canvas.create_line(scaled_points, fill="black", width=2)

    # def resetUI(self):
    #     self.drawGraph()

    # def onSplit(self):
    #     self.drawGraph()

    # def onReset(self):
    #     self.drawGraph()
