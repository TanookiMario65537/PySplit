import tkinter as tk
from tkinter import font
from Components import ValidationEntry as VE
from Components import Notifier
from Dialogs import fileDialogs
from util import readConfig as rc


class LeftFrame(tk.Frame, Notifier.Notifier):
    cellWidth = 10

    def __init__(self, parent, parentObj):
        tk.Frame.__init__(self, parent)
        Notifier.Notifier.__init__(self)
        self.userConfig = rc.getUserConfig()
        self.grid = parentObj
        self.grid.saveData.addListener(self, self.saveDataUpdated)
        self.bind("<Destroy>", self.unregisterListener)
        self.currentSplit = -1
        self._children = {
            "labels": [],
            "names": [],
            "staticNames": [],
            "fileButtons": [],
            "collapseButtons": [],
        }
        self.connectedNames = {}
        self.rowLayout = []
        self.saveDataUpdated({"type": "init"})

    def unregisterListener(self, event):
        if event.widget is self:
            self.grid.saveData.removeListener(self)
            for entry in self.connectedNames.keys():
                entry.removeListener(self)

    def saveDataUpdated(self, changeData):
        if (
            changeData["type"]
            in ["init", "splitAdded", "splitRemoved", "subrunChanged"]
        ):
            self.updateRowLayout()
            for i, rowInfo in enumerate(self.rowLayout):
                if rowInfo[0] == "staticName":
                    self._children["staticNames"][rowInfo[1]].config(
                        text=self.grid.saveData.splitNames[rowInfo[2]]
                    )

        if changeData["type"] == "splitAdded":
            self.updateCurrentSplit(changeData["data"], False)

        if changeData["type"] == "splitRemoved":
            if changeData["data"] >= len(self._children["labels"]):
                self.updateCurrentSplit(-1, False)

        if changeData["type"] == "collapsedChanged":
            (
                self._children["collapseButtons"][changeData["data"]["index"]]
            ).setIcon(
                "collapse" if changeData["data"]["collapsed"] else "expand"
            )

        for i, name in enumerate(self._children["names"]):
            name.setText(self.grid.saveData.data["splitNames"][i], True)

    def computeRowLayout(self):
        """
        The grid has two types of rows - "name" and "staticName". "name" is an
        editable name with a text field, and "staticName" is just a label,
        showing the name of a split loaded from a subrun.

        Each "name" comes with the index of the text field in the list of
        components. This also happens to be the index of the splitName it
        refers to (relative to the SAVE FILE).

        Each "staticName" comes with the index of the label in the components
        list, and the index of the label in the splits (relative to the LIST OF
        LOADED SPLITS). These may not (and likely won't) match because it may
        be the case that not all splits are part of a subrun, so we need to
        keep track of both in the row layout.
        """
        newRowLayout = []
        lastSubrun = None
        currentSubrun = None
        nameCount = 0
        labelCount = 0
        for i, split in enumerate(self.grid.saveData.splits):
            currentSubrun = (
                split.subrunPath[0]
                if split.subrunPath
                else None
            )
            if currentSubrun is None:
                newRowLayout.append(("name", nameCount))
                nameCount += 1
            elif lastSubrun == currentSubrun:
                newRowLayout.append(("staticName", labelCount, i))
                labelCount += 1
            else:
                newRowLayout.append(("name", nameCount))
                newRowLayout.append(("staticName", labelCount, i))
                nameCount += 1
                labelCount += 1
            lastSubrun = currentSubrun
        return newRowLayout, nameCount, labelCount

    def updateRowLayout(self):
        newRowLayout, nameCount, labelCount = self.computeRowLayout()

        """
        For any rows in the new layout that also existed in the old layout,
        make sure that the correct rows are in the correct places. Do nothing
        for empty rows, as the only thing they need is to ensure the row height
        is correct - they don't actually have a frame.
        """
        for i in range(min(len(newRowLayout), len(self.rowLayout))):
            """
            Check for changes to any row. "name" rows have 2 elements and
            "staticName" rows have 3, but checking row[-1] will catch the
            differences in element 3 for "staticName" and just duplicate the
            second check for "name" rows (basically it's just me being lazy).
            If the lengths are not equal, it will also be the case that row[0]
            is different, so we don't need to check it explicitly.
            """
            if (
                (newRowLayout[i][0] != self.rowLayout[i][0])
                or (newRowLayout[i][1] != self.rowLayout[i][1])
                or (newRowLayout[i][-1] != self.rowLayout[i][-1])
            ):
                if (
                    newRowLayout[i][1]
                    >= len(self._children[f"{newRowLayout[i][0]}s"])
                ):
                    """
                    If there are not enough rows of this type, make a new one.
                    """
                    self.addRow(i, newRowLayout[i])
                else:
                    """
                    If the row we expect here exists, but is not in the right
                    place, move it to be in the right place.
                    """
                    self.moveRow(i, newRowLayout[i])

        """
        Make sure that every row we need in the new row layout has been
        created.
        """
        i = len(self.rowLayout)
        while i < len(newRowLayout):
            if (
                newRowLayout[i][1]
                >= len(self._children[f"{newRowLayout[i][0]}s"])
            ):
                self.addRow(i, newRowLayout[i])
            else:
                """
                If the row we expect here exists, but is not in the right
                place, move it to be in the right place.
                """
                self.moveRow(i, newRowLayout[i])
            i += 1

        """
        Remove any rows that aren't necessary. Do this for both lists.
        """
        i = len(self._children["staticNames"]) - 1
        while i >= labelCount:
            self.removeRow("staticName")
            i -= 1

        i = len(self._children["names"]) - 1
        while i >= nameCount:
            self.removeRow("name")
            i -= 1

        self.adjustRowHeights(len(self.rowLayout), len(newRowLayout))
        self.rowLayout = newRowLayout

    def adjustRowHeights(self, oldSize, newSize):
        for i in range(newSize):
            if self.rowconfigure(i)["minsize"] != 25:
                self.rowconfigure(i, weight=1, minsize=25)
        for i in range(newSize, max(newSize, oldSize)):
            if self.rowconfigure(i)["minsize"] != 0:
                self.rowconfigure(i, weight=1, minsize=0)

    def addRow(self, rowIndex, rowInfo):
        if rowInfo[0] == "name":
            label = tk.Label(self, text=len(self._children["labels"])+1)
            label.bind("<Button-1>", self.labelClicked)
            label.grid(row=rowIndex, column=0, sticky="NSWE")
            self._children["labels"].append(label)

            name = VE.Entry(
                self,
                self.grid.saveData.data["splitNames"][rowInfo[1]],
                {"validate": self.validate},
                width=self.cellWidth
            )
            name.grid(row=rowIndex, column=1, sticky="NSEW")
            name.addListener(self, self.entryChanged)
            self.connectedNames[name] = {"index": len(self._children["names"])}
            self._children["names"].append(name)

            x = len(self._children["fileButtons"])
            button = CircularIconButton(
                self,
                "file",
                onClicked=lambda: self.fileButtonClicked(x)
            )
            button.grid(row=rowIndex, column=2, sticky="NSWE")
            self._children["fileButtons"].append(button)

            x = len(self._children["collapseButtons"])
            button = CircularIconButton(
                self,
                "collapse"
                if self.grid.saveData.subrunCollapsed(rowInfo[1])
                else "expand",
                onClicked=lambda: self.collapseClicked(x)
            )
            button.grid(row=rowIndex, column=3, sticky="NSWE")
            self._children["collapseButtons"].append(button)
        else:
            staticName = EllipsisLabel(
                self,
                text=self.grid.saveData.splits[rowInfo[2]].name,
                justify="left",
                anchor="w"
            )
            staticName.grid(
                row=rowIndex,
                column=1,
                columnspan=3,
                sticky="NSWE"
            )
            self._children["staticNames"].append(staticName)

    def moveRow(self, rowIndex, rowInfo):
        if rowInfo[0] == "name":
            self.moveItem(
                self._children["labels"][rowInfo[1]],
                row=rowIndex,
                column=0
            )
            self.moveItem(
                self._children["names"][rowInfo[1]],
                row=rowIndex,
                column=1
            )
            self.moveItem(
                self._children["fileButtons"][rowInfo[1]],
                row=rowIndex,
                column=2
            )
            self.moveItem(
                self._children["collapseButtons"][rowInfo[1]],
                row=rowIndex,
                column=3
            )
        elif rowInfo[0] == "staticName":
            self.moveItem(
                self._children["staticNames"][rowInfo[1]],
                row=rowIndex,
                column=1
            )

    def moveItem(self, item, **kwargs):
        item.grid_forget()
        item.grid(
            **kwargs,
            sticky="nswe"
        )

    def removeRow(self, rowType, rowIndex=-1):
        if rowType == "name":
            self._children["names"][rowIndex].grid_forget()
            self._children["labels"][rowIndex].grid_forget()
            self._children["fileButtons"][rowIndex].grid_forget()
            self._children["collapseButtons"][rowIndex].grid_forget()
            del self.connectedNames[self._children["names"][rowIndex]]
            del self._children["names"][rowIndex]
            del self._children["labels"][rowIndex]
            del self._children["fileButtons"][rowIndex]
            del self._children["collapseButtons"][rowIndex]
        elif rowType == "staticName":
            self._children["staticNames"][rowIndex].grid_forget()
            del self._children["staticNames"][rowIndex]

    def entryChanged(self, changeData):
        """
        validChanged is emitted immediately when VE.Entry is created. In this
        specific instance, the object isn't in self.connectedNames yet, but we
        still want the "validChanged" signal to trickle up to the top level so
        it can check whether the save button should be enabled or not at
        initialization.
        """
        try:
            index = self.connectedNames[changeData["sender"]]["index"]
        except KeyError:
            index = -1
        if changeData["type"] == "textChanged":
            if (
                changeData["data"]
                == self.grid.saveData.data["splitNames"][index]
            ):
                return
            self.grid.saveData.updateSplitName(
                index,
                changeData["data"]
            )
        elif changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "valid": changeData["data"],
                    "index": index
                }
            })

    def fileButtonClicked(self, changeData):
        splitFile = fileDialogs.chooseRun(self.userConfig)
        if not splitFile:
            return
        if self.grid.saveData.containsSelfReferenceFile(splitFile):
            fileDialogs.resursionWarning()
            return
        self.grid.saveData.updateSubrun(
            changeData,
            splitFile
        )

    def collapseClicked(self, changeData):
        self.grid.saveData.updateCollapseState(
            changeData,
            not self.grid.saveData.splitNameCollapsed(changeData)
        )

    def labelClicked(self, event):
        self.updateCurrentSplit(self._children["labels"].index(event.widget))

    def validate(self, val):
        selfReference = self.grid.saveData.containsSelfReferenceName(val)
        return len(val) > 0 and not selfReference

    def updateCurrentSplit(self, new, allowRemoval=True):
        if new == self.currentSplit and allowRemoval:
            new = -1
        for i in range(len(self._children["labels"])):
            if i == new:
                self._children["labels"][i]["bg"] = "blue"
                self._children["labels"][i]["fg"] = "white"
            elif i == self.currentSplit:
                self._children["labels"][i]["bg"] = "#d0d0d0"
                self._children["labels"][i]["fg"] = "black"
        self.currentSplit = new

    def errorList(self):
        errors = []
        for i, entry in enumerate(self._children["names"]):
            if not entry.isValid:
                errors.append({"type": "name", "index": i})
        return errors


class CircularIconButton(tk.Canvas):
    def __init__(
        self,
        parent,
        icon,
        onClicked=None,
        diameter=24,
        bg="#d9d9d9",
        hoverBg="#b0b0b0",
        pressBg="#808080",
    ):
        super().__init__(
            parent,
            width=diameter,
            height=diameter,
            highlightthickness=0,
            bg=parent.cget("bg"),
        )

        self.onClicked = onClicked
        self.defaultBg = bg
        self.hoverBg = hoverBg
        self.pressBg = pressBg
        self.diameter = diameter

        pad = 2
        self.circle = self.create_oval(
            pad,
            pad,
            diameter - pad,
            diameter - pad,
            fill=bg,
            outline="",
        )

        self.setIcon(icon)

    def onEnter(self, _):
        self.itemconfig(self.circle, fill=self.hoverBg)

    def onLeave(self, _):
        self.itemconfig(self.circle, fill=self.defaultBg)

    def onPress(self, _):
        self.itemconfig(self.circle, fill=self.pressBg)

    def onRelease(self, _):
        self.itemconfig(self.circle, fill=self.hoverBg)
        if self.onClicked:
            self.onClicked()

    def setIcon(self, icon):
        self.iconType = icon
        # Load icon
        self.icon = tk.PhotoImage(
            file=f"icons/16x16/{icon}.png"
        )

        # Center icon
        self.iconItem = self.create_image(
            self.diameter // 2,
            self.diameter // 2,
            image=self.icon
        )

        # Bind events
        for tag in (self.circle, self.iconItem):
            self.tag_bind(tag, "<Enter>", self.onEnter)
            self.tag_bind(tag, "<Leave>", self.onLeave)
            self.tag_bind(tag, "<ButtonPress-1>", self.onPress)
            self.tag_bind(tag, "<ButtonRelease-1>", self.onRelease)


class EllipsisLabel(tk.Label):
    def __init__(self, master=None, text="", tooltip_delay=400, **kwargs):
        super().__init__(master, **kwargs)

        self._full_text = text
        self._font = font.Font(font=self.cget("font"))
        self._tooltip_delay = tooltip_delay

        self._tooltip = None
        self._tooltip_after_id = None

        super().config(text=text)

        # Events
        self.bind("<Configure>", self._update_truncation)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set_text(self, text):
        self._full_text = text
        self._update_truncation()

    def config(self, *args, **kwargs):
        if "text" in kwargs:
            self._full_text = kwargs["text"]
        super().config(*args, **kwargs)
        self._update_truncation()

    # Truncate
    def _update_truncation(self, event=None):
        max_width = self.winfo_width()

        if max_width <= 1:
            return

        text = self._full_text

        if self._font.measure(text) <= max_width:
            super().config(text=text)
            self._is_truncated = False
            return

        ellipsis = "..."
        low, high = 0, len(text)

        while low < high:
            mid = (low + high) // 2
            candidate = text[:mid] + ellipsis

            if self._font.measure(candidate) <= max_width:
                low = mid + 1
            else:
                high = mid

        final = text[:low - 1] + ellipsis
        super().config(text=final)
        self._is_truncated = True

    # Tooltip
    def _on_enter(self, event):
        if not getattr(self, "_is_truncated", False):
            return

        self._tooltip_after_id = self.after(
            self._tooltip_delay,
            self._show_tooltip
        )

    def _on_leave(self, event):
        if self._tooltip_after_id:
            self.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None

        self._hide_tooltip()

    def _show_tooltip(self):
        if self._tooltip:
            return

        x = self.winfo_rootx() + 10
        y = self.winfo_rooty() + self.winfo_height() + 5

        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self._tooltip,
            text=self._full_text,
            bg="#222",
            fg="white",
            padx=6,
            pady=3,
            relief="solid",
            borderwidth=1,
            font=self.cget("font")
        )
        label.pack()

    def _hide_tooltip(self):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None
