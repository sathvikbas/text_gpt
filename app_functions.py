from twilio.rest import Client
from geopy.geocoders import Nominatim
import requests
from urllib.parse import urlparse, parse_qs
import openai
import json
import re
from flask import request
from main import twilio_client
from twilio.twiml.voice_response import VoiceResponse
from config import *


openai.api_key = openai_api_key


url = "https://weatherapi-com.p.rapidapi.com/current.json"

ybada

def respond(phone_num, msg):
    try:
        message = twilio_client.messages \
            .create(
            body=msg,
            from_='+12486022475',
            to=phone_num
        )

    except openai.error.InvalidRequestError as e:
        message = twilio_client.messages \
            .create(
            body='Error in Prompt: {}'.format(e),
            from_='+12486022475',
            to=phone_num
        )

    print(message.sid)


def respond_image(phone_num, msg, img_url):
    try:
        message = twilio_client.messages.create(
            from_='+12486022475',
            to=phone_num,
            media_url=[img_url],
            body=msg,
        )

    except openai.error.InvalidRequestError as e:
        message = twilio_client.messages \
            .create(
            body='Error in Prompt: {}'.format(e),
            from_='+12486022475',
            to=phone_num
        )

    print(message.sid)


def gen_image(number, content, message):
    response = openai.Image.create(
        prompt=content,
        n=1,
        size="256x256",
    )

    print(response["data"][0]["url"])
    print('IMAGE PROMPT: ', content)

    url = response["data"][0]["url"]

    if message is None:
        message = 'Here is your image!'

    respond_image(number, message, url)


def chatGPT(number, content, response_type=None):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": content}
        ]
    )

    chat_resposne = completion.choices[0].message.content
    print(chat_resposne)

    if response_type is not None:
        return chat_resposne

    else:
        response = chat_resposne
        respond(number, response)


def weather(form):
    number = request.form['From']

    with open('users.json') as f:
        data = json.load(f)

    for record in data:
        if number in record:
            zip_code = record[number]["zip_code"]

            querystring = {"q": zip_code}

            api_response = requests.request("GET", url, headers=weather_headers, params=querystring).json()
            curr_weather = api_response["current"]

            temperature = curr_weather["temp_f"]
            weather_condition = curr_weather["condition"]["text"]
            feels_like = curr_weather["feelslike_f"]
            wind = curr_weather["wind_mph"]

            if curr_weather["is_day"] == 1:
                time_of_day = "daytime"

            else:
                time_of_day = "nighttime"

            response = "Today's weather is {} at {} degrees Fahrenheit but feels like {}. You can expect winds of " \
                       "upto {} mph. It is currently {}".format(weather_condition, temperature, feels_like, wind,
                                                                time_of_day)

            print(response)
            img_prompt = weather_condition + ' weather at ' + time_of_day

            gen_image(number, img_prompt, response)


# def time_to_destination(content):

def near_me(number, content):
    with open('users.json', 'r') as f:
        data = json.load(f)

    latitude = ''
    longitude = ''

    for record in data:
        if number in record:
            latitude = record[number]["latitude"]
            longitude = record[number]["longitude"]

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={},{}&radius=1500&keyword={}&" \
          "key={}".format(latitude, longitude, content, google_maps_api_key)

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    for result in response['results']:
        # phone_num, msg, img_url

        try:
            if result['opening_hours']['open_now'] is True:
                is_open = 'This {} is currently open!'.format(content)

            else:
                is_open = 'This {} is currently closed :('.format(content)

        except KeyError:
            is_open = 'Unknown'

        try:
            price_level = result['price_level']

        except KeyError:
            price_level = 'Unknown'

        rating = result['rating']
        user_ratings_total = result['user_ratings_total']
        tags_string = 'This place is classified as: ' + ', '.join(tag for tag in result["types"])
        address = result['vicinity']

        message = 'Name: {}\n ' \
                  'Ratings: {} by {} users\n' \
                  'Cost: {}\n' \
                  '{}\n' \
                  '{}\n' \
                  'Located at: {}\n'.format(result['name'], rating, user_ratings_total, price_level, tags_string,
                                            is_open, address)

        respond_image(number, message, result["icon"])


    print(response)


def curr_loc(url):
    geolocator = Nominatim(user_agent="get_zip")

    if 'maps.apple.com' in url:
        # Parse the URL and extract the "ll" parameter
        parsed_url = urlparse(url)
        query_dict = parse_qs(parsed_url.query)
        ll = query_dict["ll"][0]
        latitude, longitude = ll.split(",")

        # Extract the zipcode using regular expressions
        zipcode_match = re.search(r'\b\d{5}\b', query_dict["address"][0])
        zip_code = zipcode_match.group() if zipcode_match else None

        print("Latitude:", latitude)
        print("Longitude:", longitude)
        print("Zipcode:", zip_code)

        save_person(url, latitude, longitude, zip_code)


    elif 'www.google.com/maps/place/' in url:
        pattern = r"place/(-?\d+\.\d+)\+(-?\d+\.\d+)"

        # Extract latitude and longitude using the regular expression
        match = re.search(pattern, url)

        latitude = ''
        longitude = ''

        if match:
            latitude = str(match.group(1))
            longitude = str(match.group(2))
            print("Latitude:", latitude)
            print("Longitude:", longitude)

        else:
            print("Latitude and longitude not found in URL")

        loc = latitude + ', ' + longitude
        location = geolocator.reverse(loc)
        words = location.address.split(',')

        print(words)

        for word in words:
            if len(word.strip()) == 5 and word.strip().isdigit():
                zip_code = word
                save_person(url, latitude, longitude, zip_code)

                break


def save_person(form, latitude, longitude, zip_code):
    print("SAVE")
    number = request.form['From']

    if zip_code is None:
        zip_code = request.form.get('zip_code', form.get('FromZip', None))

    name = None

    message = request.form['Body'].lower().strip('save_me')

    message_parts = message.split(',')
    for part in message_parts:
        key_value = part.split(':')
        if len(key_value) == 2:
            key = key_value[0].strip().lower()
            value = key_value[1].strip()
            if key == 'name':
                name = value

            elif key in ('zip', 'zipcode', 'zip_code'):
                zip_code = value

    with open('users.json') as f:
        data = json.load(f)

    person_d = None
    for record in data:
        if number in record:
            person_d = record
            break

    querystring = {"q": zip_code}

    api_response = requests.request("GET", url, headers=weather_headers, params=querystring).json()
    city = api_response["location"]["name"]
    state = api_response["location"]["region"]
    country = api_response["location"]["country"]

    if person_d is not None:
        # Update existing person data
        person_d[number]['name'] = name or person_d[number]['name']
        person_d[number]['city'] = city or person_d[number]['city']
        person_d[number]['state'] = state or person_d[number]['state']
        person_d[number]['country'] = country or person_d[number]['country']
        person_d[number]['zip_code'] = zip_code or person_d[number]['zip_code']
        person_d[number]['latitude'] = latitude or person_d[number]['latitude']
        person_d[number]['longitude'] = longitude or person_d[number]['longitude']

        respond(number, 'Your details have been updated')

    else:
        # Create new person data
        person_d = {number: {"name": name, "city": city, "state": state, "country": country, "zip_code": zip_code,
                             "latitude": latitude, "longitude": longitude}}
        data.append(person_d)
        respond(number, 'You have been saved')

    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)

