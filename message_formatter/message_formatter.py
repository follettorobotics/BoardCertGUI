class MessageFormatter:

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

    @staticmethod
    def relay_on_message(relay_number: int):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB1)
        # RELAY NUMBER
        request.append(relay_number)
        # CONTROL
        request.append(0x01)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def relay_off_message(relay_number: int):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB1)
        # RELAY NUMBER
        request.append(relay_number)
        # CONTROL
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def internal_motor_cw_message(motor_number: int):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB2)
        # RELAY NUMBER
        request.append(motor_number)
        # CW
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def internal_motor_ccw_message(motor_number: int):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB2)
        # RELAY NUMBER
        request.append(motor_number)
        # CW
        request.append(0xff)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def external_motor_control_message(motor_number: int):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB3)
        # RELAY NUMBER
        request.append(motor_number)
        # CW
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)
