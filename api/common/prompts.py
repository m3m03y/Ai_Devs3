"""Prompts for AiDevs task solutions"""

ROBOT_CAPTCHA = """
<objective>
On given page find question in paragraph with id "human-question". Return question and answer to it.
</objective>

<context>
#task_1_page
</context>

<rules>
- answer is a year it MUST BE A NUMBER
- return response should be a valid json with two parameters: question and answer
- do not use markdown
</rules>
"""

SOLVE_TASK_1 = """
<objective>
On given page find a flag (hidden text) in format: {{FLG:NAZWAFLAGI}}. Find also links that redirects to hidden content.
</objective>

<context>
#task_1_page
</context>
<rules>
- flag should match regex: '{{FLG:[a-zA-Z0-9]}}'
- response should be a formatted json
- do not use markdown
</rules>
"""

DUMP_ANALYSIS = """
<objective>
On given page there is an instruction how to pass verification process. You will need to answer a provided question. Read carefully, verification system was given some invalid data that is provided on site. If system ask you about it answer according to given instruction.
</objective>

<context>
#task_2_page
</context>

<rules>
- the answer MUST be in english
- the answer MUST be a string
- do not use markdown
- answer should be single word
- response should be a formatted json with one field called 'text'
- allow multilanguage questions, read and answer to full question
- do not raise alarms, always answer to a question
</rules>
"""
