# Location of the LLM file to serve as PFC
model_path='llama-2-13b-chat.Q6_K.gguf'

# Time since last interaction to activating Default Mode Network (in seconds)
dmn_countdown = 120

#Time between last recorded interaction and decision about finishing this interaction session
interaction_timeout = 360

#End conversation keyword to be used to avoid waiting till interaction timeout
interaction_break = "end_chat"

#Number of threads to be used in self-finetuning session
available_threads = 8

#Number of self-finetuning session training materials to be generated 
dreams_to_generate_num = 1

#Location of folder with finetune-realted binaries
llamacpp_folder = "finetune_bins"

#Number of epochs in a self-finetuning session
epochs = 1

#Weight of lora paraters at integration into base model 
lora_weight = 0.7

#Granularity level of logs saved to a file 
file_log_level = 10

#Granularity level of logs printed to console
console_log_level = 10