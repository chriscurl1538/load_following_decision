"""
See https://packaging.python.org/en/latest/tutorials/packaging-projects/
See https://pythonhosted.org/an_example_pypi_project/setuptools.html
See https://docs.python.org/3/distutils/setupscript.html
"""

try:
    from setuptools import setup, find_packages
except ImportError:
    import setup

setup(name='',
      version='',
      description='',
      author='Chris Curl',
      author_email='christopher.r.curl@gmail.com',
      url='',
      packages=[''])
