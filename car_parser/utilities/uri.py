from urllib import urlencode
from urlparse import urlparse, parse_qsl, urlunparse


def get_parameter(uri, parameter_name):
    parts = urlparse(uri)
    parameters = dict(parse_qsl(parts.query))
    return parameters[parameter_name]


def remove_parameter(uri, parameter_name):
    parts = list(urlparse(uri))
    parameters = dict(parse_qsl(parts[4]))
    parameters.pop(parameter_name, None)
    parts[4] = urlencode(parameters)
    return urlunparse(parts)


def set_parameter(uri, parameter_name, parameter_value):
    parts = list(urlparse(uri))
    parameters = dict(parse_qsl(parts[4]))
    parameters[parameter_name] = parameter_value
    parts[4] = urlencode(parameters)
    return urlunparse(parts)


def clear_parameters(uri):
    parts = list(urlparse(uri))
    parameters = dict(parse_qsl(parts[4]))
    parameters.clear()
    parts[4] = urlencode(parameters)
    return urlunparse(parts)