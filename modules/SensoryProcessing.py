import config
from modules import logging_utils

from modules.Stem import Stem
from modules.ShortTermMemory import ShortTermMemory

import logging
import asyncio
import os

from abc import ABC, abstractmethod

class SensoryProcessing(ABC):
    """
    Abstract class for a stimulus processing module.

    This class serves as a blueprint for modules that manage interaction between a user and a model.
    """

    def __init__(self, pfc, engaged_event: asyncio.Event, interaction_storage_path: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pfc = pfc
        self.engaged = engaged_event
        self.stimulus = None
        self._interaction_storage_path = interaction_storage_path
        self._interaction_timeout = config.interaction_timeout
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
class LanguageProcessingModule(SensoryProcessing):
    """
    A class that manages the interaction between a human user and a language learning model (LLM).

    This class handles initializing conversation parameters, managing user input, generating
    responses using an LLM, and saving conversation history.
    """
    
    def __init__(self,
                 pfc,
                 engaged_event: asyncio.Event = asyncio.Event(),
                 interaction_storage_path: str ='conversations'):
        """
        Initializes the LanguageProcessingModule class.

        Sets up the conversation environment, including the conversation prompt, keywords prompt,
        and conversation chain with the LLM.

        Args:
            pfc: The large learning model used for generating conversation responses.
            ready_for_input_event: An event flag indicating readiness for user input.
            interaction_storage_path: Path to a folder where all the conversations are being logged to 
        """

        super().__init__(pfc, engaged_event, interaction_storage_path)

        self.logger.info(f"Instantiating {self.__class__.__name__} with interaction_storage_path: {interaction_storage_path}")

        self.ready_for_input = asyncio.Event()
        self.ready_for_input.set()  # Initially set to ready

        self.stm = ShortTermMemory()

        self._conversation_prompt = Stem.get_prompt("human_interaction")
        self._interaction_history = ''

        self._keywords_generation_prompt_template = Stem.get_prompt("keyword_generation")
    
    async def start_interaction(self) -> None:
        """
        Starts the conversation loop.

        This asynchronous method continually checks for user input, processes it,
        and generates responses using the LLM. The loop ends when the user inputs interaction break keyword
        or when the inactivity limit is reached.
        """
        self.engaged.set()
        
        
        self.logger.prompt(f"Conversation prompt template:\n{self._conversation_prompt}")        
        self.logger.debug(f"Initiated interaction.")        
        
        while True:
            if not self.ready_for_input.is_set():
                self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
                self.logger.debug(f"Received input:\n{self.stimulus}")        

                if self.stimulus.lower() == config.interaction_break:
                    await self._end_interaction()
                    break
              
                self._conversation_prompt += f"{self.stimulus} [/INST] "
                self._interaction_history += f"User: {self.stimulus}\n"
                
                self.logger.monologue(f"LLM will receive following prompt:\n{self._conversation_prompt}")
                self.logger.debug(f"Awaiting response...")
                response = self.pfc.invoke(self._conversation_prompt)
                self.logger.murmur(f"Response generated:\n{response}") 
                print("AI:", response)

                self._conversation_prompt += f"{response}</s><s> [INST] "
                self._interaction_history += f"You: {response}\n"
                
                self.ready_for_input.set()  # Signal that the handler is ready for new input
                self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
                self._inactivity_count = 0
            else:
                await asyncio.sleep(1)
                self._inactivity_count += 1
                if (self._inactivity_count >= self._interaction_timeout) and self.engaged.is_set():
                    self.logger.debug(f"Inactivity count reached {self._inactivity_count} > {self._interaction_timeout}. Ending interaction.")        
                    await self._end_interaction()
                    break      
    
    async def _end_interaction(self) -> None:
        """
        Ends the conversation.

        This method saves the conversation history, clears event flags, and performs necessary cleanup actions.
        """
        self.logger.debug(f"Conversation cleanup started.")        
        self._save_interaction_history()
        self._conversation_prompt = Stem.get_prompt("human_interaction")
        self._interaction_history = ''
        self.ready_for_input.set()
        self.logger.flag(f"ready_for_input: {self.ready_for_input.is_set()}")
        self._inactivity_count = 0
        self.engaged.clear()
    
    def _summarize_interaction(self) -> list:
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
        self.logger.prompt(f"Prompt for generating keywords from conversation:\n{keywords_generation_prompt}")          
        keywords_generated_raw_output = self.pfc.invoke(keywords_generation_prompt)
        self.logger.monologue(f"Full text for summarizing conversation with keywords:\n{keywords_generated_raw_output}")  
        keywords_generated_pure = Stem.extract_keywords(keywords_generated_raw_output)
        
        return keywords_generated_pure

    def _save_interaction_history(self) -> None:
        """
        Saves the interaction history to a file.

        The interaction history is saved with a timestamp and a summary of the interaction is generated.
        """
        
        memory_path = os.path.join(self._interaction_storage_path, f"conversation_{Stem.get_timestamp()}.txt")
        self.logger.debug(f"This conversation will be saved to: {memory_path}")                
        Stem.memory_write(memory_path, self._interaction_history)
        self.logger.debug(f"Starting conversation saving.")        
        interaction_keywords = self._summarize_interaction()
        
        # Update the ShortTermMemory with the conversation and its keywords
        self.stm.memorize_keywords(interaction_keywords, memory_path)
    
    async def get_user_input(self) -> None:
        """
        Continuously captures user input in an asynchronous loop.

        This method waits for the system to be ready for input, then captures and stores user input.
        It clears the 'ready for input' state after capturing the input.
        """
        self.logger.debug(f"Starting user input loop.") 
        while True:
            await self.ready_for_input.wait()
            self.stimulus = await asyncio.get_event_loop().run_in_executor(None, input, "Enter something: ")
            self.logger.debug(f"User input received:\n{self.stimulus}")
            asyncio.create_task(self.start_interaction())
            self.ready_for_input.clear()
            self.logger.flag(f"Ready for input state: {self.ready_for_input.is_set()}")