from setuptools import setup, find_packages

setup(
    name='spacy-whisper',
    version='0.1.0',  # You can change this version number as needed
    author='Your Name',  # Replace with your name or organization
    author_email='your.email@example.com',  # Replace with your email
    description='Integrate Whisper transcriptions with spaCy for advanced NLP tasks',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/theirstory/spacy-whisper',  # Replace with the URL to your repository
    packages=find_packages(),
    install_requires=[
        'spacy>=3.0',  # Assuming spaCy v3.0 or higher is required
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
    ],
    keywords='NLP, spaCy, Whisper, transcription'
)
