import tkinter as tk
from util import timeHelpers as timeh
from Widgets import WidgetBase


class Widget(WidgetBase.WidgetBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.generatePoints()
        self.configure(height=config["height"])
        self.canvas = tk.Canvas(
            self,
            bg=self.config["colours"]["ahead"],
            height=config["height"])
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
        comparisons = [
            i for i, diff
            in enumerate(self.state.currentComparison.diffs.totals)
            if not timeh.isBlank(diff)]
        self.points = ([] if not len(comparisons) else [(0, 0)]) + [
            (
                self.state.currentRun.totals[index],
                self.state.currentComparison.diffs.totals[index]
            )
            for index in comparisons
        ]

    def initGraph(self):
        self.canvas.create_rectangle(
            0, 0,
            self.width, 0.5 * self.height,
            fill=self.config["colours"]["behind"])
        self.canvas.create_rectangle(
            0, 0.5 * self.height,
            self.width, self.height,
            fill=self.config["colours"]["ahead"])
        self.canvas.create_line(
            0, 0.5 * self.height,
            self.width, 0.5 * self.height,
            fill=self.config["colours"]["axis"],
            width=2)

    def drawGraph(self):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.canvas.delete("all")
        self.generatePoints()

        if not self.points:
            self.initGraph()
            return

        xValues = [x for x, y in self.points]
        yValues = [y for x, y in self.points]

        minX, maxX = min(xValues), max(xValues)
        minY, maxY = min(yValues), max(yValues)

        if minX == maxX:
            minX, maxX = minX - 1, maxX + 1
        if minY == maxY:
            minY, maxY = minY - 1, maxY + 1

        yRange = maxY - minY
        yAvg = (maxY + minY)/2
        minY = yAvg - yRange/2*1.1
        maxY = yAvg + yRange/2*1.1

        if minY < 0:
            minY *= 1 + self.config["bufferPercent"]*0.01
        if maxY > 0:
            maxY *= 1 + self.config["bufferPercent"]*0.01

        xScale = self.width / (maxX - minX)
        yScale = self.height / (maxY - minY)

        if maxY > 0:
            self.canvas.create_rectangle(
                0, 0,
                self.width, (maxY / (maxY - minY)) * self.height,
                fill=self.config["colours"]["behind"])
        if minY < 0:
            self.canvas.create_rectangle(
                0, (maxY / (maxY - minY)) * self.height,
                self.width, self.height,
                fill=self.config["colours"]["ahead"])

        xAxisY = (maxY / (maxY - minY)) * self.height
        self.canvas.create_line(
            0, xAxisY,
            self.width, xAxisY,
            fill=self.config["colours"]["axis"],
            width=2)

        scaledPoints = [
            (
                (x - minX) * xScale,
                self.height - (y - minY) * yScale
            ) for x, y in self.points
        ]
        self.canvas.create_line(
            scaledPoints,
            fill=self.config["colours"]["line"],
            width=2)

    def resetUI(self):
        self.drawGraph()

    def onSplit(self):
        self.drawGraph()

    def onComparisonChanged(self):
        self.drawGraph()

    def onRestart(self):
        self.drawGraph()
