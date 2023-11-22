from Widgets import WidgetBase

class Widget(WidgetBase.WidgetBase):
    def __init__(self,parent,state,config):
        super().__init__(parent,state,config)
        self.configure(\
            height=config["height"],\
            bg=config["colours"]["bg"]\
        )
