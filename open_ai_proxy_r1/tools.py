import re
from exceptions import FatalServerException, FormatServerException


def extract_boxed_content(text):
    match = re.search(r'\\boxed\{(.*?)}', text)
    if match:
        return match.group(1)
    return text


def postprocess_output(text: str, postprocess:bool) -> str:
    if text is None:
        return ""
    if postprocess:
        text = extract_boxed_content(text)
        text = text.strip()
    return text


def check_chat_format(messages: list):
    if not isinstance(messages, list):
        raise FatalServerException("Input must be a list of chat messages.")    
    system_prompt_exists = False
    dialog_state = 'user'   # initial dialog state is user

    if len(messages) == 0:
        raise FormatServerException(f'empty messages list provided')
    
    for i in range(len(messages)):
        dialog_item = messages[i]

        if 'role' not in dialog_item:
            raise FatalServerException(f'no role field in {i} chat item: {str(dialog_item)}')
        if 'content' not in dialog_item:
            raise FatalServerException(f'no content field in {i} chat item: {str(dialog_item)}')
        cur_role = dialog_item['role']

        # check system prompt
        if cur_role == 'system':
            if system_prompt_exists:
                raise FormatServerException(f'system prompt already exists another one found in {i} chat item')
            if i != 0:
                raise FormatServerException(f"system prompt should be at the dialog's start, but found in {i} chat item")
            if len(messages) == 1:
                # only system prompt exists
                raise FormatServerException(f"only system prompt exists, no another chat items")
            system_prompt_exists = True
        elif cur_role == 'user':
            if dialog_state != 'user':
                raise FormatServerException(f"expected '{dialog_state}' dialog role in {i} chat item, but got user instead")
            dialog_state = 'assistant'
        elif cur_role == 'assistant':
            if dialog_state != 'assistant':
                raise FormatServerException(f"expected '{dialog_state}' dialog role, in {i} chat item but got assistant instead")
            dialog_state = 'user'   
        else:
            raise FatalServerException(f"invalid role {cur_role} in {i} chat item, only 'user', 'assistant', 'system' are supported: {str(dialog_item)}")
    # last message should be a user message
    if messages[-1]['role'] != 'user':
        raise FormatServerException(f"last chat item should be an user prompt, got {messages[-1]['role']} instead")


# returns one user message instead of chat dialog:
def preprocess_few_shot(messages: list) -> list:
    i = 0
    system_prompt = None

    if len(messages) >= 2:
        if messages[0]['role'] == 'system':
            system_prompt = messages[0]['content']
            if len(messages) == 2:
                assert messages[1]['role'] == 'user'    # only user role can be after system
                
                return [{'role':'user', 'content': system_prompt + "\n" + messages[0]['content']}]
        # build single dialog prompt:
        result_prompt = "" if system_prompt is None else system_prompt + "\n"
        result_prompt += "here is a dialog, answer user's last query:\n"
        dialog_state = 'user'   # initial dialog state is user

        for i in range(1, len(messages)):
            dialog_item = messages[i]
            #print(f'dialog state = {dialog_state}, dialog_item role = {dialog_item['role']}')
            assert dialog_item['role'] == dialog_state
            content = dialog_item['content']

            if dialog_state == 'user':
                result_prompt += "USER: " + content + "\n"
                dialog_state = 'assistant'
            elif dialog_state == 'assistant':
                result_prompt += 'ASSISTANT: ' + content + "\n"
                dialog_state = 'user'
            else:
                assert False
        assert messages[-1]['role'] == 'user'

        return [{'role':'user', 'content': result_prompt}]
    else:
        return messages # no changes needed


def preprocess_math(prompt: str) -> str:
    return "You will be given a problem. Please reason step by step, and put your final answer within \\boxed{}:\n" + prompt


def preprocess_math_chat(messages: list) -> list:
    result_messages = []

    for i in range(len(messages)):
        chat_item = messages[i]
        if chat_item['role'] == 'user':
            chat_item['content'] = "You will be given a problem. Please reason step by step, and put your final answer within \\boxed{}:\n" + chat_item['content']
        result_messages.append(chat_item)

    return result_messages


def preprocess_system_prompt_chat(messages: list) -> list:
    result_messages = []
    sys_prompt = None
    i = 0

    while i < len(messages):
        chat_item = messages[i]
        if chat_item['role'] == 'system':
            sys_prompt = chat_item['content']
            i += 1
            continue
        if sys_prompt is not None and sys_prompt.strip() != "" and chat_item['role'] == 'user':
            chat_item['content'] = sys_prompt + '\n' + chat_item['content']
        result_messages.append(chat_item)

    return result_messages
