import glm
import numpy as np

class CP:
    def __init__(self, x : float, rgba : glm.vec4):
        self.x = x
        self.rgba = rgba

    def xa(self) -> glm.vec2:
        return glm.vec2(self.x, self.rgba.a)

    def __str__(self):
        return f'CP[{self.x}] : ({self.rgba.r}, {self.rgba.g}, {self.rgba.b}, {self.rgba.a}'

class TransFunc:

    defaultCPColor = glm.vec3(0.8)

    def controlPointsFromArray(self, cpArray):
        '''
        sets control points from an array containing formatted as:
       [x0, r0, g0, b0, a0, x1, r1, g1, b1, a1, ...]
        ''' 
        self.cp = [CP(x, glm.vec4(r, g, b, a)) 
                   for [x, r, g, b, a] in cpArray.reshape((-1, 5))] 

    def controlPointsToArray(self):
        cpArr = np.array([[p.x, p.rgba.r, p.rgba.g, p.rgba.b, p.rgba.a] for p in self.cp])
        return cpArr.reshape(-1)

    def __init__(self):
        #self.cp = [CP(0.1, glm.vec4(TransFunc.defaultCPColor, 0.02)), 
        #           CP(0.95, glm.vec4(TransFunc.defaultCPColor, 0.9))]
        #self.cp = [CP(0.2, glm.vec4(0.0, 0.8, 1.0, 0.05)), 
        #           CP(0.95, glm.vec4(1.0, 1.0, 0.0, 0.9))]
        self.cp = [CP(0.2, glm.vec4(0.9, 0.3, 0.0, 0.05)), 
                   CP(0.95, glm.vec4(0.7, 1.0, 1.0, 0.9))]
        self.interpolationFunc = TransFunc.smoothstep_1

    def __str__(self):
        tfStr=''
        for p in self.cp:
            tfStr += str(p) + '\n'
        return tfStr

    def findRightIdx(self, x):
        # find index of point to the right of coord x
        for i in range(len(self.cp)):
            if self.cp[i].x > x:
                return i
        return len(self.cp)-1

    def addCP(self, x : float, rgba : glm.vec4):
        # add new control point so that all control points are sorted by x
        rightIdx = self.findRightIdx(x)
        self.cp.insert(rightIdx, CP(x, rgba))
        return rightIdx

    def removeCP(self, cpIdx):
        # remove control point at index idx
        self.cp.pop(cpIdx)
    
    def comb(n, k):
        return np.factorial(n) / (np.factorial(k) * np.factorial(n-k))

    def linear_0(u):
        return u
    
    def smoothstep_1(u):
        return 3*u**2 - 2*u**3

    def smoothstep_2(u):
        return 6*u**5 - 15*u**4 + 10*u**3

    def smoothstep_3(u):
        return -20*u**7 + 70*u**6 - 84*u**5 + 35*u**4

    def smoothstep_n(u, n):
        return u**(n+1) * sum([TFSpline.comb(n+k, k) * TransFunc.comb(2*n+1, n-k) * (-u)**k for k in range(n+1)])

    def getData(self, n):
        # take n samples from the spline at equidistant intervals on x
        
        samples = []

        dx = 1/(n-1)
        x = [i*dx for i in range(n)] 

        for i in range(n):
            if x[i] < self.cp[0].x:
                yrgba = glm.vec4(self.cp[0].rgba.rgb, 0)                
            elif x[i] > self.cp[-1].x:
                yrgba = self.cp[-1].rgba
                
            else:    
                rIdx = self.findRightIdx(x[i]) # inefficient for a sequence of ordered equidistant points, should improve this
                p0 = self.cp[rIdx-1] # control point to the left of x
                p1 = self.cp[rIdx] # control point to the right of x
                u = (x[i] - p0.x) / (p1.x - p0.x)
                v = self.interpolationFunc(u)
                yrgba = p0.rgba + v * (p1.rgba - p0.rgba)

            #samples.append(CP(x[i], yrgba)) # this list is only for drawing even samples
            # for rendering based on transfer function only a list of rgba values is needed
            samples.extend([yrgba.r, yrgba.g, yrgba.b, yrgba.a])

        return (np.array(samples) * 255).astype(np.uint8)

    def getLinearSegmentLengths(self):
        # get linear length of each segment
        noCPs = len(self.cp)
        if noCPs <= 1: return [0]
        else:
            return [glm.length(self.cp[i].xa() - self.cp[i+1].xa()) for i in range(noCPs-1)]

    def samplesForDrawing(self, noSamples):
        # take samples suitable for drawing spline
        # noSamples is the number of samples for the entire spline
        # samples are distributed across segments according to their length

        cpLengths = self.getLinearSegmentLengths()
        totalLength = sum(cpLengths)
        cpLengths = [cpl / totalLength for cpl in cpLengths] # normalization

        samplesPerSegment = [round(noSamples * cpl) for cpl in cpLengths]
        samplesPerSegment[-1] += noSamples - sum(samplesPerSegment)
        
        samples = []

        if self.cp[0].x > 0:
            samples.extend([CP(0, glm.vec4(self.cp[0].rgba.rgb, 0)), 
                            CP(self.cp[0].x, glm.vec4(self.cp[0].rgba.rgb, 0))])

        for i in range(len(self.cp)-1):
            p0 = self.cp[i]
            p1 = self.cp[i+1]
            
            samples.append(p0)
            
            if samplesPerSegment[i] > 0:
                du = 1/samplesPerSegment[i]
                uVals = [j*du for j in range(1, samplesPerSegment[i])]
                vVals = [self.interpolationFunc(u) for u in uVals]

                uVals = [p0.x + u*(p1.x - p0.x) for u in uVals]
                vVals = [p0.rgba + v*(p1.rgba - p0.rgba) for v in vVals]

                samplesBetweenCPs = [CP(u, v) for u, v in zip(uVals, vVals)] 
                samples.extend(samplesBetweenCPs)

        samples.append(self.cp[-1])

        if self.cp[-1].x < 1:
            samples.append(CP(1, self.cp[-1].rgba))

        return samples

