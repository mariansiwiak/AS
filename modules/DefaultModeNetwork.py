import config
from modules import logging_utils

from modules.Stem import Stem
from modules.ShortTermMemory import ShortTermMemory

import logging
import asyncio
import os

class DefaultModeNetwork:
    """
    A class designed to integrate a language learning model (LLM) with a short-term memory storage system.
    This class enables the LLM to process and learn from saved conversation data autonomously.
    """

    def __init__(self,
                 pfc,
                 overwhelmed_event: asyncio.Event,
                 engaged_event: asyncio.Event
                ):
        """
        Initializes the DefaultModeNetwork class by setting up the short-term memory (STM) component.
        """
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Instantiating {self.__class__.__name__}")
        self.logger.flag(f"Overhelmed state: {overwhelmed_event.is_set()}") 
        
        self.stm = ShortTermMemory()
        self.pfc = pfc

        self.overwhelmed = overwhelmed_event
        self.engaged = engaged_event
        
        self._conclusions_dir = config.conclusions_dir
        Stem.prepare_directory(self._conclusions_dir)          

        self._keyword_selection_prompt_template = Stem.get_prompt("keyword_selection")
        self._perspective_explanation_prompt_template = Stem.get_prompt("perspective_explanation")
    
    
    async def _interesting_keywords_selection(self, keywords) -> list:
        """
        Delects a subset of keywords deemed interesting or relevant by the LLM.

        Args:
            keywords (list): A list of keywords to choose from.

        Returns:
            list: A subset of selected keywords.
        """

        starred_keywords = [f"**{keyword}**" for keyword in keywords]
        keywords_selection_prompt = self._keyword_selection_prompt_template.replace("{keywords_list}", ', '.join(starred_keywords))
        self.logger.prompt(f"Interesting keyword selection prompt:\n{keywords_selection_prompt}")        
        self.logger.debug(f"Asking LLM to select interesting keywords.")   
        keywords_selected_raw_output = self.pfc.invoke(keywords_selection_prompt)
        self.logger.monologue(f"LLM selected interesting keywords:\n{keywords_selected_raw_output}.\nMoving to keywords extraction.")   
        keywords_selected_pure = Stem.extract_keywords(keywords_selected_raw_output)
        self.logger.debug(f"Automatically detected keywords: {keywords_selected_pure}")   
        
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
        adaptation_explanation = self.pfc.invoke(perspective_explanation_prompt)
        self.logger.monologue(f"Full explanation of the required adaptation:\n{adaptation_explanation}")   
        return adaptation_explanation

    async def ponder(self) -> bool:
        """
        The main asynchronous method of the class that orchestrates the process of 
        selecting keywords, fetching conversations, and analyzing them.
        """

        self.logger.debug(f"Checking if there are any unprocessed conclusions.")           
        conclusion_files = [f for f in os.listdir(self._conclusions_dir) if f.startswith("conclusion_")]
        if conclusion_files:
            self.logger.debug(f"Found conclusion files: {conclusion_files}. Setting overwhelmed status.")
            self.overwhelmed.set()
            return True
        
        self.logger.debug(f"Checking if there are any topics to be analyzed deeper.")           
        all_keywords = self.stm.recall_all_keywords()
        if not all_keywords:
            self.logger.murmur(f"Kingdom for a good book!")
            return False

        self.logger.debug(f"Moving to selecting interesting keywords from: {all_keywords}")           
        interesting_keywords = await self._interesting_keywords_selection(all_keywords)
        self.logger.debug(f"Interesting keywords selected: {interesting_keywords}")           
        memory_files, concatenated_memories = self._fetch_memory(interesting_keywords)
        self.logger.debug(f"Concatenated conversations received.")   

        if concatenated_memories:
            self.logger.debug(f"Moving to analyze the conversation histories.")           
            adaptation_summary = await self._analyze_interaction(concatenated_memories)
            conclusion_file = os.path.join(self._conclusions_dir, f"conclusion_{Stem.get_timestamp()}.txt")
            self.logger.debug(f"Conclusions saved to {conclusion_file} .")
            Stem.memory_write(conclusion_file, adaptation_summary)
            if "**uninspiring**" not in adaptation_summary.lower():
                self.logger.murmur(f"Discussion on {interesting_keywords} indeed brought a new perspective...")
                self.overwhelmed.set()
                self.logger.flag(f"Overwhelmed state: {self.overwhelmed.is_set()}")
            else:
                self.logger.monologue(f"As per:\n{adaptation_summary}\nNothing of interest has been found in {memory_files}.")
                Stem.archive(conclusion_file)
        else:
            self.logger.error(f"Concatenated conversations turned out to be an empty string.")   
        self.logger.debug(f"Interesting or not, forgetting conversations about {interesting_keywords}.")   
        self.stm.forget_keywords(interesting_keywords)
        return True