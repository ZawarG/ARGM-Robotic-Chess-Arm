from setuptools import find_packages, setup

package_name = 'argm_chess'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Aasees',
    maintainer_email='129808072+aaseesb@users.noreply.github.com',
    description='ROS 2 nodes for the ARGM robotic chess arm',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'planner_node = argm_chess.planner_node:main',
            'arm_node = argm_chess.arm_node:main',
        ],
    },
)
