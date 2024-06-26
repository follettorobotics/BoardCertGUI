from Log.logger_config import logger


class MessageFormatter:

    INTERNAL_MOTOR_PARAMETER = {
        "Internal Motor 1": 0x01,
        "Internal Motor 2": 0x02,
        "Internal Motor 3": 0x03,
        "Internal Motor 4": 0x04,
        "Internal Motor 5": 0x05,
        "Internal Motor 6": 0x06
    }

    EXTERNAL_MOTOR_PARAMETER = {
        "External Motor 1": 0x01,
        "External Motor 2": 0x02,
        "External Motor 3": 0x03,
        "External Motor 4": 0x04
    }

    @staticmethod
    def byte_array_to_hex_string(byte_array) -> str:
        """
        Convert byte array to hex string
        :param byte_array: byte array or list of integers
        :return: hex string
        """
        # Type checking
        if not isinstance(byte_array, (bytes, bytearray, list)):
            logger.debug(f"Input must be of type bytes, bytearray, or list of integers")
            raise ValueError("Input must be of type bytes, bytearray, or list of integers")


        # Element value checking
        for x in byte_array:
            if not isinstance(x, int):
                logger.debug(f"InpElement is not an integer: {x}")
                raise ValueError(f"Element is not an integer: {x}")
            if not (0 <= x <= 255):
                logger.debug(f"Byte value out of range: {x}")
                raise ValueError(f"Byte value out of range: {x}")

        return ' '.join('{:02x}'.format(x) for x in byte_array)

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
    def relay_on_message(relay_number):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB1)
        # RELAY NUMBER
        request.append(int(relay_number))
        # CONTROL
        request.append(0x01)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def relay_off_message(relay_number):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB1)
        # RELAY NUMBER
        request.append(int(relay_number))
        # CONTROL
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def internal_motor_cw_message(motor_number):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB2)
        # RELAY NUMBER
        request.append(MessageFormatter.INTERNAL_MOTOR_PARAMETER[motor_number])
        # CW
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def internal_motor_ccw_message(motor_number):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB2)
        # RELAY NUMBER
        request.append(MessageFormatter.INTERNAL_MOTOR_PARAMETER[motor_number])
        # CW
        request.append(0xff)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def external_motor_control_message(motor_number):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB3)
        # RELAY NUMBER
        request.append(MessageFormatter.EXTERNAL_MOTOR_PARAMETER[motor_number])
        # CW
        request.append(0x00)
        # END BYTE
        request.append(0XAA)

        return bytes(request)

    @staticmethod
    def get_loadcell_value_message(cell_index):
        # REQUEST_HEAD
        request = bytearray()
        request.append(0x7E)
        # COMMAND
        request.append(0xB4)
        # INDEX
        request.append(cell_index-1)
        # END BYTE
        request.append(0XAA)

        return bytes(request)
