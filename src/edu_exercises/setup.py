import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'edu_exercises'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='DFKI Robotics Teaching',
    maintainer_email='hilmi_dogu.kuecueker@dfki.de',
    description='Student exercises (with solutions) for the teaching workspace.',
    license='BSD-3-Clause',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # The student's own files, with the TODOs to fill in.
            'ex01_publisher = edu_exercises.ex01_publisher:main',
            'ex02_subscriber = edu_exercises.ex02_subscriber:main',
            'ex03_wall_follower = edu_exercises.ex03_wall_follower:main',
            # The reference answers, runnable side by side with the above
            # so a student can see the target behaviour before reading the
            # code that produces it.
            'sol01_publisher = solutions.ex01_publisher:main',
            'sol02_subscriber = solutions.ex02_subscriber:main',
            'sol03_wall_follower = solutions.ex03_wall_follower:main',
        ],
    },
)
