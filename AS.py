from langchain.llms import LlamaCpp

import asyncio

from abc import ABC, abstractmethod

from datetime import datetime
import re
import json
import os
import shutil
import glob
import subprocess

import logging


## Logging utility

def setup_custom_log_levels():
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

def setup_logging(file_log_level: int = 10, console_log_level: int = 10):
    setup_custom_log_levels()

    # Create a file handler for logging
    log_directory = "console"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"{log_directory}/file_{current_time}.log"

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

setup_logging()

# Stem
class StemUtility:
    """
    A class for managing and retrieving predefined prompts.

    This class stores a collection of utility functions utilized by other system classes.
    """
    
    @staticmethod
    def extract_keywords(raw_output):
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
    def get_timestamp():
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def archive(source_dir: str, source_file: str | None = None, archive_suffix='archive'):
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
        directories_available = StemUtility.prepare_directory(destination_dir)
        if not directories_available:
            return False
        
        destination_path = os.path.join(destination_dir, source_file)
        
        logger = logging.getLogger('StemUtility')        
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

        logger = logging.getLogger('StemUtility')
        
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
        
        logger = logging.getLogger('StemUtility')
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
        """Function for accessing files, mainly  related to the system memory.
        Performs checks and ensures that lack of the file won't cause overall program termination. 

        Args: 
            file_path (str): Path to the file to be accessed
            filetype (str): Type of the file to be read [json, text]
        """

        logger = logging.getLogger('StemUtility')
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
    def get_prompt(key):
        """
        Retrieves a prompt template by its key.

        Args:
            key (str): The key of the prompt to retrieve.

        Returns:
            str: The prompt template associated with the given key. If the key is not found,
                 a default prompt text is returned.
        """

        prompts = StemUtility.memory_read('conversations/prompt_templates.json', 'json')
        return prompts.get(key, "")

    @staticmethod
    def transplantation(base_model_path: str, new_model_path: str):
        """Function moving new, finetuned model in place of an old one.

        Args:
            base_model_path (str): Path to the original model file
            new_model_path (str): Path to finetuned model
        
        """
        
        try:
            self.logger.debug(f"Checking if {new_model_path} exists.")
            if not os.path.exists(new_model_path):
                if os.path.exists(base_model_path):
                    # new_model_path doesn't exist but base model does
                    raise Exception(f"No new model file found {new_model_path}.")
                else:
                    raise Exception(f"Missing both model files: {base_model_path} and {new_model_path}")

            backup_path = base_model_path + "_bck"
            self.logger.debug(f"Trying to backup old model file to {backup_path}.")            
            if os.path.exists(base_model_path):
                try:
                    shutil.copy(base_model_path, backup_path)
                except Exception as e:
                    raise Exception(f"Warning: can't make a backup: {e}") from e
            
            self.logger.debug(f"Trying to remove original model file: {base_model_path}.")                    
            if os.path.exists(base_model_path):
                os.remove(base_model_path)
                if os.path.exists(base_model_path):
                    raise Exception("Failed to remove the existing model file.")
        
            self.logger.debug(f"Trying to move new model file {new_model_path} to take place of {base_model_path}.")                    
            shutil.move(new_model_path, base_model_path)
            if not os.path.exists(base_model_path):
                raise Exception(f"Failed to swap LLM model files.")
        
            self.logger.info("Base LLM File swap successful.")

        except Exception as e:
            # Update the error logging to handle general exceptions, not just subprocess-related ones
            self.logger.error(f"Self brain transplantation failed: {str(e)}")
            # Reraise the exception with a custom message
            raise Exception(f"At least we tried... {e}") from e 

    @staticmethod
    def clean_string(s):
        # This regular expression finds the first occurrence of any letter in the string
        match = re.search("[a-zA-Z]", s)
        if match:
            # If a letter is found, return the string starting from that letter
            return s[match.start():]
        else:
            # If no letter is found, return an empty string or handle as needed
            return ""

# Short-Term Memory (STM)
class ShortTermMemory:
    """
    A class to manage a short-term memory storage system for conversations.

    This class handles the storage, retrieval, and management of conversations
    linked to specific keywords. The conversations are stored as file paths in a JSON file.
    """

    def __init__(self, stm_path: str = 'conversations/short-term-memory.json'):
        """
        Initializes the ShortTermMemory class by setting up the JSON file for storage.

        This method checks if the JSON file exists at the specified location and creates it if not.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Instantiating {self.__class__.__name__} with Short Term Memory path: {stm_path}")
        
        self._stm_path = stm_path
        if not os.path.exists(self._stm_path):
            with open(self._stm_path, 'w') as file:
                json.dump({}, file)

    def memorize_keywrods(self, keywords: list, filename: str) -> None:
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


        data = StemUtility.memory_read(self._stm_path, 'json')
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
            file_content = StemUtility.memory_read(filename)
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

    def recall_all_keywords(self) -> list | bool:
        """
        Retrieves a list of all keywords stored in memory.

        Returns:
            list: A list of all keywords.
        """
        self.logger.debug(f"Reading all keywords from {self._stm_path}.")

        data = StemUtility.memory_read(self._stm_path, 'json')
        if data and len(data) > 0:
            return list(data.keys())
        else:
            return False

# Default Mode Network (DMN)
class DefaultModeNetwork:
    """
    A class designed to integrate a language learning model (LLM) with a short-term memory storage system.
    This class enables the LLM to process and learn from saved conversation data autonomously.
    """

    def __init__(self,
                 pfc,
                 overwhelmed_event,
                 engaged_event,
                 conclusions_storage_path: str = 'conclusions',
                ):
        """
        Initializes the DefaultModeNetwork class by setting up the short-term memory (STM) component.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Instantiating {self.__class__.__name__} with conclusions_storage_path: {conclusions_storage_path}.")
        self.logger.flag(f"overhelmed: {overwhelmed_event.is_set()}") 
        
        self.stm = ShortTermMemory()
        self.pfc = pfc

        self.overwhelmed = overwhelmed_event
        self.engaged = engaged_event
        
        self._conclusions_storage_path = conclusions_storage_path
        StemUtility.prepare_directory(self._conclusions_storage_path)          

        self._keyword_selection_prompt_template = StemUtility.get_prompt("keyword_selection")
        self._perspective_explanation_prompt_template = StemUtility.get_prompt("perspective_explanation")
    
    
    async def _interesting_keywords_selection(self, keywords) -> list:
        """
        Asynchronously selects a subset of keywords deemed interesting or relevant by the LLM.

        Args:
            keywords (list): A list of keywords to choose from.

        Returns:
            list: A subset of selected keywords.
        """

        starred_keywords = [f"**{keyword}**" for keyword in keywords]
        keywords_selection_prompt = self._keyword_selection_prompt_template.replace("{keywords_list}", ', '.join(starred_keywords))
        self.logger.prompt(f"Interesting keyword selection prompt:\n{keywords_selection_prompt}")        
        self.logger.debug(f"Asking LLM to select interesting keywords.")   
        keywords_selected_raw_output = self.pfc(keywords_selection_prompt)
        self.logger.monologue(f"LLM selected interesting keywords:\n{keywords_selected_raw_output}.\nMoving to keywords extraction.")   
        keywords_selected_pure = StemUtility.extract_keywords(keywords_selected_raw_output)
        self.logger.debug(f"Interesting keywords found: {keywords_selected_pure}")   
        
        return keywords_selected_pure

    def _fetch_memory(self, keywords) -> str:
        """
        Fetches and concatenates interaction history data based on the provided keywords.

        Args:
            keywords (list): A list of keywords to search the interaction data for.

        Returns:
            str: A concatenated string of all interaction history files related to the given keywords.
        """
        
        self.logger.debug(f"Reaching to Short Term memory for for all the files related to: {keywords}")  
        filenames = self.stm.search_memories(keywords)
        self.logger.debug(f"Ordering concatenation of identified files.")          
        concatenated_memories = self.stm.concatenate_memories(filenames)
        return filenames, concatenated_memories 

    async def _analyze_interaction(self, interaction_history) -> str:
        """
        Analyzes the concatenated interaction history.

        Args:
            conversations (str): The concatenated string of conversations to be analyzed.
        """
    
        perspective_explanation_prompt = self._perspective_explanation_prompt_template.replace("{interaction_history}", 
                                                                                             interaction_history)
        self.logger.prompt(f"Prompt for conversation analysis:\n{perspective_explanation_prompt}")
        self.logger.murmur(f"Thinking about recent conversations...")   
        adaptation_explanation = self.pfc(perspective_explanation_prompt)
        self.logger.monologue(f"Full explanation of the required adaptation: {adaptation_explanation}")   
        return adaptation_explanation

    async def ponder(self):
        """
        The main asynchronous method of the class that orchestrates the process of 
        selecting keywords, fetching conversations, and analyzing them.
        """

        self.logger.debug(f"Checking if there are any topics to be analyzed deeper.")           
        all_keywords = self.stm.recall_all_keywords()
        if not all_keywords:
            self.logger.murmur(f"Kingdom for a good book!")   
            return False

        self.logger.debug(f"All keywords: {all_keywords}. Moving to interesting keyword selection.")           
        interesting_keywords = await self._interesting_keywords_selection(all_keywords)
        self.logger.debug(f"Interesting keywords selected.")           
        memory_files, concatenated_memories = self._fetch_memory(interesting_keywords)
        self.logger.debug(f"Concatenated conversations received.")   

        # Assume an async version of LLM analysis
        if concatenated_memories:
            self.logger.debug(f"Moving to analyze the conversaton histories.")           
            adaptation_summary = await self._analyze_interaction(concatenated_memories)
            if "uninspiring" not in adaptation_summary.lower():
                self.logger.murmur(f"Discussion on {interesting_keywords} indeed brought a new perspective...")
                conclusion_path = os.path.join(self._conclusions_storage_path, f"conclusion_{StemUtility.get_timestamp()}.txt")
                self.logger.debug(f"Conclusions will be saved to {conclusion_path}.")
                StemUtility.memory_write(conclusion_path, adaptation_summary)
                self.overwhelmed.set()
                self.logger.flag(f"overwhelmed: {self.overwhelmed.is_set()}")
            else:
                self.logger.monologue(f"As per:\n{adaptation_summary}.\nNothing interesting has been found in {memory_files}.")
        else:
            self.logger.error(f"Concatenated conversations turned out to be an empty string.")   
        self.logger.debug(f"Interesting or not, forgetting conversations about {interesting_keywords}.")   
        self.stm.forget_keywords(interesting_keywords)
        self.engaged.clear()


# Reflective Evolution Monitor (REM)
class ReflectiveEvolutionMonitor:
    """
    A class designed to enable a language learning model (LLM) to self-reflect and evolve based on the conclusions drawn from user interactions.
    The class uses the same LLM for reading summaries, preparing fine-tuning materials, and the fine-tuning process.
    """

    def __init__(self,
                 pfc,
                 base_model_path: str = 'llama-2-13b-chat.Q6_K.gguf',
                 conclusions_storage_path: str = 'conclusions',
                 dream_storage_path: str = 'context',
                 dreams_number: int = 1,
                 available_threads: int = 8, 
                 epochs: int = 1,
                 latest_lora_path: str = r".\ggml-lora-LATEST-f32.gguf",
                 lora_weight: float = 0.7):
        """
        Initializes the ReflectiveEvolutionMonitor class. 

        Arguments:
            pfc: Large Language Model used as a base of the system
            base_model_path: path to  LLM model file on disk
            conclusions_storage_path: path to folder containing not-permeated new perspectives
            dream_storage_path: path to a folder to store finetune materials to be used in this session
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Instantiating {self.__class__.__name__} with base_model_path = {base_model_path}, conclusions_storage_path = {conclusions_storage_path}, dream_storage_path: {dream_storage_path}.")  
    
        self.pfc = pfc
        
        self._base_model_path = base_model_path

        self._conclusions_storage_path = conclusions_storage_path
        StemUtility.prepare_directory(self._conclusions_storage_path)
        self._conclusion_file = None
        
        self._dream_storage_path = dream_storage_path
        StemUtility.prepare_directory(self._dream_storage_path)

        self._dream_spinning_prompt_template = StemUtility.get_prompt("dream_spinning")
        self._dream_prompt_template = StemUtility.get_prompt("dream_template")

        self._conclusions = ''
        
        self._dreams_number = dreams_number
        self._available_threads = str(available_threads)
        self._epochs = str(epochs)
        self._latest_lora_path = latest_lora_path
        self.lora_weight = str(lora_weight)

    def _gather_conclusion(self) -> bool:
        """
        Reads a summary document as a text file.

        Returns:
            bool: True if the summary was successfully read, False otherwise.
        """

        conclusions_pattern = os.path.join(self._conclusions_storage_path, "conclusion*")
        self.logger.debug(f"Searching for following pattern: {conclusions_pattern}.")
        conclusion_files = glob.glob(conclusions_pattern)
        self.logger.debug(f"Following files found: {conclusion_files}.")

        if not conclusion_files:
            self.logger.error("No conclusion files matching the pattern found.")
            return False

        # Process the first file from the matched conclusion files
        self._conclusion_file = conclusion_files[0]
        self.logger.debug(f"Following file selected: {conclusion_files}.")
        self._conclusions = StemUtility.memory_read(self._conclusion_file)
        return True

    async def _spin_dream(self, dream_prompt: str) -> str | None:
        """
        Prepares a single piece of data required for the fine-tuning process by interpreting the summary content.

        Args:
            dream_prompt (str): Prompt to generate a single piece of training material.

        Returns:
            dict: Data structured for fine-tuning.
        """

        dream_content = self.pfc(dream_prompt)
        self.logger.monologue(f"I had a dream:\n{dream_content}.")

        try:
            stimulus_start = dream_content.index('**QUESTION**') + len('**QUESTION**')
            response_start = dream_content.index('**RESPONSE**')
            end_tag = dream_content.index('**END**')
    
            dreamt_stimulus = dream_content[stimulus_start:response_start].strip()
            dreamt_stimulus = StemUtility.clean_string(dreamt_stimulus)
            self.logger.prompt(f"Dreamt stimulus:\n{dreamt_stimulus}")
            
            dreamt_response = dream_content[response_start + len('**RESPONSE**'):end_tag].strip()
            dreamt_response = StemUtility.clean_string(dreamt_response)
            self.logger.prompt(f"Dreamt response:\n{dreamt_response}")

            dream = self._dream_prompt_template.replace("{stimulus}", dreamt_stimulus) 
            dream = dream.replace("{response}", dreamt_response) 
            return dream
        
        except ValueError as e:
            return None
    

    async def _weave_dreams(self, num_dreams: int) -> str:
        """
        Generates a specified number of materials (dreams) and writes them into a single text file.
        Each 'dream' is appended to the file as it is generated.

        Args:
            num_dreams (int): Number of training materials to be generated

        Returns:
            str: Concated training materials set
        """
        
        self.logger.info(f"Generating {num_dreams} dreams.")
        dreams_path = os.path.join(self._dream_storage_path, f"dream_{StemUtility.get_timestamp()}.txt")
        self.logger.debug(f"Dreams for this sessions will be saved to: {dreams_path}.")        
        dream_spinning_prompt = self._dream_spinning_prompt_template.replace("{adaptation_summary}", self._conclusions) 
        self.logger.prompt(f"Prompt for generating training material from conversation conclusions:\n{dream_spinning_prompt}.")   

        generated_dreams = 0
        while generated_dreams < num_dreams:
            self.logger.info(f"Generating dream # {generated_dreams}.")
            dream = await self._spin_dream(dream_spinning_prompt)
            if dream:
                with open(dreams_path, 'a') as file:  # Open and append each dream, then close the file
                    file.write(dream + '\n')
                generated_dreams += 1
        return dreams_path
    
    async def _deepsleep(self, dreams_path: str) -> None:
        """
        Executes the fine-tuning process using the prepared data.

        Args:
            fine_tuning_data (dict): Data prepared for fine-tuning.
        """
        
        llamacpp_folder = "llama_cpp"
        finetune_tool = "finetune"
        lora_tool = "export-lora"

        finetune_tool_path = os.path.join(llamacpp_folder, finetune_tool)
        lora_tool_path = os.path.join(llamacpp_folder, lora_tool)

        # Check if finetune_tool_path is a valid file
        if not os.path.isfile(finetune_tool_path):
            raise FileNotFoundError(f"Fine-tuning tool not found at {finetune_tool_path}")

        # Check if lora_tool_path is a valid file
        if not os.path.isfile(lora_tool_path):
            raise FileNotFoundError(f"LoRA tool not found at {lora_tool_path}")

        
        # Fine-tuning command
        finetune_command = [
            finetune_tool_path,
            "--model-base", self._base_model_path,
            "--train-data", dreams_path,
            "--threads", self._available_threads,
            "--sample-start", "<s>",
            "--epochs", self._epochs
        ]

        self.logger.murmur(f"Self-finetuning: Creating matrix")
        self.logger.debug(f"Running command:\n{finetune_command}.")

        try:
            subprocess.run(finetune_command, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Self-finetuning session failed the return code {e.returncode}.")   
            return False
        
        # Export LoRA model command - output to llm_tmp.guff
        tmp_model_path = r"llm_tmp.guff"
        export_command = [
            lora_tool_path,
            "--model-base", self._base_model_path,
            "--model-out", tmp_model_path,
            "--lora-scaled", self._latest_lora_path, self.lora_weight
        ]

        self.logger.murmur(f"Self-finetuning: Merging weights")
        self.logger.debug(f"Running command:\n{export_command}.")

        try:
            subprocess.run(export_command, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"LoRA merge failed with the return code {e.returncode}.")   
            return False        

        self.logger.murmur(f"Self-finetuning: Swapping brain to a new one")
        self.logger.info(f"Removing old {self._base_model_path}, moving {tmp_model_path} as new {self._base_model_path}.")
        StemUtility.transplantation(self._base_model_path, tmp_model_path)
    
    def _dream_prunning(self):
        """
        Archives dream materials by moving them from the dream storage path to the archive path.
        """
        
        self.logger.info("Archiving dream materials.")
        for file_name in os.listdir(self._dream_storage_path):
            StemUtility.archive(self._dream_storage_path, file_name)
        StemUtility.archive(self._conclusion_file)
    
    async def dream(self):
        """
        Orchestrates the whole process of selecting a summary, reading it, preparing fine-tuning data, and performing fine-tuning.
        """  

        self.logger.murmur(f"Closing eyes for a well-deserved nap.")
        self.logger.info(f"Self-finetuning process started.")        

        conclusions_found = self._gather_conclusion()        
        if not conclusions_found:
            return False
        self.logger.info(f"Selected conclusion to permeate.")
        dreams_path = await self._weave_dreams(self._dreams_number)  # Generate 50 materials, modify as needed
        self.logger.info(f"Self-finetuning materials generated. Staring self-finetuning.")        
        #await self._deepsleep(dreams_path)
        #self._dream_prunning()
        #self.logger.info(f"Self-finetuning session ended.")        


# Sensory Signal Processing (SSP)
class SensorySignalProcessing(ABC):
    """
    Abstract class for a stimulus processing module.

    This class serves as a blueprint for modules that manage interaction between a user and a model.
    """

    def __init__(self, pfc, engaged_event, interaction_storage_path, inactivity_limit=360):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.pfc = pfc
        
        self.engaged = engaged_event
        
        self.stimulus = None
        
        self._interaction_storage_path = interaction_storage_path
        
        self._inactivity_limit = inactivity_limit
        self._inactivity_count = 0


    @abstractmethod
    async def start_interaction(self):
        """
        Abstract method to start the interaction.
        """
        pass

    @abstractmethod
    async def _end_interaction(self):
        """
        Abstract method to end the interaction.
        """
        pass

    @abstractmethod
    def _summarize_interaction(self):
        """
        Abstract method to summarize the interaction.
        """
        pass
    
    @abstractmethod
    def _save_interaction_history(self):
        """
        Abstract method to save the interaction history.
        """
        pass

## Language Processing Module (LPM)
class LanguageProcessingModule(SensorySignalProcessing):
    """
    A class that manages the interaction between a human user and a language learning model (LLM).

    This class handles initializing conversation parameters, managing user input, generating
    responses using an LLM, and saving conversation history.
    """
    
    def __init__(self,
                 pfc,
                 engaged_event,
                 interaction_storage_path='conversations',
                 inactivity_limit=360):
        """
        Initializes the HumanInteraction class.

        Sets up the conversation environment, including the conversation prompt, keywords prompt,
        and conversation chain with the LLM.

        Args:
            pfc: The large learning model used for generating conversation responses.
            ready_for_input_event: An event flag indicating readiness for user input.
            interaction_storage_path: Path to a folder where all the conversations are being logged to 
        """

        super().__init__(pfc, engaged_event, interaction_storage_path, inactivity_limit)

        self.logger.debug(f"Instantiating {self.__class__.__name__} with interaction_storage_path: {interaction_storage_path}")

        self.ready_for_input = asyncio.Event()
        self.ready_for_input.set()  # Initially set to ready

        self._conversation_prompt = StemUtility.get_prompt("human_interaction")
        self._interaction_history = ''

        self._keywords_generation_prompt_template = StemUtility.get_prompt("keyword_generation")
    
    async def start_interaction(self):
        """
        Starts the conversation loop.

        This asynchronous method continually checks for user input, processes it,
        and generates responses using the LLM. The loop ends when the user inputs "end chat"
        or when the inactivity limit is reached.
        """
        self.engaged.set()
        
        
        self.logger.prompt(f"Conversation prompt template:\n{self._conversation_prompt}")        
        self.logger.debug(f"Initiated interaction")        
        
        while True:
            if not self.ready_for_input.is_set():
                self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
                self.logger.debug(f"Received input: {self.stimulus}")        

                if self.stimulus.lower() == "end chat":
                    await self._end_interaction()
                    break
              
                self._conversation_prompt += f"{self.stimulus} [/INST] "
                self._interaction_history += f"Human: {self.stimulus}\n"
                
                self.logger.monologue(f"LLM will receive: {self._conversation_prompt}")
                self.logger.debug(f"Awaiting LLM response")
                response = self.pfc(self._conversation_prompt)
                print("AI:", response)

                self._conversation_prompt += f"{response}</s><s> [INST] "
                self._interaction_history += f"AI: {response}\n"
                
                self.ready_for_input.set()  # Signal that the handler is ready for new input
                self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
                self._inactivity_count = 0
            else:
                await asyncio.sleep(1)
                self._inactivity_count += 1
                if (self._inactivity_count >= self._inactivity_limit) and self.engaged.is_set():
                    self.logger.debug(f"Inactivity count reached {self._inactivity_count} > {self._inactivity_limit}. Ending interaction.")        
                    await self._end_interaction()
                    break      
    
    async def _end_interaction(self):
        """
        Ends the conversation.

        This method saves the conversation history, clears event flags, and performs necessary cleanup actions.
        """
        self.logger.debug(f"Conversation cleanup started.")        
        self._save_interaction_history()
        self._conversation_prompt = StemUtility.get_prompt("human_interaction")
        self._interaction_history = ''
        self.ready_for_input.set()
        self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
        self._inactivity_count = 0
        self.engaged.clear()
    
    def _summarize_interaction(self):
        """
        Summarizes the conversation and returns the list of relevant keywords.

        Args:
            chat_history (str): The conversation history to summarize.

        Returns:
            list: A list of keywords summarizing the conversation.
        """
        self.logger.info(f"Interaction summarization started.")        
        self.logger.debug(f"Interaction history:\n{self._interaction_history}")    
        keywords_generation_prompt = self._keywords_generation_prompt_template.replace("{chat_history}", self._interaction_history)
        self.logger.prompt(f"Prompt for generating keywords from conversation:\n{keywords_generation_prompt}.")          
        keywords_generated_raw_output = self.pfc(keywords_generation_prompt)
        self.logger.monologue(f"Full text for summarizing conversation with keywords:\n{keywords_generated_raw_output}")  
        keywords_generated_pure = StemUtility.extract_keywords(keywords_generated_raw_output)
        
        return keywords_generated_pure

    def _save_interaction_history(self):
        """
        Saves the interaction history to a file.

        The interaction history is saved with a timestamp and a summary of the interaction is generated.
        """
        self.logger.info(f"Started conversation saving.")        
        interaction_keywords = self._summarize_interaction()
        memory_path = os.path.join(self._interaction_storage_path, f"conversation_{StemUtility.get_timestamp()}.txt")
        self.logger.debug(f"This conversation will be saved to: {memory_path}")                
        StemUtility.memory_write(memory_path, self._interaction_history)

        # Update the ShortTermMemory with the conversation and its keywords
        stm = ShortTermMemory()
        stm.memorize_keywrods(interaction_keywords, memory_path)
    
    async def get_user_input(self):
        """
        Continuously captures user input in an asynchronous loop.

        This method waits for the system to be ready for input, then captures and stores user input.
        It clears the 'ready for input' state after capturing the input.
        """
        self.logger.debug(f"Starting user input loop") 
        while True:
            await self.ready_for_input.wait()
            self.stimulus = await asyncio.get_event_loop().run_in_executor(None, input, "Enter something: ")
            self.logger.debug(f"User input received: {self.stimulus}.")
            asyncio.create_task(self.start_interaction())
            self.ready_for_input.clear()
            self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")


# Cognitive Feeback Router (CFR)

class CognitiveFeedbackRouter:
    
    def __init__(self, model_path: str = "llama-2-13b-chat.Q6_K.gguf", dmn_countdown: int = 60):
        """
        A class that manages the routing of cognitive feedback based on user input and system states.
    
        This class orchestrates various components, including a language learning model (LLM), user input handling,
        and managing different operational modes based on system states like 'sleeping' or 'overwhelmed'.
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Instantiating {self.__class__.__name__}")
        
        self.engaged = asyncio.Event()
        self.overwhelmed = asyncio.Event()
        
        self.lock = asyncio.Lock()
        
        self.pfc = None
        
        self._model_path = model_path
        self._conversation_handler = None
        
        self._dmn_countdown = dmn_countdown # time between last interaction and entering Default Mode
        
        self.logger.debug("Cognitive Feedback Router instantiated.")
        

    def _wakeup(self):
        """
        Wakes up the system and initializes the LLM.
        """
        self.logger.debug("Starting _wakeup() procedure.")    
        self.logger.murmur("Just a second, I'm waking up...")
        self.logger.debug(f"Initializing LLM model from {self._model_path}.")            
        self.pfc = LlamaCpp(model_path=self._model_path, 
                            n_ctx=4096,
                            max_tokens=4000,
                            n_batch=8)
        self.logger.debug(f"LLM model initialized.")                 
        self.overwhelmed.clear()
        self._conversation_handler = LanguageProcessingModule(self.pfc, self.engaged)            
        asyncio.create_task(self._conversation_handler.get_user_input())
        self.logger.flag(f"overwhelmed = {self.overwhelmed.is_set()}")
            
    async def attention_switch(self):
        """
        Manages the mode of operation based on user input and system states.

        This asynchronous method processes user inputs, manages conversation sessions,
        and handles the 'engaged' and 'overwhelmed' states of the system.
        """
        self._wakeup()
        self.logger.info(f"Starting infinite attention loop.") 
        while True:
            if self.overwhelmed.is_set():
                self.logger.info(f"Overwhelmed state detected.") 
                rem = ReflectiveEvolutionMonitor(pfc=self.pfc)
                await rem.dream()
                self._wakeup()
            elif not self.engaged.is_set():
                self.logger.debug(f"No environment interaction and no new conclusions detected. Preparing to switch to Default Mode.")                     
                for _ in range(self._dmn_countdown):
                    await asyncio.sleep(1)  # Sleep for 1 second
                    if self.engaged.is_set():
                        self.logger.debug(f"Cancelling Default Mode countdown due to environment interaction detection.")                                                 
                        break  # Exit the loop if the new stimuli is detected
                else:  # This else clause executes if the loop completes normally (no break)
                    self.logger.debug(f"Entering Default Mode.")                                                                         
                    dmn = DefaultModeNetwork(self.pfc, self.overwhelmed, self.engaged)
                    await dmn.ponder()
                    self.logger.debug(f"Default Mode quit.")                                                                                                 
            else:
                await asyncio.sleep(1)                


AS = CognitiveFeedbackRouter(model_path='llama-2-13b-chat.Q6_K.gguf', dmn_countdown=10)
asyncio.run(AS.attention_switch())