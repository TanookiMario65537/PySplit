from util import timeHelpers as timeh


class SyncedTimeList:
    segments: list
    totals: list
    _initSegments: list
    _initTotals: list
    default_type: str

    def __init__(self, segments=None, totals=None):
        if segments is not None:
            self.default_type = "segment"
            if len(segments) and timeh.isStringTime(segments[0]):
                segments = timeh.stringListToTimes(segments)
            self.segments = segments
            self.totals = [0 for _ in range(len(segments))]
            self.setTotals()
        elif totals is not None:
            self.default_type = "total"
            if len(totals) and timeh.isStringTime(totals[0]):
                totals = timeh.stringListToTimes(totals)
            self.totals = totals
            self.segments = [0 for _ in range(len(totals))]
            self.setSegments()

        self._initSegments = [segment for segment in self.segments]
        self._initTotals = [total for total in self.totals]

    def insert(self, time, index, ltype=""):
        if not ltype:
            ltype = self.default_type
        self.segments.insert(index, time)
        self.totals.insert(index, time)
        if ltype == "segment":
            self.setTotals()
        elif ltype == "total":
            self.setSegments()

    def remove(self, index, ltype=""):
        if not ltype:
            ltype = self.default_type
        del self.segments[index]
        del self.totals[index]
        if ltype == "segment":
            self.setTotals()
        elif ltype == "total":
            self.setSegments()

    def update(self, time, index, ltype=""):
        if not ltype:
            ltype = self.default_type
        if ltype == "segment":
            self.segments[index] = time
            self.setTotals()
        elif ltype == "total":
            self.totals[index] = time
            self.setSegments()

    def setSegments(self):
        if not len(self.totals):
            self.segments = []
            return
        self.segments[0] = self.totals[0]
        for i in range(1, len(self.totals)):
            self.segments[i] = timeh.difference(
                self.totals[i],
                self.totals[i-1])

    def setTotals(self):
        if not len(self.segments):
            self.totals = []
            return
        self.totals[0] = self.segments[0]
        for i in range(1, len(self.totals)):
            self.totals[i] = timeh.add(self.segments[i], self.totals[i-1])

    def lastNonBlank(self):
        for i in range(len(self.totals)-1, -1, -1):
            if not timeh.isBlank(self.totals[i]):
                return i
        return -1

    def resetValue(self, index):
        self.update(
            self._initSegments[index]
            if self.default_type == "segment"
            else self._initTotals[index],
            index
        )


class BptList(SyncedTimeList):
    def __init__(self, segments=None, totals=None):
        super().__init__(segments, totals)
        self.setTotal()

    def update(self, time, index, ltype=""):
        self.totals[index] = time
        self.setFutureTotals(index)

    def resetValue(self, index):
        super().resetValue(index)
        if index > 0:
            self.setFutureTotals(index-1)

    def setFutureTotals(self, index):
        for i in range(index+1, len(self.segments)):
            self.totals[i] = timeh.add(self.totals[i-1], self.segments[i])
        self.setTotal()

    def setTotal(self):
        self.total = self.totals[-1] if len(self.totals) else timeh.blank()


class CurrentRun(SyncedTimeList):
    def __init__(self, segments=None, totals=None):
        super().__init__(segments, totals)
        self.isoTimes = ["" for _ in range(len(self.segments))]

    def update(self, time, isoTime, index, ltype=""):
        super().update(time, index, ltype)
        self.isoTimes[index] = isoTime

    def resetValue(self, index):
        super().resetValue(index)
        self.isoTimes[index] = ""


class Comparison:
    times: SyncedTimeList
    diffs: SyncedTimeList
    ctype: str
    title: str
    name: str

    def __init__(self, title, totals, ctype, name=None):
        self.title = title
        self.name = name if name else title
        self.ctype = ctype
        self.times = SyncedTimeList(totals=totals)
        self.diffs = SyncedTimeList(totals=[timeh.blank() for _ in totals])

    def update(self, totaltime, index):
        self.diffs.update(
            timeh.difference(totaltime, self.times.totals[index]),
            index
        )

    def resetValue(self, index):
        self.times.resetValue(index)
        self.diffs.resetValue(index)

    def lastNonBlank(self):
        return self.times.lastNonBlank()
