import gradio as gr

from gui.content_automation_ui import GradioContentAutomationUI
from gui.ui_abstract_base import AbstractBaseUI
from gui.ui_components_html import GradioComponentsHTML
from gui.ui_tab_asset_library import AssetLibrary
from gui.ui_tab_config import ConfigUI
from shortGPT.utils.cli import CLI


class ShortGptUI(AbstractBaseUI):
    '''Class for the GUI. This class is responsible for creating the UI and launching the server.'''

    def __init__(self, colab=False):
        super().__init__(ui_name='gradio_shortgpt')
        self.colab = colab
        CLI.display_header()

    def create_interface(self):
        '''Create Gradio interface'''
        css = """
        .banner-row {
            # background-color: #007bff;
            padding: 5px;
            margin: 0px;
            border-radius: 0px;
        }
        .title {
            text-align: center;
            color: white;
            font-size: 2rem;
            margin: 0px;
        }
        .subtitle-row {
            padding: 5px 50px;
            margin: 0px;
            border-radius: 0px;
        }
        .subtitle {
            text-align: center;
            color: white;
            # font-size: 0.6rem;
            margin: 0px;
        }
        """
        
        with gr.Blocks(theme=gr.themes.Default(spacing_size=gr.themes.sizes.spacing_sm), 
                    css=css + "footer {visibility: hidden}", 
                    title="AI-Powered Video Generator") as shortGptUI:
            with gr.Row(variant='compact', elem_classes="banner-row"):
                with gr.Column() as app:
                    # Banner row with blue background
                    with gr.Row(equal_height=True, variant="compact", elem_classes="banner-row"):
                        # Logo column (left)
                        with gr.Column(scale=1, min_width=100):
                            gr.Image("assets/img/logo.png", show_label=False, show_download_button=False, show_fullscreen_button=False, container=False)
                        
                        # Title column (center)
                        with gr.Column(scale=5):
                            # Inner row for the second logo
                            with gr.Row(elem_classes="banner-row"):
                                # with gr.Column(scale=2):
                                #     pass
                                with gr.Column(scale=1):
                                    gr.Image("assets/img/vidify_logo.png", show_label=False, show_download_button=False, show_fullscreen_button=False, container=False, height=80)
                                # with gr.Column(scale=2):
                                #     pass

                            with gr.Row():
                                # Title row
                                gr.Markdown("# The Ultimate AI-Powered Video Automation Framework", elem_classes="title")
                    
                    # Subtitle row with same blue background
            with gr.Row(elem_classes="subtitle-row"):
                        gr.Markdown(
                            "#### VIDIFY automates video production with AI-driven editing, multilingual voiceovers, and media sourcing. Perfect for advertising, marketing, news, reports, education, and more, it streamlines content creation—letting you focus on storytelling, not technical hurdles.",
                            elem_classes="subtitle"
                        )
            
            # Add components outside the inner blocks
            self.content_automation = GradioContentAutomationUI(shortGptUI).create_ui()
            # self.asset_library_ui = AssetLibrary().create_ui()
            # self.config_ui = ConfigUI().create_ui()
            
        return shortGptUI

    def launch(self):
        """Launch the server"""
        # Create the user interface
        shortGptUI = self.create_interface()

        # Print a clear startup message if not in Colab
        if not getattr(self, 'colab', False):
            print("\n\n********************* STARTING VIDIFY **********************")
            print("\nVIDIFY is running here 👉 http://localhost:31415\n")
            print("********************* STARTING VIDIFY **********************\n\n")
        
        # Launch the server with the specified configuration
        shortGptUI.queue().launch(
            server_port=31415,
            height=1000,
            allowed_paths=["public/", "videos/", "fonts/"],
            share=self.colab,
            server_name="0.0.0.0"
            # server_timeout = 2000
        )

    # def launch(self):
    #     '''Launch the server'''
    #     shortGptUI = self.create_interface()
    #     if not getattr(self, 'colab', False):
    #                 print("\n\n********************* STARTING SHORGPT **********************")
    #                 print("\nShortGPT is running here 👉 http://localhost:31415\n")
    #                 print("********************* STARTING SHORGPT **********************\n\n")
    #     shortGptUI.queue().launch(server_port=31415, height=1000, allowed_paths=["public/","videos/","fonts/"], share=self.colab, server_name="0.0.0.0")



if __name__ == "__main__":
    app = ShortGptUI()
    app.launch()


import signal

def signal_handler(sig, frame):
    print("Closing Gradio server...")
    import gradio as gr
    gr.close_all()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)