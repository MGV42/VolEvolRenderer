import numpy as np
import ctypes
import OpenGL.GL as gl
import OpenGL.GLU as glu
import glm
import zpr
from dataset import VolumeDataset
from shader import GLSLShader
from transfunc import TransFunc

class VolumeRaycaster:
    def __init__(self, dataset : VolumeDataset, transFunc : TransFunc):
        
        self.dataset = dataset
        self.transFunc = transFunc
        self.dataTex = 0
        self.transFuncDataSize = 1024
        self.transFuncData = self.transFunc.getData(self.transFuncDataSize)
        self.transFuncTex = 0
        self.alphaTransFuncTex = 0
        self.cubeVBO = 0
        self.cubeVAO = 0
        self.cubeSize = glm.vec3(1)
        self.volMin = glm.vec3(0)
        self.volMax = glm.vec3(1)
        self.modelMat = glm.mat4(1)
        self.viewMat = glm.mat4(1)
        self.projMat = glm.mat4(1)

        # noise for stochastic jittering
        self.noiseSize = glm.ivec2(32, 32)
        self.noiseTex = 0 
        
        # init viewer params
        self.viewerPos = glm.vec3(0.6, -1.0, 0) 
        self.lookAtPos = glm.vec3(0)
        self.viewerUpDir = glm.vec3(0, 0, 1)
        self.lightPos = glm.vec3(0.2, -0.9, 0)

        self.backColor = glm.vec3(1.0)

        self.interactSensitivity = 5.0

        self.texelType = {'B' : gl.GL_UNSIGNED_BYTE, 
                          'u2' : gl.GL_UNSIGNED_SHORT,
                          '<u2' : gl.GL_UNSIGNED_SHORT,
                          '>u2' : gl.GL_UNSIGNED_SHORT,
                          'f' : gl.GL_FLOAT,
                          '<f' : gl.GL_FLOAT,
                          '>f' : gl.GL_FLOAT}
        
        self.shader = GLSLShader('raycaster', 'raycaster.vert', 'raycaster.frag')

    def rebuildShader(self):
        self.shader.build()

    
    def setupDatasetTexture(self):
        gl.glDeleteTextures(1, self.dataTex)
        self.dataTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.dataTex)

        gl.glTexImage3D(gl.GL_TEXTURE_3D, 0, gl.GL_RED, 
                        self.dataset.sizeX, self.dataset.sizeY, self.dataset.sizeZ, 
                        0, gl.GL_RED, self.texelType[self.dataset.dataType], 
                        self.dataset.voxelData)

        gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_WRAP_R, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_3D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    def setupNoiseTexture(self):
        noise2D = np.random.randint(0, 256, 
                                    size = [self.noiseSize[0], self.noiseSize[1]], 
                                    dtype = np.uint8)

        gl.glDeleteTextures(1, self.noiseTex)
        self.noiseTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.noiseTex)
        
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RED, 
                        self.noiseSize[0], self.noiseSize[1], 
                        0, gl.GL_RED, gl.GL_UNSIGNED_BYTE, 
                        noise2D)
        
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    def setupProxyCube(self, sizeX, sizeY, sizeZ):
        LX = sizeX / 2
        LY = sizeY / 2
        LZ = sizeZ / 2
        tmin = 0
        tmax = 1.0

        cubeData = np.array([
            #front
            -LX, -LY, LZ, tmin, tmin, tmax, LX, -LY, LZ, tmax, tmin, tmax, LX, LY, LZ, tmax, tmax, tmax,
            -LX, -LY, LZ, tmin, tmin, tmax, LX, LY, LZ, tmax, tmax, tmax, -LX, LY, LZ, tmin, tmax, tmax,  
            #back
            LX, -LY, -LZ, tmax, tmin, tmin, -LX, -LY, -LZ, tmin, tmin, tmin, -LX, LY, -LZ, tmin, tmax, tmin,
            LX, -LY, -LZ, tmax, tmin, tmin, -LX, LY, -LZ, tmin, tmax, tmin, LX, LY, -LZ, tmax, tmax, tmin,
            #left
            -LX, -LY, LZ, tmin, tmin, tmax, -LX, LY, LZ, tmin, tmax, tmax, -LX, LY, -LZ, tmin, tmax, tmin,
            -LX, -LY, LZ, tmin, tmin, tmax, -LX, LY, -LZ, tmin, tmax, tmin, -LX, -LY, -LZ, tmin, tmin, tmin,
            #right
            LX, -LY, LZ, tmax, tmin, tmax, LX, -LY, -LZ, tmax, tmin, tmin, LX, LY, -LZ, tmax, tmax, tmin,
            LX, -LY, LZ, tmax, tmin, tmax, LX, LY, -LZ, tmax, tmax, tmin, LX, LY, LZ, tmax, tmax, tmax,
            #top
            LX, LY, LZ, tmax, tmax, tmax, -LX, LY, -LZ, tmin, tmax, tmin, -LX, LY, LZ, tmin, tmax, tmax, 
            LX, LY, LZ, tmax, tmax, tmax, LX, LY, -LZ, tmax, tmax, tmin, -LX, LY, -LZ, tmin, tmax, tmin,
            #bottom
            -LX, -LY, LZ, tmin, tmin, tmax, -LX, -LY, -LZ, tmin, tmin, tmin, LX, -LY, -LZ, tmax, tmin, tmin,
            -LX, -LY, LZ, tmin, tmin, tmax, LX, -LY, -LZ, tmax, tmin, tmin, LX, -LY, LZ, tmax, tmin, tmax
            ], dtype='float32')

        self.cubeVBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.cubeVBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, cubeData, gl.GL_STATIC_DRAW)
        self.cubeVAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.cubeVAO)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(0))
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        
    def worldToVolume(self, worldCoords):
        volToCube = zpr.scaleMat(self.cubeSize) * zpr.translateMat(glm.vec3(-0.5))
        volCoords = glm.inverse(self.modelMat * volToCube) * glm.vec4(worldCoords, 1.0)
        return volCoords.xyz

    def setupTransFuncTexture(self):
        gl.glDeleteTextures(1, self.transFuncTex)
        self.transFuncTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.transFuncTex)

        gl.glTexImage1D(gl.GL_TEXTURE_1D, 0, gl.GL_RGBA, self.transFuncDataSize, 
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.transFuncData)

        gl.glTexParameteri(gl.GL_TEXTURE_1D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    
    def setupShader(self):
        self.shader.use()

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.dataTex)
        self.shader.uniformInt('dataTex', 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.transFuncTex)
        self.shader.uniformInt('transFuncTex', 1)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.noiseTex)
        self.shader.uniformInt('noiseTex', 3)

        self.shader.uniformMat4('mvp', self.projMat * self.viewMat * self.modelMat)
        self.shader.uniformVec3('viewerPos', self.worldToVolume(self.viewerPos))
        self.shader.uniformVec3('lightPos', self.worldToVolume(self.lightPos))
        self.shader.uniformVec3('volMin', self.volMin)
        self.shader.uniformVec3('volMax', self.volMax)
        self.shader.uniformVec3('backColor', self.backColor)
        self.shader.uniformVec2('viewportSize', glm.ivec2(512, 512)) # TODO: update this to work with w, h
        self.shader.uniformIVec2('noiseSize', self.noiseSize)

    def initialize(self):
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.setupProxyCube(self.cubeSize.x, self.cubeSize.y, self.cubeSize.z)
        self.setupDatasetTexture()
        self.setupTransFuncTexture()
        self.setupNoiseTexture()
        self.shader.build()
        gl.glClearColor(self.backColor.r, self.backColor.g, self.backColor.b, 1.0)

    def render(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.setupShader()
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 36)

    def resize(self, w, h):
        gl.glViewport(0, 0, w, h)
        self.projMat = glm.perspective(45, w/h, 0.1, 100)
        self.viewMat = glm.lookAt(self.viewerPos, self.lookAtPos, self.viewerUpDir)

    def interactZoom(self, dy):
        self.modelMat *= zpr.zoom(dy, self.viewMat * self.modelMat, self.interactSensitivity)

    def interactPan(self, dx, dy):
        self.modelMat *= zpr.pan(dx, dy, self.viewMat * self.modelMat, self.interactSensitivity)

    def interactRotate(self, dx, dy):
        self.modelMat *= zpr.rotate(dx, dy, self.viewMat * self.modelMat, self.interactSensitivity)

    def updateTransFunc(self):
        self.transFuncData = self.transFunc.getData(self.transFuncDataSize)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.transFuncTex)
        gl.glTexImage1D(gl.GL_TEXTURE_1D, 0, gl.GL_RGBA, self.transFuncDataSize, 
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.transFuncData)

