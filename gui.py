
import tkinter as tk
from tkinter import font
from tkinter import ttk
import threading
from cnc_vna_automate import run_measurement
import os
import subprocess


def start_measurement():
    start_freq = float(entry_start_freq.get())
    stop_freq = float(entry_stop_freq.get())
    num_points = int(entry_num_points.get())
    progress_bar['value'] = 0  # Reset progress bar
    progress_label.set("Running...")
    progress_percentage.set("0%")
    progress_bar.grid(row=4, column=0, columnspan=2,
                      pady=20)  # Show progress bar
    # Show progress label
    progress_bar_label.grid(row=5, column=0, columnspan=2)
    # Show percentage label
    percentage_label.grid(row=6, column=0, columnspan=2)
    thread = threading.Thread(target=run_measurement_with_update, args=(
        start_freq, stop_freq, num_points, progress_bar, progress_label, progress_percentage))
    thread.start()


def run_measurement_with_update(start_freq, stop_freq, num_points, progress_bar, progress_label, progress_percentage):
    def update_progress(value):
        progress_bar['value'] = value
        progress_bar.update_idletasks()
        progress_percentage.set(f"{int(value)}%")

    run_measurement(start_freq, stop_freq, num_points,
                    progress_bar, update_progress)
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
    update_position_display()


def move_y():
    y_distance = float(entry_move_y.get())
    # Add code to move the CNC machine by y_distance
    update_position_display()


def set_zero():
    # Add code to set the CNC machine position to (0, 0)
    update_position_display()


def update_position_display():
    # Update the display table with the absolute X and Y positions
    abs_x.set("Updated X")  # Replace "Updated X" with the actual X position
    abs_y.set("Updated Y")  # Replace "Updated Y" with the actual Y position


root = tk.Tk()
root.title("VNA and CNC Controller")

# Define a large font
large_font = font.Font(family="Helvetica", size=18, weight="bold")

# Center the window on the screen
window_width = 800
window_height = 700
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# Configure the grid to center the widgets
for i in range(16):
    root.grid_rowconfigure(i, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Create and place labels and entries with large font
tk.Label(root, text="Start Frequency (GHz)",
         font=large_font).grid(row=0, column=0, pady=10)
tk.Label(root, text="Stop Frequency (GHz)",
         font=large_font).grid(row=1, column=0, pady=10)
tk.Label(root, text="Number of Points", font=large_font).grid(
    row=2, column=0, pady=10)

entry_start_freq = tk.Entry(root, font=large_font)
entry_stop_freq = tk.Entry(root, font=large_font)
entry_num_points = tk.Entry(root, font=large_font)

entry_start_freq.grid(row=0, column=1, pady=10)
entry_stop_freq.grid(row=1, column=1, pady=10)
entry_num_points.grid(row=2, column=1, pady=10)

tk.Button(root, text='Start Measurement', command=start_measurement,
          font=large_font).grid(row=3, column=1, pady=20)

# Add progress bar and label
progress_bar = ttk.Progressbar(
    root, orient='horizontal', length=400, mode='determinate')
progress_label = tk.StringVar()
progress_label.set("")
progress_bar_label = tk.Label(
    root, textvariable=progress_label, font=large_font)

# Add percentage label
progress_percentage = tk.StringVar()
progress_percentage.set("0%")
percentage_label = tk.Label(
    root, textvariable=progress_percentage, font=large_font)

# Add download button
download_button = tk.Button(
    root, text="Download CSV", command=download_csv, font=large_font)
download_button.grid_remove()  # Initially hide the download button

# Initially hide progress bar and labels
progress_bar.grid_remove()
progress_bar_label.grid_remove()
percentage_label.grid_remove()

# Add move and set zero buttons and entries
tk.Label(root, text="Move X (mm)", font=large_font).grid(
    row=7, column=0, pady=10)
entry_move_x = tk.Entry(root, font=large_font)
entry_move_x.grid(row=7, column=1, pady=10)
tk.Button(root, text='Move X', command=move_x,
          font=large_font).grid(row=8, column=1, pady=10)

tk.Label(root, text="Move Y (mm)", font=large_font).grid(
    row=9, column=0, pady=10)
entry_move_y = tk.Entry(root, font=large_font)
entry_move_y.grid(row=9, column=1, pady=10)
tk.Button(root, text='Move Y', command=move_y,
          font=large_font).grid(row=10, column=1, pady=10)

tk.Button(root, text='Set 0', command=set_zero,
          font=large_font).grid(row=11, column=1, pady=10)

# Display table for absolute X and Y positions
tk.Label(root, text="Absolute X", font=large_font).grid(
    row=12, column=0, pady=10)
abs_x = tk.StringVar()
abs_x.set("0")
tk.Label(root, textvariable=abs_x, font=large_font).grid(
    row=12, column=1, pady=10)

tk.Label(root, text="Absolute Y", font=large_font).grid(
    row=13, column=0, pady=10)
abs_y = tk.StringVar()
abs_y.set("0")
tk.Label(root, textvariable=abs_y, font=large_font).grid(
    row=13, column=1, pady=10)

# Add scan range and scan points entries
tk.Label(root, text="Scan Range X (mm)", font=large_font).grid(
    row=14, column=0, pady=10)
entry_scan_range_x = tk.Entry(root, font=large_font)
entry_scan_range_x.grid(row=14, column=1, pady=10)

tk.Label(root, text="Scan Range Y (mm)", font=large_font).grid(
    row=15, column=0, pady=10)
entry_scan_range_y = tk.Entry(root, font=large_font)
entry_scan_range_y.grid(row=15, column=1, pady=10)

tk.Label(root, text="Scan Points X", font=large_font).grid(
    row=16, column=0, pady=10)
entry_scan_points_x = tk.Entry(root, font=large_font)
entry_scan_points_x.grid(row=16, column=1, pady=10)

tk.Label(root, text="Scan Points Y", font=large_font).grid(
    row=17, column=0, pady=10)
entry_scan_points_y = tk.Entry(root, font=large_font)
entry_scan_points_y.grid(row=17, column=1, pady=10)

root.mainloop()
