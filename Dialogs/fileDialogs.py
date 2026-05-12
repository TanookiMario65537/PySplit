import os
from tkinter import filedialog
import tkinter as tk


def chooseRun(config):
    return filedialog.askopenfilename(
        initialdir=config["baseDir"],
        title="Choose a Split File",
        filetypes=(
            ("PySplit Files", "*.pysplit"),
        )
    )


def chooseSaveFile(config, default):
    baseDir = config["baseDir"]
    initialFile = default
    dsp = os.path.split(default)
    if dsp[0] and os.path.exists(os.path.join(baseDir, dsp[0])):
        baseDir = os.path.join(baseDir, dsp[0])
        initialFile = dsp[1]
    return filedialog.asksaveasfilename(
        initialdir=baseDir,
        title="Save As",
        filetypes=(
            ("PySplit Files", "*.pysplit"),
        ),
        defaultextension=".pysplit",
        initialfile=initialFile
    )


def resursionWarning():
    tk.messagebox.showwarning(
        title="Save Error",
        message="Cannot save as a file that is loaded in a subrun."
    )
