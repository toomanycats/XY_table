#!/usr/bin/python

import code_tools
import copy
import numpy as np
import matplotlib.pyplot as plt
plt.ion()
thresh = 1

config = code_tools.ConfigureDataSet()
config.load_config('/home/daniel/Downloads/test.cfg')

arraytools = code_tools.ArrayTools(config)
plottools = code_tools.PlotTools(config)

data = arraytools.load_mat('/home/daniel/Downloads/test.mat')
real, v_min, v_max = plottools.get_data_type_scale(data,'real')

my_cmap = copy.copy(plt.cm.get_cmap('gray')) # get a copy of the gray color map
my_cmap.set_bad(alpha=0) # set how the colormap handles 'bad' values

lattice = plt.imread('path')
im = plt.imshow(data[0,:,:],vmin=v_min,vmax=v_max,extent=(0,32,0,32),interpolation='nearest',cmap='jet')

lattice[lattice < thresh] = np.nan # insert 'bad' values into your lattice (the white)

im2 = plt.imshow(lattice,extent=(0,32,0,32),cmap=my_cmap)
plt.show()

