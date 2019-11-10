from dataclasses import dataclass
from random import randint

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject, QMutex


import time


class ModelBusyException(ValueError):
    pass


@dataclass
class CMSACDModel(QObject):
    # properties
    _writes_now: QMutex
    _previous_text: str = ""
    _output: str = ""
    _burst_mode: bool = False

    # just for emulation
    _channel: str = ""

    # constants
    SLOT_TIME = 0.005  # of second
    COLLISION_WINDOW = 0.004  # of second

    update_signal = pyqtSignal(tuple)

    def __init__(self, writes_mutex: QMutex, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._writes_now = writes_mutex

    # for observer pattern
    def _notify(self, about: tuple):
        self.update_signal.emit(about)

    def _write_to_debug(self, value: str):
        self._notify(("debug", value))

    def set_output(self, new_output: str):
        self._output = new_output
        self._notify(("output", new_output))

    @pyqtSlot(bool)
    def set_burst_mode(self, new_burst_mode: bool):
        self._writes_now.lock()
        self._burst_mode = new_burst_mode
        self._notify(("burst_mode", new_burst_mode))
        self._writes_now.unlock()

    @property
    def burst_mode(self) -> bool:
        return self._burst_mode

    @property
    def output(self) -> str:
        return self._output

    @staticmethod
    def _wait(delay):
        time.sleep(delay)

    def _collision_found(self) -> bool:
        milliseconds_of_current_time = round(time.time() * 10000)
        return (milliseconds_of_current_time % 100) < (5 if self._burst_mode else 50)

    def _send_to_channel(self, message):
        self._channel = message

    @staticmethod
    def _channel_is_free() -> bool:
        milliseconds_of_current_time = round(time.time() * 1000)
        return (milliseconds_of_current_time % 10) < 5

    def _get_message_from_channel(self):
        self.set_output(self.output + self._channel)

    def _jam(self):
        self._write_to_debug('x')

    @pyqtSlot(str)
    def sync(self, new_input: str) -> bool:
        self._writes_now.lock()

        difference = self._difference(new_input, self._previous_text)
        self._send(difference)

        self._writes_now.unlock()

    def _calculate_delay(self, attempt: int) -> float:
        random_number: int = randint(0, 2 ** min(attempt, 10))

        return random_number * self.SLOT_TIME

    def _send_package(self, package: str) -> bool:
        attempts_counter: int = 0

        while attempts_counter < 10:
            if attempts_counter > 0:
                delay = self._calculate_delay(attempts_counter)
                self._wait(delay)

            # wait for free channel
            if not self._burst_mode:
                while not self._channel_is_free():
                    pass

            self._send_to_channel(package)
            self._wait(self.COLLISION_WINDOW)

            if not self._collision_found():
                return True

            self._jam()  # collision signal
            self._wait(self.COLLISION_WINDOW)

            attempts_counter += 1

            # if late collision
            if self._burst_mode:
                return False

        return False

    def _send(self, difference):
        changes = ""
        batch_size = 4 if self.burst_mode else 1

        while len(difference) >= batch_size:
            package = difference[:batch_size]

            for counter in range(batch_size):
                if not self._send_package(package[counter]):
                    self._write_to_debug("\n")
                    break
                self._get_message_from_channel()
                self._write_to_debug("\n")

            difference = difference[batch_size:]
            changes += package

        self._previous_text += changes

    @staticmethod
    def _difference(new: str, prev: str) -> str:
        equal_count = 0
        while equal_count < len(new) and equal_count < len(prev):
            if new[equal_count] != prev[equal_count]:
                break
            equal_count += 1

        return new[equal_count:]


class CMSACDModelTest:
    def validation(self):
        model = CMSACDModel(burst_mode=True)

        model.sync('some thing')
        model.sync('some thing')
        model.sync('some thing')
        model.sync('some thing')


if __name__ == "__main__":
    CMSACDModelTest().validation()
