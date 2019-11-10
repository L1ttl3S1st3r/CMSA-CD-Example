from PyQt5.QtCore import pyqtSignal, QObject


class Controller(QObject):
    """ The abstract base class for the all controllers """
    # abstract method
    def handle(self, argument):
        raise NotImplemented


class InputTextController(Controller):
    sync_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, argument):
        self.sync_signal.emit(argument)


class CheckBoxController(Controller):
    burst_mode_signal = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, argument):
        self.burst_mode_signal.emit(argument)
