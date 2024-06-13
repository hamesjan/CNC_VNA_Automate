import tkinter as tk


def start_measurement():
    start_freq = float(entry_start_freq.get())
    stop_freq = float(entry_stop_freq.get())
    num_points = int(entry_num_points.get())
    run_measurement(start_freq, stop_freq, num_points)


root = tk.Tk()
root.title("VNA and CNC Controller")

tk.Label(root, text="Start Frequency (Hz)").grid(row=0)
tk.Label(root, text="Stop Frequency (Hz)").grid(row=1)
tk.Label(root, text="Number of Points").grid(row=2)

entry_start_freq = tk.Entry(root)
entry_stop_freq = tk.Entry(root)
entry_num_points = tk.Entry(root)

entry_start_freq.grid(row=0, column=1)
entry_stop_freq.grid(row=1, column=1)
entry_num_points.grid(row=2, column=1)

tk.Button(root, text='Start Measurement', command=start_measurement).grid(
    row=3, column=1, sticky=tk.W, pady=4)

root.mainloop()
