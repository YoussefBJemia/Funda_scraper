from setuptools import find_packages, setup
from typing import List

cst = '-e .'
def get_requirements(file_path:str):
    requirements = []
    with open('requirements.txt') as f:
        requirements = [req.replace("\n", "") for req in f.readlines()]
        if cst in requirements:
            requirements.remove(cst)
        return requirements
        
NAME = "Funda_scraper"
URL = "https://github.com/YoussefBJemia/Funda_scraper"
EMAIL = "youssef.benjemia@hotmail.com"
AUTHOR = "Youssef Ben Jemia"
        
setup(
    name=NAME,
    version='0.0.1',
    author=AUTHOR,
    author_email=EMAIL,
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt'),
    url = URL,
    entry_points={
        'console_scripts': [
            'funda-scraper = main:main_function',
        ],
    },
)