import datetime
import json
import os
import re
import shutil
import traceback
import ffmpeg
import subprocess

from shortGPT.api_utils.pexels_api import getBestVideo as getBestVideoPexels
from shortGPT.api_utils.pixabay_api import get_best_video_pixabay as getBestVideoPixabay
from shortGPT.api_utils.own_dabase import get_best_local_video
from shortGPT.audio import audio_utils
from shortGPT.audio.audio_duration import get_asset_duration
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.config.asset_db import AssetDatabase
from shortGPT.config.languages import Language
from shortGPT.editing_framework.editing_engine import (EditingEngine,
                                                    EditingStep)
from shortGPT.editing_utils import captions
from shortGPT.engine.abstract_content_engine import AbstractContentEngine
from shortGPT.gpt import gpt_editing, gpt_translate, gpt_yt
from datetime import datetime
from shortGPT.database.db_handler import VideoMetadataDB


class ContentVideoEngine(AbstractContentEngine):

    def __init__(self, voiceModule: VoiceModule, script: str, background_music_name="", id="",
                 watermark_logo=None, isVerticalFormat=False, language: Language = Language.ENGLISH, video_data_source="Stock", api_source = "Pexels", text_position = "Middle", quality = "HD"):
        super().__init__(id, "general_video", language, voiceModule)
        if not id:
            if (watermark_logo):
                self._db_watermark_logo = watermark_logo
                print(watermark_logo)
            if background_music_name:
                self._db_background_music_name = background_music_name
            self._db_script = script
            self._db_format_vertical = isVerticalFormat
            self.video_data_source = video_data_source
            self.api_source = api_source
            self.text_position = text_position
            self.quality = quality

        self.stepDict = {
            1: self._generateTempAudio,
            2: self._speedUpAudio,
            3: self._timeCaptions,
            4: self._generateVideoSearchTerms,
            5: self._generateVideoUrls,
            6: self._chooseBackgroundMusic,
            7: self._prepareBackgroundAssets,
            8: self._prepareCustomAssets,
            9: self._editAndRenderShort,
            10: self._addMetadata
        }

    def _generateTempAudio(self):
        if not self._db_script:
            raise NotImplementedError("generateScript method must set self._db_script.")
        if (self._db_temp_audio_path):
            return
        self.verifyParameters(text=self._db_script)
        script = self._db_script
        if (self._db_language != Language.ENGLISH.value):
            self._db_translated_script = gpt_translate.translateContent(script, self._db_language)
            script = self._db_translated_script
        self._db_temp_audio_path = self.voiceModule.generate_voice(
            script, self.dynamicAssetDir + "temp_audio_path.wav")

    def _speedUpAudio(self):
        if (self._db_audio_path):
            return
        self.verifyParameters(tempAudioPath=self._db_temp_audio_path)
        # Since the video is not supposed to be a short( less than 60sec), there is no reason to speed it up
        self._db_audio_path = self._db_temp_audio_path
        return
        self._db_audio_path = audio_utils.speedUpAudio(
            self._db_temp_audio_path, self.dynamicAssetDir + "audio_voice.wav")

    def _timeCaptions(self):
        self.verifyParameters(audioPath=self._db_audio_path)
        whisper_analysis = audio_utils.audioToText(self._db_audio_path)
        max_len = 15
        if not self._db_format_vertical:
            max_len = 30
        self._db_timed_captions = captions.getCaptionsWithTime(
            whisper_analysis, maxCaptionSize=max_len)

    # def _generateVideoSearchTerms(self):
    #     self.verifyParameters(captionsTimed=self._db_timed_captions)
    #     # Returns a list of pairs of timing (t1,t2) + 3 search video queries, such as: [[t1,t2], [search_query_1, search_query_2, search_query_3]]
    #     self._db_timed_video_searches = gpt_editing.getVideoSearchQueriesTimed(self._db_timed_captions)
    def _generateVideoSearchTerms(self):
        self.verifyParameters(captionsTimed=self._db_timed_captions)
        # Returns a list of pairs of timing (t1,t2) + 3 search video queries, such as: [[t1,t2], [search_query_1, search_query_2, search_query_3]]
        self._db_timed_video_searches = gpt_editing.getVideoSearchQueriesTimed(self._db_timed_captions)

        # Ensure search terms are not too specific
        # for i, ((t1, t2), search_terms) in enumerate(self._db_timed_video_searches):
        #     if not search_terms or len(search_terms) < 3:
        #         # Add fallback search terms if necessary
        #         self._db_timed_video_searches[i][1].extend(["nature", "city", "technology"])

    def _generateVideoUrls(self):
        timed_video_searches = self._db_timed_video_searches
        self.verifyParameters(captionsTimed=timed_video_searches)
        timed_video_urls = []
        used_links = []
        for (t1, t2), search_terms in timed_video_searches:
            url = ""
            for query in reversed(search_terms):
                if self.video_data_source == "Local":
                    url = get_best_local_video(query, orientation_landscape=not self._db_format_vertical, used_vids=used_links)
                elif self.api_source == "Pexels":
                    url = getBestVideoPexels(query, orientation_landscape=not self._db_format_vertical, used_vids=used_links)
                elif self.api_source == "Pixabay":
                    url = getBestVideoPixabay(query, orientation_landscape=not self._db_format_vertical, used_vids=used_links)

                if url:
                    used_links.append(url.split('.hd')[0])
                    break
            
            # if not url:
            #     # Log a warning and skip this section
            #     print(f"Warning: No video found for search terms: {search_terms}. Skipping this section.")
            #     continue  # Skip this section instead of raising an error
            
            timed_video_urls.append([[t1, t2], url])
        
        # if not timed_video_urls:
        #     raise ValueError("No videos found for any of the search terms. Please try different search terms or check your API keys.")
        
        self._db_timed_video_urls = timed_video_urls

    def _chooseBackgroundMusic(self):
        if self._db_background_music_name:
            self._db_background_music_url = AssetDatabase.get_asset_link(self._db_background_music_name)

    def _prepareBackgroundAssets(self):
        self.verifyParameters(voiceover_audio_url=self._db_audio_path)
        if not self._db_voiceover_duration:
            self.logger("Rendering short: (1/4) preparing voice asset...")
            self._db_audio_path, self._db_voiceover_duration = get_asset_duration(
                self._db_audio_path, isVideo=False)

    def _prepareCustomAssets(self):
        self.logger("Rendering short: (3/4) preparing custom assets...")
        pass

    def _editAndRenderShort(self):
        self.verifyParameters(
            voiceover_audio_url=self._db_audio_path)

        outputPath = self.dynamicAssetDir + "rendered_video.mp4"
        if not (os.path.exists(outputPath)):
            self.logger("Rendering short: Starting automated editing...")
            videoEditor = EditingEngine()
            videoEditor.addEditingStep(EditingStep.ADD_VOICEOVER_AUDIO, {
                'url': self._db_audio_path})
            if (self._db_background_music_url):
                videoEditor.addEditingStep(EditingStep.ADD_BACKGROUND_MUSIC, {'url': self._db_background_music_url,
                                                                             'loop_background_music': self._db_voiceover_duration,
                                                                             "volume_percentage": 0.08})
            if (self._db_watermark_logo):
                videoEditor.addEditingStep(EditingStep.ADD_WATERMARK_LOGO, {'url' : self._db_watermark_logo})
            for (t1, t2), video_url in self._db_timed_video_urls:
                videoEditor.addEditingStep(EditingStep.ADD_BACKGROUND_VIDEO, {'url': video_url,
                                                                             'set_time_start': t1,
                                                                             'set_time_end': t2})
            if (self._db_format_vertical):
                if(self.text_position == "Middle"):
                    caption_type = EditingStep.ADD_CAPTION_SHORT_ARABIC if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_SHORT
                elif(self.text_position == "Top"):
                    caption_type = EditingStep.ADD_CAPTION_SHORT_ARABIC_TOP if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_SHORT_TOP
                else:
                    caption_type = EditingStep.ADD_CAPTION_SHORT_ARABIC_BOTTOM if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_SHORT_BOTTOM
            else:
                print(self.text_position, self._db_format_vertical)
                if(self.text_position == "Middle"):
                    caption_type = EditingStep.ADD_CAPTION_LANDSCAPE_ARABIC if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_LANDSCAPE
                elif(self.text_position == "Top"):
                    caption_type = EditingStep.ADD_CAPTION_LANDSCAPE_ARABIC_TOP if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_LANDSCAPE_TOP
                else:
                    caption_type = EditingStep.ADD_CAPTION_LANDSCAPE_ARABIC_BOTTOM if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_LANDSCAPE_BOTTOM
            #  if (self._db_format_vertical):
            #     caption_type = EditingStep.ADD_CAPTION_SHORT_ARABIC if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_SHORT
            # else:
            #     caption_type = EditingStep.ADD_CAPTION_LANDSCAPE_ARABIC if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_LANDSCAPE

            for (t1, t2), text in self._db_timed_captions:
                videoEditor.addEditingStep(caption_type, {'text': text.upper(),
                                                         'set_time_start': t1,
                                                         'set_time_end': t2})

            videoEditor.renderVideo(outputPath, logger=self.logger if self.logger is not self.default_logger else None)

            mv = ffmpeg.input(outputPath)
            av1 = mv.audio
            stream = mv.video

            if(self._db_format_vertical):
                if(self.quality=="4k"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=2160, h=3840)
                elif(self.quality=="HD"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=1080, h=1920)
                elif(self.quality=="SD"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=480, h=720)
                else:
                    print("Invalid resolution choice. Using default resolution (HD).")
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=1080, h=1920)
            else:
                if(self.quality=="4k"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=3840, h=2160)
                elif(self.quality=="HD"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=1920, h=1080)
                elif(self.quality=="SD"):
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=720, h=480)
                else:
                    print("Invalid resolution choice. Using default resolution (HD).")
                    stream = stream.filter('fps', fps=25, round='up').filter('scale', w=1920, h=1080)
            outputvideo = self.dynamicAssetDir + "rendered_final_video.mp4"
            outputPath = None


            ffmpeg.output(av1, stream,outputvideo, vcodec='libx264', acodec='aac', strict='-2').run(overwrite_output=True)
            
            self._db_video_path = outputvideo


    def _addMetadata(self):
        try:
            # Ensure the 'videos' directory exists
            os.makedirs('videos', exist_ok=True)

            # Generate YouTube title and description
            self._db_yt_title, self._db_yt_description = gpt_yt.generate_title_description_dict(self._db_script)
            self._db_yt_title = str(self._db_yt_title)
            now = datetime.now()
            clean_title = re.sub('[^a-zA-Z0-9 \'\\n\\.]', '', self._db_yt_title)
            newFileName = f"videos/{now.strftime('%Y-%m-%d_%H-%M-%S')} - {clean_title}"

            # Generate Thumbnail for video
            self._db_thumbnail_path = newFileName + ".jpeg"
            subprocess.call(['ffmpeg', '-i', self._db_video_path, '-ss', '00:00:01.000', '-vframes', '1', '-update', '1', self._db_thumbnail_path])

            # Check if source video exists
            if not os.path.exists(self._db_video_path):
                print(f"ERROR: Source video not found at {self._db_video_path}")
                return False

            # Move the generated video
            shutil.move(self._db_video_path, newFileName + ".mp4")
            self._db_video_path = newFileName + ".mp4"

            # Save the YouTube metadata to a text file
            with open(newFileName + ".txt", "w", encoding="utf-8") as f:
                f.write(f"---Youtube title---\n{self._db_yt_title}\n---Youtube description---\n{self._db_yt_description}")

            # Prepare video data
            video_data = {
                "generate_vid_id": now.strftime("vid_%Y-%m-%d_%H-%M-%S"),
                "thumbnail": self._db_thumbnail_path,
                "generated_video": self._db_video_path,
                "used_script": self._db_script,
                "orientation": "vertical" if self._db_format_vertical else "landscape",
                "used_videos": {f"clip_{idx+1}": {"source": url, "start_time": t1, "end_time": t2, "description": f"Clip {idx+1}"} for idx, ((t1, t2), url) in enumerate(self._db_timed_video_urls)}
            }

            # Store data using TinyMongoDB
            db = VideoMetadataDB()
            if not db.insert_video_data(video_data):  # Attempt insertion
                print("ERROR: Failed to store video metadata")
                return False
            
            return True # Returning from success state
        except Exception as e:
            print(f"Unhandled exception in _addMetadata: {e}")
            traceback.print_exc()
            return False


    # def _addMetadata(self):
    #     if not os.path.exists('videos/'):
    #         os.makedirs('videos')
    #     self._db_yt_title, self._db_yt_description = gpt_yt.generate_title_description_dict(self._db_script)

    #     now = datetime.datetime.now()
    #     date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    #     newFileName = f"videos/{date_str} - " + \
    #         re.sub(r"[^a-zA-Z0-9 '\n\.]", '', self._db_yt_title)

    #     shutil.move(self._db_video_path, newFileName+".mp4")
    #     with open(newFileName+".txt", "w", encoding="utf-8") as f:
    #         f.write(
    #             f"---Youtube title---\n{self._db_yt_title}\n---Youtube description---\n{self._db_yt_description}")
    #     self._db_video_path = newFileName+".mp4"
    #     self._db_ready_to_upload = True
