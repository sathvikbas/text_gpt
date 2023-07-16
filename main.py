from flask import Flask, request
from app_functions import *
import audioop
import base64
import json
import os
from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
import vosk
import time
from config import *

app = Flask(__name__)
sock = Sock(app)
model = vosk.Model('stt_model')

CL = '\x1b[0K'
BS = '\x08'

account_sid = twilio_sid
auth_token = twilio_token
twilio_client = Client(account_sid, auth_token)


@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    message_body = request.form['Body']
    form = request.form

    print(request.form)

    print(number)
    print(message_body)

    if 'image:' in message_body.lower():
        print('IMAGE')
        image_prompt = message_body.strip('image:')

        try:
            gen_image(number, image_prompt, message=None)

        except Exception as e:
            respond(number, e)

    elif 'save_me' in message_body.lower():
        print('SAVE ME')

        try:
            save_person(form, latitude=None, longitude=None, zip_code=None)

        except Exception as e:
            respond(number, e)

    elif 'weather' in message_body.lower():
        print('WEATHER')

        try:
            weather(form)

        except Exception as e:
            respond(number, e)

    elif 'https://www.google.com/maps/place/' in message_body.lower() or 'https://maps.apple.com/' in message_body.lower():
        print('CURR LOC')

        try:
            curr_loc(message_body)

        except Exception as e:
            respond(number, e)

    elif 'find' in message_body.lower() and 'near me' in message_body.lower():
        print('FIND')
        message_body = message_body.strip('find').strip('near me')

        try:
            near_me(number, message_body)

        except Exception as e:
            respond(number, e)

    else:
        print('CHATGPT')
        chatGPT(number, message_body)

    return str(message_body)


@app.route('/call', methods=['POST'])
def call():
    """Accept a phone call."""
    response = VoiceResponse()
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)
    response.say('Please leave a message')
    response.pause(length=60)
    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


@sock.route('/stream')
def stream(ws):
    """Receive and transcribe audio stream."""
    rec = vosk.KaldiRecognizer(model, 16000)
    while True:
        message = ws.receive()
        packet = json.loads(message)
        if packet['event'] == 'start':
            print('Streaming is starting')
        elif packet['event'] == 'stop':
            print('\nStreaming has stopped')
        elif packet['event'] == 'media':
            audio = base64.b64decode(packet['media']['payload'])
            audio = audioop.ulaw2lin(audio, 2)
            audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
            if rec.AcceptWaveform(audio):
                r = json.loads(rec.Result())
                # print(CL + r['text'] + ' ', end='', flush=True)
                transcript = CL + r['text'] + ' '
                print('transcript: ', transcript)

            else:
                r = json.loads(rec.PartialResult())
                print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)


if __name__ == '__main__':

    port = 5001
    number = twilio_client.incoming_phone_numbers.list()[0]
    print(f'Waiting for calls on {number.phone_number}')

    app.run(port=port)


