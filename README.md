This Python repository  is for controlling an experiment using an XY table powered by two MDrive23 stepper motors,
and an HP8510C vector network analyzer. All control is done with Ubuntu 10.04. I use the linux-gpib module
found on sourceforge and pySerial for the motor control, also found on sourceforge.com

The kernel version appears to make a difference. Kernel 2.6.xx works, but upgrading to 3.x caused a failure.

I use a National Instruments GPIB PCI interface card.

There's a thread on ubuntuforums.org that I started when getting this setup for the first time and
the install instructions for the linux-gpib module are there.

# Hardware
![XY Table Being Built](https://github.com/toomanycats/XY_table/master/experiment_pics/cam00236.jpg)

Each stepper motor has two end of travel switches to prevent damage to the rig and
to programatically define the available travel for the crystal carrier.
![alt text](https://github.com/toomanycats/XY_table/tree/master/experiment_pics/cam00237.jpg)

![alt text](https://github.com/toomanycats/XY_table/tree/master/experiment_pics/cam00242.jpg)


Cheers,
dpc


