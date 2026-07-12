from keyboard import mouse


class Mouse:
    def hook(self, callback):
        mouse.hook(callback)
