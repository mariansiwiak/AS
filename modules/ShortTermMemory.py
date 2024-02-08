import config
from modules import logging_utils

from modules.Stem import Stem

import logging
import os
import json
import re
from datetime import datetime
from typing import Union


class ShortTermMemory:
    """
    A class to manage a short-term memory storage system for conversations.

    This class handles the storage, retrieval, and management of conversations
    linked to specific keywords. The conversations are stored as file paths in a JSON file.
    """

    def __init__(self):
        """
        Initializes the ShortTermMemory class by setting up the JSON file for storage.
        
        This method checks if the JSON file exists at the specified location and creates it if not.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Instantiating {self.__class__.__name__}")
        
        self._stm_path = config.stm_path
        if not os.path.exists(self._stm_path):
            with open(self._stm_path, 'w') as file:
                json.dump({}, file)

    def memorize_keywords(self, keywords: list, filename: str) -> None:
        """
        Memorizes a conversation file under given keywords.

        Args:
            keywords (list): A list of keywords to associate with the conversation file.
            filename (str): The name of the file containing the conversation.

        This method updates the JSON storage with the filename under each provided keyword.
        """

        self.logger.debug(f"Saving keywords: {keywords}, related to conversation from: {filename}.")
        try:
            with open(self._stm_path, 'r+') as file:
                data = json.load(file)
                for keyword in keywords:
                    if keyword in data:
                        if filename not in data[keyword]:
                            data[keyword].append(filename)
                    else:
                        data[keyword] = [filename]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        except FileNotFoundError:
            self.logger.error(f"Short Term Memory file {self._stm_path} not found.")
        except Exception as e:
            self.logger.error(f"Unexpected error reading Short Term Memory file {self._stm_path}: {e}")
    
    def search_memories(self, keywords: list) -> list:
        """
        Searches for conversation files associated with given keywords.

        Args:
            keywords (list): A list of keywords to search for.

        Returns:
            list: A list of filenames associated with any of the given keywords.
        """

        self.logger.debug(f"Searching in {self._stm_path} for files related to keywords: {keywords}.")


        data = Stem.memory_read(self._stm_path, 'json')
        if data: 
            self.logger.debug(f"Loaded short term memory.")
        else:
            self.logger.warning(f"Failed to loaded short term memory.")
            data = {}
        
        filenames = set()
        for keyword in keywords:
            filenames.update(data.get(keyword, []))
        return list(filenames)

    def concatenate_memories(self, filenames: list) -> str:
        """
        Concatenates the contents of conversation files.

        Args:
            filenames (list): A list of filenames to concatenate.

        Returns:
            str: A single string containing all the concatenated conversations.
                 Each conversation is prefixed with its source and date.
        """

        self.logger.debug(f"Concatenating selected conversations into one file.")
        
        conversations = ""
        for filename in filenames:
            file_content = Stem.memory_read(filename)
            date_str = re.search(r'conversation_(\d{8})(\d{6})\.txt$', filename)
            if date_str:
                # Parse the date and time
                date_time = datetime.strptime(date_str.group(1) + date_str.group(2), '%Y%m%d%H%M%S')
                # Format the date and time
                formatted_date = date_time.strftime('%Y-%m-%d %H:%M:%S')
                conversations += f'Conversation from {formatted_date}\n{file_content}\n'
            else:
                conversations += f'Conversation from {filename}\n{file_content}\n'               
        
        return conversations

    def forget_keywords(self, keywords_to_clear: list) -> None:
        """
        Removes specified keywords and their associated conversations from memory.

        Args:
            keywords_to_clear (list): A list of keywords to remove from the memory.
        """
        self.logger.debug(f"Clearing {keywords_to_clear} from {self._stm_path}.")

        try:
            with open(self._stm_path, 'r+') as file:
                data = json.load(file)
                for keyword in keywords_to_clear:
                    if keyword in data:
                        del data[keyword]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
            self.logger.debug(f"Selected keywords removed from {self._stm_path}.")
            
        except FileNotFoundError:
            self.logger.error(f"Short Term Memory file {self._stm_path} not found.")
        except Exception as e:
            self.logger.error(f"Unexpected error reading Short Term Memory file {self._stm_path}: {e}")

    def recall_all_keywords(self) -> Union[bool, None]:
        """
        Retrieves a list of all keywords stored in memory.

        Returns:
            list: A list of all keywords.
        """
        self.logger.debug(f"Reading all keywords from {self._stm_path}.")

        data = Stem.memory_read(self._stm_path, 'json')
        if data and len(data) > 0:
            return list(data.keys())
        else:
            return None