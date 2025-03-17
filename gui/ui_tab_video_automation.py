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
        self.vertical_sample = "assets/videos/Sample_Verticals.mp4"
        # self.progress_counter = 0

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

    def correct_script(self, script, correction):
        """Apply corrections to the script"""
        return gpt_chat_video.correctScript(script, correction)

    def setup_voice_module(self, language):
        """Set up the EdgeTTS voice module as specified"""
        try:
            # Only use EdgeTTS as specified
            self.voice_module = EdgeTTSVoiceModule(EDGE_TTS_VOICENAME_MAPPING[language]['male'])
            print(language)
            return True, "Voice module set up successfully"
        except Exception as e:
            return False, f"Error setting up voice module: {str(e)}"

    def make_video(self, script, orientation_choice, text_position, quality, duration, progress=gr.Progress()):
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
        success, message = self.setup_voice_module(self.language)
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
            
            num_steps = videoEngine.get_total_steps()
            progress_counter = 0

            def logger(prog_str):
                progress(progress_counter / (num_steps), f"Creating video - {progress_counter} - {prog_str}")
            videoEngine.set_logger(logger)
            for step_num, step_info in videoEngine.makeContent():
                progress(progress_counter / (num_steps), f"Creating video - {step_info}")
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

    @staticmethod
    def update_visibility(radio_value):
        """Update the visibility of the script block based on the radio button's value."""
        return gr.update(visible=radio_value == "Show")

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
        with gr.Blocks() as self.video_automation:
            # First Block: Provide Textual Input for the Video
            with gr.Row():
                with gr.Column(scale=2.5):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("## Textual Input & Parameters")
                            self.text_input = gr.Textbox(label="Provide textual input", lines=5, placeholder="Enter your textual input here...")
                            self.generate_script_button = gr.Button("Generate Script", variant="primary")
                    
                    # Second Block: Generated Script
                    with gr.Row(visible=False) as self.script_block:
                        with gr.Column():
                            with gr.Row():
                                self.show_hide_radio = gr.Radio(
                                    choices=["Hide", "Show"],
                                    value="Hide",
                                    label="Script Visibility"
                                )
                            
                            with gr.Column(visible=False) as self.generated_script_block:
                                gr.Markdown("## Generated Script")
                                self.script_output = gr.Textbox(
                                    label="Generated Script",
                                    lines=10,
                                    interactive=False  # Make it non-editable by default
                                )
                                with gr.Row():
                                    self.approve_script_button = gr.Button("Use This Script", variant="primary")
                                    self.edit_script_button = gr.Button("Edit Script", visible=True)  # Initially visible
                    
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
                            
                            # Add a progress bar
                            # self.progress = gr.Progress()
                            self.generate_video_button = gr.Button("Generate Video", variant="primary", size="lg")
                            self.error_output = gr.Textbox(label="Status", visible=False)
                    
                    # Fourth Block: Generated Video
                    with gr.Row(visible=False) as self.video_block:
                        with gr.Column():
                            gr.Markdown("## Generated Video")
                            self.video_output = gr.Video(label="Generated Video")
                            with gr.Row():
                                self.download_video_button = gr.Button("Download Video", variant="primary", visible=False)
                                # self.open_folder_button = gr.Button("Open Videos Folder", visible=False)
                            
                            # Display the generated script below the video
                            self.script_output_below_video = gr.Textbox(label="Generated Script", lines=10, visible=False)
                
                with gr.Column(scale=5):
                    gr.Markdown("## Previews")
                    
                    # Sample videos section
                    with gr.Row():
                        with gr.Column():
                            # gr.Markdown("### Sample Videos")
                            self.sample_video_display = gr.Video(
                                label="Generated Video", 
                                include_audio=True,
                                height=400,
                                value=self.landscape_sample  # Set default sample to landscape
                            )
                            with gr.Row(visible=True) as self.sample_buttons_row:
                                self.landscape_icon_button = gr.Button("🖥️ Landscape Sample", variant="secondary")
                                self.vertical_icon_button = gr.Button("📱 Vertical Sample", variant="secondary")
                                
                            # gr.Markdown("Click on the icons above to view sample videos in different formats.")
                            
                
                # Add another column beside the sample videos with scale 2.5
                with gr.Column(scale=2.5):
                    gr.Markdown("## Previous Videos")
                    # Add any additional content or components here
                    self.additional_content = gr.Textbox(label="Additional Content", lines=5, placeholder="Enter additional content here...")
            
            # Event Handlers
            
            # Script generation
            self.generate_script_button.click(
                fn=lambda: gr.update(value="Generating...", interactive=False),  # Change button text and disable it
                outputs=[self.generate_script_button]
            ).then(
                fn=self.generate_script,  # Generate the script
                inputs=[self.text_input, self.language_dropdown],
                outputs=[self.script_output]
            ).then(
                fn=lambda: gr.update(value="Generate Script", interactive=True),  # Revert button text and enable it
                outputs=[self.generate_script_button]
            ).then(
                fn=self.update_script_block_visibility,  # Update script block visibility
                inputs=[self.script_output],
                outputs=[self.script_block, self.approve_script_button, self.script_output]
            )
            
            # Script visibility toggle
            self.show_hide_radio.change(
                fn=self.update_visibility,
                inputs=self.show_hide_radio,
                outputs=self.generated_script_block
            )
            
            # Enable editing when "Edit Script" is clicked
            self.edit_script_button.click(
                fn=lambda: gr.update(interactive=True),  # Make the script editable
                outputs=[self.script_output]
            )
            
            # Disable editing, hide "Edit Script" button, and show alert when "Use This Script" is clicked
            self.approve_script_button.click(
                fn=lambda: [
                    gr.update(interactive=False),  # Make the script non-editable
                    gr.update(visible=False),  # Hide the "Edit Script" button
                    gr.Info("Script approved! Editing is now disabled.")  # Show alert message
                ],
                outputs=[self.script_output, self.edit_script_button]
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
                outputs=[self.video_output, self.script_output_below_video]  # Updated to use script_output_below_video
            ).then(
                fn=self.update_video_block_visibility,
                inputs=[self.video_output, self.script_output_below_video],
                outputs=[
                    self.video_block,
                    self.video_output,
                    self.download_video_button,
                    # self.open_folder_button,
                    self.script_output_below_video
                ]
            ).then(
                fn=self.update_after_video_generation,
                inputs=[self.video_output],
                outputs=[self.sample_buttons_row, self.sample_video_display]
            ).then(
                fn=lambda: gr.update(visible=False),
                outputs=[self.error_output],

            )
            
            # Video download
            self.download_video_button.click(
                fn=self.handle_download,
                inputs=[self.video_output],
                outputs=[gr.File()]
            )
            
            # Open videos folder
            # self.open_folder_button.click(
            #     fn=lambda: AssetComponentsUtils.start_file(os.path.abspath("videos/"))
            # )

        return self.video_automation