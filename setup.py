from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='crrem',
  version='0.2.6',
  description='A climate value at risk calculator',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  long_description_content_type='text/markdown',
  author='Rupert Xu',
  author_email='rupert.xu@blockchainclimate.org',
  license='MIT', 
  classifiers=classifiers,
  keywords='climate value at risk', 
  packages=find_packages(),
  install_requires=['pandas>=1.1.3','numpy>=1.19.2','psycopg2>=2.8.6'] 
)