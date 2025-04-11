# KeyKraken v1.2

**A Cross-Platform GUI Automation Tool**

KeyKraken is a Python-based application designed to simplify and automate repetitive graphical user interface (GUI) tasks on your computer. It allows users to record mouse clicks, manually define a sequence of actions (including keyboard inputs, image searches, scrolling, and more), save these sequences as reusable scenarios, and execute them on demand.

## Key Features

* **Graphical User Interface:** Simple and intuitive interface built with Tkinter.
* **Click Recording:** Record left and right mouse clicks to quickly capture basic interactions.
* **Manual Step Creation:** Define complex automation sequences step-by-step, including:
    * **Naming:** Give each step a descriptive name.
    * **Action Types:** Choose from various actions:
        * `click`: Left or right mouse clicks at specific coordinates.
        * `image`: Find an image on the screen and click it (left-click).
        * `typewrite`: Type text strings.
        * `press`: Simulate pressing single keyboard keys (e.g., Enter, Ctrl, F1).
        * `hotkey`: Simulate keyboard shortcuts (e.g., Ctrl+C, Alt+F4).
        * `scroll`: Scroll the mouse wheel up or down by a specified amount.
        * `drag`: Simulate dragging the mouse from one point to another.
        * `delay`: Introduce explicit pauses within the sequence.
    * **Value Input:** Enter coordinates, text, keys, image paths, or amounts specific to the action type.
    * **Delay Control:** Set a delay (in seconds) *before* each step executes to accommodate load times.
* **Image Recognition:** Uses `pyautogui` and `opencv-python` to locate and interact with elements based on image matching (useful for dynamic interfaces).
* **Scenario Editing:**
    * View steps in a clear table format.
    * Select and modify any aspect of a step (name, type, value, delay, click button).
    * Reorder steps easily using "Move Up" and "Move Down" buttons.
* **Save & Load:**
    * Save automation sequences (scenarios) as human-readable JSON files.
    * Load previously saved scenarios for reuse.
    * Scenarios are stored in a dedicated `scenarios` subfolder.
* **Looping:** Execute scenarios multiple times by specifying the loop count.
* **Execution Control:**
    * Run the defined scenario.
    * Stop execution mid-sequence.
    * Visual progress bar and status updates during execution.
    * Highlights the currently executing step in the table.
* **Scroll Amount Calculator:** A built-in helper tool to detect scroll values reported by your system, aiding in setting correct scroll amounts.
* **Cross-Platform:** Built with Python libraries compatible with Windows, macOS, and Linux (though specific OS behaviors might vary slightly).
* **Basic Multi-Monitor Support:** Coordinates generally work across multiple monitors based on `pyautogui`'s virtual screen handling.

## Screenshots

* **Captures:** Using the screen capture option in lieu of providing and image will require modifications. Captures are taken of the entire screen, then opened in the systems native image viewer, and will need to be cropped to the specified area to be clicked.

## Requirements

* **Python:** Version 3.7 or higher recommended.
* **Libraries:**
    * `pyautogui`: For core GUI automation (mouse, keyboard, screen).
    * `pynput`: For reliable global mouse/keyboard event listening (recording, scroll testing).
    * `Pillow`: Image handling library (dependency for `pyautogui`).
    * `opencv-python`: Computer vision library used by `pyautogui` for image recognition confidence feature.

## Installation

### It's best practice to establish a virtual environment prior to installing requirements

1.  **Clone or Download:** Get the KeyKraken script (`.py` file).
2.  **Install Python:** Ensure you have a compatible Python version installed and added to your system's PATH.
3.  **Install Libraries:** Open your terminal or command prompt and run:
    ```bash
    pip install requirements.txt
    ```

## Usage

1.  **Run the Application:**
    ```bash
    python keykraken.py
    ```
2.  **Main Window:** The main application window will appear.
3.  **Recording Clicks:**
    * Click "Record Clicks".
    * The status bar will indicate recording is active.
    * Perform left or right clicks on your screen where you want actions to occur. Each click adds a step to the table.
    * Click "Stop Recording" when finished.
4.  **Adding/Editing Steps Manually:**
    * Use the "Edit Frame" section below the table.
    * **To Add:** Fill in the "Step Name", select "Action Type", enter the "Action Value" (see format hints below), set the "Delay Before", choose "Left/Right Click" (if type is 'click'), and click "Add Step".
    * **To Edit:** Click a row in the table. Its details will load into the edit fields. Modify the values and click "Update Step".
    * **Clear Fields:** Click "Clear Fields" to reset the edit section.
    * **Remove Step:** Select a step in the table and click "Remove Step".
5.  **Reordering Steps:**
    * Select a step in the table.
    * Use the "▲ Up" and "▼ Down" buttons next to the table to change its position.
6.  **Using "Calculate Scroll" Helper:**
    * Select "scroll" as the "Action Type".
    * Click the "Browse" button next to the "Value" input box.
    * A notification will appear indicating to *Scroll up or down to capture the scroll amount. Click 'Stop Scroll' to finish*.
    * Clicking "Ok" will make a "Stop Scroll" button appear.
    * Scroll up or down to begin calculation.
    * Clicking "Stop Scroll" will end the scroll calculation helper and add the calculated value to the "Value" input box.
7.  **Saving a Scenario:**
    * Click "Save".
    * Choose a filename (e.g., `my_automation.json`) in the `scenarios` folder. The steps currently in the table will be saved.
8.  **Loading a Scenario:**
    * Click "Load".
    * Select a previously saved `.json` file from the `scenarios` folder. The steps will load into the table, replacing any current steps.
9.  **Running a Scenario:**
    * Enter the desired number of repetitions in the "Loops" box.
    * Click "Run Scenario".
    * The application will execute the steps in order, pausing for the specified delay before each action. The progress bar and status label will update. The currently executing step will be highlighted.
    * Click "Stop Execution" to interrupt the process.

## Action Types & Value Formats

| Action Type | Required Value Format                                        | Description                                                                 |
| :---------- | :--------------------------------------------------------- | :-------------------------------------------------------------------------- |
| `click`     | Coordinates: `[X, Y]` or `X, Y`                            | Performs a mouse click (Left or Right, chosen in GUI) at the coordinates. |
| `image`     | Image file path (e.g., `button.png`, `../images/login.png`) | Locates the image on screen and performs a Left click in its center.        |
| `typewrite` | Text string (e.g., `Hello World!`)                         | Types the provided text using the keyboard.                                 |
| `press`     | Single key name (e.g., `enter`, `ctrl`, `f1`, `a`)           | Simulates pressing and releasing a single keyboard key.                     |
| `hotkey`    | Comma-separated keys (e.g., `ctrl,c`, `alt,f4`)             | Simulates pressing multiple keys simultaneously (a keyboard shortcut).      |
| `scroll`    | Integer (e.g., `10`, `-5`, `120`)                          | Scrolls the mouse wheel (Positive=Up, Negative=Down). Use "Scroll Calculation".  |
| `drag`      | Start/End Coords: `[X1,Y1];[X2,Y2]` or `X1,Y1;X2,Y2`        | Drags the mouse from the start coordinates to the end coordinates.          |
| `delay`     | Number (float/int, e.g., `5.0`, `2`)                       | Pauses execution for the specified number of seconds.                       |

* **Coordinates:** `X` and `Y` are pixel values relative to the primary monitor's top-left corner (0,0).
* **Image Paths:** Relative paths (e.g., `my_button.png`) are recommended and are relative to the `scenarios` folder where KeyKraken looks for them by default. Absolute paths also work. Use clear, unique images cropped closely around the target element.
* **Key Names:** Use lowercase key names defined by `pyautogui` (common ones include `enter`, `esc`, `f1` through `f12`, `left`, `right`, `up`, `down`, `ctrl`, `alt`, `shift`, `tab`, `space`, letters `a`-`z`, numbers `0`-`9`, etc.).

## Tips for Best Results

* **Use Adequate Delays:** Add sufficient delay before steps that interact with UI elements, especially after actions that trigger loading or animations. Start with larger delays (1-2 seconds) and reduce them carefully during testing.
* **Image Clarity:** Use clear, unique screenshots for image recognition steps. Crop them closely around the target element. Avoid capturing the mouse cursor in the image.
* **Screen Resolution:** Automation based on coordinates or images can break if the screen resolution, application window size, or UI layout changes significantly. Try to run automations under consistent screen conditions.
* **Run as Administrator (If Needed):** On some operating systems (like Windows), you might need to run KeyKraken with administrator privileges to interact with certain applications or system dialogs.
* **Target Application Focus:** Ensure the application you want to automate has focus before running steps like `typewrite` or `press`. You might need an initial `click` step to activate the target window.

## Known Limitations

* **Sensitivity to UI Changes:** Scripts relying heavily on coordinates or images may fail if the target application's UI is updated or resized.
* **Timing Issues:** The success of automation can depend on system performance and application responsiveness. Adjust delays as needed.
* **Complex Interactions:** Simulating very complex drag-and-drop operations or interactions requiring precise timing might be challenging.
* **Error Handling:** KeyKraken has basic error handling, but it may not gracefully handle every unexpected application state or popup window during execution. Execution will stop on most errors.
* **Interrupting Actions:** Stopping execution might not immediately interrupt actions that take time (like `pyautogui.dragTo` or long `typewrite` calls).

## Contributing

Found a bug or have an idea for a new feature? Feel free to report it!

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

---
*README generated based on KeyKraken v1.2 features. Current Date: Friday, April 11, 2025.*

