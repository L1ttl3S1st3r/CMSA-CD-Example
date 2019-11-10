"""
CMSA/CD algorithm example
"""
import sys
from view import MainView
from controllers import InputTextController
from controllers import CheckBoxController
from model import CMSACDModel
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, QMutex

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('lab4')
    MainWindow = QtWidgets.QMainWindow()
    lock = QMutex()

    model = CMSACDModel(lock)

    input_text_controller = InputTextController()
    check_box_controller = CheckBoxController()

    main_view = MainView(input_text_controller, check_box_controller, lock)

    model.update_signal.connect(main_view.update)
    input_text_controller.sync_signal.connect(model.sync)
    check_box_controller.burst_mode_signal.connect(model.set_burst_mode)

    worker = QThread()
    model.moveToThread(worker)
    worker.start()

    MainWindow.setCentralWidget(main_view)
    MainWindow.show()
    sys.exit(app.exec_())