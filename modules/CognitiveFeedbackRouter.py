import config
from modules import logging_utils

from modules.SensoryProcessing import LanguageProcessingModule
from modules.Stem import Stem
from modules.ShortTermMemory import ShortTermMemory
from modules.ReflectiveEvolutionMonitor import ReflectiveEvolutionMonitor
from modules.DefaultModeNetwork import DefaultModeNetwork

from langchain_community.llms import LlamaCpp
import logging
import asyncio

class CognitiveFeedbackRouter:
    def __init__(self):
        """
        A class that manages the routing of cognitive feedback based on user input and system states.
    
        This class orchestrates various components, including a language learning model (LLM), user input handling,
        and managing different operational modes based on system states like 'sleeping' or 'overwhelmed'.
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Instantiating {self.__class__.__name__}")
        
        self.engaged = asyncio.Event()
        self.overwhelmed = asyncio.Event()
        
        self.pfc = None
        
        self._dmn_countdown = config.dmn_countdown
        
        self.logger.debug("Cognitive Feedback Router instantiated.")        

    async def _sharpen_senses(self) -> None:
        "Starts sensory functions"
        _conversation_handler = LanguageProcessingModule(self.pfc, self.engaged)            
        asyncio.create_task(_conversation_handler.get_user_input())

    async def _wakeup(self) -> None:
        """
        Wakes up the system and initializes the LLM.
        """
        self.logger.debug("Starting _wakeup() procedure.")    
        self.logger.murmur("Just a second, I'm waking up...")
        self.logger.debug(f"Initializing LLM model from {config.model_path}")
        try:
            self.logger.debug(f"Loading LLM.")            
            self.pfc = LlamaCpp(model_path=config.model_path,
                                temperature=config.model_temp,
                                n_ctx=4096,
                                max_tokens=4000,
                                n_parts=config.available_threads,
                                n_batch=4*config.available_threads)
        except Exception as e:
            self.logger.error(f"Error initializing LLM model: {e}")
            raise
        self.logger.debug(f"LLM initialized.")                 
        self.overwhelmed.clear()
        self.logger.flag(f"Overwhelmed status: {self.overwhelmed.is_set()}")
        await self._sharpen_senses()

    async def attention_switch(self) -> None:
        """
        Manages the mode of operation based on user input and system states.

        This asynchronous method processes user inputs, manages conversation sessions,
        and handles the 'engaged' and 'overwhelmed' states of the system.
        """
        await self._wakeup()
        self.logger.info(f"Starting infinite attention loop.") 
        while True:
            if self.overwhelmed.is_set():
                self.logger.info(f"Overwhelmed state: {self.overwhelmed.is_set()}") 
                rem = ReflectiveEvolutionMonitor(pfc=self.pfc)
                await rem.dream()
                await self._wakeup()
            elif not self.engaged.is_set():
                self.logger.debug(f"No environment interaction and no new conclusions detected. Preparing to switch to Default Mode.")                     
                for _ in range(self._dmn_countdown):
                    await asyncio.sleep(1)
                    if self.engaged.is_set():
                        self.logger.debug(f"Cancelling Default Mode countdown due to environment interaction detection.")
                        break
                else:
                    self.logger.debug(f"Entering Default Mode.")                                                                         
                    dmn = DefaultModeNetwork(self.pfc, self.overwhelmed, self.engaged)
                    await dmn.ponder()
                    self.engaged.clear()
                    await self._sharpen_senses()
                    self.logger.debug(f"Default Mode quit.")                                                                                                 
            else:
                await asyncio.sleep(1)
