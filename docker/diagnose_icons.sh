#!/usr/bin/env bash
# Diagnose missing desktop icons. Run inside the container:
#   docker exec ros2-gazebo-edu bash /workspace/docker/diagnose_icons.sh
echo "=== 1. Which .desktop files exist on the Desktop? ==="
ls -l "$HOME/Desktop"/*.desktop 2>/dev/null | awk '{print $1, $5, $NF}'
echo
echo "=== 2. Which exist in the repo (source of truth)? ==="
ls -1 /workspace/docker/desktop/*.desktop 2>/dev/null | xargs -n1 basename
echo
echo "=== 3. Do the launcher scripts they point to exist? ==="
for f in "$HOME"/Desktop/*.desktop; do
    [ -e "$f" ] || continue
    e=$(grep -m1 '^Exec=' "$f" | cut -d= -f2-)
    n=$(grep -m1 '^Name=' "$f" | cut -d= -f2-)
    [ -x "$e" ] && echo "  OK      [$n]" || echo "  BROKEN  [$n] -> $e"
done
echo
echo "=== 4. Do their Icon= names resolve in the installed theme? ==="
for f in "$HOME"/Desktop/*.desktop; do
    [ -e "$f" ] || continue
    i=$(grep -m1 '^Icon=' "$f" | cut -d= -f2-)
    n=$(grep -m1 '^Name=' "$f" | cut -d= -f2-)
    hit=$(find /usr/share/icons /usr/share/pixmaps -name "${i}.*" 2>/dev/null | head -1)
    [ -n "$hit" ] && echo "  OK      [$n] $i" || echo "  MISSING [$n] icon '$i' not in theme"
done
echo
echo "=== 5. Icon theme in use ==="
export DISPLAY="${DISPLAY:-:1}"
xfconf-query -c xsettings -p /Net/IconThemeName 2>&1
echo
echo "=== 6. autostart log ==="
tail -20 /tmp/autostart_setup.log 2>/dev/null || echo "  (no autostart log - image predates self-provisioning)"
