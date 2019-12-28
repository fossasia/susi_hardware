""" Class to Represent Recognizing State
"""
import logging
import threading
from threading import get_ident
import speech_recognition as sr
from .base_state import State
from .internet_test import internet_on
from .lights import lights
from ..player import player
from ..config import susi_config

try:
    import RPi.GPIO as GPIO
except:
    pass

logger = logging.getLogger(__name__)


class RecognizingState(State):
    """
    Recognizing State inherits from Base State class. In this state,
    audio is recorded from the microphone and  recognized with the
    Speech Recognition Engine set as default in the configuration.
    """

    def __recognize_audio(self, recognizer, audio):
        logger.info("Trying to recognize audio with %s in language: %s", 
                    self.components.config['default_stt'], 
                    susi_config["language"])
        if self.components.config['default_stt'] == 'google':
            return recognizer.recognize_google(
                audio, language=susi_config["language"])

        elif self.components.config['default_stt'] == 'watson':
            username = self.components.config['watson_stt_config']['username']
            password = self.components.config['watson_stt_config']['password']
            return recognizer.recognize_ibm(
                username=username,
                password=password,
                language=susi_config["language"],
                audio_data=audio)

        elif self.components.config['default_stt'] == 'pocket_sphinx':
            lang = susi_config["language"].replace("_", "-")
            if internet_on():
                self.components.config['default_stt'] = 'google'
                return recognizer.recognize_google(audio, language=lang)
            else:
                return recognizer.recognize_sphinx(audio, language=lang)

        elif self.components.config['default_stt'] == 'bing':
            api_key = self.components.config['bing_speech_api_key']
            return recognizer.recognize_bing(
                audio_data=audio, key=api_key,
                language=susi_config["language"])

        elif self.components.config['default_stt'] == 'deepspeech-local':
            lang = susi_config["language"].replace("_", "-")
            return recognizer.recognize_deepspeech(audio, language=lang)

    def on_enter(self, payload=None):
        """
        Executed on the entry to the Recognizing State. Upon entry,
        audio is captured from the Microphone and recognition with
        preferred speech recognition engine is done. If successful,
        the machine transitions to Busy State. On failure, it transitions
        to Error state.
        :param payload: No payload is expected by this state.
        :return: None
        """
        """
        Starting the Timer else SUSI would remain infinitely in the
        recognizing state.
        """

        logger.debug("RECOGNIZING(" + str(get_ident()) + "): entering")
        self.timer = threading.Timer(10.0, 
                                     lambda : self.transition(self.allowedStateTransitions.get('error'),
                                                                    payload='DetectionTimeout'))
        self.timer.start()


        logger.info('Recognizing')
        self.notify_renderer('listening')
        recognizer = self.components.recognizer

        try:
            logger.info("Let's say something!")
            if self.useGPIO:
                GPIO.output(22, True)
            with self.components.microphone as source:
                audio = recognizer.listen(source, phrase_time_limit=5)
            self.notify_renderer('recognizing')
            if self.useGPIO:
                GPIO.output(22, False)
            logger.info("Got it! Now to recognize it...")
            lights.off()
            lights.think()
            try:
                value = self.__recognize_audio(
                    audio=audio, recognizer=recognizer)
                logger.debug("__recognize_audio => %s", value)
                self.notify_renderer('recognized', value)
                self.transition(self.allowedStateTransitions.get(
                    'busy'), payload=value)
            except sr.UnknownValueError as e:
                logger.error("UnknownValueError from SpeechRecognition: %s", e)
                self.transition(self.allowedStateTransitions.get('error'),
                                payload='RecognitionError')

            except sr.RequestError as e:
                logger.error(
                    "Uh oh! Couldn't request results from Speech Recognition service. Error: %s", e)
                self.transition(self.allowedStateTransitions.get(
                    'error'), payload='ConnectionError')

        except KeyboardInterrupt:
            pass
        except RuntimeError:
            pass
        except ImportError:
            logger.warning("This device doesn't have GPIO port")
        logger.debug("RECOGNIZING(" + str(get_ident()) + "): entering done")

    def on_exit(self):
        """
        Method to executed upon exit from Recognizing State.
        :return:
        """
        logger.debug("RECOGNIZING(" + str(get_ident()) + "): leaving")
        # we saved the volume when doing a beep
        player.restore_softvolume()
        if hasattr(self, 'timer'):
            self.timer.cancel()
        if self.useGPIO:
            try:
                GPIO.output(27, False)
                GPIO.output(22, False)
            except RuntimeError:
                pass
        pass
        logger.debug("RECOGNIZING(" + str(get_ident()) + "): leaving done")
