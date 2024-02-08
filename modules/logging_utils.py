import config

import logging
import os
from datetime import datetime

# Logging utility
def setup_custom_log_levels():
    """
    Sets up custom logging levels for a more granular logging control.

    This function defines four custom logging levels: MURMUR, FLAG, PROMPTING, and MONOLOGUE, 
    with respective level numbers. It also attaches corresponding methods (log_murmur, 
    log_flag, log_prompting, log_monologue) to the logging.Logger class for convenient logging 
    at these levels. These custom levels allow for distinct logging behaviors for different 
    types of messages, such as PFC actions, status flags, prompt messages, and internal monologues.

    Each custom level has a specific purpose:
    - MURMUR (level 39): For logging quieter PFC actions.
    - FLAG (level 13): For logging status flags.
    - PROMPTING (level 12): For logging complete prompt messages sent to PFC.
    - MONOLOGUE (level 11): For logging PFC internal monologue.
    """

    # Define custom logging levels
    MURMUR_LEVEL_NUM = 39
    logging.addLevelName(MURMUR_LEVEL_NUM, "MURMUR")
    def log_murmur(self, message, *args, **kwargs):
        """ 
        Logging PFC actions.
        """
        
        if self.isEnabledFor(MURMUR_LEVEL_NUM):
            self._log(MURMUR_LEVEL_NUM, message, args, **kwargs)
    logging.Logger.murmur = log_murmur

    FLAG_LEVEL_NUM = 13
    logging.addLevelName(FLAG_LEVEL_NUM, "FLAG")
    def log_flag(self, message, *args, **kwargs):
        """
        Logging status flags statuses.
        """
        
        if self.isEnabledFor(FLAG_LEVEL_NUM):
            self._log(FLAG_LEVEL_NUM, message, args, **kwargs)
    logging.Logger.flag = log_flag

    PROMPTING_LEVEL_NUM = 12
    logging.addLevelName(PROMPTING_LEVEL_NUM, "PROMPTING")
    def log_prompting(self, message, *args, **kwargs):
        """
        Logging complete prompt messages sent to PFC. 
        """
        
        if self.isEnabledFor(PROMPTING_LEVEL_NUM):
            self._log(PROMPTING_LEVEL_NUM, message, args, **kwargs)
    logging.Logger.prompt = log_prompting

    MONOLOGUE_LEVEL_NUM = 11
    logging.addLevelName(MONOLOGUE_LEVEL_NUM, "MONOLOGUE")
    def log_monologue(self, message, *args, **kwargs):
        """
        Logging PFC internal monologue.
        """
        
        if self.isEnabledFor(MONOLOGUE_LEVEL_NUM):
            self._log(MONOLOGUE_LEVEL_NUM, message, args, **kwargs)
    logging.Logger.monologue = log_monologue

def setup_logging(file_log_level: int, console_log_level: int) -> None:
    """
    Initializes and configures the logging system for both file and console output.

    This function first sets up custom log levels and then configures logging handlers 
    for output to a file and the console. It creates a new log file for each session 
    with a timestamp in its name, ensuring that log data is stored in a unique file 
    for each run. The logging levels for both file and console can be independently set.

    Parameters:
    file_log_level (int): The logging level for the file handler.
    console_log_level (int): The logging level for the console handler.

    The function configures a formatter for the log messages and applies it to both 
    file and console handlers. It also ensures that any existing log handlers are 
    removed before setting up the new ones.
    """
    
    setup_custom_log_levels()

    # Create a file handler for logging
    log_directory = config.log_dir
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"{log_directory}/log_{current_time}.log"

    file_handler = logging.FileHandler(log_file_name)
    file_handler.setLevel(file_log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(min([file_log_level, console_log_level])) 

    # Clear existing handlers (if any), and then add new handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

setup_logging(file_log_level=config.file_log_level, console_log_level=config.console_log_level)