def run_measurement(start_freq, stop_freq, num_points):
    # Initialize CNC
    cnc_serial = initialize_cnc()

    # Initialize VNA
    vna = initialize_vna()
    configure_vna(vna, start_freq, stop_freq, num_points)

    # Example points to move to (expand as needed)
    points = [(10, 10, 0), (20, 20, 0), (30, 30, 0)]

    for point in points:
        move_cnc(cnc_serial, *point)
        data = collect_vna_data(vna)
        print(f"Data at {point}: {data}")

    # Close CNC connection
    cnc_serial.close()
