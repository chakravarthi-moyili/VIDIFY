import os
import traceback
from enum import Enum

import gradio as gr
import requests
import time

from gui.asset_components import AssetComponentsUtils
from gui.ui_abstract_component import AbstractComponentUI
from gui.ui_components_html import GradioComponentsHTML
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
from shortGPT.config.api_db import ApiKeyManager
from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
                                       ELEVEN_SUPPORTED_LANGUAGES,
                                       LANGUAGE_ACRONYM_MAPPING,
                                       Language)
from shortGPT.engine.content_video_engine import ContentVideoEngine
from shortGPT.gpt import gpt_chat_video


class Chatstate(Enum):
    IDLE = 1
    GENERATE_SCRIPT = 2
    MAKE_VIDEO = 3


class VideoAutomationUI(AbstractComponentUI):
    def __init__(self, shortGptUI: gr.Blocks):
        self.shortGptUI = shortGptUI
        self.state = Chatstate.IDLE
        self.isVertical = False
        self.voice_module = None
        self.language = Language.ENGLISH
        self.script = ""
        self.video_html = ""
        self.video_path = ""
        self.video_automation = None
        self.api_source = "Pexels"  # Default API source
        self.text_position = "Middle"  # Changed default to Middle
        self.quality = "4k"  # Changed default to 4k
        self.duration = 15  # Default duration of 15 seconds
        self.video_generated = False
        # Sample video paths - update these with your actual sample videos
        self.landscape_sample = "assets/videos/Sample_Landscape.mp4"
        self.vertical_sample = "assets/videos/Sample_Vertical.mp4"

    def check_api_keys(self):
        """Check if required API keys are available"""
        missing_keys = []
        
        # Check for Gemini API key
        gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
        openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
        
        if not gemini_key and not openai_key:
            missing_keys.append("Gemini or OpenAI")
        
        # Check video API keys based on orientation
        if self.isVertical:
            pexels_key = ApiKeyManager.get_api_key("PEXELS_API_KEY")
            if not pexels_key:
                missing_keys.append("Pexels")
        else:
            pixabay_key = ApiKeyManager.get_api_key("PIXABAY_API_KEY")
            if not pixabay_key:
                missing_keys.append("Pixabay")
        
        if missing_keys:
            return f"Missing API keys: {', '.join(missing_keys)}. Please go to the config tab and enter the required API keys."
        return None

    def generate_script(self, message, language):
        """Generate a script based on the description and language"""
        self.state = Chatstate.GENERATE_SCRIPT
        return gpt_chat_video.generateScript(message, language)
        
        # # Validate inputs
        # if not description:
        #     return "Please provide a description for your video."
        
        # # Check API keys
        # missing_keys = self.check_api_keys()
        # if missing_keys:
        #     return missing_keys
        
        # try:
        #     # Convert language string to Language enum if needed
        #     if isinstance(language_value, str):
        #         language = next((lang for lang in Language if lang.value == language_value), Language.ENGLISH)
        #     else:
        #         language = language_value
            
        #     self.language = language
            
        #     # Check which API key is available
        #     gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
        #     openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
            
        #     if gemini_key:
        #         # Use Gemini API
        #         self.script = generateScript(description, language.value, api_type="gemini")
        #     elif openai_key:
        #         # Use OpenAI API
        #         self.script = generateScript(description, language.value, api_type="openai")
        #     else:
        #         return "No valid API key found for Gemini or OpenAI."
            
        #     # Make script block visible
        #     return self.script
        # except Exception as e:
        #     traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        #     error_message = f"Error generating script: {str(e)}\n{traceback_str}"
        #     print(error_message)
        #     return f"Error generating script: {str(e)}"

    def correct_script(self, script, correction):
        """Apply corrections to the script"""
        return gpt_chat_video.correctScript(script, correction)
        # try:
        #     gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
        #     openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
            
        #     if gemini_key:
        #         corrected_script = gpt_chat_video.correctScript(script, correction, api_type="gemini")
        #     elif openai_key:
        #         corrected_script = gpt_chat_video.correctScript(script, correction, api_type="openai")
        #     else:
        #         return "No valid API key found for Gemini or OpenAI."
            
        #     self.script = corrected_script
        #     return corrected_script
        # except Exception as e:
        #     return f"Error correcting script: {str(e)}"

    def setup_voice_module(self):
        """Set up the EdgeTTS voice module as specified"""
        try:
            # Only use EdgeTTS as specified
            self.voice_module = EdgeTTSVoiceModule(EDGE_TTS_VOICENAME_MAPPING[self.language]['male'])
            return True, "Voice module set up successfully"
        except Exception as e:
            return False, f"Error setting up voice module: {str(e)}"

    def make_video(self, script, orientation_choice, text_position, quality, duration):
        """Generate the video based on script and settings"""
        self.state = Chatstate.MAKE_VIDEO
        
        # Set orientation
        self.isVertical = True if orientation_choice == "Vertical" else False
        
        # Set API source based on orientation
        self.api_source = "Pexels" if self.isVertical else "Pixabay"
        
        # Save the settings
        self.text_position = text_position
        self.quality = quality
        self.duration = duration
        
        # Set up voice module
        success, message = self.setup_voice_module()
        if not success:
            return None, message
        
        # Check API keys
        missing_keys = self.check_api_keys()
        if missing_keys:
            return None, missing_keys
        
        try:
            # Create video engine
            videoEngine = ContentVideoEngine(
                voiceModule=self.voice_module, 
                script=script, 
                isVerticalFormat=self.isVertical,
                api_source=self.api_source,
                # text_position=self.text_position,
                # quality=self.quality,
                # duration=self.duration
            )
            
            # Set up progress tracking
            num_steps = videoEngine.get_total_steps()
            progress_counter = 0
            
            def logger(prog_str):
                nonlocal progress_counter
                # progress(progress_counter / num_steps, f"Creating video - {progress_counter} - {prog_str}")
                progress_counter += 1
            
            videoEngine.set_logger(logger)
            
            # Generate the video
            for step_num, step_info in videoEngine.makeContent():
                # progress(progress_counter / num_steps, f"Creating video - {step_info}")
                progress_counter += 1
            
            # Get the output path
            self.video_path = videoEngine.get_video_output_path()
            return self.video_path, script
            
        except requests.exceptions.ChunkedEncodingError as e:
            error_message = f"Network error while streaming content: {str(e)}"
            print(error_message)
            return None, "Network error while streaming content. Please check your internet connection and try again."
        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            error_message = f"Error generating video: {str(e)}\n{traceback_str}"
            print(error_message)
            return None, f"Error generating video: {str(e)}"

    def update_script_block_visibility(self, script):
        """Update the visibility of the script block based on script content"""
        if script and script.strip():
            return gr.update(visible=True), gr.update(visible=True), gr.update(value=script, visible=True)
        return gr.update(visible=False), gr.update(visible=False), gr.update(value="", visible=False)

    def update_video_block_visibility(self, video_path, script):
        """Update the visibility of video block based on video path"""
        if video_path and os.path.exists(video_path):
            return (
                gr.update(visible=True),
                gr.update(value=video_path, visible=True),
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(value=script, visible=True)
            )
        return (
            gr.update(visible=False),
            gr.update(value=None, visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(value="", visible=False)
        )

    def update_after_video_generation(self, video_path):
        """Update UI after video generation"""
        self.video_generated = True
        # Replace sample video with generated video and hide sample buttons
        if video_path and os.path.exists(video_path):
            return gr.update(visible=False), gr.update(value=video_path)
        return gr.update(visible=True), gr.update()

    def handle_download(self, video_path):
        """Handle video download"""
        if video_path and os.path.exists(video_path):
            return video_path
        return None
        
    def show_sample_video(self, sample_type):
        """Display the selected sample video"""
        if sample_type == "landscape":
            return gr.update(value=self.landscape_sample, visible=True)
        else:  # vertical
            return gr.update(value=self.vertical_sample, visible=True)

    def create_ui(self):
        # Create blocks with custom CSS
        with gr.Blocks(css="""
            .sample-video-container {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .fixed-height-video {
                height: 80vh !important;
                max-height: 50% !important;
                margin: 0 auto;
            }
            /* Custom button colors */
            .custom-primary-button {
                background-color: #007c56 !important;
                border-color: #007c56 !important;
            }
            .video-js .vjs-volume-control {
                display: flex !important;
            }
        """) as self.video_automation:
            # First Block: Provide Textual Input for the Video
            with gr.Row():
                with gr.Column(scale=3):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("## Textual Input & Parameters")
                            self.text_input = gr.Textbox(label="Provide textual input", lines=5, placeholder="Enter your textual input here...")
                            self.generate_script_button = gr.Button("Generate Script", variant="primary", elem_classes="custom-primary-button")
                    
                    # Second Block: Generated Script
                    with gr.Row(visible=False) as self.script_block:
                        with gr.Column():
                            gr.Markdown("## Generated Script")
                            self.show_hide_button = gr.Button("Show/Hide Script")
                            self.script_output = gr.Textbox(label="Generated Script", lines=10, visible=False)
                            with gr.Row():
                                self.approve_script_button = gr.Button("Use This Script", variant="primary", elem_classes="custom-primary-button", visible=False)
                                self.edit_script_button = gr.Button("Edit Script", visible=False)
                    
                    # Third Block: Video Generation Settings
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("## Parameters")
                            
                            with gr.Row():
                                with gr.Column(scale=1):
                                    gr.Markdown("### Orientation")
                                    self.orientation_dropdown = gr.Dropdown(
                                        choices=["Vertical", "Landscape"], 
                                        label="Format",
                                        value="Vertical"
                                    )
                                
                                with gr.Column(scale=1):
                                    gr.Markdown("### Language")
                                    self.language_dropdown = gr.Dropdown(
                                        choices=[lang.value for lang in Language], 
                                        label="Content Language",
                                        value=Language.ENGLISH.value
                                    )
                            
                            with gr.Row():
                                with gr.Column(scale=1):
                                    gr.Markdown("### Text Position")
                                    self.text_position_dropdown = gr.Dropdown(
                                        choices=["Top", "Middle", "Bottom"], 
                                        label="Caption Position",
                                        value="Middle"  # Changed default to Middle
                                    )
                                
                                with gr.Column(scale=1):
                                    gr.Markdown("### Quality")
                                    self.quality_dropdown = gr.Dropdown(
                                        choices=["SD", "HD", "4k"], 
                                        label="Video Quality",
                                        value="4k"  # Changed default to 4k
                                    )
                            
                            with gr.Row():
                                with gr.Column():
                                    gr.Markdown("### Duration (Seconds)")
                                    self.duration_slider = gr.Slider(
                                        minimum=1,
                                        maximum=60,
                                        value=15,  # Default value set to 15
                                        step=1,
                                        label="Video Duration"
                                    )
                            
                            self.generate_video_button = gr.Button("Generate Video", variant="primary", size="lg", elem_classes="custom-primary-button")
                            self.error_output = gr.Textbox(label="Status", visible=False)
                    
                    # Fourth Block: Generated Video
                    with gr.Row(visible=False) as self.video_block:
                        with gr.Column():
                            gr.Markdown("## Generated Video")
                            self.video_output = gr.Video(label="Generated Video", visible=False, elem_id="video_player", elem_classes="video-js")
                            with gr.Row():
                                self.download_video_button = gr.Button("Download Video", variant="primary", visible=False)
                                self.assets_used_button = gr.Button("Show Script Used", visible=False)
                                self.open_folder_button = gr.Button("Open Videos Folder", visible=False)
                    
                    # Fifth Block: Script Used in Generated Video
                    with gr.Row(visible=False) as self.script_used_block:
                        with gr.Column():
                            gr.Markdown("## Script Used in Generated Video")
                            self.script_used_output = gr.Textbox(label="Script Used", visible=False, lines=10)
                
                with gr.Column(scale=7, elem_classes="sample-video-container"):
                    gr.Markdown("## Previews")
                    
                    # Sample videos section
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Sample Videos")
                            self.sample_video_display = gr.Video(
                                label="Sample Video", 
                                include_audio=True,
                                elem_classes="fixed-height-video",
                                value=self.landscape_sample  # Set default sample to landscape
                            )
                            with gr.Row(visible=True) as self.sample_buttons_row:
                                self.landscape_icon_button = gr.Button("🖥️ Landscape Sample", variant="secondary")
                                self.vertical_icon_button = gr.Button("📱 Vertical Sample", variant="secondary")
                                
                            gr.Markdown("Click on the icons above to view sample videos in different formats.")
            
            # Event Handlers
            
            # Script generation
            self.generate_script_button.click(
                fn=self.generate_script,
                inputs=[self.text_input, self.language_dropdown],
                outputs=[self.script_output]
            ).then(
                fn=self.update_script_block_visibility,
                inputs=[self.script_output],
                outputs=[self.script_block, self.approve_script_button, self.script_output]
            )
            
            # Script visibility toggle
            self.show_hide_button.click(
                fn=lambda visible: gr.update(visible=not visible),
                inputs=[self.script_output],
                outputs=[self.script_output]
            )
            
            # Sample video display
            self.landscape_icon_button.click(
                fn=lambda: self.show_sample_video("landscape"),
                outputs=[self.sample_video_display]
            )
            
            self.vertical_icon_button.click(
                fn=lambda: self.show_sample_video("vertical"),
                outputs=[self.sample_video_display]
            )
            
            # Video generation
            self.generate_video_button.click(
                fn=lambda: gr.update(visible=True, value="Starting video generation..."),
                outputs=[self.error_output]
            ).then(
                fn=self.make_video,
                inputs=[
                    self.script_output,
                    self.orientation_dropdown,
                    self.text_position_dropdown,
                    self.quality_dropdown,
                    self.duration_slider
                ],
                outputs=[self.video_output, self.script_used_output]
            ).then(
                fn=self.update_video_block_visibility,
                inputs=[self.video_output, self.script_used_output],
                outputs=[
                    self.video_block,
                    self.video_output,
                    self.download_video_button,
                    self.assets_used_button,
                    self.script_used_block,
                    self.script_used_output
                ]
            ).then(
                fn=self.update_after_video_generation,
                inputs=[self.video_output],
                outputs=[self.sample_buttons_row, self.sample_video_display]
            ).then(
                fn=lambda: gr.update(visible=False),
                outputs=[self.error_output]
            )
            
            # Video download
            self.download_video_button.click(
                fn=self.handle_download,
                inputs=[self.video_output],
                outputs=[gr.File()]
            )
            
            # Show/hide script used
            self.assets_used_button.click(
                fn=lambda visible: gr.update(visible=not visible),
                inputs=[self.script_used_block],
                outputs=[self.script_used_block]
            )
            
            # Open videos folder
            self.open_folder_button.click(
                fn=lambda: AssetComponentsUtils.start_file(os.path.abspath("videos/"))
            )

        return self.video_automation

























# import os
# import traceback
# from enum import Enum

# import gradio as gr

# from gui.asset_components import AssetComponentsUtils
# from gui.ui_abstract_component import AbstractComponentUI
# from gui.ui_components_html import GradioComponentsHTML
# from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
# from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
# from shortGPT.config.api_db import ApiKeyManager
# from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
#                                        ELEVEN_SUPPORTED_LANGUAGES,
#                                        LANGUAGE_ACRONYM_MAPPING,
#                                        Language)
# from shortGPT.engine.content_video_engine import ContentVideoEngine
# from shortGPT.gpt import gpt_chat_video


# class Chatstate(Enum):
#     ASK_ORIENTATION = 1
#     ASK_VIDEO_SET = 2
#     ASK_VOICE_MODULE = 3
#     ASK_LANGUAGE = 4
#     ASK_DESCRIPTION = 5
#     GENERATE_SCRIPT = 6
#     ASK_SATISFACTION = 7
#     MAKE_VIDEO = 8
#     ASK_CORRECTION = 9


# class VideoAutomationUI(AbstractComponentUI):
#     def __init__(self, shortGptUI: gr.Blocks):
#         self.shortGptUI = shortGptUI
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.voice_module = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False
#         self.video_automation = None
#         self.chatbot = None
#         self.msg = None
#         self.restart_button = None
#         self.video_folder = None
#         self.errorHTML = None
#         self.outHTML = None
#         self.video_set = None  # Initialize video_set

#     def is_key_missing(self):
#         openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
#         gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
#         if not openai_key and not gemini_key:
#             return "Your Genmini or OpenAI key is missing. Please go to the config tab and enter the API key."

#         if self.video_set == "Pexels":
#             pexels_api_key = ApiKeyManager.get_api_key("PEXELS_API_KEY")
#             if not pexels_api_key:
#                 return "Your Pexels API key is missing. Please go to the config tab and enter the API key."
#         elif self.video_set == "Pixabay":
#             pixabay_api_key = ApiKeyManager.get_api_key("PIXABAY_API_KEY")
#             if not pixabay_api_key:
#                 return "Your Pixabay API key is missing. Please go to the config tab and enter the API key."

#     def generate_script(self, message, language):
#         return gpt_chat_video.generateScript(message, language)

#     def correct_script(self, script, correction):
#         return gpt_chat_video.correctScript(script, correction)

#     def make_video(self, script, voice_module, isVertical, progress=gr.Progress()):
#         videoEngine = ContentVideoEngine(voiceModule=voice_module, script=script, isVerticalFormat=isVertical)
#         num_steps = videoEngine.get_total_steps()
#         progress_counter = 0

#         def logger(prog_str):
#             progress(progress_counter / (num_steps), f"Creating video - {progress_counter} - {prog_str}")
#         videoEngine.set_logger(logger)
#         for step_num, step_info in videoEngine.makeContent():
#             progress(progress_counter / (num_steps), f"Creating video - {step_info}")
#             progress_counter += 1

#         video_path = videoEngine.get_video_output_path()
#         return video_path, script

#     def reset_components(self):
#         return gr.update(value=self.initialize_conversation()), gr.update(visible=True), gr.update(value="", visible=False), gr.update(value="", visible=False)

#     def initialize_conversation(self):
#         return "Welcome! Describe your video idea to get started."

#     def create_ui(self):
#         with gr.Blocks() as self.video_automation:
#             # First Block: Provide Textual Input for the Video
#             with gr.Row():
#                 with gr.Column(scale=3):
#                     with gr.Row():
#                         with gr.Column():
#                             gr.Markdown("## Provide Textual Input for the Video")
#                             self.text_input = gr.Textbox(label="Enter your video description", lines=5)
#                             self.generate_script_button = gr.Button("Generate Script")
                    
#                     # Second Block: Generated Script
#                     with gr.Row(visible=False) as self.script_block:
#                         with gr.Column():
#                             gr.Markdown("## Generated Script")
#                             self.show_hide_button = gr.Button("Show/Hide")
#                             self.script_output = gr.Textbox(label="Generated Script", visible=False)
#                             self.approve_script_button = gr.Button("Approve Script", visible=False)
                    
#                     # Third Block: Video Generation Settings
#                     with gr.Row():
#                         with gr.Column():
#                             gr.Markdown("## Orientation")
#                             self.orientation_dropdown = gr.Dropdown(choices=["Horizontal", "Vertical"], label="Select Orientation")
#                             gr.Markdown("## Output Quality")
#                             self.quality_dropdown = gr.Dropdown(choices=["4K", "HD", "SD"], label="Select Quality")
#                             gr.Markdown("## Language")
#                             self.language_dropdown = gr.Dropdown(choices=[lang.value for lang in Language], label="Select Language")
#                             gr.Markdown("## Text Position")
#                             self.text_position_dropdown = gr.Dropdown(choices=["Top", "Middle", "Bottom"], label="Select Text Position")
#                             gr.Markdown("## Duration (seconds)")
#                             self.duration_slider = gr.Slider(minimum=1, maximum=60, step=1, label="Select Duration")
#                             self.generate_video_button = gr.Button("Generate Video")
                    
#                     # Fourth Block: Generated Video
#                     with gr.Row(visible=False) as self.video_block:
#                         with gr.Column():
#                             gr.Markdown("## Generated Video")
#                             self.video_output = gr.Video(label="Generated Video", visible=False)
#                             with gr.Row():
#                                 self.download_video_button = gr.Button("Download Video", visible=False)
#                                 self.assets_used_button = gr.Button("Assets Used", visible=False)
                    
#                     # Fifth Block: Script Used in Generated Video
#                     with gr.Row(visible=False) as self.script_used_block:
#                         with gr.Column():
#                             gr.Markdown("## Script Used in Generated Video")
#                             self.script_used_output = gr.Textbox(label="Script Used", visible=False)
                
#                 with gr.Column(scale=7):
#                     gr.Markdown("## Sample video")

                    
#             # Event Handlers
#             self.generate_script_button.click(self.generate_script, inputs=[self.text_input, self.language_dropdown], outputs=[self.script_output])
#             self.show_hide_button.click(lambda visible: not visible, inputs=[self.script_output.visible], outputs=[self.script_output])
#             self.approve_script_button.click(lambda: gr.update(visible=True), outputs=[self.video_block])
#             self.generate_video_button.click(self.make_video, inputs=[self.script_output, self.orientation_dropdown], outputs=[self.video_output, self.script_used_output])
#             self.download_video_button.click(lambda video_path: video_path, inputs=[self.video_output], outputs=[self.download_video_button])
#             self.assets_used_button.click(lambda: gr.update(visible=True), outputs=[self.script_used_block])
            

#         return self.video_automation





















# import os
# import traceback
# from enum import Enum

# import gradio as gr

# from gui.asset_components import AssetComponentsUtils
# from gui.ui_abstract_component import AbstractComponentUI
# from gui.ui_components_html import GradioComponentsHTML
# from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
# from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
# from shortGPT.config.api_db import ApiKeyManager
# from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
#                                         ELEVEN_SUPPORTED_LANGUAGES,
#                                         LANGUAGE_ACRONYM_MAPPING,
#                                         Language)
# from shortGPT.engine.content_video_engine import ContentVideoEngine
# from shortGPT.gpt import gpt_chat_video


# class Chatstate(Enum):
#     ASK_ORIENTATION = 1
#     ASK_VIDEO_SET = 2
#     ASK_VOICE_MODULE = 3
#     ASK_LANGUAGE = 4
#     ASK_DESCRIPTION = 5
#     GENERATE_SCRIPT = 6
#     ASK_SATISFACTION = 7
#     MAKE_VIDEO = 8
#     ASK_CORRECTION = 9


# class VideoAutomationUI(AbstractComponentUI):
#     def __init__(self, shortGptUI: gr.Blocks):
#         self.shortGptUI = shortGptUI
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.voice_module = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False
#         self.video_automation = None
#         self.chatbot = None
#         self.msg = None
#         self.restart_button = None
#         self.video_folder = None
#         self.errorHTML = None
#         self.outHTML = None
#         self.video_set = None

#     def is_key_missing(self):
#         openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
#         gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
#         if not openai_key and not gemini_key:
#             return "Your Genmini or OpenAI key is missing. Please go to the config tab and enter the API key."

#         if self.video_set == "Pexels":
#             pexels_api_key = ApiKeyManager.get_api_key("PEXELS_API_KEY")
#             if not pexels_api_key:
#                 return "Your Pexels API key is missing. Please go to the config tab and enter the API key."
#         elif self.video_set == "Pixabay":
#             pixabay_api_key = ApiKeyManager.get_api_key("PIXABAY_API_KEY")
#             if not pixabay_api_key:
#                 return "Your Pixabay API key is missing. Please go to the config tab and enter the API key."

#     def generate_script(self, message, language):
#         return gpt_chat_video.generateScript(message, language)

#     def correct_script(self, script, correction):
#         return gpt_chat_video.correctScript(script, correction)

#     def make_video(self, script, voice_module, isVertical, progress):
#         videoEngine = ContentVideoEngine(voiceModule=voice_module, script=script, isVerticalFormat=isVertical, api_source=self.video_set)
#         num_steps = videoEngine.get_total_steps()
#         progress_counter = 0

#         def logger(prog_str):
#             progress(progress_counter / (num_steps), f"Creating video - {progress_counter} - {prog_str}")
#         videoEngine.set_logger(logger)
#         for step_num, step_info in videoEngine.makeContent():
#             progress(progress_counter / (num_steps), f"Creating video - {step_info}")
#             progress_counter += 1

#         video_path = videoEngine.get_video_output_path()
#         return video_path

#     def reset_components(self):
#         return gr.update(value=self.initialize_conversation()), gr.update(visible=True), gr.update(value="", visible=False), gr.update(value="", visible=False)

#     def chatbot_conversation(self):
#         def respond(message, chat_history, progress=gr.Progress()):
#             error_html = ""
#             errorVisible = False
#             inputVisible = True
#             folderVisible = False
#             if self.state == Chatstate.ASK_ORIENTATION:
#                 errorMessage = self.is_key_missing()
#                 if errorMessage:
#                     bot_message = errorMessage
#                 else:
#                     self.isVertical = "vertical" in message.lower() or "short" in message.lower()
#                     self.state = Chatstate.ASK_VIDEO_SET
#                     bot_message = "Which video source do you want to use? Please type 'Pexels' or 'Pixabay'."
#             elif self.state == Chatstate.ASK_VIDEO_SET:
#                 if "pexels" in message.lower():
#                     self.video_set = "Pexels"
#                 elif "pixabay" in message.lower():
#                     self.video_set = "Pixabay"
#                 else:
#                     bot_message = "Invalid video source. Please type 'Pexels' or 'Pixabay'."
#                     return
#                 self.state = Chatstate.ASK_VOICE_MODULE
#                 bot_message = "Which voice module do you want to use? Please type 'ElevenLabs' for high quality, 'EdgeTTS' for free medium quality voice."
#             elif self.state == Chatstate.ASK_VOICE_MODULE:
#                 if "elevenlabs" in message.lower():
#                     eleven_labs_key = ApiKeyManager.get_api_key("ELEVENLABS_API_KEY")
#                     if not eleven_labs_key:
#                         bot_message = "Your ELEVENLABS_API_KEY API key is missing. Please go to the config tab and enter the API key."
#                         return
#                     self.voice_module = ElevenLabsVoiceModule
#                     language_choices = [lang.value for lang in ELEVEN_SUPPORTED_LANGUAGES]
#                 elif "edgetts" in message.lower():
#                     self.voice_module = EdgeTTSVoiceModule
#                     language_choices = [lang.value for lang in Language]
#                 else:
#                     bot_message = "Invalid voice module. Please type 'ElevenLabs' or 'EdgeTTS'."
#                     return
#                 self.state = Chatstate.ASK_LANGUAGE
#                 bot_message = f"🌐What language will be used in the video?🌐 Choose from one of these ({', '.join(language_choices)})"
#             elif self.state == Chatstate.ASK_LANGUAGE:
#                 self.language = next((lang for lang in Language if lang.value.lower() in message.lower()), None)
#                 self.language = self.language if self.language else Language.ENGLISH
#                 if self.voice_module == ElevenLabsVoiceModule:
#                     self.voice_module = ElevenLabsVoiceModule(ApiKeyManager.get_api_key('ELEVENLABS_API_KEY'), "Chris", checkElevenCredits=True)
#                 elif self.voice_module == EdgeTTSVoiceModule:
#                     self.voice_module = EdgeTTSVoiceModule(EDGE_TTS_VOICENAME_MAPPING[self.language]['male'])
#                 self.state = Chatstate.ASK_DESCRIPTION
#                 bot_message = "Amazing 🔥 ! 📝Can you describe thoroughly the subject of your video?📝 I will next generate you a script based on that description"
#             elif self.state == Chatstate.ASK_DESCRIPTION:
#                 self.script = self.generate_script(message, self.language.value)
#                 self.state = Chatstate.ASK_SATISFACTION
#                 bot_message = f"📝 Here is your generated script: \n\n--------------\n{self.script}\n\n・Are you satisfied with the script and ready to proceed with creating the video? Please respond with 'YES' or 'NO'. 👍👎"
#             elif self.state == Chatstate.ASK_SATISFACTION:
#                 if "yes" in message.lower():
#                     self.state = Chatstate.MAKE_VIDEO
#                     inputVisible = False
#                     yield gr.update(visible=False), gr.update(value=[[None, "Your video is being made now! 🎬"]]), gr.update(value="", visible=False), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=False)
#                     try:
#                         video_path = self.make_video(self.script, self.voice_module, self.isVertical, progress=progress)
#                         file_name = video_path.split("/")[-1].split("\\")[-1]
#                         current_url = self.shortGptUI.share_url+"/" if self.shortGptUI.share else self.shortGptUI.local_url
#                         file_url_path = f"{current_url}gradio_api/file={video_path}"
#                         self.video_html = f'''
#                             <div style="display: flex; flex-direction: column; align-items: center;">
#                                 <video width="{600}" height="{300}" style="max-height: 100%;" controls>
#                                     <source src="{file_url_path}" type="video/mp4">
#                                     Your browser does not support the video tag.
#                                 </video>
#                                 <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
#                                     <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Download Video</button>
#                                 </a>
#                             </div>'''
#                         self.videoVisible = True
#                         folderVisible = True
#                         bot_message = "Your video is completed! 🎬. Scroll down below to open its file location."
#                     except Exception as e:
#                         traceback_str = ''.join(traceback.format_tb(e.__traceback__))
#                         error_name = type(e).__name__.capitalize() + " : " + f"{e.args[0]}"
#                         errorVisible = True
#                         gradio_content_automation_ui_error_template = GradioComponentsHTML.get_html_error_template()
#                         error_html = gradio_content_automation_ui_error_template.format(error_message=error_name, stack_trace=traceback_str)
#                         bot_message = "We encountered an error while making this video ❌"
#                         print("Error", traceback_str)
#                         yield gr.update(visible=False), gr.update(value=[[None, "Your video is being made now! 🎬"]]), gr.update(value="", visible=False), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)


#                 else:
#                     self.state = Chatstate.ASK_CORRECTION  # change self.state to ASK_CORRECTION
#                     bot_message = "Explain me what you want different in the script"
#             elif self.state == Chatstate.ASK_CORRECTION:  # new self.state
#                 self.script = self.correct_script(self.script, message)  # call generateScript with correct=True
#                 self.state = Chatstate.ASK_SATISFACTION
#                 bot_message = f"📝 Here is your corrected script: \n\n--------------\n{self.script}\n\n・Are you satisfied with the script and ready to proceed with creating the video? Please respond with 'YES' or 'NO'. 👍👎"
#             chat_history.append((message, bot_message))
#             yield gr.update(value="", visible=inputVisible), gr.update(value=chat_history), gr.update(value=self.video_html, visible=self.videoVisible), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)

#         return respond

#     def initialize_conversation(self):
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False
#         return [[None, "🤖 Welcome to ShortGPT! 🚀 I'm a python framework aiming to simplify and automate your video editing tasks.\nLet's get started! 🎥🎬\n\n Do you want your video to be in landscape or vertical format? (landscape OR vertical)"]]

#     def reset_conversation(self):
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False

#     def create_ui(self):
#         with gr.Row(visible=False) as self.video_automation:
#             with gr.Column():
#                 self.chatbot = gr.Chatbot(self.initialize_conversation, height=365)
#                 self.msg = gr.Textbox()
#                 self.restart_button = gr.Button("Restart")
#                 self.video_folder = gr.Button("📁", visible=False)
#                 self.video_folder.click(lambda _: AssetComponentsUtils.start_file(os.path.abspath("videos/")))

#                 respond = self.chatbot_conversation()

#             self.errorHTML = gr.HTML(visible=False)
#             self.outHTML = gr.HTML('<div style="min-height: 80px;"></div>')
#             self.restart_button.click(self.reset_components, [], [self.chatbot, self.msg, self.errorHTML, self.outHTML])
#             self.restart_button.click(self.reset_conversation, [])
#             self.msg.submit(respond, [self.msg, self.chatbot], [self.msg, self.chatbot, self.outHTML, self.errorHTML, self.video_folder, self.restart_button])

#         return self.video_automation

































# import os
# import traceback
# from enum import Enum

# import gradio as gr

# from gui.asset_components import AssetComponentsUtils
# from gui.ui_abstract_component import AbstractComponentUI
# from gui.ui_components_html import GradioComponentsHTML
# from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
# from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
# from shortGPT.config.api_db import ApiKeyManager
# from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
#                                         ELEVEN_SUPPORTED_LANGUAGES,
#                                         LANGUAGE_ACRONYM_MAPPING,
#                                         Language)
# from shortGPT.engine.content_video_engine import ContentVideoEngine
# from shortGPT.gpt import gpt_chat_video


# class Chatstate(Enum):
#     ASK_ORIENTATION = 1
#     ASK_VOICE_MODULE = 2
#     ASK_LANGUAGE = 3
#     ASK_DESCRIPTION = 4
#     GENERATE_SCRIPT = 5
#     ASK_SATISFACTION = 6
#     MAKE_VIDEO = 7
#     ASK_CORRECTION = 8


# class VideoAutomationUI(AbstractComponentUI):
#     def __init__(self, shortGptUI: gr.Blocks):
#         self.shortGptUI = shortGptUI
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.voice_module = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False
#         self.video_automation = None
#         self.chatbot = None
#         self.msg = None
#         self.restart_button = None
#         self.video_folder = None
#         self.errorHTML = None
#         self.outHTML = None

#     def is_key_missing(self):
#         openai_key = ApiKeyManager.get_api_key("OPENAI_API_KEY")
#         gemini_key = ApiKeyManager.get_api_key("GEMINI_API_KEY")
#         if not openai_key and not gemini_key:
#             return "Your Genmini or OpenAI key is missing. Please go to the config tab and enter the API key."

#         pexels_api_key = ApiKeyManager.get_api_key("PEXELS_API_KEY")
#         if not pexels_api_key:
#             return "Your Pexels API key is missing. Please go to the config tab and enter the API key."

#     def generate_script(self, message, language):
#         return gpt_chat_video.generateScript(message, language)

#     def correct_script(self, script, correction):
#         return gpt_chat_video.correctScript(script, correction)

#     def make_video(self, script, voice_module, isVertical, progress):
#         videoEngine = ContentVideoEngine(voiceModule=voice_module, script=script, isVerticalFormat=isVertical)
#         num_steps = videoEngine.get_total_steps()
#         progress_counter = 0

#         def logger(prog_str):
#             progress(progress_counter / (num_steps), f"Creating video - {progress_counter} - {prog_str}")
#         videoEngine.set_logger(logger)
#         for step_num, step_info in videoEngine.makeContent():
#             progress(progress_counter / (num_steps), f"Creating video - {step_info}")
#             progress_counter += 1

#         video_path = videoEngine.get_video_output_path()
#         return video_path

#     def reset_components(self):
#         return gr.update(value=self.initialize_conversation()), gr.update(visible=True), gr.update(value="", visible=False), gr.update(value="", visible=False)

#     def chatbot_conversation(self):
#         def respond(message, chat_history, progress=gr.Progress()):
#             # global self.state, isVertical, voice_module, language, script, videoVisible, video_html
#             error_html = ""
#             errorVisible = False
#             inputVisible = True
#             folderVisible = False
#             if self.state == Chatstate.ASK_ORIENTATION:
#                 errorMessage = self.is_key_missing()
#                 if errorMessage:
#                     bot_message = errorMessage
#                 else:
#                     self.isVertical = "vertical" in message.lower() or "short" in message.lower()
#                     self.state = Chatstate.ASK_VOICE_MODULE
#                     bot_message = "Which voice module do you want to use? Please type 'ElevenLabs' for high quality, 'EdgeTTS' for free medium quality voice."
#             elif self.state == Chatstate.ASK_VOICE_MODULE:
#                 if "elevenlabs" in message.lower():
#                     eleven_labs_key = ApiKeyManager.get_api_key("ELEVENLABS_API_KEY")
#                     if not eleven_labs_key:
#                         bot_message = "Your ELEVENLABS_API_KEY API key is missing. Please go to the config tab and enter the API key."
#                         return
#                     self.voice_module = ElevenLabsVoiceModule
#                     language_choices = [lang.value for lang in ELEVEN_SUPPORTED_LANGUAGES]
#                 elif "edgetts" in message.lower():
#                     self.voice_module = EdgeTTSVoiceModule
#                     language_choices = [lang.value for lang in Language]
#                 else:
#                     bot_message = "Invalid voice module. Please type 'ElevenLabs' or 'EdgeTTS'."
#                     return
#                 self.state = Chatstate.ASK_LANGUAGE
#                 bot_message = f"🌐What language will be used in the video?🌐 Choose from one of these ({', '.join(language_choices)})"
#             elif self.state == Chatstate.ASK_LANGUAGE:
#                 self.language = next((lang for lang in Language if lang.value.lower() in message.lower()), None)
#                 self.language = self.language if self.language else Language.ENGLISH
#                 if self.voice_module == ElevenLabsVoiceModule:
#                     self.voice_module = ElevenLabsVoiceModule(ApiKeyManager.get_api_key('ELEVENLABS_API_KEY'), "Chris", checkElevenCredits=True)
#                 elif self.voice_module == EdgeTTSVoiceModule:
#                     self.voice_module = EdgeTTSVoiceModule(EDGE_TTS_VOICENAME_MAPPING[self.language]['male'])
#                 self.state = Chatstate.ASK_DESCRIPTION
#                 bot_message = "Amazing 🔥 ! 📝Can you describe thoroughly the subject of your video?📝 I will next generate you a script based on that description"
#             elif self.state == Chatstate.ASK_DESCRIPTION:
#                 self.script = self.generate_script(message, self.language.value)
#                 self.state = Chatstate.ASK_SATISFACTION
#                 bot_message = f"📝 Here is your generated script: \n\n--------------\n{self.script}\n\n・Are you satisfied with the script and ready to proceed with creating the video? Please respond with 'YES' or 'NO'. 👍👎"
#             elif self.state == Chatstate.ASK_SATISFACTION:
#                 if "yes" in message.lower():
#                     self.state = Chatstate.MAKE_VIDEO
#                     inputVisible = False
#                     yield gr.update(visible=False), gr.update(value=[[None, "Your video is being made now! 🎬"]]), gr.update(value="", visible=False), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=False)
#                     try:
#                         video_path = self.make_video(self.script, self.voice_module, self.isVertical, progress=progress)
#                         file_name = video_path.split("/")[-1].split("\\")[-1]
#                         current_url = self.shortGptUI.share_url+"/" if self.shortGptUI.share else self.shortGptUI.local_url
#                         file_url_path = f"{current_url}gradio_api/file={video_path}"
#                         self.video_html = f'''
#                             <div style="display: flex; flex-direction: column; align-items: center;">
#                                 <video width="{600}" height="{300}" style="max-height: 100%;" controls>
#                                     <source src="{file_url_path}" type="video/mp4">
#                                     Your browser does not support the video tag.
#                                 </video>
#                                 <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
#                                     <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Download Video</button>
#                                 </a>
#                             </div>'''
#                         self.videoVisible = True
#                         folderVisible = True
#                         bot_message = "Your video is completed !🎬. Scroll down below to open its file location."
#                     except Exception as e:
#                         traceback_str = ''.join(traceback.format_tb(e.__traceback__))
#                         error_name = type(e).__name__.capitalize() + " : " + f"{e.args[0]}"
#                         errorVisible = True
#                         gradio_content_automation_ui_error_template = GradioComponentsHTML.get_html_error_template()
#                         error_html = gradio_content_automation_ui_error_template.format(error_message=error_name, stack_trace=traceback_str)
#                         bot_message = "We encountered an error while making this video ❌"
#                         print("Error", traceback_str)
#                         yield gr.update(visible=False), gr.update(value=[[None, "Your video is being made now! 🎬"]]), gr.update(value="", visible=False), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)

#                 else:
#                     self.state = Chatstate.ASK_CORRECTION  # change self.state to ASK_CORRECTION
#                     bot_message = "Explain me what you want different in the script"
#             elif self.state == Chatstate.ASK_CORRECTION:  # new self.state
#                 self.script = self.correct_script(self.script, message)  # call generateScript with correct=True
#                 self.state = Chatstate.ASK_SATISFACTION
#                 bot_message = f"📝 Here is your corrected script: \n\n--------------\n{self.script}\n\n・Are you satisfied with the script and ready to proceed with creating the video? Please respond with 'YES' or 'NO'. 👍👎"
#             chat_history.append((message, bot_message))
#             yield gr.update(value="", visible=inputVisible), gr.update(value=chat_history), gr.update(value=self.video_html, visible=self.videoVisible), gr.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)

#         return respond

#     def initialize_conversation(self):
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False
#         return [[None, "🤖 Welcome to ShortGPT! 🚀 I'm a python framework aiming to simplify and automate your video editing tasks.\nLet's get started! 🎥🎬\n\n Do you want your video to be in landscape or vertical format? (landscape OR vertical)"]]

#     def reset_conversation(self):
#         self.state = Chatstate.ASK_ORIENTATION
#         self.isVertical = None
#         self.language = None
#         self.script = ""
#         self.video_html = ""
#         self.videoVisible = False

#     def create_ui(self):
#         with gr.Row(visible=False) as self.video_automation:
#             with gr.Column():
#                 self.chatbot = gr.Chatbot(self.initialize_conversation, height=365)
#                 self.msg = gr.Textbox()
#                 self.restart_button = gr.Button("Restart")
#                 self.video_folder = gr.Button("📁", visible=False)
#                 self.video_folder.click(lambda _: AssetComponentsUtils.start_file(os.path.abspath("videos/")))
#                 respond = self.chatbot_conversation()

#             self.errorHTML = gr.HTML(visible=False)
#             self.outHTML = gr.HTML('<div style="min-height: 80px;"></div>')
#             self.restart_button.click(self.reset_components, [], [self.chatbot, self.msg, self.errorHTML, self.outHTML])
#             self.restart_button.click(self.reset_conversation, [])
#             self.msg.submit(respond, [self.msg, self.chatbot], [self.msg, self.chatbot, self.outHTML, self.errorHTML, self.video_folder, self.restart_button])
#         return self.video_automation
