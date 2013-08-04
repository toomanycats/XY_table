#!/usr/bin/python

import numpy as np
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
import scipy.io as sio
from time import sleep

def main(path, type, Sleep):

    data = sio.loadmat(path)
    data = data['Out_Data']
    freq = data[0]
    comp = data[1]
    inten = data[2]
    phase = data[3]

    if type == 'real':
        pdata = comp.real
        vmin = pdata.min(0).mean()/pdata.min(0).std()
        vmax = pdata.max(0).mean()/pdata.max(0).std()
    elif type == 'inten':
        pdata = inten
        vmin = 0
        vmax = pdata.max(0).mean()/pdata.max(0).std()
    elif type == 'mag':
        pdata = np.sqrt(inten)
        vmin = 0
        vmax = pdata.max(0).mean()/pdata.max(0).std() 
    elif type == 'phase':
        pdata = phase
        vmin = pdata.min()
        vmax = pdata.max() 

    plt.ion()
    plt.figure()

    

    plt.imshow(pdata[0,:,:],cmap='jet',interpolation='nearest',vmin=vmin,vmax=vmax,origin='lower')
    plt.title('Type:  %s  Freq: %e' %(type,freq[0]) )
    plt.colorbar()

    sleep(Sleep)

    for i in xrange(1,pdata.shape[0]):
        plt.imshow(pdata[i,:,:],cmap='jet',interpolation='nearest',vmin=vmin,vmax=vmax,origin='lower')
        plt.title('Type:  %s  Freq: %e' %(type,freq[i]) )
        plt.draw()
        sleep(Sleep)

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="path",
                  help="path to .mat file")
    parser.add_option("-t", "--type", dest="type", default='real',
                  help="types are: real, inten, phase, mag")

    parser.add_option("-s","--sleep",dest="Sleep", type="float", default=0.3,
                  help="number or fraction of seconds to pause between frames")

    (options, args) = parser.parse_args()
    
    main(options.path,options.type,options.Sleep)
