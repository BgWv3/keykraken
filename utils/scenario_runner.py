import os
import json
import time
from tkinter import messagebox

def load_scenario(file_path):
    """Load a scenario from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            scenario = json.load(file)
        return scenario
    except Exception as e:
        print(f"Error loading scenario: {e}")
        return None

def run_scenario(scenario, automation_func):
    """
    Run a single scenario.
    :param scenario: The scenario data (list of steps).
    :param automation_func: The function to execute the steps.
    """
    try:
        steps = scenario.get("steps", [])
        loops = int(scenario.get("loops", 1))
        print(f"Running scenario: {scenario.get('name', 'Unnamed')} with {loops} loop(s).")
        automation_func(steps, loops)
    except Exception as e:
        print(f"Error running scenario: {e}")

def run_multiple_scenarios(scenario_files, automation_func):
    """
    Run multiple scenarios back-to-back.
    :param scenario_files: List of file paths to the scenarios.
    :param automation_func: The function to execute the steps.
    """
    for file_path in scenario_files:
        print(f"Loading scenario: {file_path}")
        scenario = load_scenario(file_path)
        if scenario:
            run_scenario(scenario, automation_func)
            time.sleep(1)  # Optional delay between scenarios
        else:
            print(f"Skipping scenario: {file_path}")
    messagebox.showinfo("Scenarios Complete", "All scenarios have been executed.")