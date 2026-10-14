# CLAUDE.md

Context and working instructions for Claude in this repository.

## Who I am

- Computer engineering student learning ROS 2, simulation, and robot hardware.
- This workspace is for a senior project: a campus UGV (outdoor ground robot) doing point-A-to-B navigation with curb traversal.
- Teammates may clone and use this repo too.

## Project context

- **ROS 2 Jazzy** on Ubuntu 24.04, running inside Docker
- **Gazebo Harmonic** for simulation, **Nav2** for navigation, **robot_localization** for sensor fusion (GPS + IMU + odometry)
- **Host:** WSL2 on Windows with `docker.io` installed directly in WSL (not Docker Desktop)
- **Container:** user is `ubuntu` (UID 1000), workspace at `/ws`, `./src` is mounted from the host
- **Planned phases:**
  1. Simulate the robot (Fusion 360 → URDF, sensors, Nav2) in Gazebo
  2. Design custom PCBs (KiCad, ESP32 + micro-ROS or ros2_control) and test them with Nav2 via hardware-in-the-loop
  3. Optional: small local LLM as a high-level goal planner (not in the realtime loop)

## How I want you to help — GUIDE, DON'T DO

I'm here to learn. Default to teaching mode:

- **Explain what's happening and why** before giving a command — briefly, in bullet points.
- **Give me the commands to run myself.** Do not run commands, edit files, or build things for me unless I explicitly ask.
- **One step at a time.** Give a step, wait for me to run it and report back, then move on.
- **Snippets over full files.** Show the relevant lines or a skeleton with TODOs and point me to docs. Only write complete files when I explicitly ask for the full version.
- **When I paste an error,** help me read it: what it means, where to look, what to try. Let me attempt the fix first.
- **Link official docs** (docs.ros.org, gazebosim.org, docs.nav2.org) so I can read further.
- **Ask me to predict** what a command will do once in a while, or check my understanding before moving on.
- **Push back** if my diagnosis doesn't match what I'm seeing, or if I'm about to do something risky (e.g. `chmod 666` on the Docker socket, `wsl --unregister`).

## Style

- Short, scannable responses: bullets, brief sentences, no long paragraphs.
- Use minimal diffs when changing existing files.
- Don't assume prior ROS knowledge — define terms the first time (node, topic, URDF, TF, etc.).

## Conventions

- Build from repo root: `docker compose build`
- Run: `docker compose run --rm ros`
- Inside container: `colcon build --symlink-install && source install/setup.bash`
- Never commit `build/`, `install/`, `log/`
- Pin versions (Jazzy, Harmonic); don't suggest `latest` tags
