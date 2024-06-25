import tkinter as tk
from tkinter import font
from tkinter import ttk
import threading
from cnc_vna_automate import run_measurement, move_x_cnc, move_y_cnc, initialize_cnc, go_to_home
import os
import subprocess
import serial
import time
from tkinter import messagebox

absolute_pos = [838, 838, 0]
zero_home = [838, 838, 0]
movement_locked = False
test_running = False
cnc_serial = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=1)


def initialize_all():
    cnc_serial.write(b'\n')  # Wake up the machine
    cnc_serial.write(b'$X\n')  # Unlock the machine
    response = cnc_serial.readlines()  # Read all available responses
    for line in response:
        print("Initialize response:", line.decode().strip())
    send_command_gui(cnc_serial, '$H\n')
    send_command_gui(cnc_serial, 'G91\n')  # incremental positioning pode
    send_command_gui(cnc_serial, 'G21\n')
    thread = threading.Thread(target=move_x_cnc, args=(cnc_serial, 3,))
    thread.start()
    thread.join()
    thread = threading.Thread(target=move_y_cnc, args=(cnc_serial, 3,))
    thread.start()
    thread.join()
    return


def send_command_gui(cnc_serial, command):
    cnc_serial.write(command.encode())
    time.sleep(0.5)
    response = cnc_serial.readlines()
    for line in response:
        print(f"Response to {command.strip()}: {line.decode().strip()}")


def initialize_program():
    init_button.grid_remove()  # Hide the initialize button
    init_label.grid(row=1, column=0, pady=10)  # Show the initializing label
    initialize_all()
    root.after(2000, show_main_ui)  # Show main UI after 5 seconds


def show_main_ui():
    init_label.grid_remove()  # Hide the initializing label
    for widget in main_widgets:
        widget.grid()  # Show all main widgets


def toggle_lock():
    global movement_locked
    if movement_locked:
        # Unlock: Enable entries and buttons, change button text to "Lock"
        entry_move_x.config(state='normal')
        entry_move_y.config(state='normal')
        move_x_button.config(state='normal')
        move_y_button.config(state='normal')
        home_button.config(state='normal')
        lock_button.config(text='Set 0 and Lock')
    else:
        # Lock: Disable entries and buttons, change button text to "Unlock"
        set_current_position_at_home()
        entry_move_x.config(state='disabled')
        entry_move_y.config(state='disabled')
        move_x_button.config(state='disabled')
        move_y_button.config(state='disabled')
        home_button.config(state='disabled')
        lock_button.config(text='Go to 0 and Unlock')
    movement_locked = not movement_locked


def show_alert():
    messagebox.showinfo("ALERT", "CNC will move out of bounds")


def show_alert_incorrect_params():
    messagebox.showinfo("ALERT", "Params are incorrect")


def start_measurement():
    abs_x.set("test")
    abs_y.set("running")

    start_freq = float(entry_start_freq.get())
    stop_freq = float(entry_stop_freq.get())
    num_points = int(entry_num_points.get())
    esrx = float(entry_scan_range_x.get())
    esry = float(entry_scan_range_y.get())
    espx = int(entry_scan_points_x.get())
    espy = int(entry_scan_points_y.get())

    if (0 <= absolute_pos[0] - esrx / 2 <= 838) and (0 <= absolute_pos[0] + esrx / 2 <= 838) and (0 <= absolute_pos[1] - esry / 2 <= 838) and (0 <= absolute_pos[1] + esry / 2 <= 838):
        if (num_points <= 0) or (esrx <= 0) or (esry <= 0) or espx <= 0 or espy <= 0:
            show_alert_incorrect_params()
        else:
            progress_bar['value'] = 0  # Reset progress bar
            progress_label.set("Running...")
            progress_percentage.set("0%")
            progress_bar.grid(row=4, column=0, columnspan=2,
                              pady=20)  # Show progress bar
            # Show progress label
            progress_bar_label.grid(row=5, column=0, columnspan=2)
            # Show percentage label
            percentage_label.grid(row=6, column=0, columnspan=2)
            thread = threading.Thread(target=run_measurement_with_update, args=(cnc_serial, start_freq, stop_freq,
                                      num_points, esrx, esry, espx, espy, absolute_pos, progress_bar, progress_label, progress_percentage))
            thread.start()
    else:
        show_alert()


def run_measurement_with_update(cnc_serial, start_freq, stop_freq, num_points, esrx, esry, espx, espy, absolute_pos, progress_bar, progress_label, progress_percentage):
    def update_progress(value):
        progress_bar['value'] = value
        progress_bar.update_idletasks()
        progress_percentage.set(f"{int(value)}%")

    run_measurement(cnc_serial, start_freq, stop_freq, num_points, esrx,
                    esry, espx, espy, absolute_pos, progress_bar, update_progress)
    progress_label.set("Done")
    progress_percentage.set("100%")
    # Show download button
    download_button.grid(row=15, column=0, columnspan=2)


def download_csv():
    # Provide a download link to the CSV file
    csv_file = 'measurement_data.csv'
    if os.path.exists(csv_file):
        subprocess.call(['xdg-open', csv_file])


def move_x():
    x_distance = float(entry_move_x.get())
    # Add code to move the CNC machine by x_distance
    if (0 <= absolute_pos[0] + x_distance <= 838):
        absolute_pos[0] += x_distance
        thread = threading.Thread(
            target=move_x_cnc, args=(cnc_serial, x_distance,))
        thread.start()
        update_position_display()
    else:
        show_alert()


def move_y():
    y_distance = float(entry_move_y.get())
    # Add code to move the CNC machine by x_distance
    if (0 <= absolute_pos[1] + y_distance <= 838):
        absolute_pos[1] += y_distance
        thread = threading.Thread(
            target=move_y_cnc, args=(cnc_serial, y_distance,))
        thread.start()
        update_position_display()
    else:
        show_alert()


def go_to_home_gui():
    thread = threading.Thread(target=go_to_home, args=(cnc_serial, zero_home,))
    thread.start()
    thread.join()
    absolute_pos[0] = zero_home[0]
    absolute_pos[1] = zero_home[1]
    update_position_display()


def stop_machine():
    try:
        cnc_serial.write(b'!')
        # Giving a small delay to ensure the command is processed
        time.sleep(1)
        print("CNC stopped immediately.")
    except Exception as e:
        print(f"Error stopping CNC: {e}")


def reset_machine():
    try:
        cnc_serial.write(b'$H')
        # Giving a small delay to ensure the command is processed
        time.sleep(1)
        print("CNC reset immediately.")
    except Exception as e:
        print(f"Error restting CNC: {e}")


def set_current_position_at_home():
    zero_home[0] = absolute_pos[0]
    zero_home[1] = absolute_pos[1]


def update_position_display():
    # Update the display table with the absolute X and Y positions
    # Replace "Updated X" with the actual X position
    abs_x.set(absolute_pos[0])
    # Replace "Updated Y" with the actual Y position
    abs_y.set(absolute_pos[1])


root = tk.Tk()
root.title("VNA and CNC Controller")

large_font = font.Font(family="Helvetica", size=18, weight="bold")
medium_font = font.Font(family="Helvetica", size=14, weight="bold")

# Center the window on the screen
window_width = 1000
window_height = 700
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# Configure the main grid
for i in range(10):
    root.grid_rowconfigure(i, weight=1)
for i in range(3):
    root.grid_columnconfigure(i, weight=1)

# Initialize program button
init_button = tk.Button(root, text='Initialize Program',
                        command=initialize_program, font=large_font)
init_button.grid(row=0, column=0, pady=10)

# Initializing label
init_label = tk.Label(root, text="Initializing...", font=large_font)

# Main UI components (initially hidden)
main_widgets = []

# Abs Frame (topleft)
abs_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
main_widgets.append(abs_frame)
abs_frame.grid(row=0, column=0, rowspan=1, columnspan=1,
               padx=10, pady=10, sticky="nsew")
for i in range(2):
    abs_frame.grid_rowconfigure(i, weight=1)
    abs_frame.grid_columnconfigure(i, weight=1)
tk.Label(abs_frame, text="Absolute X (mm)\n[0,838]", font=medium_font).grid(
    row=0, column=0, pady=10)
abs_x = tk.StringVar()
abs_x.set("838")
tk.Label(abs_frame, textvariable=abs_x, font=large_font).grid(
    row=1, column=0, pady=10)
tk.Label(abs_frame, text="Absolute Y (mm)\n[0,838]", font=medium_font).grid(
    row=0, column=1, pady=10)
abs_y = tk.StringVar()
abs_y.set("838")
tk.Label(abs_frame, textvariable=abs_y, font=large_font).grid(
    row=1, column=1, pady=10)

# Move Frame
move_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
main_widgets.append(move_frame)
move_frame.grid(row=2, column=0, rowspan=1, columnspan=1,
                padx=10, pady=10, sticky="nsew")
for i in range(2):
    move_frame.grid_rowconfigure(i, weight=1)
    move_frame.grid_columnconfigure(i, weight=1)
move_frame.grid_rowconfigure(2, weight=1)
move_frame.grid_rowconfigure(3, weight=1)
entry_move_x = tk.Entry(move_frame, font=large_font,
                        width=10, justify='center')
entry_move_x.grid(row=0, column=0, pady=10)

move_x_button = tk.Button(move_frame, text='Move X',
                          command=move_x, font=large_font)
move_x_button.grid(row=0, column=1, pady=10)

entry_move_y = tk.Entry(move_frame, font=large_font,
                        width=10, justify='center')
entry_move_y.grid(row=1, column=0, pady=10)

move_y_button = tk.Button(move_frame, text='Move Y',
                          command=move_y, font=large_font)
move_y_button.grid(row=1, column=1, pady=10)

home_button = tk.Button(move_frame, text='Go to 0',
                        command=go_to_home_gui, font=large_font)
home_button.grid(row=2, columnspan=2, column=0, pady=10)

lock_button = tk.Button(move_frame, text='Set 0 and Lock',
                        command=toggle_lock, font=large_font)
lock_button.grid(row=3, columnspan=2, column=0, pady=10)
# Subgrid 3: 4x1 grid
scan_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
main_widgets.append(scan_frame)
scan_frame.grid(row=4, column=0, rowspan=2, padx=3, pady=3, sticky="nsew")
for i in range(4):
    scan_frame.grid_rowconfigure(i, weight=1)
scan_frame.grid_columnconfigure(0, weight=1)
scan_frame.grid_columnconfigure(1, weight=1)
tk.Label(scan_frame, text="Scan Range X (mm)",
         font=medium_font).grid(row=0, column=0, pady=10)
entry_scan_range_x = tk.Entry(scan_frame, font=large_font)
entry_scan_range_x.grid(row=0, column=1, pady=10)
tk.Label(scan_frame, text="Scan Range Y (mm)",
         font=medium_font).grid(row=1, column=0, pady=10)
entry_scan_range_y = tk.Entry(scan_frame, font=medium_font)
entry_scan_range_y.grid(row=1, column=1, pady=10)
tk.Label(scan_frame, text="Scan Points X",
         font=medium_font).grid(row=2, column=0, pady=10)
entry_scan_points_x = tk.Entry(scan_frame, font=medium_font)
entry_scan_points_x.grid(row=2, column=1, pady=10)
tk.Label(scan_frame, text="Scan Points Y",
         font=medium_font).grid(row=3, column=0, pady=10)
entry_scan_points_y = tk.Entry(scan_frame, font=medium_font)
entry_scan_points_y.grid(row=3, column=1, pady=10)

# Subgrid 4: 4x2 grid
freq_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
main_widgets.append(freq_frame)
freq_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=10, sticky="nsew")
for i in range(3):
    freq_frame.grid_rowconfigure(i, weight=1)
for i in range(2):
    freq_frame.grid_columnconfigure(i, weight=1)
tk.Label(freq_frame, text="Start\nFreq (GHz)",
         font=large_font).grid(row=0, column=0, pady=10)
tk.Label(freq_frame, text="Stop\nFreq (GHz)",
         font=large_font).grid(row=1, column=0, pady=10)
tk.Label(freq_frame, text="Number of Points",
         font=large_font).grid(row=2, column=0, pady=10)
entry_start_freq = tk.Entry(freq_frame, font=large_font)
entry_stop_freq = tk.Entry(freq_frame, font=large_font)
entry_num_points = tk.Entry(freq_frame, font=large_font)
entry_start_freq.grid(row=0, column=1, pady=10)
entry_stop_freq.grid(row=1, column=1, pady=10)
entry_num_points.grid(row=2, column=1, pady=10)

# Subgrid 3: 4x1 grid
measure_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
main_widgets.append(measure_frame)
measure_frame.grid(row=4, column=2, rowspan=2, padx=3, pady=3, sticky="nsew")
for i in range(5):
    measure_frame.grid_rowconfigure(i, weight=1)
measure_frame.grid_columnconfigure(0, weight=1)
tk.Button(measure_frame, text='Start Measurement', command=start_measurement,
          font=large_font).grid(row=0, column=0, pady=10)

tk.Button(measure_frame, text='STOP MACHINE', command=stop_machine,
          font=large_font, bg='red').grid(row=1, column=0, pady=10)
tk.Button(measure_frame, text='RESET MACHINE', command=reset_machine,
          font=large_font, bg='grey').grid(row=2, column=0, pady=10)

# Add progress bar and label
progress_bar = ttk.Progressbar(
    measure_frame, orient='horizontal', length=400, mode='determinate')
progress_label = tk.StringVar()
progress_label.set("")
progress_bar_label = tk.Label(
    measure_frame, textvariable=progress_label, font=large_font)

# Add percentage label
progress_percentage = tk.StringVar()
progress_percentage.set("0%")
percentage_label = tk.Label(
    measure_frame, textvariable=progress_percentage, font=large_font)

# Add download button
download_button = tk.Button(
    measure_frame, text="Download CSV", command=download_csv, font=large_font)
download_button.grid_remove()  # Initially hide the download button

# Initially hide progress bar and labels
progress_bar.grid_remove()
progress_bar_label.grid_remove()
percentage_label.grid_remove()

# Hide main UI components initially
for widget in main_widgets:
    widget.grid_remove()

root.mainloop()
