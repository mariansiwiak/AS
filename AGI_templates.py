# Set up the base template
interaction_template = """
<s>[INST] <<SYS>>
Engage in a bidirectional communication and a meaningful interaction in a way you find appropriate. 
If you feel like getting some additional information from external sources, you have access to the following tools:
{tools}
You must use the following format:

Discussed issue: the topic of the interaction 
Thought: you should think about refining your answer by interating over your initial response to see if it really reflects what you want to communicate.
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

<</SYS>>

Discussed issue: {input}
{agent_scratchpad} [/INST]
"""

