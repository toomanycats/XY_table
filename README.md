# XY Table
This Python repository  is for controlling an experiment using an XY table
powered by two MDrive23 stepper motors, and an HP8510C vector network analyzer.
All control is done with Ubuntu 10.04. I use the linux-gpib module found on
sourceforge and pySerial for the motor control, also found on sourceforge.com

The kernel version appears to make a difference. Kernel 2.6.xx works, but
upgrading to 3.x caused a failure.

I use a National Instruments GPIB PCI interface card.

There's a thread on ubuntuforums.org that I started when getting this setup for
the first time and the install instructions for the linux-gpib module are
there.

# Moving Table Hardware
The moving table was produced in house at SFSU by Peter Verdone.

<table class="image">
<caption align="bottom">XY Table without ceiling plane.</caption>
<tr><td><img src="https://github.com/toomanycats/XY_table/blob/master/experiment_pics/CAM00236.jpg", width=200/></td></tr>
</table>

<table class="image">
<caption align="bottom">XY Table with ceiling plane installed.</caption>
<tr><td><img src="https://github.com/toomanycats/XY_table/blob/master/experiment_pics/CAM00241.jpg", width=200/></td></tr>
</table>

Each stepper motor has two end of travel switches to prevent damage to the rig and
to programatically define the available travel for the crystal carrier.
<table class="image">
<caption align="bottom">End of travel sensors.</caption>
<tr><td><img src="https://github.com/toomanycats/XY_table/blob/master/experiment_pics/CAM00237.jpg", width=200/></td></tr>
</table>

<table class="image">
<caption align="bottom">HP8510C Vector Network Analyzer. Old unit had some boards repaired.</caption>
<tr><td><img src="https://github.com/toomanycats/XY_table/blob/master/experiment_pics/CAM00245.jpg", width=200/></td></tr>
</table>

<table class="image">
<caption align="bottom">Early crystal designed with dielectric rods and spacers.</caption>
<tr><td><img src="https://github.com/toomanycats/XY_table/blob/master/experiment_pics/CAM00246.jpg", width=200/></td></tr>
</table>

Cheers,
dpc


