class recstat():
    """ Enum class for holding recording status codes. """
    IDLE = 0
    PREPARING = 1
    RECORDING = 2
    LISTENING = 3
    ENCODING = 4
    UPLOADING = 5


class serstat():
    """ Enum class for holding server status codes. """
    NOTHING = 0
    OK = 1
    ERROR = -1
    NOT_UNDERSTOOD = -2
