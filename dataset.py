import os
import numpy as np

# for now, assume volume scaling is (1, 1, 1)

class VolumeDataset:
    def __init__(self, dataFile, 
                 sizeX, sizeY, sizeZ, 
                 bytesPerVoxel, 
                 bigEndian = True, 
                 normalizeToFloat = False, 
                 headerSkip = 0):
        
        # purpose of headerSkip: if a volume data file has a header, 
        # we can skip the first headerSkip bytes when reading voxel data
        
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.sizeZ = sizeZ
        noVoxels = self.sizeX * self.sizeY * self.sizeZ
        self.dataType = None
        
        if not os.path.exists(dataFile):
            print(f'Error: file not found: {dataFile}')
            return

        fileSize = os.path.getsize(dataFile)

        dataSize = noVoxels * bytesPerVoxel + headerSkip;

        if fileSize != dataSize:
            print(f'Error reading {dataFile} : file size {fileSize} does not match specified data size {dataSize}')

        endianChar = '>' if bigEndian else '<'

        if bytesPerVoxel == 1: 
            self.dataType = 'B' # unsigned byte
            endianChar = ''
        if bytesPerVoxel == 2: self.dataType = f'{endianChar}u2' # unsigned short
        if bytesPerVoxel == 4: self.dataType = f'{endianChar}f' # probably 32 bit float

        self.voxelData = np.fromfile(dataFile, dtype = self.dataType, offset = headerSkip)

        #self.voxelData[self.voxelData > 1.e+10] = 0.001
        #self.voxelData.tofile('datasets/QVAPORf28_1.bin')
        
        if normalizeToFloat:
            maxVoxel = np.max(self.voxelData)
            self.voxelData = self.voxelData.astype(np.float32)/maxVoxel
            self.dataType = f'{endianChar}f' # 32 bit float
            

        


