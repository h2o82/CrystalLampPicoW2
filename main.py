import network
import socket
import neopixel
from machine import Pin, Timer
import time
import ntptime
import random

# ----------------------------------------------------------------
# 1) Configuration
# ----------------------------------------------------------------
LED_COUNT = 36         # Number of WS2812B LEDs in your ring
DATA_PIN = 0           # GPIO pin for NeoPixel data line
WIFI_SSID = ""   # Wi-Fi SSID
WIFI_PASS = ""      # Wi-Fi password

ntptime.host = "uk.pool.ntp.org"

# Offset so code's LED 0 appears physically at 12 o'clock 
# if hardware LED 0 is physically at 6 o'clock.
OFFSET = 18

def map_led(pos):
    """
    Shift the 'logical' LED position by OFFSET 
    so code's LED 0 is physically at 12 o'clock.
    """
    return (pos + OFFSET) % LED_COUNT

# ----------------------------------------------------------------
# 2) Build a Custom Order for "Center-Out" Matrix
# ----------------------------------------------------------------
def build_matrix_order(center, length):
    """
    Returns a list of LED indices, starting at `center`,
    then going +1, -1, +2, -2, etc., until we fill the ring.

    Example for center=18 on a 36-LED ring might be:
      [18, 19, 17, 20, 16, 21, 15, 22, 14, ...]
    so the "rain" starts at index 18, then flows outward 
    to the right and left in an alternating pattern.
    """
    order = [center]
    step = 1
    direction = +1  # alternate +1 (right) and -1 (left)
    while len(order) < length:
        new_idx = (center + direction * step) % length
        order.append(new_idx)
        # flip direction after each append
        direction = -direction
        if direction < 0:
            # we completed a +step and a -step, so increase step
            step += 1
    return order

MATRIX_ORDER = build_matrix_order(center=0, length=LED_COUNT)
# This defines the "path" along which intensities will travel.

# ----------------------------------------------------------------
# 3) Initialize NeoPixel + Wi-Fi
# ----------------------------------------------------------------
np = neopixel.NeoPixel(Pin(DATA_PIN), LED_COUNT)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)
print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    pass
print("Wi-Fi connected!")
print("IP Address:", wlan.ifconfig()[0])

# ----------------------------------------------------------------
# 4) Global Flags & Indices
# ----------------------------------------------------------------
chase_active = False
purplegreen_active = False
clock_mode = False
heartbeat_active = False
rainbow_active = False
star_active = False
matrix_active = False

# Indices for chasing
chase_index = 0
chase_index2 = LED_COUNT - 1

# Timer counters
clock_counter = 0
heartbeat_index = 0
rainbow_index = 0

# ----------------------------------------------------------------
# 5) Heartbeat Frames
# ----------------------------------------------------------------
heartbeat_frames = [10, 80, 255, 80, 20, 150, 60, 20, 10, 0]

# ----------------------------------------------------------------
# 6) Buffers
# ----------------------------------------------------------------

# For the "standard top-down" matrix, use matrix_buf by direct index.
# store intensities by the "logical" LED index (0..35).
# store them in an array, but SHIFT them according to MATRIX_ORDER.
matrix_buf = [0] * LED_COUNT  # Each is a green intensity

# ----------------------------------------------------------------
# 7) Helper Functions
# ----------------------------------------------------------------
def set_color(color):
    """Set ALL LEDs to a single colour, then write out."""
    for i in range(LED_COUNT):
        np[map_led(i)] = color
    np.write()

def wheel(pos):
    """Rainbow colour generator."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def sync_ntp():
    """Sync the Pico's RTC with NTP (UTC)."""
    try:
        ntptime.settime()
        print("Time successfully synced from NTP.")
    except Exception as e:
        print("Failed to sync time from NTP:", e)

def update_clock_display():
    """
    Show the current time on the ring:
      Hour = red, Minute = green, Second = blue
    Scale 0..59 -> 0..35.
    """
    now = time.localtime()
    hour = now[3]    # 0..23
    minute = now[4]  # 0..59
    second = now[5]  # 0..59

    second_led = (second * LED_COUNT) // 60
    minute_led = (minute * LED_COUNT) // 60
    hour_fraction = minute / 60.0
    hour_position = (hour % 12) + hour_fraction
    hour_led = int((hour_position * LED_COUNT) / 12) % LED_COUNT

    np.fill((0,0,0))

    np[map_led(hour_led)]   = (255, 0,   0)
    np[map_led(minute_led)] = (0,   255, 0)
    np[map_led(second_led)] = (0,   0,   255)
    np.write()

# ----------------------------------------------------------------
# 8) Web Server
# ----------------------------------------------------------------
def serve_client(client):
    global chase_active, purplegreen_active, clock_mode
    global heartbeat_active, rainbow_active, star_active, matrix_active
    global chase_index, chase_index2

    request = client.recv(1024)
    request_str = str(request)

    if "GET /off" in request_str:
        set_color((0, 0, 0))
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /red" in request_str:
        set_color((255, 0, 0))
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /green" in request_str:
        set_color((0, 255, 0))
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /blue" in request_str:
        set_color((0, 0, 255))
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /chase" in request_str:
        chase_active = True
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False
        chase_index = 0
        chase_index2 = 0

    elif "GET /purplegreen" in request_str:
        chase_active = False
        purplegreen_active = True
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False
        chase_index = 0
        chase_index2 = LED_COUNT - 1

    elif "GET /clock" in request_str:
        chase_active = False
        purplegreen_active = False
        clock_mode = True
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /heartbeat" in request_str:
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = True
        rainbow_active = False
        star_active = False
        matrix_active = False

    elif "GET /rainbow" in request_str:
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        star_active = False
        matrix_active = False
        rainbow_active = True

    elif "GET /stars" in request_str:
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        matrix_active = False
        star_active = True

    elif "GET /matrix" in request_str:
        # "Center-Out" Matrix mode
        chase_active = False
        purplegreen_active = False
        clock_mode = False
        heartbeat_active = False
        rainbow_active = False
        star_active = False
        matrix_active = True
        # Reset the matrix buffer
        for i in range(LED_COUNT):
            matrix_buf[i] = 0
        # Clear ring
        set_color((0,0,0))

    elif "GET /ntp" in request_str:
        sync_ntp()

    # Build and send the HTML response
    response = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
    <title>LED Control</title>
</head>
<body>
    <h1>LED Light Control</h1>
    <p>IP Address: """ + wlan.ifconfig()[0] + """</p>
    <button onclick="location.href='/off'">Off</button>
    <button onclick="location.href='/red'">Red</button>
    <button onclick="location.href='/green'">Green</button>
    <button onclick="location.href='/blue'">Blue</button>
    <button onclick="location.href='/chase'">Red/Green Chase</button>
    <button onclick="location.href='/purplegreen'">Purple/Green Chase</button>
    <hr>
    <button onclick="location.href='/clock'">Clock</button>
    <button onclick="location.href='/heartbeat'">Heartbeat</button>
    <button onclick="location.href='/rainbow'">Rainbow</button>
    <button onclick="location.href='/stars'">Stars</button>
    <button onclick="location.href='/matrix'">Matrix (Center-Out)</button>
    <hr>
    <button onclick="location.href='/ntp'">Sync NTP</button>
</body>
</html>"""
    client.send(response)
    client.close()

# ----------------------------------------------------------------
# 9) Timer Callback (100ms)
# ----------------------------------------------------------------
def chase_effect(timer):
    global chase_index, chase_index2
    global chase_active, purplegreen_active, clock_mode
    global heartbeat_active, rainbow_active, star_active, matrix_active
    global heartbeat_index, rainbow_index, clock_counter
    global matrix_buf

    clock_counter += 1

    # 1) CLOCK MODE
    if clock_mode:
        if clock_counter >= 10:  # 100ms * 10 = 1 second
            clock_counter = 0
            update_clock_display()
        return

    # 2) HEARTBEAT MODE (full ring)
    if heartbeat_active:
        brightness = heartbeat_frames[heartbeat_index]
        for i in range(LED_COUNT):
            np[map_led(i)] = (brightness, 0, 0)
        np.write()
        heartbeat_index = (heartbeat_index + 1) % len(heartbeat_frames)
        return

    # 3) RAINBOW MODE
    if rainbow_active:
        for i in range(LED_COUNT):
            pixel_index = (i * 256 // LED_COUNT + rainbow_index) & 255
            np[map_led(i)] = wheel(pixel_index)
        np.write()
        rainbow_index = (rainbow_index + 1) % 256
        return

    # 4) STARS MODE
    if star_active:
        np.fill((0,0,0))
        led_index = random.randrange(LED_COUNT)
        r = random.randrange(256)
        g = random.randrange(256)
        b = random.randrange(256)
        np[map_led(led_index)] = (r, g, b)
        np.write()
        return

    # 5) MATRIX (Center-Out)
    if matrix_active:
        # SHIFT from the end of MATRIX_ORDER down to 1
        # so matrix_buf[MATRIX_ORDER[i]] = matrix_buf[MATRIX_ORDER[i-1]] - fade
        for i in range(LED_COUNT-1, 0, -1):
            src_idx = MATRIX_ORDER[i-1]
            dst_idx = MATRIX_ORDER[i]
            # dim the intensity as it moves outward
            old_val = matrix_buf[src_idx]
            matrix_buf[dst_idx] = max(0, old_val - 5)

        # Possibly spawn a new drip at the center (MATRIX_ORDER[0] = 18)
        if random.random() < 0.8:
            matrix_buf[MATRIX_ORDER[0]] = random.randint(180, 255)

        # Write to LEDs
        for i in range(LED_COUNT):
            g_intensity = matrix_buf[i]
            np[map_led(i)] = (0, g_intensity, 0)
        np.write()
        return

    # 6) CHASE ANIMATIONS
    if chase_active:
        np.fill((0, 0, 0))
        # Toggle red/green pixel
        color = (255 * (chase_index % 2), 255 * ((chase_index + 1) % 2), 0)
        np[map_led(chase_index)] = color
        np.write()
        chase_index = (chase_index + 1) % LED_COUNT

    elif purplegreen_active:
        np.fill((0, 0, 0))
        purple = (128, 0, 128)
        green  = (0, 255, 0)
        np[map_led(chase_index)]  = purple
        np[map_led(chase_index2)] = green
        np.write()
        chase_index = (chase_index + 1) % LED_COUNT
        chase_index2 = (chase_index2 - 1) % LED_COUNT


# ----------------------------------------------------------------
# 10) Start Timer + Web Server
# ----------------------------------------------------------------
chase_timer = Timer()
chase_timer.init(period=100, mode=Timer.PERIODIC, callback=chase_effect)

sock = socket.socket()
sock.bind(('', 80))
sock.listen(5)
print("Web server listening on http://{}:80/".format(wlan.ifconfig()[0]))

while True:
    client, addr = sock.accept()
    print("Client connected from", addr)
    serve_client(client)

