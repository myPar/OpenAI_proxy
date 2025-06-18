import re
from exceptions import FormatServerException
from settings import FewShotMode
from dtos import ChatCompletionRequest, CompletionRequest, ChatMessage


def extract_boxed_content(text):
    match = re.search(r'\\boxed\{(.*?)}', text)
    if match:
        return match.group(1)
    return text


def postprocess_output(text: str, math_mode:bool) -> str:
    if text is None:
        return ""
    if math_mode:
        text = extract_boxed_content(text)
        text = text.strip()
        return text

    return text


def check_chat_format(request_dto: ChatCompletionRequest):
    messages: list = request_dto.messages
    
    if not isinstance(messages, list):
        raise FormatServerException("Input must be a list of chat messages.")    
    system_prompt_exists = False
    dialog_state = 'user'   # initial dialog state is user
    
    for i in range(len(messages)):
        dialog_item = messages[i]
        cur_role = dialog_item.role

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
            raise FormatServerException(f"invalid role {cur_role} in {i} chat item, only 'user', 'assistant', 'system' are supported: {str(dialog_item)}")
    # last message should be a user message
    if messages[-1].role != 'user':
        raise FormatServerException(f"last chat item should be an user prompt, got {messages[-1].role} instead")


def drop_few_shot(messages: list) -> list:
    result = []

    if len(messages) <= 1:
        return messages
    system_item = None if messages[0].role != 'system' else messages[0]
    assert messages[-1].role == 'user'

    if system_item is not None:
        result.append(system_item)
    result.append(messages[-1])

    return result


# returns one user message instead of chat dialog:
def join_few_shot(messages: list) -> list:
    i = 0
    system_prompt = None

    if len(messages) >= 2:
        if messages[0].role == 'system':
            system_prompt = messages[0].content
            if len(messages) == 2:
                assert messages[1].role == 'user'    # only user role can be after system
                result_msg = ChatMessage.model_validate({'role':'user', 'content': (system_prompt + "\n" if system_prompt.strip() != '' else "") + messages[1].content})

                return [result_msg]
        # build single dialog prompt:
        result_prompt = "" if system_prompt is None else system_prompt + "\n"
        result_prompt += "Ниже приведён пример ожидаемого от тебя диалога, ответь на последний запрос пользователя, с учётом контекста:\n"
        dialog_state = 'user'   # initial dialog state is user

        for i in range(1, len(messages)):
            dialog_item = messages[i]
            assert dialog_item.role == dialog_state
            content = dialog_item.content

            if dialog_state == 'user':
                result_prompt += "Пользователь: " + content + "\n"
                dialog_state = 'assistant'
            elif dialog_state == 'assistant':
                result_prompt += 'Твой ответ: ' + content + "\n"
                dialog_state = 'user'
            else:
                assert False
        assert messages[-1].role == 'user'
        result_msg = ChatMessage.model_validate({'role':'user', 'content': result_prompt})

        return [result_msg]
    else:
        return messages # no changes needed


def preprocess_math(request_dto: CompletionRequest) -> str:
    if request_dto.r1_settings.math:
        return "You will be given a problem. Please reason step by step, and put your final answer within \\boxed{}:\n" + request_dto.prompt
    return request_dto.prompt
    

def preprocess_math_chat(request_dto: ChatCompletionRequest) -> list:
    messages = request_dto.messages
    if not request_dto.r1_settings.math:
        return messages # no preprocessing
    result_messages = []

    for i in range(len(messages)):
        chat_item = messages[i]

        if chat_item.role == 'user':
            chat_item.content = "You will be given a problem. Please reason step by step, and put your final answer within \\boxed{}:\n" + chat_item.content
        result_messages.append(chat_item)

    return result_messages


def preprocess_few_shot(request_dto: ChatCompletionRequest) -> list:
    messages: list = request_dto.messages
    mode: FewShotMode = request_dto.r1_settings.few_shot_mode

    if mode == FewShotMode.NO_PREPROCESS:
        return messages
    elif mode == FewShotMode.DROP:
        messages = drop_few_shot(messages)
        return join_few_shot(messages)
    elif mode == FewShotMode.PREPROCESS:
        return join_few_shot(messages)
    else:
        assert False
