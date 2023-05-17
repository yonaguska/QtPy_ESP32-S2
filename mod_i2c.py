import board
import busio

def init():
    """ I2C setup """
    # Create i2c object, communicating over the board's i2c qwiic bus
    try:
        i2c_qwiic = busio.I2C(board.SCL1, board.SDA1)  # QT Py
    except:
        i2c_qwiic = None

    # Create i2c object, communicating over the board's default I2C bus
    try:
        i2c_board = board.I2C()  # uses board.SCL and board.SDA
    except:
        i2c_board = None

    return i2c_board, i2c_qwiic

