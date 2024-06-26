import serial
import time
import pyvisa
import csv
import threading
import pandas as pd

stopped_machine = False


def run_measurement(cnc_serial, start_freq, stop_freq, num_points, esrx, esry, espx, espy, absolute_pos, progress_bar, update_progress):
    vna = initialize_vna()
    configure_vna(vna, start_freq=start_freq,
                  stop_freq=stop_freq, num_points=num_points)

    # Set to incremental positioning mode
    send_command(cnc_serial, 'G91\n')
    send_command(cnc_serial, 'G21\n')

    feed_rate = 1000  # Reduce speed to avoid mechanical issues

    print(
        f"Running measurement from {start_freq} GHz to {stop_freq} GHz with {num_points} points.")

    # Define the dimensions of your CNC's working area

    move_cnc(cnc_serial, x=-(esrx / 2), y=0, z=0, feed_rate=5000)
    time.sleep(2)
    move_cnc(cnc_serial, x=0, y=(esry / 2), z=0, feed_rate=5000)
    time.sleep(2)
    absolute_pos[0] -= esrx/2
    absolute_pos[1] += esry/2

    # Define the positions
    pos_or_neg = -1
    increment_y = esry / (espy - 1)
    increment_x = esrx / (espx - 1)
    positions = []
    for i in range(espx - 1):
        temp_pos = [(0, increment_y * pos_or_neg, 0) for i in range(espy - 1)]
        pos_or_neg = pos_or_neg * -1
        positions.extend(temp_pos)
        positions.append((increment_x, 0, 0))
    temp_pos = [(0, increment_y * pos_or_neg, 0) for i in range(espy - 1)]
    positions.extend(temp_pos)

#     positions = [
#         (-10, -10, 0),
#         (-20, -10, 0)
#         # Add more positions here if needed (incremental)
#     ]
    print(positions)
    print("length: " + str(len(positions)))
    progress_step = 100 / len(positions)
    current_progress = 0
    positions.insert(0, (0, 0, 0))

    current_position = [-(esrx/2), (esry/2), 0]
    csv_file = 'measurement_data.csv'

    # Create or clear the CSV file and write the header
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['pt', 'x', 'y'] + \
            [item for i in range(num_points)
             for item in (f'amp{i+1}', f'phase{i+1}')]
        writer.writerow(header)

    start_time = time.time()

    for pt, (dx, dy, dz) in enumerate(positions):
        # Move the CNC to the next position

        # Collect VNA data
        thread = threading.Thread(
            target=check_position, args=(cnc_serial, absolute_pos,))
        thread.start()
        thread.join()
        data_collected = False
        if stopped_machine:
            break
        while not data_collected:
            data = collect_vna_data(vna)
            print("collecting data")
            if data:
                # Parse the data
                parsed_data = parse_vna_data(data)
                # Write data to the CSV file
                with open(csv_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    row = [pt] + [current_position[0] + dx,
                                  current_position[1] + dy] + parsed_data
                    writer.writerow(row)
                # Update the current position after the move
                current_position = [
                    current_position[0] + dx, current_position[1] + dy, current_position[2] + dz]
                absolute_pos = [absolute_pos[0] + dx, absolute_pos[1] + dy]
                data_collected = True
            else:
                print("Data collection failed, retrying...")
        move_cnc(cnc_serial, dx, dy, dz, feed_rate)
        time.sleep(1)
        current_progress += progress_step
        update_progress(current_progress)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Loop completed in {elapsed_time:.2f} seconds")

    df = pd.read_csv(csv_file)
    grouped_df = df.groupby('x', group_keys=False).apply(
        lambda x: x.sort_values('y', ascending=False))
    grouped_df.to_csv(csv_file, index=False)

    cnc_serial.close()


def initialize_vna():
    rm = pyvisa.ResourceManager('@py')
    vna = rm.open_resource('TCPIP0::169.254.234.85::inst0::INSTR')
    vna.timeout = 45000  # Set timeout to 45000 milliseconds (45 seconds)
    return vna


def configure_vna(vna, start_freq=None, stop_freq=None, num_points=None):
    try:
        if start_freq and stop_freq and num_points:
            start_freq = start_freq * 1e9  # Convert GHz to Hz
            stop_freq = stop_freq * 1e9  # Convert GHz to Hz
            vna.write(f"SENS:FREQ:START {start_freq}")
            vna.write(f"SENS:FREQ:STOP {stop_freq}")
            vna.write(f"SENS:SWE:POIN {num_points}")
            vna.write("CALC:PAR:DEF 'Meas1', 'S12'")
        print("Configuration completed.")
    except pyvisa.errors.VisaIOError as e:
        print(f"Configuration Error: {e}")


def collect_vna_data(vna):
    try:
        vna.write("INIT:IMM")
        # Check for operation complete
        status = vna.query("*OPC?")
        # print(f"Sweep completed: {status}")
        if status.strip() == "1":
            data = vna.query("CALC:DATA:SDAT?")
            return data
        else:
            print("Sweep not completed, please check VNA settings.")
            return None
    except pyvisa.errors.VisaIOError as e:
        print(f"Data Collection Error: {e}")
        return None


def parse_vna_data(data):
    lines = data.strip().split('\n')
    # print("Split lines:", lines)
    values = []

    for line in lines:
        # Remove the initial identifier if present
        if line.startswith('#'):
            line = line.split(' ', 1)[1]  # Split only on the first space
        split_values = [v.strip() for v in line.split(',')]
       # print("Split values from line:", split_values)
        values.extend(split_values)

#    print("All extracted values:", values)

    # Interleave amplitudes and phases
    interleaved = []
    for i in range(0, len(values) - 1, 2):
        try:
            interleaved.append(float(values[i]))    # Amplitude
            interleaved.append(float(values[i + 1]))  # Phase
        except ValueError as e:
            print(
                f"Error converting value to float: {values[i]} or {values[i + 1]}, {e}")

    print("Interleaved values:", interleaved)
    return interleaved


def initialize_all():
    cnc_serial = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=1)
    time.sleep(2)  # Wait for connection to establish
    cnc_serial.write(b'\n')  # Wake up the machine
    time.sleep(1)
    cnc_serial.write(b'$X\n')  # Unlock the machine
    time.sleep(1)
    response = cnc_serial.readlines()  # Read all available responses
    for line in response:
        print("Initialize response:", line.decode().strip())
    return


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
    send_command(cnc_serial, '$H\n')
    send_command(cnc_serial, 'G91\n')  # incremental positioning pode
    # set to mm (metric system) for movements
    send_command(cnc_serial, 'G21\n')
    return cnc_serial


def send_command(cnc_serial, command):
    cnc_serial.write(command.encode())
    time.sleep(0.5)
    response = cnc_serial.readlines()
    for line in response:
        print(f"Response to {command.strip()}: {line.decode().strip()}")


def move_cnc(cnc_serial, x, y, z, feed_rate):
    command = f"G1 X{x} Y{y} Z{z} F{feed_rate}\n"
    send_command(cnc_serial, command)


def move_x_cnc(cnc_serial, x):
    move_cnc(cnc_serial, x, 0, 0, 5000)


def move_y_cnc(cnc_serial, y):
    move_cnc(cnc_serial, 0, y, 0, 5000)


def go_to_home(cnc_serial, zero_home):
    send_command(cnc_serial, 'G90\n')  # abs mode
    move_cnc(cnc_serial, -(838 - zero_home[0]), -(838 - zero_home[1]), 0, 5000)
    send_command(cnc_serial, 'G91\n')  # abs mode


def check_position(cnc_serial, absolute_pos, tolerance=1.00):
    hold_count = 0
    global stopped_machine
    while True:
        cnc_serial.write(b"?")
        response = cnc_serial.readline().decode().strip()
        if response:
            print("Position check response:", response)
            status_parts = response.split('|')
            for part in status_parts:
                if part.startswith('MPos:'):
                    pos = part[5:].split(',')
                    current_x = float(pos[0])
                    current_y = float(pos[1])
                    if (abs(current_x + (838 - absolute_pos[0])) < tolerance and
                            abs(current_y + (838 - absolute_pos[1])) < tolerance):
                        print(
                            f"Reached position: X={current_x}, Y={current_y}")
                        return True
                if part.startswith("Hold"):
                    hold_count += 1
                    if hold_count > 10:
                        stopped_machine = True
                        return False

        time.sleep(0.5)
