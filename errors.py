class Error(Exception):
    pass


class WidgetTypeError(Error):
    message = ""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'The component type "{self.message}" is not a valid type'


class HotKeyTypeError(Error):
    message = ""
    default = ""
    control = ""

    def __init__(self, message, default, control):
        self.message = message
        self.default = default
        self.control = control
        super().__init__(self.message)

    def __str__(self):
        return (
            f'The hotkey "{self.message}" is an invalid key.  '
            f'Using the default hotkey "{self.default}" '
            f'for the control action "{self.control}"'
        )


class ConfigValueError(Error):
    key = ""
    user = ""
    default = ""

    def __init__(self, key, user, default):
        self.key = key
        self.user = user
        self.default = default
        super().__init__(self.key)

    def __str__(self):
        return (
            f'The configuration key "{self.key}" '
            f'has an invalid value "{self.user}". '
            f'Setting to the default value "{self.default}".'
        )
