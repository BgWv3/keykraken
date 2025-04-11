import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, PhotoImage
import pyautogui
from PIL import ImageGrab
import json
import os
import time
import threading
from pynput import mouse
from pynput import keyboard
from pynput.mouse import Listener as MouseListener
import ast # For safely evaluating coordinate strings

# --- Constants ---
SCENARIO_FOLDER = "scenarios"
DEFAULT_DELAY = 0.5
DEFAULT_CONFIDENCE = 0.9
APP_VERSION = "1.2" # Incremented version
# Supported action types
ACTION_TYPES = [
    "click", # Single type for click, button specified separately
    "image",
    "typewrite",
    "press",
    "hotkey",
    "scroll",
    "drag",
    "delay"
]

# --- Global Variables ---
recording_active = False
listener_thread = None
listener_instance = None
execution_thread = None
stop_execution_flag = False
root = None
# --- Edit Frame Widgets (declared globally for easier access) ---
step_name_entry = None
step_type_combobox = None
step_value_entry = None
step_delay_entry = None
value_hint_label = None
click_button_var = None # Variable for radio buttons
left_click_radio = None
right_click_radio = None
click_options_frame = None # Frame to hold radio buttons
tree = None
status_label = None
progress_bar = None
loop_entry = None
record_button = None
stop_record_button = None
run_button = None
stop_run_button = None
# --- End Global Widget Declarations ---


# --- Utility Functions ---
def create_scenario_folder():
    if not os.path.exists(SCENARIO_FOLDER):
        try:
            os.makedirs(SCENARIO_FOLDER)
            print(f"Created folder: {SCENARIO_FOLDER}")
        except OSError as e:
            messagebox.showerror("Error", f"Could not create scenario folder: {e}")
            return False
    return True

def validate_float(P):
    if P == "" or P == ".": return True
    try: float(P); return True
    except ValueError: return False

def validate_int(P):
    if P == "": return True
    try: int(P); return True
    except ValueError: return False

def parse_coords(coord_str):
    try:
        coords = ast.literal_eval(coord_str)
        if isinstance(coords, (list, tuple)) and len(coords) == 2 and all(isinstance(n, int) for n in coords):
            return list(coords)
    except (ValueError, SyntaxError, TypeError):
        try:
            parts = [p.strip() for p in coord_str.split(',')]
            if len(parts) == 2: return [int(parts[0]), int(parts[1])]
        except ValueError: pass
    return None

def parse_drag_coords(drag_str):
     parts = drag_str.split(';')
     if len(parts) == 2:
         start_coords = parse_coords(parts[0])
         end_coords = parse_coords(parts[1])
         if start_coords and end_coords:
             return {"start": start_coords, "end": end_coords}
     return None

def capture_screen_region():
    """Capture a region of the screen and return the saved image path."""
    messagebox.showinfo("Capture Region", "After clicking OK, select a region of the screen.")
    try:
        # Use pyautogui to capture the screen
        screenshot = pyautogui.screenshot()
        screenshot.show()  # Show the screenshot for reference

        # Use ImageGrab to allow the user to select a region
        region = ImageGrab.grab(bbox=None)  # Replace with a region selection tool if needed
        create_scenario_folder()
        image_path = os.path.join(SCENARIO_FOLDER, f"capture_{int(time.time())}.png")
        region.save(image_path)
        return image_path
    except Exception as e:
        messagebox.showerror("Capture Error", f"Failed to capture screen region:\n{e}")
        return None

def capture_scroll_action():
    """Capture cumulative scroll amount by listening to mouse scroll events until the user presses a Stop button."""
    global stop_flag, scroll_data
    scroll_data = {"total_scroll": 0}
    stop_flag = {"stop": False}

    def on_scroll(x, y, dx, dy):
        scroll_data["total_scroll"] += dy  # Accumulate the scroll amount
        print(f"Captured scroll: dx={dx}, dy={dy}, total={scroll_data['total_scroll']}")

    def start_scroll_listener():
        # Start the mouse listener
        with MouseListener(on_scroll=on_scroll) as mouse_listener:
            while not stop_flag["stop"]:
                time.sleep(0.1)  # Keep the thread alive
            mouse_listener.stop()  # Stop the mouse listener

    # Update button states
    start_scroll_button.config(state=tk.DISABLED)
    stop_scroll_button.config(state=tk.NORMAL)

    # Start the scroll listener in a separate thread
    threading.Thread(target=start_scroll_listener, daemon=True).start()

    messagebox.showinfo("Capture Scroll", "Scroll up or down to capture the scroll amount. Click 'Stop Scroll' to finish.")

def stop_scroll_listener():
    """Stop the scroll listener and finalize the scroll value."""
    global stop_flag, scroll_data, stop_scroll_button, start_scroll_button
    stop_flag["stop"] = True
    finalize_scroll()

def finalize_scroll():
    """Finalize the scroll value and update the input field."""
    root.after(0, lambda: step_value_entry.delete(0, tk.END))  # Clear the entry field
    root.after(0, lambda: step_value_entry.insert(0, str(scroll_data["total_scroll"])))  # Insert the total scroll value
    stop_scroll_button.config(state=tk.DISABLED)  # Disable the Stop Scroll button
    start_scroll_button.config(state=tk.NORMAL)  # Re-enable the Start Scroll button

def capture_drag_action():
    """Capture drag start and end coordinates by listening to mouse events in a separate thread."""
    drag_data = {"start": None, "end": None}

    def on_click(x, y, button, pressed):
        if pressed and drag_data["start"] is None:
            drag_data["start"] = (x, y)
            print(f"Drag start: {drag_data['start']}")
        elif not pressed and drag_data["start"] is not None:
            drag_data["end"] = (x, y)
            print(f"Drag end: {drag_data['end']}")
            drag_value = f"{drag_data['start']};{drag_data['end']}"
            root.after(0, lambda: step_value_entry.delete(0, tk.END))  # Clear the entry field
            root.after(0, lambda: step_value_entry.insert(0, drag_value))  # Insert the captured drag value
            return False  # Stop listener after capturing drag action

    def start_drag_listener():
        with MouseListener(on_click=on_click) as listener:
            listener.join()

    messagebox.showinfo("Capture Drag", "Click and drag to capture start and end coordinates.")
    threading.Thread(target=start_drag_listener, daemon=True).start()

# --- Recording Logic ---
def on_click(x, y, button, pressed):
    """Callback function for mouse listener - now records button type."""
    global tree, root
    # Only record on button press
    if not pressed or not recording_active:
        return

    click_button_type = None
    if button == mouse.Button.left:
        click_button_type = "left"
    elif button == mouse.Button.right:
        click_button_type = "right"
    # Ignore other buttons (middle, etc.) for now
    else:
        return

    coords = (int(x), int(y))
    print(f"Recorded {click_button_type} click at: {coords}")

    new_step = {
        "name": f"{click_button_type.capitalize()} Click Step {len(tree.get_children()) + 1}", # Default name
        "type": "click",
        "value": list(coords), # Value is just coordinates
        "button": click_button_type, # Store the button clicked
        "delay": DEFAULT_DELAY
    }
    # Safely add step to treeview from the listener thread
    if root:
         root.after(0, add_step_to_treeview, new_step) # Use root.after for thread safety

def start_recording_thread():
    global listener_thread, listener_instance, recording_active, root, record_button, stop_record_button, status_label, execution_thread

    if recording_active:
        messagebox.showwarning("Recording", "Already recording.")
        return

    if execution_thread and execution_thread.is_alive():
        messagebox.showwarning("Busy", "Cannot record while scenario is running.")
        return

    # Stop any existing listener thread before starting a new one
    if listener_thread and listener_thread.is_alive():
        print("Stopping existing listener thread...")
        recording_active = False  # This will stop the existing listener
        if listener_instance:
            listener_instance.stop()  # Explicitly stop the listener
        listener_thread.join()  # Wait for the thread to finish

    recording_active = True
    if root:
        status_label.config(text="Status: Recording... (Left/Right click to record)")
        record_button.config(state=tk.DISABLED)
        stop_record_button.config(state=tk.NORMAL)

    def listener_func():
        # pynput listener in a separate thread
        global listener_instance
        with mouse.Listener(on_click=on_click) as listener:
            listener_instance = listener  # Store the listener instance
            listener.join()  # Wait until listener.stop() is called or thread exits

    listener_thread = threading.Thread(target=listener_func, daemon=True)
    listener_thread.start()
    print("Listener thread started.")

def stop_recording():
    global recording_active, listener_instance, listener_thread, root, record_button, stop_record_button, status_label
    if not recording_active:
        return

    recording_active = False
    if listener_instance:
        print("Stopping listener instance...")
        listener_instance.stop()  # Explicitly stop the listener
        listener_instance = None  # Clear the reference

    if listener_thread and listener_thread.is_alive():
        listener_thread.join()  # Wait for the thread to finish

    print("Listener stopped.")
    if root:
        status_label.config(text="Status: Recording stopped.")
        record_button.config(state=tk.NORMAL)
        stop_record_button.config(state=tk.DISABLED)
        messagebox.showinfo("Recording", "Recording stopped.")

# --- Scenario Execution Logic ---
def run_scenario():
    global execution_thread, stop_execution_flag, root, run_button, stop_run_button, progress_bar, loop_entry
    if execution_thread and execution_thread.is_alive():
        messagebox.showwarning("Busy", "Another scenario is already running.")
        return
    if recording_active:
        messagebox.showwarning("Busy", "Cannot run scenario while recording.")
        return

    steps = get_steps_from_treeview()
    if not steps:
        messagebox.showwarning("Empty Scenario", "No steps to execute.")
        return

    try: loops = int(loop_entry.get()); assert loops > 0
    except: messagebox.showerror("Invalid Input", "Loops must be a positive integer."); return

    stop_execution_flag = False
    run_button.config(state=tk.DISABLED)
    stop_run_button.config(state=tk.NORMAL)
    progress_bar['value'] = 0
    progress_bar['maximum'] = len(steps) * loops

    execution_thread = threading.Thread(target=_automation_thread_func, args=(steps, loops), daemon=True)
    execution_thread.start()

def _automation_thread_func(steps, loops):
    global stop_execution_flag, root
    total_steps_executed = 0
    current_loop = 0
    current_step_index = 0
    try:
        for i in range(loops):
            current_loop = i + 1
            if stop_execution_flag:
                break
            root.after(0, update_status, f"Status: Running loop {current_loop}/{loops}...")
            for j, step in enumerate(steps):
                current_step_index = j + 1
                if stop_execution_flag:
                    break
                step_name = step.get('name', 'Unnamed')
                step_type = step.get('type', 'N/A')
                root.after(0, update_status, f"Status: Loop {current_loop}/{loops}, Step {current_step_index}/{len(steps)} ({step_name})")
                root.after(0, highlight_step, j)  # Highlight current step

                # 1. Delay with Countdown Timer
                delay = float(step.get('delay', 0.0))
                start_time = time.time()
                while time.time() - start_time < delay:
                    if stop_execution_flag:
                        break
                    remaining_time = delay - (time.time() - start_time)
                    root.after(0, update_status, f"Status: Loop {current_loop}/{loops}, Step {current_step_index}/{len(steps)} ({step_name}) - Waiting {remaining_time:.1f}s")
                    time.sleep(0.1)  # Update every 0.1 seconds
                if stop_execution_flag:
                    break

                # 2. Action
                action_value = step.get("value")
                print(f"  Executing: {step_name} ({step_type}) Val={action_value}")
                try:
                    time.sleep(0.05)  # Tiny pause
                    if step_type == "click":
                        coords = step.get("value_parsed")
                        button_type = step.get("button", "left")  # Default to left
                        if coords:
                            print(f"    Clicking {button_type} at {coords}")
                            pyautogui.click(x=coords[0], y=coords[1], button=button_type)
                        else:
                            print(f"    WARNING: Invalid coords for click: {action_value}")

                    elif step_type == "image":
                        # Retry logic for image detection
                        image_path = str(action_value)
                        confidence = float(step.get('confidence', DEFAULT_CONFIDENCE))
                        full_path = image_path
                        if not os.path.isabs(full_path) and os.path.exists(os.path.join(SCENARIO_FOLDER, full_path)):
                            full_path = os.path.join(SCENARIO_FOLDER, full_path)
                        if not os.path.exists(full_path):
                            raise FileNotFoundError(f"Image not found: {full_path}")

                        print(f"    Searching for image: {full_path} (conf={confidence})")
                        location = None
                        for attempt in range(3):  # Retry up to 3 times
                            location = pyautogui.locateCenterOnScreen(full_path, confidence=confidence)
                            if location:
                                print(f"    Image found at: {location}. Clicking.")
                                pyautogui.click(location)  # Default left click
                                break
                            else:
                                print(f"    Attempt {attempt + 1}: Image not found. Retrying...")
                                time.sleep(1)  # Wait before retrying
                        if not location:
                            print(f"    WARNING: Image not found after 3 attempts: {image_path}")
                            raise Exception("Image not found after 3 attempts")

                    elif step_type == "typewrite":
                        text = str(action_value)
                        interval = float(step.get('interval', 0.01))
                        print(f"    Typing: '{text}' (interval={interval}s)")
                        pyautogui.write(text, interval=interval)

                    elif step_type == "press":
                        key = str(action_value).lower()
                        if key in pyautogui.KEYBOARD_KEYS:
                            print(f"    Pressing key: {key}")
                            pyautogui.press(key)
                        else:
                            print(f"    WARNING: Invalid key for press: {action_value}")

                    elif step_type == "hotkey":
                        keys_str = str(action_value).lower().replace(' ', '')
                        keys = keys_str.split(',')
                        valid_keys = [k for k in keys if k in pyautogui.KEYBOARD_KEYS]
                        if len(valid_keys) == len(keys) and valid_keys:
                            print(f"    Hotkey: {valid_keys}")
                            pyautogui.hotkey(*valid_keys)
                        else:
                            print(f"    WARNING: Invalid keys in hotkey: {action_value}")

                    elif step_type == "scroll":
                        amount = step.get("value_parsed")
                        if amount is not None:
                            print(f"    Scrolling: {amount}")
                            pyautogui.scroll(amount)
                        else:
                            print(f"    WARNING: Invalid scroll amount: {action_value}")

                    elif step_type == "drag":
                        drag_coords = step.get("value_parsed")
                        if drag_coords:
                            start = drag_coords["start"]
                            end = drag_coords["end"]
                            duration = float(step.get('duration', 0.5))
                            print(f"    Dragging from {start} to {end} ({duration}s)")
                            pyautogui.moveTo(start[0], start[1])
                            pyautogui.dragTo(end[0], end[1], duration=duration)
                        else:
                            print(f"    WARNING: Invalid coords for drag: {action_value}")

                    elif step_type == "delay":
                        duration = step.get("value_parsed")
                        if duration is not None and duration > 0:
                            print(f"    Explicit delay: {duration}s")
                            start_time = time.time()
                            while time.time() - start_time < duration:
                                if stop_execution_flag:
                                    break
                                time.sleep(0.05)
                        else:
                            print(f"    WARNING: Invalid duration for delay: {action_value}")
                    else:
                        print(f"    WARNING: Unknown step type: {step_type}")

                except Exception as e:
                    print(f"  ERROR executing {step_name}: {e}")
                    root.after(0, update_status, f"Status: ERROR step {current_step_index}")
                    stop_execution_flag = True

                total_steps_executed += 1
                root.after(0, progress_bar.config, {'value': total_steps_executed})
                root.after(0, root.update_idletasks)
            if stop_execution_flag:
                break  # Break outer loop

        # --- Finished ---
        final_status = "Status: Ready"
        if not stop_execution_flag:
            final_status = "Status: Scenario completed."
            print(final_status)
            root.after(0, messagebox.showinfo, "Complete", "Scenario finished.")
        else:
            final_status = f"Status: Stopped (Loop {current_loop}, Step {current_step_index})."
            print("Execution stopped.")
        root.after(0, update_status, final_status)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        root.after(0, update_status, f"Status: FATAL ERROR")
        root.after(0, messagebox.showerror, "Error", f"Unexpected error: {e}")
    finally:
        root.after(0, _reset_execution_controls)
        root.after(0, clear_highlight)

def update_status(message):
    if root and status_label: status_label.config(text=message)

def _reset_execution_controls():
    if root: run_button.config(state=tk.NORMAL); stop_run_button.config(state=tk.DISABLED); progress_bar['value'] = 0

def stop_execution():
    global stop_execution_flag, execution_thread
    if execution_thread and execution_thread.is_alive():
        print("Stop signal sent."); stop_execution_flag = True
        if root: stop_run_button.config(state=tk.DISABLED); update_status("Status: Stopping...")
    else: print("No execution thread running.")

# --- GUI Functions ---
def setup_gui(app_root):
    global root, tree, status_label, progress_bar, loop_entry, record_button, stop_record_button
    global run_button, stop_run_button
    global step_name_entry, step_type_combobox, step_value_entry, step_delay_entry, value_hint_label
    global click_button_var, left_click_radio, right_click_radio, click_options_frame
    global description_text, start_scroll_button, stop_scroll_button  # Add global variables for scroll buttons

    root = app_root
    root.title(f"KeyKraken v{APP_VERSION}")
    root.geometry("1250x750")  # Adjusted size to accommodate the description window

    # Create a ttk.Style object
    style = ttk.Style()

    # Define a custom style for buttons
    style.configure("Custom.TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"))
    style.map("Custom.TButton",
              background=[("active", "#45a049")],  # Change color when the button is active
              foreground=[("disabled", "gray")])  # Change text color when disabled

    # Set custom icon
    try:
        icon_path = os.path.join("images", "icon.png")
        app_icon = PhotoImage(file=icon_path)
        root.iconphoto(True, app_icon)
    except Exception as e:
        print(f"Error loading icon: {e}")

    vcmd_float = (root.register(validate_float), '%P')
    vcmd_int = (root.register(validate_int), '%P')

    # --- Frames ---
    top_frame = ttk.Frame(root, padding="5")
    top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))

    tree_frame = ttk.Frame(root, padding="5")
    tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

    edit_frame = ttk.Frame(root, padding="10")
    edit_frame.pack(side=tk.TOP, fill=tk.X, padx=5)

    status_frame = ttk.Frame(root, padding=(5, 2), relief=tk.SUNKEN)
    status_frame.pack(side=tk.BOTTOM, fill=tk.X)

    description_frame = ttk.Frame(root, padding="10")
    description_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

    # --- Top Frame ---
    ttk.Button(top_frame, text="New", command=new_scenario).pack(side=tk.LEFT, padx=2)
    ttk.Button(top_frame, text="Load", command=load_scenario).pack(side=tk.LEFT, padx=2)
    ttk.Button(top_frame, text="Save", command=save_scenario).pack(side=tk.LEFT, padx=2)
    ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
    record_button = ttk.Button(top_frame, text="Record Clicks", command=start_recording_thread)
    record_button.pack(side=tk.LEFT, padx=2)
    stop_record_button = ttk.Button(top_frame, text="Stop Recording", command=stop_recording, state=tk.DISABLED)
    stop_record_button.pack(side=tk.LEFT, padx=2)
    ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
    # --- Run Scenario Buttons ---
    run_button = ttk.Button(top_frame, text="Run Scenario", command=run_scenario)
    run_button.pack(side=tk.LEFT, padx=2)
    stop_run_button = ttk.Button(top_frame, text="Stop Scenario", command=stop_execution, state=tk.DISABLED)
    stop_run_button.pack(side=tk.LEFT, padx=2)

    # --- Treeview Frame ---
    tree_container = ttk.Frame(tree_frame)
    tree_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    move_button_frame = ttk.Frame(tree_frame)
    move_button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

    columns = ("#", "Name", "Type", "Value / Button", "Delay (s)")
    tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")
    tree.heading("#", text="#", command=lambda: sort_treeview_column(tree, "#", False))
    tree.heading("Name", text="Step Name", command=lambda: sort_treeview_column(tree, "Name", False))
    tree.heading("Type", text="Action Type", command=lambda: sort_treeview_column(tree, "Type", False))
    tree.heading("Value / Button", text="Value / Click Button", command=lambda: sort_treeview_column(tree, "Value / Button", False))
    tree.heading("Delay (s)", text="Delay Before", command=lambda: sort_treeview_column(tree, "Delay (s)", False))

    tree.column("#", width=40, stretch=tk.NO, anchor=tk.CENTER)
    tree.column("Name", width=150)
    tree.column("Type", width=80, stretch=tk.NO)
    tree.column("Value / Button", width=250)
    tree.column("Delay (s)", width=80, stretch=tk.NO, anchor=tk.E)

    vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    hsb.pack(side=tk.BOTTOM, fill=tk.X)
    tree.bind('<<TreeviewSelect>>', on_tree_select)
    tree.tag_configure('highlight', background='lightblue')

    ttk.Button(move_button_frame, text="▲", width=5, command=move_step_up).pack(pady=5, padx=2)
    ttk.Button(move_button_frame, text="▼", width=5, command=move_step_down).pack(pady=5, padx=2)
    ttk.Separator(move_button_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
    # Add/Edit/Remove Buttons
    ttk.Button(move_button_frame, text="Add Step", command=add_new_step).pack(pady=5, padx=2)
    ttk.Button(move_button_frame, text="Update Step", command=update_selected_step).pack(pady=5, padx=2)
    ttk.Button(move_button_frame, text="Remove Step", command=remove_selected_step).pack(pady=5, padx=2)
    ttk.Separator(move_button_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
    # Scroll Calculator Buttons
    start_scroll_button = ttk.Button(move_button_frame, text="Start Scroll", command=capture_scroll_action, state=tk.DISABLED)
    start_scroll_button.pack(pady=5, padx=2)
    stop_scroll_button = ttk.Button(move_button_frame, text="Stop Scroll", command=stop_scroll_listener, state=tk.DISABLED)
    stop_scroll_button.pack(pady=5, padx=2)
    ttk.Separator(move_button_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
    # Click Options Buttons
    click_button_var = tk.StringVar(value="left")
    left_click_radio = ttk.Radiobutton(move_button_frame, text="Left Click", variable=click_button_var, value="left", state=tk.DISABLED)
    left_click_radio.pack(pady=5, padx=2)

    right_click_radio = ttk.Radiobutton(move_button_frame, text="Right Click", variable=click_button_var, value="right", state=tk.DISABLED)
    right_click_radio.pack(pady=5, padx=2)


    # --- Edit Frame Widgets ---
    ttk.Label(edit_frame, text="Step Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
    step_name_entry = ttk.Entry(edit_frame, width=38)
    step_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

    ttk.Label(edit_frame, text="Action Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
    step_type_combobox = ttk.Combobox(edit_frame, values=ACTION_TYPES, state="readonly", width=35)
    step_type_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
    step_type_combobox.bind("<<ComboboxSelected>>", on_action_type_change)

    ttk.Label(edit_frame, text="Value:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
    step_value_entry = ttk.Entry(edit_frame, width=38)
    step_value_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

    ttk.Button(edit_frame, text="Browse", command=browse_for_value).grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)

    value_hint_label = ttk.Label(edit_frame, text="Hint: ", anchor=tk.W)
    value_hint_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

    ttk.Label(edit_frame, text="Delay (s):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
    step_delay_entry = ttk.Entry(edit_frame, validate="key", validatecommand=vcmd_float, width=10)
    step_delay_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
 
    ttk.Label(edit_frame, text="Loops:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
    loop_entry = ttk.Entry(edit_frame, validate="key", validatecommand=vcmd_int, width=10)
    loop_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=2)
    loop_entry.insert(0, "1")  # Default to 1 loop

    # --- Description Frame ---
    ttk.Label(description_frame, text="Scenario Description:").pack(anchor=tk.W, padx=5, pady=(0, 5))
    description_text = tk.Text(description_frame, wrap=tk.WORD, height=20, width=40)
    description_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Status Bar ---
    status_label = ttk.Label(status_frame, text="Status: Ready", anchor=tk.W)
    status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
    progress_bar = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=150, mode='determinate')
    progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)

    clear_edit_fields()  # Initial setup

def clear_edit_fields():
    step_name_entry.delete(0, tk.END); step_type_combobox.set('')
    step_value_entry.delete(0, tk.END); step_delay_entry.delete(0, tk.END)
    step_delay_entry.insert(0, str(DEFAULT_DELAY))
    click_button_var.set("left") # Reset click choice
    on_action_type_change() # Update hints and hide click options

def on_action_type_change(event=None):
    """Handles changes in the Action Type combobox."""
    action_type = step_type_combobox.get()
    update_value_hint(action_type)

    # Enable/disable scroll buttons
    if action_type == "scroll":
        start_scroll_button.config(state=tk.NORMAL)
        stop_scroll_button.config(state=tk.DISABLED)
    else:
        start_scroll_button.config(state=tk.DISABLED)
        stop_scroll_button.config(state=tk.DISABLED)

    # Enable/disable click options
    if action_type == "click":
        left_click_radio.config(state=tk.NORMAL)
        right_click_radio.config(state=tk.NORMAL)
    else:
        left_click_radio.config(state=tk.DISABLED)
        right_click_radio.config(state=tk.DISABLED)

def update_value_hint(action_type):
    """Updates the hint label based on the selected action type."""
    hint = "Hint: "
    if action_type == "click":
        hint += "Enter coordinates e.g., [100, 200] or 'Record Clicks'."
    elif action_type == "image":
        hint += "Capture a region of the screen or select an image file."
    elif action_type == "typewrite":
        hint += "Enter text to type"
    elif action_type == "press":
        hint += "Enter single key name (e.g., enter, ctrl, a)"
    elif action_type == "hotkey":
        hint += "Enter keys separated by commas (e.g., ctrl,shift,s)"
    elif action_type == "scroll":
        hint += "Enter scroll amount (integer: + up, - down)"
    elif action_type == "drag":
        hint += "Enter start;end coords (e.g., [100,100];[500,500])"
    elif action_type == "delay":
        hint += "Enter delay duration in seconds (e.g., 5.0)"
    else:
        hint = ""
    value_hint_label.config(text=hint)

def browse_for_value():
    action_type = step_type_combobox.get()
    if action_type == "image":
        if messagebox.askyesno("Capture Image", "Would you like to capture a region of the screen?"):
            image_path = capture_screen_region()
            if image_path:
                step_value_entry.delete(0, tk.END)
                step_value_entry.insert(0, make_path_relative(image_path))
        else:
            filepath = filedialog.askopenfilename(
                title="Select Image File",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")],
                initialdir=SCENARIO_FOLDER
            )
            if filepath:
                step_value_entry.delete(0, tk.END)
                step_value_entry.insert(0, make_path_relative(filepath))
    elif action_type == "scroll":
        capture_scroll_action()
    elif action_type == "drag":
        capture_drag_action()
    else:
        messagebox.showinfo("Browse", "This action type does not support browsing.")

def make_path_relative(filepath):
     try:
        script_dir = os.path.dirname(os.path.abspath(__file__)); scenario_dir_abs = os.path.abspath(os.path.join(script_dir, SCENARIO_FOLDER))
        filepath_abs = os.path.abspath(filepath); common_path = os.path.commonpath([scenario_dir_abs, filepath_abs])
        if common_path == scenario_dir_abs: rel_path = os.path.relpath(filepath_abs, scenario_dir_abs); print(f"Relative path: {rel_path}"); return rel_path
        else: print(f"Outside scenario folder, absolute: {filepath_abs}"); return filepath_abs
     except ValueError: print(f"Cannot determine relative path, using absolute: {filepath}"); return os.path.abspath(filepath)

def on_tree_select(event=None):
    selected_items = tree.selection()
    if not selected_items: return
    item_id = selected_items[0]; item_data = tree.item(item_id, 'values')
    if not item_data or len(item_data) < 5: clear_edit_fields(); return

    _, step_name, step_type, value_button_str, step_delay = item_data
    step_name_entry.delete(0, tk.END); step_name_entry.insert(0, step_name)
    step_type_combobox.set(step_type); step_delay_entry.delete(0, tk.END); step_delay_entry.insert(0, step_delay)

    # Handle click type specifically to extract button and coords
    value_str = value_button_str # Default
    button_type = "left" # Default
    if step_type == "click":
        parts = value_button_str.split(' (') # Split value and button part
        if len(parts) == 2:
            value_str = parts[0].strip() # Get the coordinate part
            button_part = parts[1].strip(') ')
            if button_part.lower() in ["left", "right"]:
                button_type = button_part.lower()
        else: # Handle case where button wasn't stored correctly in display
            value_str = value_button_str

    step_value_entry.delete(0, tk.END); step_value_entry.insert(0, value_str)
    click_button_var.set(button_type) # Set radio button
    on_action_type_change() # Update hints and show/hide radio buttons

def add_new_step():
    step_name = step_name_entry.get().strip(); step_type = step_type_combobox.get()
    value_str = step_value_entry.get().strip(); delay_str = step_delay_entry.get().strip()
    button_type = click_button_var.get() # Get button choice

    if not step_name: step_name = f"New {step_type.capitalize()} Step"
    if not step_type: messagebox.showwarning("Missing Info", "Select Action Type."); return
    if step_type not in ["delay"] and not value_str: # Allow empty value only for delay? Maybe not. Require value for all.
        messagebox.showwarning("Missing Info", f"Enter Value for '{step_type}'."); return

    try: delay = float(delay_str if delay_str else "0.0"); assert delay >= 0
    except: messagebox.showerror("Invalid Input", "Delay must be a non-negative number."); return

    validation_error = validate_step_value(step_type, value_str, button_type)
    if validation_error: messagebox.showerror("Invalid Value", f"{validation_error}\nValue: '{value_str}'"); return

    new_step_data = {"name": step_name, "type": step_type, "value": value_str, "delay": delay}
    if step_type == "click": new_step_data["button"] = button_type # Add button info for clicks

    add_step_to_treeview(new_step_data)

def update_selected_step():
    selected_items = tree.selection()
    if not selected_items: messagebox.showwarning("No Selection", "Select step to update."); return
    item_id = selected_items[0]; item_index = tree.index(item_id)

    new_name = step_name_entry.get().strip(); new_type = step_type_combobox.get()
    new_value_str = step_value_entry.get().strip(); new_delay_str = step_delay_entry.get().strip()
    new_button_type = click_button_var.get() # Get selected button

    if not new_name: new_name = f"Updated Step"
    if not new_type: messagebox.showwarning("Missing Info", "Select Action Type."); return
    if not new_value_str: messagebox.showwarning("Missing Info", f"Enter Value for '{new_type}'."); return

    try: new_delay = float(new_delay_str if new_delay_str else "0.0"); assert new_delay >= 0
    except: messagebox.showerror("Invalid Input", "Delay must be non-negative."); return

    validation_error = validate_step_value(new_type, new_value_str, new_button_type)
    if validation_error: messagebox.showerror("Invalid Value", f"{validation_error}\nValue: '{new_value_str}'"); return

    # Format display value for treeview
    display_value = new_value_str
    if new_type == "click":
        display_value = f"{new_value_str} ({new_button_type.capitalize()})"

    tree.item(item_id, values=(item_index + 1, new_name, new_type, display_value, f"{new_delay:.2f}"))
    print(f"Updated step {item_index + 1}")

def remove_selected_step():
    selected_items = tree.selection()
    if not selected_items: messagebox.showwarning("No Selection", "Select step to remove."); return
    if messagebox.askyesno("Confirm", "Remove selected step?"):
        for item_id in selected_items: tree.delete(item_id)
        renumber_treeview(); clear_edit_fields()

def validate_step_value(step_type, value_str, button_type):
    """Includes button_type validation for clicks."""
    if step_type == "click":
        if parse_coords(value_str) is None: return "Click: Use format [x, y] or x, y."
        if button_type not in ["left", "right"]: return "Click: Invalid button type selected."
    elif step_type == "image":
        if not value_str: return "Image: Path cannot be empty."
    elif step_type == "typewrite": pass
    elif step_type == "press":
        if not value_str or value_str.lower() not in pyautogui.KEYBOARD_KEYS: return f"Press: Invalid key name '{value_str}'. See PyAutoGUI docs."
    elif step_type == "hotkey":
        keys = value_str.lower().replace(' ', '').split(',')
        if not keys or any(k not in pyautogui.KEYBOARD_KEYS for k in keys): return "Hotkey: Invalid key(s). Use comma-separated valid keys."
    elif step_type == "scroll":
        try: int(value_str)
        except ValueError: return "Scroll: Amount must be an integer."
    elif step_type == "drag":
         if parse_drag_coords(value_str) is None: return "Drag: Use format [x1,y1];[x2,y2] or x1,y1;x2,y2."
    elif step_type == "delay":
         try: duration = float(value_str); assert duration >= 0
         except: return "Delay: Duration must be a non-negative number."
    return None # OK

def add_step_to_treeview(step_data):
    if not root: return
    current_items = tree.get_children(); new_index = len(current_items)
    step_type = step_data.get("type", "N/A"); value = step_data.get("value", "")
    button = step_data.get("button", "left") # Get button if present
    delay = float(step_data.get('delay', 0.0)); name = step_data.get("name", "Unnamed")

    # Format value for display
    display_value = str(value)
    if step_type == "click":
        coords_str = f"[{value[0]}, {value[1]}]" if isinstance(value, list) else str(value)
        display_value = f"{coords_str} ({button.capitalize()})"

    new_iid = tree.insert("", tk.END, values=(new_index + 1, name, step_type, display_value, f"{delay:.2f}"))
    tree.see(new_iid)

def update_treeview(steps):
    if not root: return
    clear_highlight();
    for item in tree.get_children(): tree.delete(item)
    for i, step in enumerate(steps):
        value = step.get("value", "") # Raw value stored
        step_type = step.get("type", "N/A")
        button = step.get("button", "left") # Get button if it exists
        display_value = str(value)
        # Format display specifically for clicks
        if step_type == "click":
             coords_str = str(value) # Assume stored value is string coords like "[x, y]" or "x, y"
             parsed_coords = parse_coords(coords_str)
             if parsed_coords: # If parsing works, format nicely
                 coords_str = f"[{parsed_coords[0]}, {parsed_coords[1]}]"
             display_value = f"{coords_str} ({button.capitalize()})"
        elif step_type == "drag": # Format drag coords nicely too
             parsed_drag = parse_drag_coords(str(value))
             if parsed_drag: display_value = f"[{parsed_drag['start'][0]},{parsed_drag['start'][1]}];[{parsed_drag['end'][0]},{parsed_drag['end'][1]}]"

        tree.insert("", tk.END, iid=str(i), values=(
            i + 1, step.get("name", "Unnamed"), step_type,
            display_value, f"{float(step.get('delay', 0.0)):.2f}"
        ))

def renumber_treeview():
     children = tree.get_children()
     for i, item_id in enumerate(children):
         current_values = list(tree.item(item_id, 'values'))
         current_values[0] = i + 1
         tree.item(item_id, values=tuple(current_values))

def get_steps_from_treeview():
    steps = []
    children = tree.get_children()
    for item_id in children:
        item_data = tree.item(item_id, 'values')
        if not item_data or len(item_data) < 5: continue
        _, step_name, step_type, value_button_str, delay_str = item_data

        try:
            delay = float(delay_str)
            value_str = value_button_str # Start with the full string from the column
            button_type = "left" # Default

            # Extract button and actual value if it's a click step
            if step_type == "click":
                parts = value_button_str.split(' (')
                if len(parts) == 2:
                    value_str = parts[0].strip() # Coordinate part
                    button_part = parts[1].strip(') ')
                    if button_part.lower() in ["left", "right"]: button_type = button_part.lower()
                else: # Fallback if format is wrong
                     value_str = value_button_str # Use the whole string as value? Or maybe error? Let's assume it's just coords.
                     print(f"Warning: Could not parse button type for click step '{step_name}'. Defaulting to left.")


            # Validate the extracted/original value string based on type
            validation_error = validate_step_value(step_type, value_str, button_type)
            if validation_error:
                 print(f"Warning: Skipping step '{step_name}' due to invalid value format: {validation_error}")
                 continue

            # Pre-parse values for execution
            parsed_value = value_str
            value_to_store = value_str # Value stored in JSON is the coord/text part
            if step_type == "click": parsed_value = parse_coords(value_str)
            elif step_type == "drag": parsed_value = parse_drag_coords(value_str)
            elif step_type == "scroll": parsed_value = int(value_str)
            elif step_type == "delay": parsed_value = float(value_str)

            step_dict = {"name": step_name, "type": step_type, "value": value_to_store, "value_parsed": parsed_value, "delay": delay}
            if step_type == "click": step_dict["button"] = button_type # Add button to dict
            if step_type == "image": step_dict["confidence"] = DEFAULT_CONFIDENCE
            if step_type == "typewrite": step_dict["interval"] = 0.01
            if step_type == "drag": step_dict["duration"] = 0.5
            steps.append(step_dict)

        except ValueError as e: print(f"Warning: Skipping step '{step_name}' due to invalid delay: {e}")
        except Exception as e: print(f"Warning: Skipping step '{step_name}' due to error: {e}") # Catch other potential errors
    return steps


# --- Row Reordering ---
def move_step_up():
    selected_items = tree.selection();
    if not selected_items: messagebox.showwarning("No Selection", "Select step to move."); return
    item_id = selected_items[0]; current_index = tree.index(item_id)
    if current_index > 0: tree.move(item_id, "", current_index - 1); renumber_treeview(); tree.selection_set(item_id); tree.see(item_id)

def move_step_down():
    selected_items = tree.selection();
    if not selected_items: messagebox.showwarning("No Selection", "Select step to move."); return
    item_id = selected_items[0]; current_index = tree.index(item_id); total_items = len(tree.get_children())
    if current_index < total_items - 1: tree.move(item_id, "", current_index + 1); renumber_treeview(); tree.selection_set(item_id); tree.see(item_id)

# --- Highlighting ---
def highlight_step(index):
    clear_highlight(); children = tree.get_children()
    if 0 <= index < len(children): item_id = children[index]; tree.selection_set(item_id); tree.item(item_id, tags=('highlight',)); tree.see(item_id)

def clear_highlight():
    for item_id in tree.get_children():
        tags = list(tree.item(item_id, 'tags'));
        if 'highlight' in tags: tags.remove('highlight'); tree.item(item_id, tags=tuple(tags))

# --- Sorting ---
def sort_treeview_column(tv, col, reverse):
    try:
        # Use the display value for sorting the combined column
        col_key = "Value / Button" if col == "Value / Button" else col
        data_list = [(tv.set(k, col_key), k) for k in tv.get_children('')]
        is_numeric = col in ["#", "Delay (s)"]
        if is_numeric:
            def sort_key(item): 
                try: return float(item[0]) 
                except ValueError: return float('inf')
            data_list.sort(key=sort_key, reverse=reverse)
        else: data_list.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (val, k) in enumerate(data_list): tv.move(k, '', index)
        tv.heading(col, command=lambda: sort_treeview_column(tv, col, not reverse)); renumber_treeview()
    except Exception as e: print(f"Error sorting {col}: {e}")

# --- File Operations ---
def new_scenario():
    if recording_active or (execution_thread and execution_thread.is_alive()): messagebox.showwarning("Busy", "Stop activity first."); return
    if tree.get_children() and messagebox.askyesno("Confirm", "Clear current steps?"): update_treeview([]); clear_edit_fields(); status_label.config(text="Status: New scenario.")
    elif not tree.get_children(): update_treeview([]); clear_edit_fields(); status_label.config(text="Status: New scenario.")

def load_scenario():
    if recording_active or (execution_thread and execution_thread.is_alive()):
        messagebox.showwarning("Busy", "Stop activity first.")
        return
    create_scenario_folder()
    filepath = filedialog.askopenfilename(initialdir=SCENARIO_FOLDER, title="Load Scenario", filetypes=[("JSON", "*.json"), ("All", "*.*")])
    if not filepath:
        return
    try:
        with open(filepath, 'r') as f:
            content = json.load(f)
        if isinstance(content, dict) and "steps" in content:
            loaded_steps = content["steps"]
            description = content.get("description", "")  # Load description if available
        elif isinstance(content, list):
            loaded_steps = content
            description = ""  # No description in old format
        else:
            raise ValueError("Invalid file format.")
        # Basic validation and adding defaults if missing
        for i, step in enumerate(loaded_steps):
            if not isinstance(step, dict) or "type" not in step or "value" not in step:
                raise ValueError(f"Invalid step {i+1}")
            if "name" not in step:
                step["name"] = f"Step {i+1}"
            if "delay" not in step:
                step["delay"] = DEFAULT_DELAY
            if step["type"] == "click" and "button" not in step:
                step["button"] = "left"  # Add default button if missing

        update_treeview(loaded_steps)
        description_text.delete("1.0", tk.END)
        description_text.insert("1.0", description)  # Display the description
        clear_edit_fields()
        status_label.config(text=f"Status: Loaded '{os.path.basename(filepath)}'")
        print(f"Loaded: {filepath}")
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to load scenario:\n{e}")

def save_scenario():
    if recording_active or (execution_thread and execution_thread.is_alive()):
        messagebox.showwarning("Busy", "Stop activity first.")
        return
    steps_to_save = get_steps_from_treeview()
    if not steps_to_save:
        messagebox.showwarning("Empty", "Nothing to save.")
        return

    clean_steps = []  # Remove temporary parsed values before saving
    for step in steps_to_save:
        clean_step = step.copy()
        clean_step.pop("value_parsed", None)
        clean_steps.append(clean_step)

    create_scenario_folder()
    filepath = filedialog.asksaveasfilename(initialdir=SCENARIO_FOLDER, title="Save As", filetypes=[("JSON", "*.json")], defaultextension=".json")
    if not filepath:
        return

    description = description_text.get("1.0", tk.END).strip()  # Get the description text
    scenario_data = {
        "version": APP_VERSION,
        "name": os.path.basename(filepath).replace(".json", ""),
        "description": description,  # Save the description
        "steps": clean_steps,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        with open(filepath, 'w') as f:
            json.dump(scenario_data, f, indent=4)
        status_label.config(text=f"Status: Saved to '{os.path.basename(filepath)}'")
        print(f"Saved: {filepath}")
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save file:\n{e}")

# --- Main Application ---
if __name__ == "__main__":
    if not create_scenario_folder(): exit(1)
    main_window = tk.Tk()
    setup_gui(main_window)
    status_label.config(text="Status: Ready.")
    main_window.mainloop()
    if recording_active: stop_recording() # Attempt cleanup
    if execution_thread and execution_thread.is_alive(): stop_execution()
    print("Exiting PyAutoClicker GUI.")