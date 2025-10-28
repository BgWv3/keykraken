# KeyKraken 🐙

**KeyKraken** is a powerful, modern macro automation application built with Python and Qt. Create, record, and execute custom automation scenarios to streamline repetitive tasks.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

### 🎯 Core Functionality
- **Visual Scenario Management**: Create, edit, and organize automation scenarios with an intuitive GUI
- **Live Recording**: Record mouse clicks and keyboard inputs in real-time
- **Manual Step Editing**: Fine-tune automation steps with precise control
- **Multi-Iteration Support**: Run scenarios 1-1000 times automatically
- **Multiple Action Types**: Support for clicks, typing, keypresses, scrolling, mouse movement, and delays

### 🎨 Modern Interface
- Clean Qt-based GUI with split-panel design
- Real-time execution feedback and progress tracking
- Step reordering with drag-free up/down controls
- Status bar with live updates
- Custom icons and splash screen support

### 🔒 Safety Features
- PyAutoGUI failsafe (move mouse to corner to stop)
- 3-second preparation countdown before execution
- Manual stop capability during recording
- Error handling and validation

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the repository**
```bash
git clone https://github.com/BgWv3/keykraken.git
cd keykraken
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create required directories**
```bash
mkdir scenarios
mkdir images
```

4. **Add optional images** (for enhanced UI)
   - Place `icon.png` in `images/` folder for app icon
   - Place `keykraken_header_v2.png` in `images/` folder for splash screen

5. **Run the application**
```bash
python keykraken.py
```

## Quick Start Guide

### Creating Your First Scenario

1. **Launch KeyKraken** and click "New Scenario"
2. **Enter a name** for your scenario
3. **Add a description** (optional but recommended)
4. **Add steps** using one of two methods:
   - **Manual**: Click "Add Step" and configure each action
   - **Recording**: Click "🔴 Start Recording" and perform actions

### Step Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| **Click** | Mouse click at coordinates | Click buttons, select items |
| **Type** | Type text string | Enter form data, fill fields |
| **Keypress** | Single key press | Press Enter, Tab, Escape |
| **Scroll** | Scroll up/down | Navigate long pages |
| **Move** | Move mouse to position | Hover over elements |
| **Delay** | Wait specified time | Allow page loads, timing |

### Recording Macros

1. Click **"🔴 Start Recording"**
2. Perform your actions (mouse clicks and key presses)
3. Click **"⏹️ Stop Recording"** when finished
4. Review and edit recorded steps as needed
5. Click **"💾 Save Scenario"**

### Executing Scenarios

1. **Load** a scenario from the left panel
2. **Set iterations** (how many times to run)
3. Click **"▶️ Execute Scenario"**
4. **Position windows** during 3-second countdown
5. Watch automated execution with real-time feedback

### Editing Steps

- **Add Step**: Insert new actions manually
- **Edit Step**: Modify existing action details
- **Delete Step**: Remove unwanted actions
- **Move Up/Down**: Reorder steps for proper sequence

## Scenario File Format

Scenarios are stored as JSON files in the `scenarios/` directory:

```json
{
    "version": "1.2",
    "name": "example_scenario",
    "description": "This is an example automation scenario",
    "steps": [
        {
            "name": "Click Login Button",
            "type": "click",
            "value": [1310, 687],
            "delay": 0.25,
            "button": "left"
        },
        {
            "name": "Type Username",
            "type": "type",
            "value": "myusername",
            "delay": 0.1
        },
        {
            "name": "Press Enter",
            "type": "keypress",
            "value": "enter",
            "delay": 0.25
        }
    ],
    "saved_at": "2025-10-28 14:30:00"
}
```

## Advanced Usage

### Custom Delays

Adjust delay times for each step to match application response times:
- **Fast actions**: 0.1 seconds
- **Normal actions**: 0.25 seconds (default)
- **Slow actions**: 0.5-1.0 seconds
- **Page loads**: 2-5 seconds (use delay step)

### Mouse Button Options

Click steps support three mouse buttons:
- **Left**: Standard clicks
- **Right**: Context menus
- **Middle**: Special actions

### Keyboard Keys

Supported key names include:
- Letters: `a-z`
- Numbers: `0-9`
- Special: `enter`, `tab`, `escape`, `space`, `backspace`, `delete`
- Modifiers: `shift`, `ctrl`, `alt`
- Function: `f1-f12`
- Arrows: `up`, `down`, `left`, `right`

### Screen Resolution Considerations

⚠️ **Important**: Mouse coordinates are absolute screen positions. Scenarios recorded on one screen resolution may not work correctly on different resolutions. For best results:
- Use the same screen resolution when recording and executing
- Keep display scaling at 100%
- Record scenarios on the machine where they'll be executed

## Troubleshooting

### Common Issues

**Problem**: Clicks are off-target
- **Solution**: Ensure screen scaling is set to 100% and resolution matches recording environment

**Problem**: Scenario executes too fast
- **Solution**: Increase delay values for individual steps

**Problem**: Application doesn't respond during execution
- **Solution**: Move mouse to top-left corner to trigger PyAutoGUI failsafe

**Problem**: Recording doesn't capture actions
- **Solution**: Ensure the application has proper system permissions for input monitoring

**Problem**: Steps fail to execute
- **Solution**: Check that coordinate values are valid lists `[x, y]` in JSON file

### Debug Tips

1. Test scenarios with 1 iteration before running multiple times
2. Add delay steps between actions for timing-sensitive operations
3. Use descriptive step names for easier debugging
4. Review the status bar for execution progress and errors

## Best Practices

### Scenario Design
- ✅ Break complex tasks into smaller, reusable scenarios
- ✅ Add descriptive names and documentation
- ✅ Test with single iteration before bulk runs
- ✅ Include adequate delays for application response times

### Recording
- ✅ Clear desktop of unnecessary windows before recording
- ✅ Perform actions slowly and deliberately
- ✅ Review and clean up recorded steps
- ✅ Test recorded scenario immediately

### Execution
- ✅ Close unrelated applications to prevent interference
- ✅ Ensure target applications are properly positioned
- ✅ Don't interact with mouse/keyboard during execution
- ✅ Monitor first few iterations for accuracy

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, Linux
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum
- **Display**: 1024x768 minimum resolution

## Dependencies

```
MouseInfo==0.1.3
PyAutoGUI==0.9.54
PyGetWindow==0.0.9
PyMsgBox==2.0.1
pynput==1.8.1
pyperclip==1.11.0
PyRect==0.2.0
PyScreeze==1.0.1
PySide6==6.10.0
PySide6_Addons==6.10.0
PySide6_Essentials==6.10.0
pytweening==1.2.0
setuptools==80.9.0
shiboken6==6.10.0
six==1.17.0
```

## Project Structure

```
keykraken/
├── keykraken.py          # Main application file
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── scenarios/           # Scenario JSON files
│   ├── example1.json
│   └── example2.json
└── images/              # Optional UI assets
    ├── icon.png
    └── keykraken_header_v2.png
```

## Contributing

Contributions are welcome! Areas for improvement:
- Additional step types (drag-and-drop, OCR-based clicking)
- Scenario templates and marketplace
- Variable support and conditional logic
- Screenshot-based validation
- Scheduled execution
- Cloud sync for scenarios

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing scenarios in the community
- Review the troubleshooting section

## Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) (Qt for Python)
- Automation powered by [PyAutoGUI](https://pyautogui.readthedocs.io/)
- Input monitoring via [pynput](https://pynput.readthedocs.io/)

---

**⚠️ Disclaimer**: Use KeyKraken responsibly. Automated actions should comply with the terms of service of any applications you interact with. The developers are not responsible for misuse of this tool.