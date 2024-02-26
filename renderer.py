from dataset import VolumeDataset
from transfunc import TransFunc
from raycaster import VolumeRaycaster
from PySide2.QtGui import QOpenGLContext, QOffscreenSurface, QSurfaceFormat
import OpenGL.GL as gl
import numpy as np

# for offscreen rendering, context switching 
class VolumeRenderer(VolumeRaycaster):
    def getGLVersionStr():
        rendererStr = gl.glGetString(gl.GL_RENDERER).decode()
        versionStr = gl.glGetString(gl.GL_VERSION).decode()
        return f'OpenGL renderer: {rendererStr}, version: {versionStr}'

    def __init__(self, dataset : VolumeDataset, 
                 transFunc : TransFunc, alphaTransFunc : TransFunc,
                 w : int, h : int):
        super().__init__(dataset, transFunc, alphaTransFunc)
        self.fbo = 0
        self.renderTex = 0
        self.depthTex = 0
        self.w = w
        self.h = h
        self.surfaceFormat = QSurfaceFormat()
        self.surfaceFormat.setVersion(4.4, 3.0)
        self.openglContext = QOpenGLContext()
        self.openglContext.setFormat(self.surfaceFormat)
        self.openglContext.create()
        if not self.openglContext.isValid():
            print('Error: Could not create opengl context.')
        self.renderSurface = QOffscreenSurface()
        self.renderSurface.setFormat(self.surfaceFormat)
        self.renderSurface.create()
        if not self.renderSurface.isValid():
            print('Error: Could not create offscreen render surface.')
        self.openglContext.makeCurrent(self.renderSurface)

        #print(VolumeRenderer.getGLVersionStr())

        super().initialize()

        # setup FBO and render / depth textures
        self.renderTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderTex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self.depthTex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.depthTex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self.fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, 
                                  gl.GL_TEXTURE_2D, self.renderTex, 0)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, 
                                  gl.GL_TEXTURE_2D, self.depthTex, 0)

        self.resize(self.w, self.h)

    def resize(self, w, h):
        #self.w = w
        #self.h = h
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderTex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.w, self.h, 
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.depthTex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT16, self.w, self.h, 
                        0, gl.GL_DEPTH_COMPONENT, gl.GL_UNSIGNED_SHORT, None)
        
        super().resize(self.w, self.h)
        
    def getPixels(self):
        '''
        retrieve pixels from framebuffer-bound texture
        
        '''
        # TODO this is probably an expensive operation, should use a pixel buffer in the future
        # TODO consider using glGetTextureSubImage (opengl 4.5 only!)
        
        #gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderTex)
        #return gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)

        return gl.glReadPixels(0, 0, self.w, self.h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)


    
