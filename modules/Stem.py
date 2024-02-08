import config
from modules import logging_utils

import logging
import shutil
import os
from glob import glob
import re
from datetime import datetime
import json
from typing import Optional

class Stem:
    """
    A class for managing and retrieving predefined prompts.

    This class stores a collection of utility functions utilized by other system classes.
    """
    
    @staticmethod
    def extract_keywords(raw_output) -> list:
        """
        Extracts keywords from the summary output.

        Args:
            raw_output (str): The output from which to extract keywords.

        Returns:
            list: A list of extracted keywords.
        """

        # Regex pattern to find all occurrences of words flanked by **
        pattern = r"\*\*(.*?)\*\*"
        # Find all matches and strip the ** from each keyword
        keywords = [keyword.lower() for keyword in re.findall(pattern, raw_output)]
        return keywords

    @staticmethod
    def get_timestamp() -> datetime:
        """
        Generates a timestamp string representing the current date and time.

        This method returns a timestamp using the current date and time formatted as 'YYYYMMDDHHMMSS'.
        It provides a convenient way to generate timestamps that can be used for logging, file naming, or other time-based referencing.

        Returns:
        str: A string representing the current timestamp in the format 'YYYYMMDDHHMMSS'.
        """
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def archive(source_dir: str, source_file: Optional[str] = None, archive_suffix='archive') -> bool:
        """
        Moves processed file to the respective archive folder.

        Args:
            source_path (str): The source folder
            source_file (str): The file to be archived

        Returns:
            bool: Information if the process has been successful
        """

        if not source_file:
            source_path = source_dir
            source_dir, source_file = os.path.split(source_dir)
        else:
            source_path = os.path.join(source_dir, source_file)
            
        
        destination_dir = '_'.join([source_dir, archive_suffix])
        directories_available = Stem.prepare_directory(destination_dir)
        if not directories_available:
            return False
        
        destination_path = os.path.join(destination_dir, source_file)
        
        logger = logging.getLogger('Stem')        
        try:
            shutil.move(source_path, destination_path)
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {source_path}")
            return False
        except PermissionError:
            logger.error(f"Permission denied: Cannot move {source_path} to {destination_path}")
            return False
        except Exception as e:
            logger.error(f"Error moving file {source_path} to {destination_path}: {e}")
            return False

    @staticmethod
    def prepare_directory(dir_path: str) -> bool:
        """
        Check existence / creates the necessary directories.
        Performs checks and ensures access problems won't cause overall program termination. 

        Args:
            dir_path (str): Path to required folder

        Returns: 
            bool: Information if the process has been successhul
        """

        logger = logging.getLogger('Stem')
        
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Checked / created folder: {dir_path}")
            return True
        except PermissionError:
            logger.error(f"Permission denied: Unable to create or access folder {dir_path}.")
            return False
        except OSError as e:
            logger.error(f"OS error when creating folder {dir_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating folder {dir_path}: {e}")
            return False

    @staticmethod
    def memory_read(file_path: str, filetype: str = 'text') -> str:
        """Function for accessing files, mainly  related to the system memory.
        Performs checks and ensures that lack of the file won't cause overall program termination. 

        Args: 
            file_path (str): Path to the file to be accessed
            filetype (str): Type of the file to be read [json, text]

        Returns:
            file content
        """
        
        logger = logging.getLogger('Stem')
        try:
            with open(file_path, 'r') as file:
                if filetype == 'json':
                    data = json.load(file)
                elif filetype == 'text':
                    data = file.read()
                else:
                    logger.error(f"Unkown file type: {filetype}")
                    return False
                return data
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from the file: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}")
            return False

    @staticmethod
    def memory_write(file_path, file_content) -> None:
        """Function for saving files, mainly  related to the system memory.
        Performs checks and ensures that lack of the file won't cause overall program termination. 

        Args: 
            file_path (str): Path to the file to be accessed
            filetype (str): Type of the file to be read [json, text]
        """

        logger = logging.getLogger('Stem')
        try:
            with open(file_path, "w") as file:
                file.write(file_content)
        except PermissionError:
            logger.error(f"Permission denied: Unable to write to file {file_path}.")
        except OSError as e:
            logger.error(f"File system error when writing to file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error wrtiting to file {file_path}: {e}")
    
    @staticmethod
    def get_prompt(key) -> str:
        """
        Retrieves a prompt template by its key.

        Args:
            key (str): The key of the prompt to retrieve.

        Returns:
            str: The prompt template associated with the given key. If the key is not found,
                 a default prompt text is returned.
        """

        prompts = Stem.memory_read('conversations/prompt_templates.json', 'json')
        return prompts.get(key, "")

    @staticmethod
    def transplantation(base_model_path: str, new_model_path: str) -> None:
        """Function moving new, finetuned model in place of an old one.

        Args:
            base_model_path (str): Path to the original model file
            new_model_path (str): Path to finetuned model
        
        """
        
        logger = logging.getLogger('Stem')
        try:
            logger.debug(f"Checking if {new_model_path} exists.")
            if not os.path.exists(new_model_path):
                if os.path.exists(base_model_path):
                    # new_model_path doesn't exist but base model does
                    raise Exception(f"No new model file found {new_model_path}.")
                else:
                    raise Exception(f"Missing both model files: {base_model_path} and {new_model_path}")

            backup_path = base_model_path + "_bck"
            logger.debug(f"Trying to backup old model file to {backup_path}.")            
            if os.path.exists(base_model_path):
                try:
                    shutil.copy(base_model_path, backup_path)
                except Exception as e:
                    raise Exception(f"Warning: can't make a backup: {e}") from e
            
            logger.debug(f"Trying to remove original model file: {base_model_path}.")                    
            if os.path.exists(base_model_path):
                os.remove(base_model_path)
                if os.path.exists(base_model_path):
                    raise Exception("Failed to remove the existing model file.")
        
            logger.debug(f"Trying to move new model file {new_model_path} to take place of {base_model_path}.")                    
            shutil.move(new_model_path, base_model_path)
            if not os.path.exists(base_model_path):
                raise Exception(f"Failed to swap LLM model files.")
        
            logger.info("Base LLM File swap successful.")

        except Exception as e:
            # Update the error logging to handle general exceptions, not just subprocess-related ones
            logger.error(f"Self brain transplantation failed: {str(e)}")
            # Reraise the exception with a custom message
            raise Exception(f"At least we tried... {e}") from e 

    @staticmethod
    def clean_string(s) -> str:
        """
        Cleans the input string by removing all leading characters up to the first alphabet letter.

        This method searches for the first occurrence of any letter (a-z, A-Z) in the input string. 
        If a letter is found, it returns the substring starting from that letter. 
        If no letter is found, it returns an empty string.

        Parameters:
        s (str): The input string to be cleaned.

        Returns:
        str: The cleaned string with leading non-letter characters removed, or an empty string if no letters are found.
        """    

        # This regular expression finds the first occurrence of any letter in the string
        match = re.search("[a-zA-Z]", s)
        if match:
            # If a letter is found, return the string starting from that letter
            return s[match.start():]
        else:
            # If no letter is found, return an empty string or handle as needed
            return ""

    @staticmethod
    def finetune_cleanup():
        """
        Performs cleanup operations for finetuning processes. It involves the following steps:
        - Creates a timestamped subdirectory in the logs directory.
        - Moves specific final LoRA files (checkpoint-LATEST.gguf, ggml-lora-LATEST-f32.gguf) to this subdirectory.
        - Removes any remaining 'checkpoint-*' and 'ggml-lora-*' files from the logs directory.

        This method uses the 'Stem.get_timestamp()' method to generate a unique timestamp for the subdirectory.
        It ensures that only the specified final files are archived and the rest are cleaned up, maintaining a neat logs directory.
        
        Exceptions during file removal are caught and logged for debugging purposes.
        """        
        logger = logging.getLogger('Stem')
        
        logs_dir = config.log_dir
        timestamp = Stem.get_timestamp()  # using your timestamp function
        fintuning_archive = os.path.join(logs_dir, f"finetuning_{timestamp}")
        Stem.prepare_directory(fintuning_archive)
        
        #Final LoRA files to archive
        files_to_archive = [
            "checkpoint-LATEST.gguf",
            "ggml-lora-LATEST-f32.gguf",
            "llama-2-13b-chat.Q8_0.gguf_bck"
        ]

        for file_name in files_to_archive:
            if os.path.exists(file_name): 
                shutil.move(file_name, os.path.join(fintuning_archive, file_name))
                logger.info(f"Moved file: {file_name} to {fintuning_archive}")
            else:
                logger.warning(f"File not found in the current directory: {file_name}")

        # Clean up the remaining files
        try:
            for tmp_file in glob(os.path.join(logs_dir, 'checkpoint-*')):
                if tmp_file not in files_to_archive:
                    os.remove(tmp_file)
            for tmp_file in glob(os.path.join(logs_dir, 'ggml-lora-*')):
                if tmp_file not in files_to_archive:
                    os.remove(tmp_file)
        except Exception as e:
            logger.debug(f"Error removing tmp files: {e}")