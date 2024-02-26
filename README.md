This is a standalone application illustrating an early version of volume rendering component of the VolEvol prototype.

Dependencies / requirements:

- Python interpreter v3.8 or above (may work with earlier versions)
- support for OpenGL 4.0 and Shader Model 4.0 (most dedicated/integrated GPUS within the last 5-6 years should support this)   
- the Qt library v5.x or above (used for the user interface and the OpenGL context), obtainable from https://download.qt.io/archive/qt/
- the following Python libraries:
   - numpy	
   - matplotlib
   - PySide2 
   - PyOpenGL
   - pyglm

Usage:

The user interface consists of the following two elements:

1) A rendering widget where the representation of the volume dataset is dynamically displayed. The user may interact with the widget using the mouse and keyboard as follows:

- left-click drag = rotate the volume
- right-click drag = zoom in-out
- Ctrl + left-click drag = pan the volume left/right/up/down

2) A transfer function editor. The transfer function is a piecewise spline defined by at least two control points. The editor can be used to change the shape of the transfer function by moving / inserting / removing the control points, thus controlling the distribution of color and opacity throughout the volume:

- left-click drag control point = move control point
- right-click on control point = change control point color
- Ctrl + left-click on control point = remove control point
- Ctrl + left-click on empty space = add control point with default color
- Ctrl + Shift + left-click on empty space = add control point by first specifying its color


