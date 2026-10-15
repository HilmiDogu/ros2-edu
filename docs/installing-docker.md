# Installing Docker

You need Docker and nothing else — no ROS, no Linux install, no Python.
Everything the course uses lives inside the container.

Do this once, before the first session. It takes 15–30 minutes including
a large download, so **please do not leave it until the lab starts**:
thirty people downloading several GB on lecture-hall wifi does not work.

Jump to your system:

- [Windows](#windows)
- [Linux — Ubuntu and Debian](#linux--ubuntu-and-debian)
- [macOS](#macos)
- [Checking it worked](#checking-it-worked)
- [Common install problems](#common-install-problems)

---

## Windows

### What you need

- Windows 10 (version 2004 or later) or Windows 11
- **16 GB RAM recommended**, 8 GB workable but slow
- ~20 GB free disk
- Virtualisation enabled in the BIOS (usually on by default)

### 1. Install WSL 2

Docker on Windows runs Linux inside a lightweight virtual machine called
WSL 2. Open **PowerShell as Administrator** (right-click Start →
*Terminal (Admin)*) and run:

```powershell
wsl --install
```

Reboot when it asks. If it says WSL is already installed, update it:

```powershell
wsl --update
```

> If `wsl --install` fails with a virtualisation error, virtualisation is
> switched off in your BIOS/UEFI. Reboot, enter BIOS setup (usually F2,
> F10 or Del during startup) and enable **Intel VT-x** or **AMD-V**.

### 2. Limit how much memory WSL may take

**Do not skip this.** By default WSL 2 may claim up to half your RAM and
never give it back, which makes the simulation freeze mid-run. Create
the file `C:\Users\<your-name>\.wslconfig` — the project ships one ready
to copy:

```powershell
copy docker\wslconfig-example.ini $env:USERPROFILE\.wslconfig
wsl --shutdown
```

(If you have not cloned the project yet, come back and do this
afterwards — it only takes a moment.)

### 3. Install Docker Desktop

Download and run the installer from
<https://www.docker.com/products/docker-desktop/>.

During setup, leave **"Use WSL 2 instead of Hyper-V"** ticked.

After installing, **start Docker Desktop** and wait for the whale icon in
the system tray to stop animating. Docker is only usable once it has
finished starting, and it does not start automatically after install.

### 4. Give Docker enough resources

Docker Desktop → **Settings** (gear icon) → **Resources**:

- **CPUs:** 6 or more if you have them
- **Memory:** 6–8 GB

Click **Apply & Restart**.

---

## Linux — Ubuntu and Debian

Do **not** install the `docker.io` package from the Ubuntu archive: it is
usually several versions behind and often lacks the Compose plugin this
project needs. Use Docker's own repository.

### 1. Remove any old versions

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

Nothing happens if they were not installed.

### 2. Add Docker's repository

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

> On **Debian**, replace both occurrences of `ubuntu` in the URLs with
> `debian`.

### 3. Install

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

### 4. Run Docker without sudo

Otherwise every command in this course needs `sudo`:

```bash
sudo usermod -aG docker $USER
```

**Log out and back in** for this to take effect — a new terminal is not
enough, the group membership is attached at login.

### Other distributions

- **Fedora / RHEL:** follow <https://docs.docker.com/engine/install/fedora/>
- **Arch:** `sudo pacman -S docker docker-compose`, then
  `sudo systemctl enable --now docker`

On any distro, the same `usermod -aG docker $USER` step applies.

---

## macOS

Download Docker Desktop from
<https://www.docker.com/products/docker-desktop/> — take the **Apple
Silicon** build for M1/M2/M3/M4 Macs, or **Intel** for older ones.

Install it, start it, and wait for the whale icon in the menu bar to
settle. Then give it room: **Settings → Resources**, 6+ CPUs and 6–8 GB
of memory.

> **Apple Silicon note.** The course image is built for x86_64 and runs
> under emulation on Apple Silicon, so the simulation is noticeably
> slower. It works, but Gazebo will not feel smooth. If you have the
> choice, use an Intel Mac, a Windows machine or Linux.

---

## Checking it worked

In a terminal — PowerShell on Windows, any terminal on Linux/macOS:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

You should see a version from each of the first two, and a short
"Hello from Docker!" message from the third.

Two things to note:

- `docker compose version` (a space, not a hyphen) is the modern plugin
  this project uses. If only `docker-compose` works, your Docker is too
  old — reinstall from the instructions above.
- If `hello-world` prints a permission error on Linux, you skipped the
  `usermod` step, or have not logged out and back in since.

Once all three work, go back to the [README](../README.md) and start the
workspace.

---

## Common install problems

### Windows: "Docker Desktop requires a newer WSL kernel version"

```powershell
wsl --update
```

Then restart Docker Desktop.

### Windows: "Hardware assisted virtualization is not enabled"

Virtualisation is off in your BIOS/UEFI. Reboot, enter BIOS setup
(usually F2, F10 or Del), and enable **Intel VT-x** or **AMD-V**. The
setting is often under *Advanced*, *CPU Configuration* or *Security*.

### Windows: "cannot be loaded because running scripts is disabled"

PowerShell blocks local scripts by default, so `.\docker\up.ps1` is
refused. Allow scripts for the current window only:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

`-Scope Process` applies to that one PowerShell window and is forgotten
when you close it, so it changes nothing permanently on the machine.

### Windows: Docker commands hang or fail after sleep

Docker Desktop sometimes loses its connection after the machine sleeps.
Quit it from the tray icon and start it again. If that does not help:

```powershell
wsl --shutdown
```

then restart Docker Desktop.

### Linux: "permission denied ... Docker daemon socket"

You are not in the `docker` group, or have not logged out since being
added:

```bash
groups            # does this list 'docker'?
sudo usermod -aG docker $USER
```

Then log out and back in. To check without logging out:

```bash
newgrp docker
docker run --rm hello-world
```

### Linux: "Cannot connect to the Docker daemon"

The service is not running:

```bash
sudo systemctl start docker
sudo systemctl enable docker     # start it at boot too
```

### Any system: the download is extremely slow

The first build pulls roughly 4 GB. On a slow or shared connection this
can take a long time. Options, in order of preference:

1. Run it at home, or overnight, before the session.
2. Ask whoever is running the course for a pre-built image file: it can
   be handed out on a USB stick and loaded with `docker load`, which
   needs no download at all.

### Disk filling up

Docker keeps old images and build caches. To reclaim space:

```bash
docker system df       # what is using space
docker system prune    # remove unused data (safe)
```

`docker system prune -a` removes more, including images you are not
currently running — you would then have to download this project's image
again, so use it only if you are short on space.

---

## What gets installed where

Worth knowing, so none of this feels like magic:

| Lives on your machine | Lives inside the container |
|-----------------------|----------------------------|
| Docker itself | ROS 2 Jazzy |
| This git repository | Gazebo Harmonic |
| Your edits to `src/` | The Linux desktop you see in the browser |
| | The compiled workspace |

The project folder is *shared into* the container, so edits you make in
VS Code appear inside immediately, and nothing you write is lost when
the container stops. Removing the container does not touch your code.
