from utils import merge
import re

def get_para(target, node, para, timeout=1):
    data = target.run_command("nodeparaget {} {}".format(node, para), timeout=timeout)
    return data[2][4:]


def get_temperature(target):
    return int(get_para(target, 4, 73))/10.0 # degC

def get_co2(target):
    return int(get_para(target, 4, 74)) # ppm

def get_humidity(target):
    return int(get_para(target, 4, 75))/100.0 # %

def get_network_data(target):
    line_regex = re.compile(r'^((?:[^\|]+?\|){19}[^\|]+?)$')
    field_regex = re.compile(r'([^ \|\n]+) *(?:\||$)')

    fields = \
        list(
            list(
                i.group(1) for i in field_regex.finditer(l)
            )
            for l
            in (
                i.group(1) for i in (
                    line_regex.match(l)
                    for l
                    in target.run_command("network")
                ) if i is not None
            )
        )
    keys = fields[0]
    values = fields[1:]
    return dict((fields[0], dict(zip(keys, ((v if v != "-" else None) for v in fields)))) for fields in values)

def get_fan_speed(target):
    line_regex = re.compile(r'^FanSpeed:(.+)$')
    field_regex = re.compile(r'([A-Z][a-z]+) ([0-9]+) \[rpm\]')

    fields = \
        list(
            dict(
                (i.group(1), int(i.group(2))) for i in field_regex.finditer(l)
            )
            for l
            in (
                i.group(1) for i in (
                    line_regex.match(l)
                    for l
                    in target.run_command("fanspeed")
                ) if i is not None
            )
        )
    return merge(fields)
