import serial
import time


def initialize_cnc(port='/dev/ttyACM0', baudrate=115200):
    cnc_serial = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # Wait for connection to establish
    cnc_serial.write(b'\n')  # Wake up the machine
    time.sleep(1)
    cnc_serial.write(b'$X\n')  # Unlock the machine
    time.sleep(1)
    response = cnc_serial.readlines()  # Read all available responses
    for line in response:
        print("Initialize response:", line.decode().strip())
    return cnc_serial


def send_command(cnc_serial, command):
    cnc_serial.write(command.encode())
    time.sleep(0.5)
    response = cnc_serial.readlines()
    for line in response:
        print(f"Response to {command.strip()}: {line.decode().strip()}")


def move_cnc(cnc_serial, x, y, z, feed_rate):
    gcode = f"G1 X{x} Y{y} Z{z} F{feed_rate}\n"
    send_command(cnc_serial, gcode)


if __name__ == "__main__":
    # Initialize the CNC machine
    # Change to the correct port if necessary
    cnc_serial = initialize_cnc(port='/dev/ttyACM0')

    # Set to incremental positioning mode
    send_command(cnc_serial, '$H\n')

    send_command(cnc_serial, 'G91\n')

    feed_rate = 10000  # speed of machine

    # Example movement commands
    # negative x is left, negative y is down
    move_cnc(cnc_serial, x=-600, y=-600, z=0, feed_rate=feed_rate)
    move_cnc(cnc_serial, x=200, y=100, z=0, feed_rate=feed_rate)

    # Close the serial connection
    cnc_serial.close()
