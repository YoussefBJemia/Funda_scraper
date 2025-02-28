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
        

        
setup(
    name = 'Funda_scraper',
    version = '0.0.1',
    author = 'YBJ',
    author_email = 'y.benjemia@tilburguniversity.edu',
    packages = find_packages(),
    install_requires = get_requirements('requirements.txt')
)