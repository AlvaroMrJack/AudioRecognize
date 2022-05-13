import os
import time
import shutil
import asyncio
import zipfile
import pathlib
import logging
import traceback
import subprocess
from datetime import datetime
from pydub import AudioSegment
import speech_recognition as sr
from pydub.silence import split_on_silence

#logging.basicConfig(filename='execution.log',level=logging.DEBUG)
CURRENT_DIRECTORY   = pathlib.Path().resolve()
FOLDER_NAME         = "audio-chunks"
FFMPEG              = os.path.join("C:\\", "ffmpeg", "bin", "ffmpeg") 
PRINCIPAL_LANG      = "es-CL"
FILES               = []
NEW_FILE_PATH       = ""
NEW_TEXT_FILE_PATH  = ""
NEW_TEXT_FILE_PATH  = ""
FINAL_TEXT          = ""
ROOT                = ""
r = sr.Recognizer()

def run_speech_recognition():
    for root, dirs, files in os.walk(CURRENT_DIRECTORY):
        ROOT = root
        for file in files: 
            if file.endswith('.mp3'):
                FILES.append(os.path.join(root,file))
        for src in FILES:
            NEW_TEXT_FILE_PATH = src.replace(".mp3", ".txt")
            if not os.path.exists(NEW_TEXT_FILE_PATH):
                NEW_FILE_PATH = os.path.join(root,src.replace(".mp3", ".wav"))
                if not os.path.exists(NEW_FILE_PATH):
                    subprocess.call([FFMPEG, '-i', src, NEW_FILE_PATH])
                try:
                    loop = asyncio.get_event_loop()
                    FINAL_TEXT = loop.run_until_complete(get_large_audio_transcription(NEW_FILE_PATH))
                    with open(os.path.join(root, NEW_TEXT_FILE_PATH), "w") as text_file:
                        text_file.write(FINAL_TEXT)
                    os.remove(NEW_FILE_PATH)
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.info(e)
        
async def get_large_audio_transcription(path):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """
    # open the audio file using pydub
    sound = AudioSegment.from_wav(path)  
    # split audio sound where silence is 700 miliseconds or more and get chunks
    chunks = split_on_silence(sound,
        # experiment with this value for your target audio file
        min_silence_len = 500,
        # adjust this per requirement
        silence_thresh = sound.dBFS-14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=500,
    )
    # create a directory to store the audio chunks
    if not os.path.isdir(FOLDER_NAME):
        os.mkdir(FOLDER_NAME)
    whole_text = ""
    # process each chunk 
    for i, audio_chunk in enumerate(chunks, start=1):
        # export audio chunk and save it in
        # the `FOLDER_NAME` directory.
        chunk_filename = os.path.join(FOLDER_NAME, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        # recognize the chunk
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            # try converting it to text
            try:
                text = r.recognize_google(audio_listened, language = PRINCIPAL_LANG)
            except sr.UnknownValueError as e:
                #print("Error:", str(e))
                #logging.error(traceback.format_exc())
                pass
            else:
                text = f"{text.capitalize()}. "
                #print(chunk_filename, ":", text)
                whole_text += text
    # return the text for all chunks detected
    return whole_text

def validate_ffmpeg():
    try:
        subprocess.call([FFMPEG])
        return True
    except FileNotFoundError:
        ffmpeg_file_path    = os.path.join(CURRENT_DIRECTORY, "ffmpeg.zip")
        dir_expected        = os.path.join("C:\\", "ffmpeg")
        log_time            = datetime.today().strftime('%Y-%m-%d %H_%M_%S_%f')
        log_file_name       = f"execution_{log_time}.log"
        try:
            if not os.path.isdir(dir_expected):
                with zipfile.ZipFile(ffmpeg_file_path, 'r') as zip_ref:
                    zip_ref.extractall("C://")
                    return True
            else:
                try:
                    subprocess.call([FFMPEG])
                    return True
                except FileNotFoundError as e:
                    logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
                    logging.info(e)
                    logging.error(traceback.format_exc())
                    return False
        except Exception as e:
            logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
            logging.error(traceback.format_exc())
            logging.info(e)
            return False
if __name__ == '__main__':
    if validate_ffmpeg():
        run_speech_recognition()
        if os.path.isdir(os.path.join(ROOT, FOLDER_NAME)):
            shutil.rmtree(os.path.join(ROOT, FOLDER_NAME))

# https://realpython.com/python-speech-recognition/
# https://www.thepythoncode.com/article/using-speech-recognition-to-convert-speech-to-text-python