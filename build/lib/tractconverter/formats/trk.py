# -*- coding: UTF-8 -*-

#Documentation available here:
#http://www.trackvis.org/docs/?subsect=fileformat

import os
import numpy as np

from tractconverter.formats.header import Header


def readBinaryBytes(f, nbBytes, dtype):
    buff = f.read(nbBytes * dtype.itemsize)
    return np.frombuffer(buff, dtype=dtype)

class TRK:
    MAGIC_NUMBER = "TRACK"
    OFFSET = 1000
    #self.hdr
    #self.filename
    #self.endian
    #self.FIBER_DELIMITER
    #self.END_DELIMITER
    
    #####
    #Static Methods
    ###
    @staticmethod
    def create(filename, hdr, anatFile=None):
        f = open(filename, 'wb')
        f.write(TRK.MAGIC_NUMBER + "\n")
        f.close()
        
        trk = TRK(filename, load=False)
        trk.hdr = hdr
        trk.writeHeader();

        return trk

    #####
    #Methods
    ###
    def __init__(self, filename, anatFile=None, load=True):
        self.filename = filename
        if not self._check():
            raise NameError("Not a TRK file.")
        
        self.hdr = {}
        if load:
            self._load()
    
    def _check(self):
        f = open(self.filename, 'rb')
        magicNumber = f.read(5)
        f.close()
        return magicNumber == self.MAGIC_NUMBER
    

    def _load(self):
        f = open(self.filename, 'rb')
        
        #####
        #Read header
        ###
        ## Read number of scalars appended to each point of a tract.
        f.seek(36)  # Skip to n_scalars

        buffer = f.read(2)
        nb_scalars = np.frombuffer(buffer, dtype='<i2')
        
        self.hdr[Header.NB_SCALARS_BY_POINT] = nb_scalars[0]
        
        ## Read number of properties by tract.
        f.seek(200, os.SEEK_CUR)
        
        buffer = f.read(2)
        nb_properties = np.frombuffer(buffer, dtype='<i2')
        
        self.hdr[Header.NB_PROPERTIES_BY_TRACT] = nb_properties[0]
        
        ## Go to n_count, to get the remaining data        
        f.seek(self.OFFSET-4-4-4)
        
        buffer = f.read(4+4+4)
        infos = np.frombuffer(buffer, dtype='<i4')
        
        #Check if little or big endian
        self.endian = '<'
        if infos[2] != 1000:
            infos = np.frombuffer(buffer, dtype='>i4')
            self.endian = '>'
        
        self.hdr[Header.NB_FIBERS] = infos[0]
        if self.hdr[Header.NB_FIBERS] == 0:
            #NbFibers not provided, let's count manually...

            remainingBytes = os.path.getsize(self.filename) - self.OFFSET
            while remainingBytes > 0:
                #Read points
                nbPoints = readBinaryBytes(f, 1, np.dtype(self.endian + "i4"))[0]
                # This seek is used to go to the next points number indication in the file.
                f.seek((nbPoints * (3 + self.hdr[Header.NB_SCALARS_BY_POINT]) + self.hdr[Header.NB_PROPERTIES_BY_TRACT]) * 4, 1) #Relative seek
                remainingBytes -= (nbPoints * (3 + self.hdr[Header.NB_SCALARS_BY_POINT]) + self.hdr[Header.NB_PROPERTIES_BY_TRACT]) * 4 + 4
                self.hdr[Header.NB_FIBERS] += 1
        
        f.close()
            
    def writeHeader(self):
        f = open(self.filename, 'wb')
        f.write(self.MAGIC_NUMBER + " ")
        f.write(np.zeros(self.OFFSET-4-4-4-6, dtype='i1'))
        f.write(np.array([self.hdr[Header.NB_FIBERS], 2, self.OFFSET], dtype='<i4'))
        f.close()
        
    def close(self):
        pass

    def __iadd__(self, fibers):
        f = open(self.filename, 'ab')
        for fib in fibers:
            f.write(np.array([len(fib)], '<i4').tostring())
            f.write(fib.tostring())
        f.close()
        
        return self
        
            
    #####
    #Iterate through fibers
    ###
    def __iter__(self):
        f = open(self.filename, 'rb')
        f.seek(self.OFFSET)
        
        remainingBytes = os.path.getsize(self.filename) - self.OFFSET

        cpt = 0
        while cpt < self.hdr[Header.NB_FIBERS] or remainingBytes > 0:
            #Read points
            nbPoints = readBinaryBytes(f, 1, np.dtype(self.endian + "i4"))[0]
            ptsAndScalars = readBinaryBytes(f, nbPoints * (3 + self.hdr[Header.NB_SCALARS_BY_POINT]), np.dtype(self.endian + "f4"))
            
            newShape = [-1, 3 + self.hdr[Header.NB_SCALARS_BY_POINT]]
            ptsAndScalars = ptsAndScalars.reshape(newShape)

            pointsWithoutScalars = ptsAndScalars[:, 0:3]
            yield pointsWithoutScalars
            
            # For now, we do not process the tract properties, so just skip over them.
            remainingBytes -= nbPoints * (3 + self.hdr[Header.NB_SCALARS_BY_POINT]) * 4 + 4
            remainingBytes -= self.hdr[Header.NB_PROPERTIES_BY_TRACT] * 4
            cpt += 1
            
        f.close()