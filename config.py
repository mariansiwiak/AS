from os import cpu_count

# Location of the LLM file to serve as PFC
model_path='llama-2-13b-chat.Q8_0.gguf'

# Model temperature
model_temp = 1

# Time between last interaction and activating Default Mode Network (in seconds)
dmn_countdown = 120

# Time between last input and ending interaction session
interaction_timeout = 360

# End conversation keyword to be used to avoid waiting till interaction timeout
interaction_break = "end_chat"

# Number of threads to be used in self-finetuning session
available_threads = cpu_count()

# Number of self-finetuning session training materials to be generated 
dreams_to_generate_num = 500

# Location of folder with finetune-realted binaries
finetune_dir = "finetune_bins"

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

# Directory containing conversation conclusions
conclusions_dir = 'conclusions'

# Directory containing generated training materials
context_dir = 'dreams'

#Log directory
log_dir = 'logs'
