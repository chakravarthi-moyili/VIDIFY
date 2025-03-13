from shortGPT.gpt import gpt_utils
import json
import time
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_markdown(text):
    """Formats the given text as Markdown."""
    # Add your markdown formatting logic here
    return text

def generateScript(script_description, language):
    out = {'script': ''}
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/chat_video_script.yaml')
    chat = chat.replace("<<DESCRIPTION>>", script_description).replace("<<LANGUAGE>>", language)
    retry_count = 0
    max_retries = 5
    retry_delay = 1

    while not ('script' in out and out['script']):
        try:
            result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1)
            try:
                # Remove Markdown code block
                result = re.sub(r'^\s*```(?:json)?\s*', '', result)
                result = re.sub(r'\s*```\s*$', '', result)

                out = json.loads(result)
            except json.JSONDecodeError as json_error:
                logging.error(f"JSON parsing error: {json_error}, raw response: {result}")
                out = {'script': f"Error: Could not parse LLM response. Raw response: {result}"}
            retry_count = 0
        except Exception as e:
            if "429 Resource has been exhausted" in str(e) and retry_count < max_retries:
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay *= 2
                logging.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds. Retry {retry_count}/{max_retries}")
            else:
                logging.error(f"Error in generateScript: {e}")
                break
    return format_markdown(out['script'])

def correctScript(script, correction):
    out = {'script': ''}
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/chat_video_edit_script.yaml')
    chat = chat.replace("<<ORIGINAL_SCRIPT>>", script).replace("<<CORRECTIONS>>", correction)
    retry_count = 0
    max_retries = 5
    retry_delay = 1

    while not ('script' in out and out['script']):
        try:
            result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1)
            try:
                # Remove Markdown code block
                result = re.sub(r'^\s*```(?:json)?\s*', '', result)
                result = re.sub(r'\s*```\s*$', '', result)

                out = json.loads(result)
            except json.JSONDecodeError as json_error:
                logging.error(f"JSON parsing error: {json_error}, raw response: {result}")
                out = {'script': f"Error: Could not parse LLM response. Raw response: {result}"}
            retry_count = 0
        except Exception as e:
            if "429 Resource has been exhausted" in str(e) and retry_count < max_retries:
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay *= 2
                logging.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds. Retry {retry_count}/{max_retries}")
            else:
                logging.error(f"Error in correctScript: {e}")
                break
    return format_markdown(out['script'])


























# from shortGPT.gpt import gpt_utils
# import json
# def generateScript(script_description, language):
#     out = {'script': ''}
#     chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/chat_video_script.yaml')
#     chat = chat.replace("<<DESCRIPTION>>", script_description).replace("<<LANGUAGE>>", language)
#     while not ('script' in out and out['script']):
#         try:
#             result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1)
#             out = json.loads(result)
#         except Exception as e:
#             print(e, "Difficulty parsing the output in gpt_chat_video.generateScript")
#     return out['script']

# def correctScript(script, correction):
#     out = {'script': ''}
#     chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/chat_video_edit_script.yaml')
#     chat = chat.replace("<<ORIGINAL_SCRIPT>>", script).replace("<<CORRECTIONS>>", correction)

#     while not ('script' in out and out['script']):
#         try:
#             result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1)
#             out = json.loads(result)
#         except Exception as e:
#             print("Difficulty parsing the output in gpt_chat_video.generateScript")
#     return out['script']