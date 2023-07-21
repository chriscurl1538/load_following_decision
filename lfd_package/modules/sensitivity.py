"""
Module Description:
    This module performs a sensitivity analysis on the following Python variables:
    - Electricity costs
    - Fuel costs
    - Incentives
    - TES Size
"""

# from sensitivity import SensitivityAnalyzer as sa


def make_param_list(base=None, increm=None, variation=None):
    start_val = base - variation
    stop_val = base + variation + 1
    param_list = []
    for value in range(start_val, stop_val, increm):
        param_list.append(value)
    return param_list


if __name__ == "__main__":
    test_list = make_param_list(base=20, increm=1, variation=4)
    for item in test_list:
        print(item)
