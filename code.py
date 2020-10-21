#  Launch Deck Trellis M4
#  USB HID button box for launching applications, media control, camera switching and more
#  Use it with your favorite keyboard controlled launcher, such as Quicksilver and AutoHotkey

import time
import random
import adafruit_trellism4
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Rotation of the trellis. 0 is when the USB is upself.
# The grid coordinates used below require portrait mode of 90 or 270
ROTATION = 90

# the two command types -- MEDIA for ConsumerControlCodes, KEY for Keycodes
# this allows button press to send the correct HID command for the type specified
MEDIA = 1
KEY = 2
# button mappings
# customize these for your desired postitions, colors, and keyboard combos
# specify (button coordinate): (color hex value, command type, command/keycodes)
PAGE_DOWN = 78
PAGE_UP = 75
F11 = 44
f5 = 62
RIGHT_ARROW=79
DOWN_ARROW = 81
LEFT_ARROW = 50
UP_ARROW = 82
ENTER=40
keymap = { 
    (0,0): (0x001100, MEDIA, ConsumerControlCode.PLAY_PAUSE),
    (1,0): (0x110011, MEDIA, ConsumerControlCode.SCAN_PREVIOUS_TRACK),
    (2,0): (0x110011, MEDIA, ConsumerControlCode.SCAN_NEXT_TRACK),
    (3,0): (0x000033, MEDIA, ConsumerControlCode.VOLUME_INCREMENT),

    (0,1): (0x110000, MEDIA, ConsumerControlCode.MUTE),
    (1,1): (0x003300 , KEY, (Keycode.GUI, Keycode.ALT, Keycode.CONTROL, Keycode.K)), # Spotify
   #(2,1): (),  
    (3,1): ((0,0,10), MEDIA, ConsumerControlCode.VOLUME_DECREMENT),

    
    # #(0,2): (),
    (1,2): (0x121212, KEY, Keycode.UP_ARROW),  
    # #(2,2): (), 
    #(3,2): (0x979D97, KEY, (Keycode.f5)), 

    (0,3): (0x121212, KEY, Keycode.LEFT_ARROW),
    (1,3): (0x121212, KEY, (Keycode.ENTER)),
    (2,3): (0x121212, KEY, (Keycode.RIGHT_ARROW)),    
    # #(3,3): (),
 
    # #(0,4): (),
    (1,4): (0x121212, KEY, (Keycode.DOWN_ARROW)),
    # #(2,4): (),  
    # #(3,4): (),

    (0,5): (0x444444, KEY, (Keycode.GUI, Keycode.T)), # Terminal
    (1,5): (0x004ca8, KEY, (Keycode.GUI, Keycode.SHIFT, Keycode.CONTROL, Keycode.C)), # VsCode
    #(2,5): (),
    #(3,5): (), 

    (0,6): (0x551100, KEY, (Keycode.GUI, Keycode.CONTROL, Keycode.F, Keycode.ALT)), # FireFox
    (1,6): (0x2f68c7, KEY, (Keycode.GUI, Keycode.ALT, Keycode.CONTROL, Keycode.TWO)), # Chrome
    (2,6): (0x221100, KEY, (Keycode.CONTROL, Keycode.PAGE_UP)), # back cycle tabs 
    (3,6): (0x221100, KEY, (Keycode.CONTROL, Keycode.PAGE_DOWN)) # cycle tabs
    

    # (0,7): (0x060606, KEY, (Keycode.GUI, Keycode.H)),  # hide front app, all windows
    # (1,7): (0x222200, KEY, (Keycode.GUI, Keycode.GRAVE_ACCENT)),  # cycle windows of app
    # (2,7): (0x010001, KEY, (Keycode.GUI, Keycode.TAB)),  # cycle apps forwards
    # (3,7): (0x010001, KEY, (Keycode.GUI, Keycode.SHIFT, Keycode.TAB)) # cycle apps backards

}
# Time in seconds to stay lit before sleeping.
TIMEOUT = 90

# Time to take fading out all of the keys. 
FADE_TIME = 1

# Once asleep, how much time to wait between "snores" which fade up and down one button.
SNORE_PAUSE = 0.5

# Time in seconds to take fading up the snoring LED.
SNORE_UP = 2

# Time in seconds to take fading down the snoring LED.
SNORE_DOWN = 1

TOTAL_SNORE = SNORE_PAUSE + SNORE_UP + SNORE_DOWN

kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

trellis = adafruit_trellism4.TrellisM4Express(rotation=ROTATION)
for button in keymap:
    trellis.pixels[button] = keymap[button][0]

current_press = set()
last_press = time.monotonic()
snore_count = -1
while True:
    pressed = set(trellis.pressed_keys)
    now = time.monotonic()
    sleep_time = now - last_press
    sleeping = sleep_time > TIMEOUT
    for down in pressed - current_press:
        if down in keymap and not sleeping:
            print("down", down)
            # Lower the brightness so that we don't draw too much current when we turn all of
            # the LEDs on.
            trellis.pixels.brightness = 0.2
            trellis.pixels.fill(keymap[down][0])
            if keymap[down][1] == KEY:
                kbd.press(*keymap[down][2]) if type(keymap[down][2]) == tuple else kbd.press(keymap[down][2])
            else:
                cc.send(keymap[down][2])
            # else if the entry starts with 'l' for layout.write
        last_press = now
    for up in current_press - pressed:
        if up in keymap:
            print("up", up)
            if keymap[up][1] == KEY:
                if type(keymap[down][2]) == tuple:
                    kbd.release(*keymap[down][2])
                else:
                    kbd.release(keymap[down][2])

    # Reset the LEDs when there was something previously pressed (current_press) but nothing now
    # (pressed).
    if not pressed and current_press:
        trellis.pixels.brightness = 1
        trellis.pixels.fill((0, 0, 0))
        for button in keymap:
            trellis.pixels[button] = keymap[button][0]

    if not sleeping:
        snore_count = -1
    else:
        sleep_time -= TIMEOUT
        # Fade all out
        if sleep_time < FADE_TIME:
            brightness = (1 - sleep_time / FADE_TIME)
        # Snore by pausing and then fading a random button up and back down.
        else:
            sleep_time -= FADE_TIME
            current_snore = int(sleep_time / TOTAL_SNORE)
            # Detect a new snore and pick a new button
            if current_snore > snore_count:
                button = random.choice(list(keymap.keys()))
                trellis.pixels.fill((0, 0, 0))
                trellis.pixels[button] = keymap[button][0]
                snore_count = current_snore

            sleep_time = sleep_time % TOTAL_SNORE
            if sleep_time < SNORE_PAUSE:
                brightness = 0
            else:
                sleep_time -= SNORE_PAUSE
                if sleep_time < SNORE_UP:
                    brightness = sleep_time / SNORE_UP
                else:
                    sleep_time -= SNORE_UP
                    brightness = 1 - sleep_time / SNORE_DOWN
        trellis.pixels.brightness = brightness
    current_press = pressed

