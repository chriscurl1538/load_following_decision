"""
Set global unit registry for use throughout the software package
"""

from pint import UnitRegistry, set_application_registry
ureg = UnitRegistry()
set_application_registry(ureg)
Q_ = ureg.Quantity
