import importlib
from util import readConfig as rc
import errors as Errors

class WidgetLoader:
    # app = None
    # state = None
    # rootWindow = None

    def __init__(self,app,state,rootWindow):
        self.app = app
        self.state = state
        self.rootWindow = rootWindow

    def loadWidget(self,ctype,configFileName=""):
        filename = ctype[0].upper() + ctype[1:]

        try:
            module = importlib.import_module("Widgets." + filename)
        except ModuleNotFoundError:
            """
            File doesn't exist
            """
            raise Errors.WidgetTypeError(ctype)

        try:
            myClass = getattr(module, "Widget")
        except AttributeError:
            """
            File doesn't have a "Widget" class. This should only happen for
            practice-related widgets and widget base classes.
            """
            raise Errors.WidgetTypeError(ctype)

        config = rc.getCUserConfig(ctype,configFileName)
        if ctype == "controlButtons":
            return myClass(self.rootWindow,self.state,config,self.app)
        else:
            return myClass(self.rootWindow,self.state,config)
