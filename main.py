import pycom
import urequests as requests
import machine
from machine import Pin
import time
import binascii
from dht import DHT
import credentials


## Define helping variables

delay = 60 * 15  # Delay in seconds = 15 minutes

prompt_count = 0 # Helping variable for a 'Thank you' statement below


## Defining functions for sending json to Ubidots as a request
# Builds the json to send the request
def build_json(variable1, value1, variable2, value2, variable3, value3, variable4, value4):
    try:
        data = {variable1: {"value": value1},
                variable2: {"value": value2},
                variable3: {"value": value3},
                variable4: {"value": value4}}
        return data
    except:
        return None

# Sends the request. Please reference the REST API reference https://ubidots.com/docs/api/
def post_var(device, value1, value2, value3, value4):
    try:
        url = "https://industrial.api.ubidots.com/"
        url = url + "api/v1.6/devices/" + device
        headers = {"X-Auth-Token": credentials.ubidots_token, "Content-Type": "application/json"}
        data = build_json("Temperature", value1, "Humidity", value2, "Close_shutters_prompt", value3, "Thank_you_statement", value4)
        if data is not None:
            req = requests.post(url=url, headers=headers, json=data)
            return req.json()
        else:
            pass
    except:
        pass


## Setup sensors
# Setup for DHT11
th = DHT(Pin('P23', mode=Pin.OPEN_DRAIN), 0)
time.sleep(2)

# Setup for photoresistor window
adc_w = machine.ADC()
apin_w = adc_w.channel(pin='P14')

# Setup for photoresistor table
adc_t = machine.ADC()
apin_t = adc_t.channel(pin='P13')


## Define light measure function
def light_measure(pin_input):
    light = pin_input()
    return light


## Main body of the funtion
while True:

## Measure temperature and humidity, create variables and print to console
    result = th.read()
    while not result.is_valid():
        time.sleep(.5)
        result = th.read()

    temperature = result.temperature
    humidity = result.humidity

    print('Temp: ', temperature)
    print()
    print('RH: ', humidity)
    print()


## Measure light at window and table and print values to console
# Measure light at window and print value:
    light_w = light_measure(apin_w)
    print('Light window: ', light_w)
    print('')

# Measure light at table and print value
    light_t = light_measure(apin_t)
    print('Light table: ', light_t)
    print('')


## Check whether a shutter close prompt must be sent and activate LED accordingly
# Define helping variables to analyse need for closing of shutters
    sunlight = False
    shutters_open = True
    close_shutters_prompt = 0
    thank_you_statement = 0

# If the sunlight on the windowsill gets intense, the variable sunlight turns True
    if light_w < 600:
        sunlight = True

# If the difference between the light at the window and the light at the table is high enough, closed shuttters are indicated
    if light_t > (light_w + 1500):
        shutters_open = False

# If there is strong sunlight at the window and the shutters are opened, the LED turns red, a prompt to close the shutters is printed to the console and the changed variable triggers an event at Ubidots which sends an e-mail with a close shutters prompt
# The two lower if-clauses avoid the prompt from being sent too often => Once every 4 x delay
    if sunlight == True and shutters_open == True:
        if prompt_count == 4:
            prompt_count = 0
        if prompt_count == 0:
            close_shutters_prompt = 1
            print('Close the shutters, please!')
            print()
        prompt_count += 1 # Variable is incremented to steer the 'Thank you' statement below
        pycom.rgbled(0xFF0000) # LED is red


# If the shutters were closed after a close prompt, the LED turns green, the 'Thank you' statement is printed to the console, the prompt counter is reset and an event is triggered at Ubidots sending the 'Thank you' statement via e-mail
# This part of the function avoids the event from being triggered in each loop
    if shutters_open == False and prompt_count > 0:
        thank_you_statement = 1
        print('Thank you for closing the shutters!')
        print()
        prompt_count = 0 # Reset prompt count to avoid 'Thank you' message from being sent more than once
        pycom.rgbled(0x007f00) # LED is green

# If the sunlight is low or the shutters are closed no prompt is neccessary and the LED is green
    else:
        prompt_count = 0 # Reset prompt_count for next day if it is not yet 0
        pycom.rgbled(0x007f00) # LED is green


## Post data to Ubidots
    post_var("LTH", temperature, humidity, close_shutters_prompt, thank_you_statement)


## Set device into sleep mode for time defined in delay
    time.sleep(delay)
