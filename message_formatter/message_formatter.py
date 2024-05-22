class MessageFormatter:

    def __init__(self):
        pass

    @staticmethod
    def sensor_message():
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB0)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

