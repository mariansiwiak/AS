import config
from modules import logging_utils

from modules.Stem import Stem

import logging
import asyncio
import subprocess
import os
from glob import glob
from typing import Optional, Union

class ReflectiveEvolutionMonitor:
    """
    A class designed to enable a language learning model (LLM) to self-reflect and evolve based on the conclusions drawn from user interactions.
    The class uses the same LLM for reading summaries, preparing fine-tuning materials, and the fine-tuning process.
    """

    def __init__(self, pfc):
        """
        Initializes the ReflectiveEvolutionMonitor class. 

        Arguments:
            pfc: Large Language Model used as a base of the system
            base_model_path: path to  LLM model file on disk
            conclusions_storage_path: path to folder containing not-permeated new perspectives
            dream_storage_path: path to a folder to store finetune materials to be used in this session
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Instantiating {self.__class__.__name__}")
    
        self.pfc = pfc
        
        self._base_model_path = config.model_path

        self._conclusions_dir = config.conclusions_dir
        Stem.prepare_directory(self._conclusions_dir)
        self._conclusion_file = None
        
        self._dream_storage_path = config.context_dir
        Stem.prepare_directory(self._dream_storage_path)

        self._dream_spinning_prompt_template = Stem.get_prompt("dream_spinning")
        self._dream_prompt_template = Stem.get_prompt("dream_template")

        self._conclusions = ''
        
        self._dreams_to_generate_num = config.dreams_to_generate_num
        self._available_threads = str(config.available_threads)
        self._epochs = str(config.epochs)
        self.lora_weight = str(config.lora_weight)

        self._lora_to_integrate = config.lora_to_integrate    
    
    def _gather_conclusion(self) -> bool:
        """
        Reads a summary document as a text file.

        Returns:
            bool: True if the summary was successfully read, False otherwise.
        """

        conclusions_pattern = os.path.join(self._conclusions_dir, "conclusion*")
        self.logger.debug(f"Searching for following pattern:\n{conclusions_pattern}.")
        conclusion_files = glob(conclusions_pattern)
        self.logger.debug(f"Following files found: {conclusion_files}")

        if not conclusion_files:
            self.logger.error("No conclusion files matching the pattern found.")
            return False

        # Process the first file from the matched conclusion files
        self._conclusion_file = conclusion_files[0]
        self.logger.debug(f"Conclusion file to be processed: {self._conclusion_file}")
        self._conclusions = Stem.memory_read(self._conclusion_file)
        return True

    def _spin_dream(self, dream_prompt: str) -> Union[str, None]:
        """
        Prepares a single piece of data required for the fine-tuning process by interpreting the summary content.

        Args:
            dream_prompt (str): Prompt to generate a single piece of training material.

        Returns:
            dict: Data structured for fine-tuning.
        """

        dream_content = self.pfc.invoke(dream_prompt)
        self.logger.monologue(f"I had a dream:\n{dream_content}")

        try:
            stimulus_start = dream_content.index(config.dream_markers['stimulus']) + len(config.dream_markers['stimulus'])
            response_start = dream_content.index(config.dream_markers['reaction'])
            end_tag = dream_content.index(config.dream_markers['end'])
    
            dreamt_stimulus = dream_content[stimulus_start:response_start].strip()
            dreamt_stimulus = Stem.clean_string(dreamt_stimulus)
            self.logger.prompt(f"Dreamt stimulus:\n{dreamt_stimulus}")
            
            dreamt_reaction = dream_content[response_start + len(config.dream_markers['reaction']):end_tag].strip()
            dreamt_reaction = Stem.clean_string(dreamt_reaction)
            self.logger.prompt(f"Dreamt response:\n{dreamt_reaction}")

            if len(dreamt_stimulus) > 0 and len(dreamt_reaction) > 0 and dreamt_reaction != config.dream_markers['end']:
                dream = self._dream_prompt_template.replace("{stimulus}", dreamt_stimulus) 
                dream = dream.replace("{reaction}", dreamt_reaction) 
                return dream
            else:
                return None
        
        except ValueError as e:
            return None
    

    async def _weave_dreams(self, num_dreams: int = 1) -> str:
        """
        Generates a specified number of materials (dreams) and writes them into a single text file.
        Each 'dream' is appended to the file as it is generated.

        Args:
            num_dreams (int): Number of training materials to be generated

        Returns:
            str: Concated training materials set
        """
        
        self.logger.info(f"Generating {num_dreams} dreams.")
        dreams_path = os.path.join(self._dream_storage_path, f"dream_{Stem.get_timestamp()}.txt")
        self.logger.debug(f"Dreams for this sessions will be saved to: {dreams_path}")        
        dream_spinning_prompt = self._dream_spinning_prompt_template.replace("{adaptation_summary}", self._conclusions) 
        self.logger.prompt(f"Prompt for generating training material from conversation conclusions:\n{dream_spinning_prompt}.")   

        generated_dreams = 0
        while generated_dreams < num_dreams:
            self.logger.info(f"Generating dream # {generated_dreams} of {num_dreams}.")
            dream = self._spin_dream(dream_spinning_prompt) 
            if dream:
                with open(dreams_path, 'a') as file: 
                    file.write(dream + '\n')
                generated_dreams += 1
        return dreams_path
    
    async def _deepsleep(self, dreams_path: str) -> None:
        """
        Executes the fine-tuning process using the prepared data.

        Args:
            fine_tuning_data (dict): Data prepared for fine-tuning.
        """
        
        finetune_dir = config.finetune_dir
        finetune_tool = config.finetune_tool
        lora_tool = config.lora_tool

        finetune_tool_path = os.path.join(finetune_dir, finetune_tool)
        lora_tool_path = os.path.join(finetune_dir, lora_tool)

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

        self.logger.murmur(f"Self-finetuning: Creating LoRA")
        self.logger.debug(f"Running command:\n{finetune_command}")

        try:
            subprocess.run(finetune_command, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Self-finetuning session failed the return code {e.returncode}")   
            return False
        
        # Export LoRA model command - output to llm_tmp.gguf
        tmp_model_path = r"llm_tmp.gguf"
        export_command = [
            lora_tool_path,
            "--model-base", self._base_model_path,
            "--model-out", tmp_model_path,
            "--lora-scaled", self._lora_to_integrate, self.lora_weight
        ]

        self.logger.murmur(f"Self-finetuning: Merging base model with LoRA")
        self.logger.debug(f"Running command:\n{export_command}")

        try:
            subprocess.run(export_command, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"LoRA merge failed with the return code {e.returncode}")   
            return False        

        self.logger.murmur(f"Self-finetuning: Transplanting brain to a new one.")
        self.logger.info(f"Removing old {self._base_model_path}, moving {tmp_model_path} as new {self._base_model_path}.")
        Stem.transplantation(self._base_model_path, tmp_model_path)
        Stem.finetune_cleanup()
            
    def _dream_prunning(self) -> None:
        """
        Archives dream materials by moving them from the dream storage path to the archive path.
        """
        
        self.logger.info("Archiving dream materials.")
        for file_name in os.listdir(self._dream_storage_path):
            if file_name[:6] == 'dream_':
                Stem.archive(self._dream_storage_path, file_name)
        Stem.archive(self._conclusion_file)
    
    async def dream(self) -> Optional[bool]:
        """
        Orchestrates the whole process of selecting a summary, reading it, preparing fine-tuning data, and performing fine-tuning.
        """  

        self.logger.murmur(f"Closing eyes for a well-deserved nap.")
        self.logger.info(f"Self-finetuning process started.")        

        conclusions_found = self._gather_conclusion()        
        if not conclusions_found:
            return False
        self.logger.info(f"Selected conclusion to permeate.")
        dreams_path = await self._weave_dreams(self._dreams_to_generate_num)  # Generate 50 materials, modify as needed
        self.logger.info(f"Self-finetuning materials generated. Staring self-finetuning.")        
        await self._deepsleep(dreams_path)
        self._dream_prunning()
        self.logger.info(f"Self-finetuning session ended.")        