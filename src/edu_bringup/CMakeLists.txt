cmake_minimum_required(VERSION 3.8)
project(edu_bringup)

find_package(ament_cmake REQUIRED)

# This package ships no compiled code: everything in it is data that the
# launch system reads at runtime, so it only needs installing.
install(
  DIRECTORY launch worlds models rviz config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
