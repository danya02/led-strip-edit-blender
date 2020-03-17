#!/usr/bin/python3
import gpiozero

# Due to a weird electrical issue with my relay used to control the power
# supply for the LEDs, it is active whenever the pin is bound to a gpiozero
# object (so it is driven high or low), but it is inactive when the object
# is closed (the pin is floating). This is probably a significant issue, and
# it may break the RPi over time, but because of time (and component)
# constraints here is a software solution.

RELAY_PIN = 16
RELAY_PIN_OBJ = None

def enable_led_psu():
    global RELAY_PIN_OBJ
    if RELAY_PIN_OBJ is not None:
        RELAY_PIN_OBJ.close()
    RELAY_PIN_OBJ = gpiozero.LED(RELAY_PIN)

def disable_led_psu():
    global RELAY_PIN_OBJ
    if RELAY_PIN_OBJ is not None:
        RELAY_PIN_OBJ.close()
    RELAY_PIN_OBJ = None

if __name__ == '__main__':
    # for now, just start the PSU on script start, then wait for exit.
    enable_led_psu()
    import signal
    try:
        signal.pause()
    finally:
        disable_led_psu()
