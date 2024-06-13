import pyvisa


def initialize_vna():
    rm = pyvisa.ResourceManager()
    # Replace with your VNA's address
    vna = rm.open_resource('TCPIP0::192.168.0.1::inst0::INSTR')
    return vna


def configure_vna(vna, start_freq, stop_freq, num_points):
    vna.write(f"SENS:FREQ:START {start_freq}")
    vna.write(f"SENS:FREQ:STOP {stop_freq}")
    vna.write(f"SENS:SWE:POIN {num_points}")


def collect_vna_data(vna):
    vna.write("INIT:IMM; *WAI")
    data = vna.query("CALC:DATA? SDATA")
    return data


# import pyvisa

# def initialize_vna():
#     rm = pyvisa.ResourceManager()
#     # Replace with your VNA's address
#     vna = rm.open_resource('TCPIP0::192.168.0.1::inst0::INSTR')
#     return vna

# def configure_vna(vna, frequency_list):
#     """
#     Configure the VNA with a list of discrete frequencies.

#     :param vna: The VNA resource object.
#     :param frequency_list: A list of frequencies in Hz.
#     """
#     # Convert the frequency list to a comma-separated string
#     frequency_list_str = ','.join([f"{freq}Hz" for freq in frequency_list])

#     # Send the frequency list to the VNA
#     vna.write(f":SENS1:FREQ:IND:DISC {frequency_list_str}")

# def collect_vna_data(vna):
#     vna.write("INIT:IMM; *WAI")
#     data = vna.query("CALC:DATA? SDATA")
#     return data

# # Example usage
# if __name__ == "__main__":
#     # Initialize VNA connection
#     vna = initialize_vna()

#     # Example frequency list in Hz
#     frequency_list = [3e9, 4e9, 5e9]  # 3 GHz, 4 GHz, 5 GHz

#     # Configure the VNA with the frequency list
#     configure_vna(vna, frequency_list)

#     # Collect and print VNA data
#     data = collect_vna_data(vna)
#     print(data)
