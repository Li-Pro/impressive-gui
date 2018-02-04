#!/bin/bash
#
# Turns a Raspberry Pi into a simple digital signage system that shows one or
# more PDF, image or video files from the SD card on booting, with no user
# interaction.
#
# Features:
# - starts early in the boot phase (before systemd, actually)
# - still possible to cancel autostart and boot normally;
#   normal boot also happens when Impressive exits for any reason
# - no unneccessary stuff running in the background, not even network
# - all filesystems are still mounted read-only, i.e. it's perfectly safe
#   to just turn the power off without risk of filesystem corruption
#
# Usage:
# - install Impressive, either using the package manager (apt install
#   impressive) or from the official website; make sure it's placed in a
#   standard location, e.g. /usr/(local/)bin/impressive; note that at least
#   version 0.11.3 is required
# - install mupdf-tools (normally there's a choice which PDF renderer to use;
#   not this time!)
# - copy this script somewhere and make it executable, e.g.
#       install -m 755 boot_impressive.sh /usr/local/sbin/boot_impressive
# - add the following parameter to /boot/cmdline.txt:
#       init=/usr/local/sbin/boot_impressive
# - make sure that the option "disable_overscan=1" is present and active in
#   /boot/config.txt, and that there's no line that reads like 
#   "dtoverlay=vc4-(f)kms-v3d"
# - create a directory "slides" on the FAT partition of the SD card
#   (i.e. /boot/slides from the RasPi's point of view)
# - put one or more .pdf, image or video files in that directory
# - (optional) create a file "options.txt" in that directory that contains
#   additional command-line options for Impressive, e.g. "-a 30" to change
#   slides every 30s instead of every 10s
# That's it. After rebooting, the slideshow should start automatically.

function normal_boot {
	echo " -- OK, booting normally."
	exec /sbin/init
}
trap normal_boot INT
echo "Running Impressive in 5 seconds, press ^C to cancel and boot normally."
sleep 1
echo "Running Impressive in 4 seconds, press ^C to cancel and boot normally."
sleep 1
echo "Running Impressive in 3 seconds, press ^C to cancel and boot normally."
sleep 1
echo "Running Impressive in 2 seconds, press ^C to cancel and boot normally."
sleep 1
echo "Running Impressive in 1 second, press ^C to cancel and boot normally."
sleep 1
trap - INT

clear

echo "Mounting filesystems for presentation ..."
mount -t sysfs none /sys
mount -t proc none /proc
mount -o ro /boot

echo "Running Impressive with configured parameters ..."
opts="--bare --no-overview --no-cursor -cz -a 10 -w $(grep -v '^#' /boot/options.txt 2>/dev/null | tr '\n' ' ')"
( cd /boot/slides ; set -x ; impressive $opts * )

echo
echo "Impressive quit, resuming normal boot in 5 seconds."
sleep 5

echo "Unmounting filesystems first ..."
umount /boot

echo "Now continuing with normal init ..."
exec /sbin/init
