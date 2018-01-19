from control import DucoboxControl
import RPi.GPIO as GPIO
import logging
from time import sleep
# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class DucoboxGpioControl(DucoboxControl):

    def __init__(self, config):
        log.info("Initializing Duco GPIO controller")
        super(DucoboxGpioControl, self).__init__(config)
        self._invert = config['active_low']
        self._states = dict(
            (state.upper(), dict(
                (
                    int(pin),
                    val != self._invert
                ) for
                (pin, val) in sett.items())
            ) for
            (state, sett)
            in config['states'].items())
        # this gets the unique pin numbers from the states object,
        # I have no idea how it works, but it does
        self._pins = set(k for v in self._states.values() for k in v.keys())
        self._values = {}

    def open(self):
        GPIO.setmode(GPIO.BCM)
        initial_value = GPIO.HIGH if self._invert else GPIO.LOW
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT, initial=initial_value)
        self._initial_values = dict((pin, initial_value) for pin in self._pins)
        self._values = dict(self._initial_values)

    def close(self):
        GPIO.cleanup()

    def set_state(self, value):
        value = value.upper()
        if value not in self._states:
            raise NotImplementedError("Unsupported value {}".format(value))
        self.set_values(self._states[value])

    def set_values(self, values):
        current_values = dict((p,v) for (p,v)
                              in self._values.iteritems()
                              if p in values)

        if current_values == values:
            if values == self._initial_values:
                self.set_state("CNT2")
            else:
                self.set_values(self._initial_values)
            sleep(0.1)

        for (pin, pin_value) in values.iteritems():
            GPIO.output(pin, pin_value)
            self._values[pin] = pin_value
