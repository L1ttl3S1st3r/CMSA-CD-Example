from PyQt5 import QtCore, QtGui, QtWidgets
from model import ModelBusyException


class DisableableTextEdit(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input_disabled = False
        self._value = ""

    def disable_input(self):
        self._input_disabled = True
        self.setDisabled(True)
        self.setReadOnly(True)
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        self.focusNextChild()

    def enable_input(self):
        self._input_disabled = False
        self.setDisabled(False)
        self.setReadOnly(False)
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        self.setFocus()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if not self._input_disabled:
            print('handle press')
            super().keyPressEvent(e)
            self._value = self.toPlainText()
            e.accept()
        else:
            self.setText(self._value)
            e.ignore()

    def keyReleaseEvent(self, e: QtGui.QKeyEvent) -> None:
        if not self._input_disabled:
            super().keyReleaseEvent(e)
            self._value = self.toPlainText()
            e.accept()
        else:
            self.setText(self._value)
            e.ignore()


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(846, 626)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.input_label = QtWidgets.QLabel(self.centralWidget)
        self.input_label.setObjectName("input_label")
        self.verticalLayout_2.addWidget(self.input_label)
        self.input_text = DisableableTextEdit(self.centralWidget)
        self.input_text.setObjectName("input_text")
        self.verticalLayout_2.addWidget(self.input_text)
        self.output_label = QtWidgets.QLabel(self.centralWidget)
        self.output_label.setObjectName("output_label")
        self.verticalLayout_2.addWidget(self.output_label)
        self.output_text = QtWidgets.QTextEdit(self.centralWidget)
        self.output_text.setReadOnly(True)
        self.output_text.setObjectName("output_text")
        self.verticalLayout_2.addWidget(self.output_text)
        self.debug_label = QtWidgets.QLabel(self.centralWidget)
        self.debug_label.setObjectName("debug_label")
        self.verticalLayout_2.addWidget(self.debug_label)
        self.debug_text = QtWidgets.QTextEdit(self.centralWidget)
        self.debug_text.setReadOnly(True)
        self.debug_text.setObjectName("debug_text")
        self.verticalLayout_2.addWidget(self.debug_text)
        self.checkBox = QtWidgets.QCheckBox(self.centralWidget)
        self.checkBox.setObjectName("check_box")
        self.verticalLayout_2.addWidget(self.checkBox)
        MainWindow.setCentralWidget(self.centralWidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.input_label.setText(_translate("MainWindow", "Input"))
        self.output_label.setText(_translate("MainWindow", "Output"))
        self.debug_label.setText(_translate("MainWindow", "Debug"))
        self.checkBox.setText(_translate("MainWindow", "Enable Burst Mode"))


class MainView(QtWidgets.QMainWindow):
    """ Main view of application """

    def __init__(self, input_controller, check_box_controller, writes_mutex: QtCore.QMutex, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.input_controller = input_controller
        self.check_box_controller = check_box_controller

        ui = Ui_MainWindow()
        ui.setupUi(self)

        # connect widgets with their handlers in view
        check_box: QtWidgets.QCheckBox = self.findChild(QtWidgets.QCheckBox, 'check_box')
        input_text: QtWidgets.QTextEdit = self.findChild(DisableableTextEdit, 'input_text')

        input_text.textChanged.connect(self.handle_input)
        check_box.stateChanged.connect(self.handle_check_box)

        self.previous_text: str = ""
        self.previous_state: bool = False

        self.writes_mutex = writes_mutex

    def write_to_debug(self, some_text: str):
        debug_text: QtWidgets.QTextEdit = self.findChild(QtWidgets.QTextEdit, 'debug_text')
        debug_text.setText(debug_text.toPlainText() + some_text)
        debug_text.moveCursor(QtGui.QTextCursor.End)

    def update(self, changings: tuple):
        what_changed = changings[0]
        new_value = changings[1]

        if what_changed == 'debug':
            self.write_to_debug(new_value)
        elif what_changed == 'output':
            output: QtWidgets.QTextEdit = self.findChild(QtWidgets.QTextEdit, 'output_text')
            output.setText(new_value)
            output.moveCursor(QtGui.QTextCursor.End)
        elif what_changed == 'burst_mode':
            check_box: QtWidgets.QCheckBox = self.findChild(QtWidgets.QCheckBox, 'check_box')
            check_box.setChecked(new_value)

    @staticmethod
    def valid_input(previous_text: str,
                    new_text: str) -> bool:
        if len(new_text) > len(previous_text):
            size_difference = abs(len(new_text) - len(previous_text))
            return previous_text == new_text[:-size_difference]
        else:
            return False

    def handle_input(self):
        """ input text field handler """
        locked = False
        try:
            input_text: DisableableTextEdit = self.findChild(DisableableTextEdit, 'input_text')
            if self.writes_mutex.tryLock():
                locked = True
                input_text.disable_input()

                if self.valid_input(self.previous_text, input_text.toPlainText()):
                    self.input_controller.handle(input_text.toPlainText())
                    self.previous_text = input_text.toPlainText()
                else:
                    input_text.textChanged.disconnect(self.handle_input)
                    input_text.setText(self.previous_text)
                    input_text.moveCursor(QtGui.QTextCursor.End)
                    input_text.textChanged.connect(self.handle_input)
            else:
                input_text.textChanged.disconnect(self.handle_input)
                input_text.setText(self.previous_text)
                input_text.moveCursor(QtGui.QTextCursor.End)
                input_text.textChanged.connect(self.handle_input)

        except ModelBusyException:
            input_text.textChanged.disconnect(self.handle_input)
            input_text.setText(self.previous_text)
            input_text.moveCursor(QtGui.QTextCursor.End)
            input_text.textChanged.connect(self.handle_input)
        except Exception as ex:
            self.write_to_debug(str(ex))
        finally:
            if locked:
                self.writes_mutex.unlock()
            input_text.enable_input()

    def handle_check_box(self):
        """ check box handler """
        locked = False
        try:
            check_box: QtWidgets.QCheckBox = self.findChild(QtWidgets.QCheckBox, 'check_box')
            if self.writes_mutex.tryLock():
                locked = True
                self.check_box_controller.handle(check_box.isChecked())
                self.previous_state = check_box.isChecked()
            else:
                check_box.stateChanged.disconnect(self.handle_check_box)
                check_box.setChecked(self.previous_state)
                check_box.stateChanged.connect(self.handle_check_box)
        except ModelBusyException:
            check_box.stateChanged.disconnect(self.handle_check_box)
            check_box.setChecked(self.previous_state)
            check_box.stateChanged.connect(self.handle_check_box)
        except Exception as ex:
            self.write_to_debug(str(ex))
        finally:
            if locked:
                self.writes_mutex.unlock()
