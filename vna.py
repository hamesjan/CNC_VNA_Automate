import pyvisa
import time


def list_resources():
    rm = pyvisa.ResourceManager('@py')
    resources = rm.list_resources()
    print("Available resources:", resources)


def initialize_vna():
    rm = pyvisa.ResourceManager('@py')
    vna = rm.open_resource('TCPIP0::169.254.234.85::inst0::INSTR')
    vna.timeout = 45000  # Set timeout to 45000 milliseconds (45 seconds)
    return vna


def reset_vna(vna):

    try:
        vna.write("*RST")
        time.sleep(5)  # Wait for reset to complete
    except pyvisa.errors.VisaIOError as e:
        print(f"Reset Error: {e}")


def configure_vna(vna, start_freq=None, stop_freq=None, num_points=None):
    try:
        if start_freq and stop_freq and num_points:
            vna.write(f"SENS:FREQ:START {start_freq}")
            time.sleep(2)  # Longer delay to ensure the command is processed
            vna.write(f"SENS:FREQ:STOP {stop_freq}")
            time.sleep(2)
            vna.write(f"SENS:SWE:POIN {num_points}")
            time.sleep(2)
            vna.write("CALC:PAR:DEF 'Meas1', 'S12'")
            time.sleep(2)
        print("Configuration completed.")
    except pyvisa.errors.VisaIOError as e:
        print(f"Configuration Error: {e}")


def collect_vna_data(vna):
    try:
        vna.write("INIT:IMM")
        time.sleep(10)  # Ensure the measurement is started
        # Check for operation complete
        status = vna.query("*OPC?")
        print(f"Sweep completed: {status}")
        if status.strip() == "1":
            time.sleep(10)  # Additional wait time before querying data
            data = vna.query("CALC:DATA:SDAT?")
            return data
        else:
            print("Sweep not completed, please check VNA settings.")
            return None
    except pyvisa.errors.VisaIOError as e:
        print(f"Data Collection Error: {e}")
        return None


def test_simple_command(vna):
    try:
        response = vna.query("*IDN?")
        print("VNA Identification:", response)
    except pyvisa.errors.VisaIOError as e:
        print(f"Simple Command Error: {e}")


def go_to_local(vna):
    try:
        vna.write("GTL")  # Send the Go To Local command
        print("VNA switched to local mode.")
    except pyvisa.errors.VisaIOError as e:
        print(f"GTL Command Error: {e}")


# Example usage
if __name__ == "__main__":
    # List available resources
    list_resources()

    # Initialize VNA connection
    vna = initialize_vna()

    # Reset the VNA
    reset_vna(vna)

    # Test a simple command to ensure basic communication
    test_simple_command(vna)

    # Configure with start and stop frequencies
    start_freq = 35.5e9  # 3 GHz
    stop_freq = 36e9  # 5 GHz
    num_points = 11

    configure_vna(vna, start_freq=start_freq,
                  stop_freq=stop_freq, num_points=num_points)

    # Collect and print VNA data
    data = collect_vna_data(vna)
    if data:
        print(data)

    # Switch VNA to local mode
    # go_to_local(vna)
