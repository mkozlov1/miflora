import urllib.request
import base64
import time
from miflora.miflora_poller import MiFloraPoller, \
    MI_CONDUCTIVITY, MI_MOISTURE, MI_LIGHT, MI_TEMPERATURE, MI_BATTERY

LOOP_COUNT = 5
SLEEP_TIME_SECONDS = 3
# Settings for the domoticz server

# Forum see: http://domoticz.com/forum/viewtopic.php?f=56&t=13306&hilit=mi+flora&start=20#p105255

domoticzserver   = "127.0.0.1:8080"
domoticzusername = ""
domoticzpassword = ""

# So id devices use: sudo hcitool lescan

# Sensor IDs

# Create 4 virtual sensors in dummy hardware
# type temperature
# type lux
# type percentage (moisture)
# type custom (fertility)

base64string = base64.encodestring(('%s:%s' % (domoticzusername, domoticzpassword)).encode()).decode().replace('\n', '')

def domoticzrequest (url):
  request = urllib.request.Request(url)
  request.add_header("Authorization", "Basic %s" % base64string)
  response = urllib.request.urlopen(request)
  return response.read()

def pollValues(address, idx_moist, idx_temp, idx_lux, idx_cond):

    poller = MiFloraPoller(address)

    # reading error in poller (happens sometime, you go and bug the original author):
    #
    # 26231 fertility
    # 136% moisture
    # 4804.2 temperature
    # 61149 lux
    loop = 0
    try:
        temp = poller.parameter_value(MI_TEMPERATURE)
    except:
        temp = 201
    
    while loop < 2 and temp > 200:
        print("Error reading value retry after 5 seconds...\n")
        time.sleep(5)
        poller = MiFloraPoller(address)
        loop += 1
        try:
            temp = poller.parameter_value(MI_TEMPERATURE)
        except:
            temp = 201
    
    if temp > 200:
        raise Exception("Error reading value")

    #print("Mi Flora: " + address)
    #print("Firmware: {}".format(poller.firmware_version()))
    #print("Name: {}".format(poller.name()))
    val_temp = "{}".format(poller.parameter_value(MI_TEMPERATURE))
    val_lux = "{}".format(poller.parameter_value(MI_LIGHT))
    val_moist = "{}".format(poller.parameter_value(MI_MOISTURE))
    val_cond = "{}".format(poller.parameter_value(MI_CONDUCTIVITY))
    val_bat  = "{}".format(poller.parameter_value(MI_BATTERY))
    return float(val_moist), float(val_temp), float(val_lux), float(val_cond), float(val_bat)

def update(address, idx_moist, idx_temp, idx_lux, idx_cond):
    val_temp_total = 0
    val_lux_total = 0
    val_moist_total = 0
    val_cond_total = 0
    val_bat_total = 0
    loop = 0
    success_count = 0
    while loop < LOOP_COUNT:
        try:
            val_moist, val_temp, val_lux, val_cond, val_bat = pollValues(address, idx_moist, idx_temp, idx_lux, idx_cond)
        except Exception:
            continue

        val_temp_total += val_temp
        val_lux_total += val_lux
        val_moist_total += val_moist
        val_cond_total += val_cond
        val_bat_total += val_bat
        loop += 1
        success_count += 1
        time.sleep(SLEEP_TIME_SECONDS)

    val_temp_total = round(val_temp_total/success_count, 2)
    val_lux_total = round(val_lux_total/success_count, 2)
    val_moist_total = round(val_moist_total/success_count, 2)
    val_cond_total = round(val_cond_total/success_count, 2)
    val_bat_total = round(val_bat_total/success_count, 2)

    print("Temperature: {}°C".format(val_temp_total))
    print("Moisture: {}%".format(val_moist_total))
    print("Light: {} lux".format(val_lux_total))
    print("Fertility: {} uS/cm?".format(val_cond_total))
    print("Battery: {}%".format(val_bat_total))

    pushData(idx_temp, idx_lux, idx_cond, val_temp_total, val_lux_total, val_moist_total, val_cond_total, val_bat_total)
    time.sleep(1)

def pushData(idx_moist, idx_temp, idx_lux, idx_cond, val_temp, val_lux, val_moist, val_cond, val_bat):
    global domoticzserver

    # Update temp
    domoticzrequest("http://" + domoticzserver + "/json.htm?type=command&param=udevice&idx=" + idx_temp + "&nvalue=0&svalue=" + val_temp + "&battery=" + val_bat)

    # Update lux
    domoticzrequest("http://" + domoticzserver + "/json.htm?type=command&param=udevice&idx=" + idx_lux + "&svalue=" + val_lux + "&battery=" + val_bat)

    # Update moisture
    domoticzrequest("http://" + domoticzserver + "/json.htm?type=command&param=udevice&idx=" + idx_moist + "&svalue=" + val_moist + "&battery=" + val_bat)

    # Update fertility
    domoticzrequest("http://" + domoticzserver + "/json.htm?type=command&param=udevice&idx=" + idx_cond + "&svalue=" + val_cond + "&battery=" + val_bat)
