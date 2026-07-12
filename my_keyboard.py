import keyboard


_initialized = False


class Keyboard:
    def __init__(self):
        global _initialized
        if not _initialized:
            keyboard.init(
                linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT)
        _initialized = True

    def write(self, s: str):
        keyboard.write(s)

    def write_list(self, s: list[str]):
        keyboard.write_list(s)

    def backspace(self, n_times: int = 1):
        for _ in range(0, n_times):
            keyboard.press_and_release("backspace")

    def hook(self, callback):
        keyboard.hook(callback)
