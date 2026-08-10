import keyboard
from constants import KEYBOARD_NAME
from linux_keyboard import LinuxKeyboardType

_initialized = False


class Keyboard:
    def __init__(self, keyboard_mode: LinuxKeyboardType = LinuxKeyboardType.PATIENT):
        global _initialized
        if not _initialized:
            keyboard.init(
                device_name=KEYBOARD_NAME,
            )
            self.update_keyboard(keyboard_mode)
        _initialized = True

    def update_keyboard(self, t: LinuxKeyboardType):

        if t == LinuxKeyboardType.PATIENT:
            keyboard.patient_collision_safe_mode()
        else:
            keyboard.end_patient_collision_safe_mode()

        if t == LinuxKeyboardType.GRAB:
            keyboard.grab()
        else:
            keyboard.ungrab()

    def write(self, s: str):
        keyboard.write(s)

    def write_list(self, s: list[str]):
        keyboard.write_list(s)

    def backspace(self, n_times: int = 1):
        if n_times > 0 and keyboard.is_grabbed():
            keyboard.release("backspace")
        for _ in range(n_times):
            keyboard.press_and_release("backspace")

    def grabbed(self):
        return keyboard.is_grabbed()

    def propagate(self, event):
        keyboard.propagate(event)

    def hook(self, callback):
        keyboard.hook(callback)
