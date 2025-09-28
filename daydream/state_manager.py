import os
import yaml
from flask import session, current_app
import logging

class StateManager:
    """
    Manages the application's state based on a YAML configuration file.

    This class is responsible for loading the state manifest, tracking the
    current state of the user's session, and providing information about
    available states and tools.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Implements the Singleton pattern to ensure only one StateManager
        # instance is loaded per application lifecycle.
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, manifest_path='app_state.yaml'):
        # The __init__ will be called every time StateManager() is invoked,
        # but the state loading should only happen once.
        if not hasattr(self, '_initialized'):
            logging.info("Initializing StateManager...")
            self.manifest_path = manifest_path
            self.manifest = self._load_manifest()
            self.entry_point = self.manifest.get('entry_point', 'MainMenu')
            self._initialized = True
            logging.info(f"StateManager initialized with entry point '{self.entry_point}'.")

    def _load_manifest(self):
        """Loads and parses the state manifest YAML file."""
        if not os.path.exists(self.manifest_path):
            logging.error(f"FATAL: State manifest file not found at '{self.manifest_path}'.")
            raise FileNotFoundError(f"State manifest file not found at '{self.manifest_path}'")
        with open(self.manifest_path, 'r') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                logging.error(f"FATAL: Error parsing state manifest YAML: {e}")
                raise

    def get_current_state(self):
        """
        Retrieves the current state from the user's session.

        If no state is set, it returns the default entry point state.
        """
        return session.get('app_state', self.entry_point)

    def set_state(self, new_state):
        """
        Updates the user's session with a new state.

        Args:
            new_state (str): The name of the state to transition to.

        Returns:
            bool: True if the state was successfully changed, False if the
                  new state is invalid.
        """
        if new_state in self.manifest['states']:
            session['app_state'] = new_state
            logging.info(f"Session state transitioned to '{new_state}'.")
            return True
        elif new_state == "TERMINATE":
            # A special case for exiting or logging out.
            session.clear()
            logging.info("Session state terminated.")
            return True
        logging.warning(f"Attempted to transition to an invalid state: '{new_state}'.")
        return False

    def get_state_definition(self, state_name=None):
        """
        Retrieves the full definition for a given state.

        If no state name is provided, it returns the definition for the
        current session state.
        """
        if state_name is None:
            state_name = self.get_current_state()
        return self.manifest['states'].get(state_name)

    def get_available_tools(self, state_name=None):
        """
        Retrieves the list of available tools for a given state.

        If no state name is provided, it returns the tools for the current
        session state.
        """
        state_def = self.get_state_definition(state_name)
        if state_def:
            return state_def.get('available_tools', [])
        return []

    def get_ui_view(self, state_name=None):
        """
        Retrieves the UI view function or template path for a given state.
        """
        state_def = self.get_state_definition(state_name)
        if state_def:
            return state_def.get('ui_view')
        return None