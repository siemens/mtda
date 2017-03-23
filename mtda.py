# System imports
import configparser
import importlib

# Local imports
import power_controller

parser = configparser.ConfigParser()
config_files = [ 'mtda.ini' ]
configs_found = parser.read(config_files)

if parser.has_section('power'):
   try:
       # Get variant
       variant = parser.get('power', 'variant')
       # Try loading its support class
       mod = importlib.import_module(variant)
       factory = getattr(mod, 'instantiate')
       power_controller = factory()
       # Configure and probe the power controller
       power_controller.configure(dict(parser.items('power')))
       power_controller.probe()
   except configparser.NoOptionError:
       print('power controller variant not defined!')
   except ImportError:
       print('power controller "%s" could not be found/loaded!' % (variant))


