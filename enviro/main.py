import time
from machine import Pin, ADC, UART
from picographics import PicoGraphics, DISPLAY_ENVIRO_PLUS
from pimoroni import RGBLED, Button
from breakout_bme68x import BreakoutBME68X, STATUS_HEATER_STABLE
from pimoroni_i2c import PimoroniI2C
from breakout_ltr559 import BreakoutLTR559
import umqtt.simple
import WIFI_CONFIG
from network_manager import NetworkManager
import uasyncio

"""
This example reads from all the sensors on Enviro+.
(plus the optional particulate sensor)
Posts results via MQTT.
"""

# change this to adjust temperature compensation
TEMPERATURE_OFFSET = 3

# MQTT broker settings
CLIENT_ID = "EnviroPlus"
SERVER_ADDRESS = "io.adafruit.com"
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
UPDATE_INTERVAL = 60  # how often to post MQTT data, in seconds


def status_handler(mode, status, ip):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("Network: {}".format(WIFI_CONFIG.SSID), 10, 10, scale=2)
    status_text = "Connecting..."
    if status is not None:
        if status:
            status_text = "Connection successful!"
        else:
            status_text = "Connection failed!"

    display.text(status_text, 10, 30, scale=2)
    display.text("IP: {}".format(ip), 10, 60, scale=2)
    display.update()

def describe_pressure(pressure_hpa):
    """Convert pressure into barometer-type description."""
    if pressure_hpa < 970:
        description = "storm"
    elif 970 <= pressure_hpa < 990:
        description = "rain"
    elif 990 <= pressure_hpa < 1010:
        description = "change"
    elif 1010 <= pressure_hpa < 1030:
        description = "fair"
    elif pressure_hpa >= 1030:
        description = "dry"
    else:
        description = ""
    return description

def describe_humidity(corrected_humidity):
    """Convert relative humidity into good/bad description."""
    if 40 < corrected_humidity < 60:
        description = "good"
    else:
        description = "bad"
    return description

def adjust_to_sea_pressure(pressure_hpa, temperature, altitude):
    """
    Adjust pressure based on your altitude.

    credits to @cubapp https://gist.github.com/cubapp/23dd4e91814a995b8ff06f406679abcf
    """

    # Adjusted-to-the-sea barometric pressure
    adjusted_hpa = pressure_hpa + ((pressure_hpa * 9.80665 * altitude) / (287 * (273 + temperature + (altitude / 400))))
    return adjusted_hpa

def get_all_sensors():
    # read BME688
    temperature, pressure, humidity, gas, status, _, _ = bme.read()
    heater = "Stable" if status & STATUS_HEATER_STABLE else "Unstable"

    # correct temperature and humidity using an offset
    corrected_temperature = temperature - TEMPERATURE_OFFSET
    dewpoint = temperature - ((100 - humidity) / 5)
    corrected_humidity = 100 - (5 * (corrected_temperature - dewpoint))
    # convert pressure into hpa
    pressure_hpa = pressure / 100

    # correct pressure
    pressure_hpa = adjust_to_sea_pressure(pressure_hpa, corrected_temperature, altitude)

    # read LTR559
    ltr_reading = ltr.get_reading()
    lux = ltr_reading[BreakoutLTR559.LUX]
    prox = ltr_reading[BreakoutLTR559.PROXIMITY]

    # read mic
    mic_reading = mic.read_u16()

    if not(heater == "Stable" and ltr_reading is not None):
        raise BaseException("No values")

    return corrected_temperature, pressure_hpa, describe_pressure(pressure), corrected_humidity, describe_humidity(humidity), gas, status, mic_reading, lux

def draw_measurements(temperature, humidity, humidity_description, pressure, pressure_description, gas):
    led.set_rgb(0, 0, 0)

    # draw some stuff on the screen
    display.set_pen(BLACK)
    display.clear()

    # draw the top box
    display.set_pen(GREY)
    display.rectangle(0, 0, WIDTH, 60)

    # pick a pen colour based on the temperature
    display.set_pen(GREEN)
    if temperature > 30:
        display.set_pen(RED)
    if temperature < 10:
        display.set_pen(CYAN)
    display.text(f"{temperature:.1f}°c", 5, 15, WIDTH, scale=4)

    # draw the first column of text
    display.set_pen(WHITE)
    display.text(f"rh {humidity:.0f}%", 0, 75, WIDTH, scale=3)
    display.text(f"{pressure:.0f}hPa", 0, 125, WIDTH, scale=3)

    # draw the second column of text
    display.text(f"{humidity_description}", 125, 75, WIDTH, scale=3)
    display.text(f"{pressure_description}", 125, 125, WIDTH, scale=3)

    # draw bar for gas
    if min_gas != max_gas:
        # light the LED and set pen to red if the gas / air quality reading is less than 50%
        if (gas - min_gas) / (max_gas - min_gas) < GAS_ALERT:
            led.set_rgb(255, 0, 0)
            display.set_pen(RED)
        else:
            display.set_pen(GREEN)

        display.rectangle(236, HEIGHT - round((gas - min_gas) / (max_gas - min_gas) * HEIGHT), 4, round((gas - min_gas) / (max_gas - min_gas) * HEIGHT))
        display.text("gas", 185, 210, WIDTH, scale=3)

    display.update()

# set up wifi
network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=status_handler)

# set up the display
display = PicoGraphics(display=DISPLAY_ENVIRO_PLUS)
display.set_backlight(1.0)

# set up the LED
led = RGBLED(6, 7, 10, invert=True)
led.set_rgb(255, 0, 0)

# set up the buttons
button_a = Button(12, invert=True)
button_b = Button(13, invert=True)

# set up the Pico W's I2C
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}
i2c = PimoroniI2C(**PINS_BREAKOUT_GARDEN)

# set up BME688 and LTR559 sensors
bme = BreakoutBME68X(i2c, address=0x77)
ltr = BreakoutLTR559(i2c)

# set up analog channel for microphone
mic = ADC(Pin(26))

# sets up MQTT
mqtt_client = umqtt.simple.MQTTClient(client_id=CLIENT_ID, server=SERVER_ADDRESS, user=MQTT_USERNAME, password=MQTT_PASSWORD, keepalive=30)

# some constants we'll use for drawing
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
CYAN = display.create_pen(0, 255, 255)
MAGENTA = display.create_pen(200, 0, 200)
YELLOW = display.create_pen(200, 200, 0)
BLUE = display.create_pen(0, 0, 200)
FFT_COLOUR = display.create_pen(255, 0, 255)
GREY = display.create_pen(75, 75, 75)

WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

# some other variables we'll use to keep track of stuff
current_time = 0
mqtt_time = 0
mqtt_success = False
e = "Wait a minute"

# change this to adjust pressure based on your altitude
altitude = 0
min_gas = 100000.0
max_gas = 0.0

# light the LED red if the gas reading is less than 50%
GAS_ALERT = 0.5

# connect to wifi
uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))

# the gas sensor gives a few weird readings to start, lets discard them
temperature, pressure, humidity, gas, status, _, _ = bme.read()
time.sleep(0.5)
temperature, pressure, humidity, gas, status, _, _ = bme.read()
time.sleep(0.5)

temperature = 0
pressure = 0
pressure_description = "nah"
humidity = 0
humidity_description = "nah"
gas = 0.0

while True:

    try:
        temperature, pressure, pressure_description, humidity, humidity_description, gas, status, mic_reading, lux = get_all_sensors()

        # record min and max gas readings
        if gas > max_gas:
            max_gas = gas
        if gas < min_gas:
            min_gas = gas

        led.set_rgb(0, 0, 0)
        current_time = time.ticks_ms()
        if (current_time - mqtt_time) / 1000 >= UPDATE_INTERVAL:
            # then do an MQTT
            try:
                mqtt_client.connect()
                mqtt_client.publish(topic="renatolond/feeds/EnviroTemperature", msg=bytes(str(temperature), 'utf-8'), qos=1)
                mqtt_client.publish(topic="renatolond/feeds/EnviroHumidity", msg=bytes(str(humidity), 'utf-8'), qos=1)
                mqtt_client.publish(topic="renatolond/feeds/EnviroPressure", msg=bytes(str(pressure), 'utf-8'), qos=1)
                mqtt_client.publish(topic="renatolond/feeds/EnviroGas", msg=bytes(str(gas), 'utf-8'), qos=1)
                mqtt_client.publish(topic="renatolond/feeds/EnviroLux", msg=bytes(str(lux), 'utf-8'), qos=1)
                mqtt_client.publish(topic="renatolond/feeds/EnviroMic", msg=bytes(str(mic_reading), 'utf-8'), qos=1)
                mqtt_client.disconnect()
                mqtt_success = True
                mqtt_time = time.ticks_ms()
                led.set_rgb(0, 50, 0)
            except Exception as e:
                print(e)
                mqtt_success = False
                led.set_rgb(255, 0, 0)
    except Exception as e:
        print(e)
        # light up the LED red if there's a problem with MQTT or sensor readings
        led.set_rgb(255, 0, 0)

    # turn off the backlight with A and turn it back on with B
    # things run a bit hotter when screen is on, so we're applying a different temperature offset
    if button_a.is_pressed:
        display.set_backlight(1.0)
        TEMPERATURE_OFFSET = 5
        time.sleep(0.5)
    elif button_b.is_pressed:
        display.set_backlight(0)
        TEMPERATURE_OFFSET = 3
        time.sleep(0.5)

    draw_measurements(temperature, humidity, humidity_description, pressure, pressure_description, gas)

    time.sleep(1.0)
