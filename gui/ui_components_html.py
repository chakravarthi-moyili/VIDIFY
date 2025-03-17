class GradioComponentsHTML:

    @staticmethod
    def get_html_header() -> str:
        '''Create HTML for the header with flexbox layout'''
        return '''
            <div style="display: flex; width: 100%; height: 100%; padding: 5px; background-color: #007bff;">
                <div style="flex: 1; display: flex; justify-content: center; align-items: center;">
                    <img src="/app/assets/img/logo.png" alt="Logo" style="max-width: 100%; height: auto;">
                </div>
                <div style="flex: 5; display: flex; flex-direction: column; justify-content: center;">
                <div style="flex: 1; display: flex; justify-content: center; align-items: center;">
                    <img src="/app/assets/img/logo.png" alt="Logo" style="max-width: 100%; height: auto;">
                </div>
                <h1 style="font-size: 2rem; text-align: center; color: white;">VIDIFY – The Ultimate AI-Powered Video Automation Framework</h1>
                </div>
            </div>
            <div style="weight: 100%; padding: 5px 50px">
                <h3 style="font-size: 0.8rem; text-align: center; color: white;">VIDIFY automates video production with AI-driven editing, multilingual voiceovers, and media sourcing. Perfect for advertising, marketing, news, reports, education, and more, it streamlines content creation—letting you focus on storytelling, not technical hurdles.</h3>
            </div>
        '''

    @staticmethod
    def get_html_error_template() -> str:
        return '''
        <div style='text-align: center; background: #ff7f7f; color: #a94442; padding: 20px; border-radius: 5px; margin: 10px;'>
          <h2 style='margin: 0; color: black'>ERROR : {error_message}</h2>
          <p style='margin: 10px 0; color: black'>Traceback Info : {stack_trace}</p>
          <p style='margin: 10px 0; color: black'>If the problem persists, don't hesitate to contact our support. We're here to assist you.</p>
          <a href='https://discord.gg/qn2WJaRH' target='_blank' style='background: #a94442; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; text-decoration: none;'>Get Help on Discord</a>
        </div>
        '''

    @staticmethod
    def get_html_video_template(file_url_path, file_name, width="auto", height="auto"):
        """
        Generate an HTML code snippet for embedding and downloading a video.

        Parameters:
        file_url_path (str): The URL or path to the video file.
        file_name (str): The name of the video file.
        width (str, optional): The width of the video. Defaults to "auto".
        height (str, optional): The height of the video. Defaults to "auto".

        Returns:
        str: The generated HTML code snippet.
        """
        html = f'''
            <div style="display: flex; flex-direction: column; align-items: center;">
                <video width="{width}" height="{height}" style="max-height: 100%;" controls>
                    <source src="{file_url_path}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
                    <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Download Video</button>
                </a>
            </div>
        '''
        return html
