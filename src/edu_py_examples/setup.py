import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'edu_py_examples'

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
    description='Worked examples for the ROS 2 + Gazebo teaching workspace.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        # Each line here is what makes `ros2 run edu_py_examples <name>`
        # work. Add a new node file and you must add a line here too, then
        # rebuild - forgetting this step is the usual reason a brand new
        # node "does not exist".
        'console_scripts': [
            # Module 01 - core ROS 2 concepts
            'talker = edu_py_examples.talker:main',
            'listener = edu_py_examples.listener:main',
            'parameter_demo = edu_py_examples.parameter_demo:main',
            'service_demo = edu_py_examples.service_demo:main',
            # Module 02 - sensors
            'lidar_monitor = edu_py_examples.lidar_monitor:main',
            # Module 03 - TF2 and odometry
            'tf_listener = edu_py_examples.tf_listener:main',
            'square_driver = edu_py_examples.square_driver:main',
            # Module 04 - control
            'obstacle_avoider = edu_py_examples.obstacle_avoider:main',
        ],
    },
)
