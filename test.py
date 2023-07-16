from urllib.parse import urlparse, parse_qs
import re
import openai
import json
import re
from flask import Flask, request
from twilio.rest import Client
from geopy.geocoders import Nominatim
import requests


apple_url = "https://maps.apple.com/?address=3616%20Spring%20Garden%20St,%20Philadelphia,%20PA%20%2019104,%20United%20States&ll=39.962294,-75.195263&q=My%20Location&t=h"
google_url = ""


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

def save_person(item1, item2, item3, item4):
   return None


ll(google_url)
