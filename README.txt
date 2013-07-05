This Python module is for controlling an HP8510C vector network analyzer with a Debian system.
I'm currently using it with Ubuntu 10.04 and the kernel version appears to make a difference.
Kernel 2.6.xx works, but upgrading to 3.x caused a failure. 

I use a National Instruments GPIB interface card and the linux-gpib libary from sourceforge.org.

There's a thread on ubuntuforums.org that I started when getting this setup for the first time and
the install instructions for the linux-gpib module are there. 

The module I'm providing, vna_tools.py, contains onw class object with methods for controlling the VNA.

It's not a stand alone module for general yet...but I'd like it to become that. For now, it's a somewhat
generalized set of tools that fits the lab's needs.

It should certainly serve as a good jumping off point for anyone learning gpib and python for the first time.

Cheers,
dpc


