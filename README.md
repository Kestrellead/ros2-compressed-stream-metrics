![ci](https://github.com/Kestrellead/ros2-compressed-stream-metrics/actions/workflows/ci.yml/badge.svg)

# ros2-compressed-stream-metrics
Simulated camera/ToF streaming with configurable compression and end-to-end latency/loss metrics.
Pure Python now; ROS 2 wrappers later.

## GSoC Pitch (short)
- Problem: quantify compression vs. latency/loss for RGB/ToF streams.
- Today: pure-Python simulation with encoder choices, metrics, CSV export, CI, tests.
- Next: ROS 2 `rclpy` nodes mapping to `sensor_msgs/Image` and `image_transport`.
- Outcome: reproducible benchmarks + drop-in metrics node for robotics pipelines.
