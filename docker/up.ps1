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
while ($true) {
    $logs = docker logs $container 2>&1 | Out-String
    if ($logs -match 'noVNC started on TCP port') { break }

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
$installLaunchers = @'
set -e
mkdir -p "$HOME/Desktop"
cp /workspace/docker/desktop/*.desktop "$HOME/Desktop/"
chmod +x "$HOME"/Desktop/*.desktop
for f in "$HOME"/Desktop/*.desktop; do
    gio set "$f" metadata::xfce-exe-checksum "$(sha256sum "$f" | cut -d" " -f1)" 2>/dev/null || true
done
'@
docker exec $container bash -lc $installLaunchers

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
Write-Host '    "04 Navigation"       - SLAM mapping'
Write-Host '    "ROS 2 Terminal"      - a shell with ROS 2 already sourced'
Write-Host ''
Write-Host '  Stop with:   docker compose -f docker/docker-compose.yml down'
