from control import DucoboxControl
import RPi.GPIO as GPIO
import logging
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

    def open(self):
        GPIO.setmode(GPIO.BCM)
        initial_state = GPIO.HIGH if self._invert else GPIO.LOW
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT, initial=initial_state)

    def close(self):
        GPIO.cleanup()

    def set_state(self, value):
        value = value.upper()
        if value not in self._states:
            raise NotImplementedError("Unsupported value {}".format(value))
        pins = self._states[value].keys()
        values = self._states[value].values()
        GPIO.output(pins, values)
