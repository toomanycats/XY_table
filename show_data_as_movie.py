#!/usr/bin/python

import code_tools

def main(path, type, Sleep):
    '''No config is needed.  '''
    arraytools = code_tools.ArrayTools()
    plottools = code_tools.PlotTools()
    
    data = arraytools.load_mat(path)
    
    plottools.plot_movie(data,type,Sleep)    

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
