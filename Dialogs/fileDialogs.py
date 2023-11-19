import os
from tkinter import filedialog


def chooseRun(config):
    return filedialog.askopenfilename(
        initialdir=config["baseDir"],
        title="Choose a Split File",
        filetypes=(
            ("Pysplit Files", "*.pysplit"),
        ))


def addNewRun(config, default):
    baseDir = config["baseDir"]
    initialFile = default
    dsp = os.path.split(default)
    if dsp[0] and os.path.exists(os.path.join(baseDir, dsp[0])):
        baseDir = os.path.join(baseDir, dsp[0])
        initialFile = dsp[1]
    return filedialog.asksaveasfilename(
        initialdir=baseDir,
        title="Save New Splits",
        filetypes=(
            ("Pysplit Files", "*.pysplit"),
        ),
        defaultextension=".pysplit",
        initialfile=initialFile)
