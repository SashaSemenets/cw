from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp

import speech_recognition as srec

from email.message import EmailMessage
import ssl
import smtplib

import logging
from pythonjsonlogger import jsonlogger
from datetime import datetime
from decouple import config

KV = '''
BoxLayout:
    orientation: 'vertical'
    
    MDLabel:
        id: info
        text: ""
        halign: "center"

    BoxLayout:
        size_hint: None, None
        size: "48dp", "48dp"
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        MDIconButton:
            icon: "microphone"
            on_touch_down: app.on_button_down()
'''


def recognize_speech(rec, mic):
    with mic as source:
        rec.adjust_for_ambient_noise(source)
        audio = rec.listen(source, phrase_time_limit=5)
    try:
        res = {"Текст": rec.recognize_google(audio, show_all=False, language="uk-UA")}
    except:
        res = {"Текст": None}
    return res


class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stled = "OFF"
        self.voiceCommand = ""
        self.data_rp = f"status led: {self.stled}\n" \
                       f"{self.voiceCommand}\n"
        self.email_sender = config("EMAIL_SENDER", default='')
        self.email_password = config("EMAIL_PASSWORD", default='')
        self.email_receiver = config("EMAIL_RECEIVER", default='')
        self.subject = "LED status was changed"
        self.body = """"""

    def on_start(self):
        self.root.ids.info.text = self.data_rp

    def build(self):
        return Builder.load_string(KV)

    def update_data(self):
        self.data_rp = f"status led: {self.stled}\n" \
                       f"{self.voiceCommand}\n"

    def setStatusLed(self, val):
        self.stled = "ON" if val else "OFF"
        print("Status LED changed in: " + str(self.stled))

    def sendEmail(self):
        self.body = self.data_rp

        em = EmailMessage()
        em['From'] = self.email_sender
        em['To'] = self.email_receiver
        em['Subject'] = self.subject
        em.set_content(self.body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(self.email_sender, self.email_password)
            smtp.sendmail(self.email_sender, self.email_receiver, em.as_string())


    def update_log(self):
        formatter = jsonlogger.JsonFormatter()
        json_handler = logging.FileHandler(filename='NewLog.json')
        json_handler.setFormatter(formatter)
        logger = logging.getLogger('my_json')
        logger.addHandler(json_handler)
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(formatted_datetime, extra={'status_led': self.stled})


    def on_button_down(self):
        print("Кнопка утримується натиснутою")
        recognizer = srec.Recognizer()
        mic = srec.Microphone()
        result = recognize_speech(recognizer, mic)
        self.voiceCommand = 'Вами було сказано: \n{}'.format(result['Текст'])
        print(self.voiceCommand)

        if result['Текст'] == "Вимкнути світло":
            self.setStatusLed(False)
        if result['Текст'] == "Увімкнути світло":
            self.setStatusLed(True)

        self.update_data()
        self.root.ids.info.text = self.data_rp
        self.sendEmail()
        self.update_log()


if __name__ == "__main__":
    try:
        Window.size = (300, 600)
        MyApp().run()
    except KeyboardInterrupt:
        print("exiting")
        MyApp().client.disconnect()
