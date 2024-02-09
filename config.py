from os import cpu_count

# Location of the LLM file to serve as PFC
model_path = r"llama-2-13b-chat.Q8_0.gguf"

# Model temperature
model_temp = 1

# Time between last interaction and activating Default Mode Network (in seconds)
dmn_countdown = 120

# Time between last input and ending interaction session
interaction_timeout = 360

# End conversation keyword to be used to avoid waiting till interaction timeout
interaction_break = 'end_chat'

# Number of threads to be used in self-finetuning session
available_threads = cpu_count()

# Number of self-finetuning session training materials to be generated 
dreams_to_generate_num = 150

# Location of folder with finetune-realted binaries
finetune_dir = r"finetune_bins"

# Binary used for finetuning
finetune_tool = r"finetune"

# Binary used for merging LoRA weights with the base model
lora_tool = r"export-lora"

# Number of epochs in a self-finetuning session
epochs = 5

# File with lora parameters to integrate into base model
lora_to_integrate = r"ggml-lora-LATEST-f32.gguf"

# Weight of lora parameters at integration into base model 
lora_weight = 1

# Granularity level of logs saved to a file 
file_log_level = 10

# Granularity level of logs printed to console
console_log_level = 10

# Directory containing conversation's histories
conversations_dir = r"conversations"

# Directory containing conversation conclusions
conclusions_dir = r"conclusions"

# Directory containing generated training materials
context_dir = r"dreams"

#Log directory
log_dir = r"logs"

# Location of the JSON file serving as short term memory
stm_path = r"conversations/short-term-memory.json"

# Markers dividing different parts of generated dreams - needs to be aligned with a relevant prompt
dream_markers = {'stimulus': '**QUESTION**', 'reaction': '**RESPONSE**', 'end': '**END**'}
