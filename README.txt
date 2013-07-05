This Python repository  is for controlling an experiment using an XY table powered by two MDrive23 stepper motors, 
and an HP8510C vector network analyzer. All control is done with Ubuntu 10.04. I use the linux-gpib module
found on sourceforge and pySerial for the motor control, also found on sourceforge.com

The kernel version appears to make a difference. Kernel 2.6.xx works, but upgrading to 3.x caused a failure. 
I'll eventually get around to documenting these details more thoroughly. 

I use a National Instruments GPIB PCI interface card.

There's a thread on ubuntuforums.org that I started when getting this setup for the first time and
the install instructions for the linux-gpib module are there. 


Cheers,
dpc


