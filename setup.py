import setuptools

setuptools.setup(
    name='negwm',
    version='0.9.1',
    description='An example package',
    url='#',
    author='Neg',
    install_requires=[
        'asyncinotify',
        'docopt',
        'ewmh',
        'i3ipc',
        'inotipy',
        'psutil',
        'pulsectl',
        'rich',
        'xdg',
        'Xlib',
        'yamlloader',
    ],
    author_email='serg.zorg@gmail.com',
    packages=setuptools.find_packages(),
    zip_safe=False
)
