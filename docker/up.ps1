# Build and start the educational ROS 2 + Gazebo workspace (Windows).
#
#   .\docker\up.ps1
#
# Then open http://localhost:6902 (VNC password: ros2edu).
#
# Windows PowerShell 5.1 compatible: no && chaining, no ternary operators.

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $here 'docker-compose.yml'
$container = 'ros2-gazebo-edu'

# Host ports. Defaults avoid 6901/5901, which another noVNC container may
# already hold. Override for this run:
#   $env:NOVNC_PORT=6910; .\docker\up.ps1
if (-not $env:NOVNC_PORT) { $env:NOVNC_PORT = '6902' }
if (-not $env:VNC_PORT)   { $env:VNC_PORT   = '5902' }

Write-Host '[up] building image (first run downloads ~4GB, allow 10-20 min)...'
docker compose -f $composeFile build
if ($LASTEXITCODE -ne 0) { throw 'docker compose build failed' }

Write-Host '[up] starting container...'
docker compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed' }

Write-Host '[up] waiting for the desktop...'
# Probe noVNC itself rather than grepping `docker logs` for a startup
# line: the base image is :latest, and newer versions no longer print
# "noVNC started on TCP port" to stdout, which left this loop waiting
# forever on a desktop that was already up. 6901 is the in-container
# port, so this works whatever NOVNC_PORT the host side was mapped to.
#
# 'Continue' around the probe: under 'Stop', PowerShell 5.1 turns any
# stderr from docker exec (e.g. while the container is still starting)
# into a terminating error, even with 2>$null.
while ($true) {
    $ErrorActionPreference = 'Continue'
    docker exec $container curl -sf -o /dev/null http://localhost:6901/vnc.html 2>$null
    $ready = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = 'Stop'
    if ($ready) { break }

    $status = docker ps --filter "name=$container" --format '{{.Status}}'
    if (-not ($status -match 'Up')) {
        Write-Host '[up] container exited unexpectedly:' -ForegroundColor Red
        docker logs --tail 40 $container
        throw 'container did not start'
    }
    Start-Sleep -Seconds 2
}

Write-Host '[up] installing desktop launchers...'
# Copied into the desktop user's home rather than launched from the
# bind-mounted /workspace, so they behave like normal desktop entries.
# They exist because the noVNC clipboard does not bridge to the host.
#
# No double quotes in this snippet, on purpose: Windows PowerShell 5.1
# does not escape embedded " when passing an argument to a native exe,
# so `"$(sha256sum "$f" ...)"` arrived in bash broken. None of these
# paths contain spaces, so leaving them unquoted is safe.
$installLaunchers = @'
set -e
mkdir -p ~/Desktop
cp /workspace/docker/desktop/*.desktop ~/Desktop/
chmod +x ~/Desktop/*.desktop
for f in ~/Desktop/*.desktop; do
    gio set $f metadata::xfce-exe-checksum $(sha256sum $f | cut -d' ' -f1) 2>/dev/null || true
done
'@
# .gitattributes checks .ps1 files out as CRLF, so this here-string
# carries a \r on every line; bash then fails on `do\r`. Strip them.
$installLaunchers = $installLaunchers -replace "`r", ''
docker exec $container bash -lc $installLaunchers
if ($LASTEXITCODE -ne 0) { throw 'installing desktop launchers failed' }

Write-Host '[up] building the ROS 2 workspace (colcon)...'
docker exec $container bash -lc '/workspace/docker/build_ws.sh'
if ($LASTEXITCODE -ne 0) { throw 'colcon build failed' }

Write-Host ''
Write-Host '[up] ready.' -ForegroundColor Green
Write-Host ''
Write-Host "  Open:  http://localhost:$($env:NOVNC_PORT)      (VNC password: ros2edu)"
Write-Host ''
Write-Host '  On the browser desktop, double-click:'
Write-Host '    "01 Hello ROS 2"      - talker/listener, the core pub/sub demo'
Write-Host '    "02 Gazebo World"     - EduBot in Gazebo + RViz2, lidar and camera'
Write-Host '    "03 Teleop"           - drive the robot with the keyboard'
Write-Host '    "04 SLAM Mapping"     - build a map with slam_toolbox'
Write-Host '    "05 Obstacle Avoider" - the robot drives itself, avoiding obstacles'
Write-Host '    "06 Moon Rover"       - six-wheel rover on the Moon'
Write-Host '    "07 Mars Rover"       - six-wheel rover on Mars'
Write-Host '    "08 Rover Camera"     - the rover''s forward camera view'
Write-Host '    "09 Nav2 Waypoints"   - click goals in RViz; the rover drives there'
Write-Host '    "ROS 2 Terminal"      - a shell with ROS 2 already sourced'
Write-Host ''
Write-Host '  Stop with:   docker compose -f docker/docker-compose.yml down'
