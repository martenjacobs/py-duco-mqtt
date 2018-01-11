
class DucoboxControl(object):

    def __init__(self, config):
        pass

    # TODO: should probably have open and close methods

    def open(self):
        raise NotImplementedError("Abstract method")
        
    def close(self):
        raise NotImplementedError("Abstract method")

    def set_state(self, value):
        raise NotImplementedError("Abstract method")
