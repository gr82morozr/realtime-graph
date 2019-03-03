import os,sys,time
import argparse
import moderngl
import numpy as np
from objloader import Obj
from PIL import Image
from pyrr import Matrix44
from typing import Any, Tuple,List
from pathlib import Path
from importlib import import_module

OPTIONS_TRUE = ['yes', 'on', 'true', 't', 'y', '1']
OPTIONS_FALSE = ['no', 'off', 'false', 'f', 'n', '0']
OPTIONS_ALL = OPTIONS_TRUE + OPTIONS_FALSE

class BaseWindow:
    """
    Helper base class for a generic window implementation
    """
    keys = None  # type: BaseKeys

    def __init__(self, title="Example", gl_version=(3, 3), size=(1280, 720), resizable=True,
                 fullscreen=False, vsync=True, aspect_ratio=16/9, samples=4, cursor=True, **kwargs):
        """
        Args:
            title (str): The window title
            gl_version (tuple): Major and minor version of the opengl context to create
            size (tuple): Window size x, y
            resizable (bool): Should the window be resizable?
            fullscreen (bool): Open window in fullsceeen mode
            vsync (bool): Enable/disable vsync
            aspect_ratio (float): The desired aspect ratio. Can be set to None.
            samples (int): Number of MSAA samples for the default framebuffer
            cursor (bool): Enable/disable displaying the cursor inside the window
        """
        self.title = title
        self.gl_version = gl_version
        self.width, self.height = size
        self.resizable = resizable
        self.buffer_width, self.buffer_height = size
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.aspect_ratio = aspect_ratio
        self.samples = samples
        self.cursor = cursor

        self.ctx = None  # type: moderngl.Context
        self.example = None  # type: Example
        self.frames = 0  # Frame counter
        self._close = False

        if not self.keys:
            raise ValueError("Window {} class missing keys".format(self.__class__))

    @property
    def size(self) -> Tuple[int, int]:
        """
        Returns: (width, height) tuple with the current window size
        """
        return self.width, self.height

    @property
    def buffer_size(self) -> Tuple[int, int]:
        """
        Returns: (with, heigh) tuple with the current window buffer size
        """
        return self.buffer_width, self.buffer_height

    @property
    def is_closing(self) -> bool:
        """
        Returns: (bool) Is the window about to close?
        """
        return self._close

    def close(self):
        """
        Signal for the window to close
        """
        self._close = True

    def render(self, time: float, frame_time: float):
        """
        Renders the assigned example

        Args:
            time (float): Current time in seconds
            frame_time (float): Delta time from last frame in seconds
        """
        self.example.render(time, frame_time)

    def swap_buffers(self):
        """
        A library specific buffer swap method is required
        """
        raise NotImplementedError()

    def resize(self, width, height):
        """
        Should be called every time window is resized
        so the example can adapt to the new size if needed
        """
        if self.example:
            self.example.resize(width, height)

    def destroy(self):
        """
        A library specific destroy method is required
        """
        raise NotImplementedError()

    def set_default_viewport(self):
        """
        Calculates the viewport based on the configured aspect ratio.
        Will add black borders and center the viewport if the window
        do not match the configured viewport.

        If aspect ratio is None the viewport will be scaled
        to the entire window size regardless of size.
        """
        if self.aspect_ratio:
            expected_width = int(self.buffer_height * self.aspect_ratio)
            expected_height = int(expected_width / self.aspect_ratio)

            if expected_width > self.buffer_width:
                expected_width = self.buffer_width
                expected_height =  int(expected_width / self.aspect_ratio)

            blank_space_x = self.buffer_width - expected_width
            blank_space_y = self.buffer_height - expected_height

            self.ctx.viewport = (
                blank_space_x // 2,
                blank_space_y // 2,
                expected_width,
                expected_height,
            )
        else:
            self.ctx.viewport = (0, 0, self.buffer_width, self.buffer_height)

    @property
    def gl_version_code(self) -> int:
        """
        Generates the version code integer for the selected OpenGL version.
        Example: gl_version (4, 1) returns 410
        """
        return self.gl_version[0] * 100 +  self.gl_version[1] * 10

    def print_context_info(self):
        """
        Prints moderngl context info.
        """
        print("Context Version:")
        print('ModernGL:', moderngl.__version__)
        print('vendor:', self.ctx.info['GL_VENDOR'])
        print('renderer:', self.ctx.info['GL_RENDERER'])
        print('version:', self.ctx.info['GL_VERSION'])
        print('python:', sys.version)
        print('platform:', sys.platform)
        print('code:', self.ctx.version_code)



class Example:
    """
    Base class for making an example.
    Examples can be rendered by any supported window library and platform.
    """
    window_size = (1280, 720)
    resizable = True
    gl_version = (3, 3)
    title = "Example"
    aspect_ratio = 16 / 9

    def __init__(self, ctx=None, wnd=None, **kwargs):
        self.ctx = ctx
        self.wnd = wnd

    def render(self, time: float, frame_time: float):
        """
        Renders the assigned effect

        Args:
            time (float): Current time in seconds
            frame_time (float): Delta time from last frame in seconds
        """
        raise NotImplementedError("Example:render not implemented")

    def resize(self, width: int, height: int):
        """
        Called every time the window is resized
        in case the example needs to do internal adjustments.

        Width and height are reported in buffer size (not window size)
        """
        pass

    def key_event(self, key: Any, action: Any):
        """
        Called for every key press and release

        Args:
            key (int): The key that was press. Compare with self.wnd.keys.
            action: self.wnd.keys.ACTION_PRESS or ACTION_RELEASE
        """
        pass

    def mouse_position_event(self, x: int, y: int):
        """
        Reports the current mouse cursor position in the window

        Args:
            x (int): X postion of the mouse cursor
            y Iint): Y position of the mouse cursor
        """
        pass

    def mouse_press_event(self, x: int, y: int, button: int):
        """
        Called when a mouse button in pressed

        Args:
            x (int): X position the press occured
            y (int): Y position the press occured
            button (int): 1 = Left button, 2 = right button
        """
        pass

    def mouse_release_event(self, x: int, y: int, button: int):
        """
        Called when a mouse button in released

        Args:
            x (int): X position the release occured
            y (int): Y position the release occured
            button (int): 1 = Left button, 2 = right button
        """
        pass
























class CrateExample(Example):
    title = "Crate"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform mat4 Mvp;

                in vec3 in_vert;
                in vec3 in_norm;
                in vec2 in_text;

                out vec3 v_vert;
                out vec3 v_norm;
                out vec2 v_text;

                void main() {
                    gl_Position = Mvp * vec4(in_vert, 1.0);
                    v_vert = in_vert;
                    v_norm = in_norm;
                    v_text = in_text;
                }
            ''',
            fragment_shader='''
                #version 330

                uniform vec3 Light;
                uniform sampler2D Texture;

                in vec3 v_vert;
                in vec3 v_norm;
                in vec2 v_text;

                out vec4 f_color;

                void main() {
                    float lum = clamp(dot(normalize(Light - v_vert), normalize(v_norm)), 0.0, 1.0) * 0.8 + 0.2;
                    f_color = vec4(texture(Texture, v_text).rgb * lum, 1.0);
                }
            ''',
        ) 

        self.mvp = self.prog['Mvp']
        self.light = self.prog['Light']

        obj = Obj.open('E:/Projects/github/realtime_graph/build_3/examples/data/shuttle10.obj')
        img = Image.open('E:/Projects/github/realtime_graph/build_3/examples/data/shuttle.png').transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        self.texture = self.ctx.texture(img.size, 3, img.tobytes())
        self.texture.use()

        self.vbo = self.ctx.buffer(obj.pack('vx vy vz nx ny nz tx ty'))
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert', 'in_norm', 'in_text')

    def render(self, time, frame_time):
        angle = time/10
        self.ctx.clear(1.0, 1.0, 1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)

        camera_pos = (np.cos(angle) * 5.0, np.sin(angle) * 5.0, 2.0)

        proj = Matrix44.perspective_projection(45.0, self.aspect_ratio, 0.1, 100.0)
        lookat = Matrix44.look_at(
            camera_pos,
            (1.0, 0.0, 1.0),
            (1.0, 0.0, 1.0),
        )

        self.mvp.write((proj * lookat).astype('f4').tobytes())
        self.light.value = camera_pos
        self.vao.render()




def run_example(example_cls: Example, args=None):
    """
    Run an example entering a blocking main loop

    Args:
        example_cls: The exmaple class to render
        args: Override sys.args
    """
    values = parse_args(args)
    window_cls = get_window_cls(values.window)

    window = window_cls(
        title=example_cls.title,
        size=example_cls.window_size,
        fullscreen=values.fullscreen,
        resizable=example_cls.resizable,
        gl_version=example_cls.gl_version,
        aspect_ratio=example_cls.aspect_ratio,
        vsync=values.vsync,
        samples=values.samples,
        cursor=values.cursor,
    )

    window.example = example_cls(ctx=window.ctx, wnd=window)

    start_time = time.time()
    current_time = start_time
    prev_time = start_time
    frame_time = 0

    while not window.is_closing:
        current_time, prev_time = time.time(), current_time
        frame_time = max(current_time - prev_time, 1 / 1000)

        window.render(current_time - start_time, frame_time)
        window.swap_buffers()

    duration = time.time() - start_time
    window.destroy()
    print("Duration: {0:.2f}s @ {1:.2f} FPS".format(duration, window.frames / duration))

def get_window_cls(window: str) -> BaseWindow:
    """
    Attept to obtain the configured window class
    """
    return import_string('window.{}.window.Window'.format(window))



def parse_args(args=None):
    """Parse arguments from sys.argv"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-w', '--window',
        default="pyqt5",
        choices=find_window_classes(),
        help='Name for the window type to use',
    )
    parser.add_argument(
        '-fs', '--fullscreen',
        action="store_true",
        help='Open the window in fullscreen mode',
    )
    parser.add_argument(
        '-vs', '--vsync',
        type=str2bool,
        default="1",
        help="Enable or disable vsync",
    )
    parser.add_argument(
        '-s', '--samples',
        type=int,
        default=4,
        help="Specify the desired number of samples to use for multisampling",
    )
    parser.add_argument(
        '-c', '--cursor',
        type=str2bool,
        default="true",
        help="Enable or disable displaying the mouse cursor",
    )

    return parser.parse_args(args or sys.argv[1:])


def find_window_classes() -> List[str]:
    """
    Find available window packages

    Returns:
        A list of avaialble window packages
    """
    return [
        path.parts[-1] for path in Path(__file__).parent.iterdir()
        if path.is_dir() and not path.parts[-1].startswith('__')
    ]

def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    
    Args:
        dotted_path: The path to attempt importing

    Returns:
        Imported class/attribute
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)) from err


def str2bool(value):
    value = value.lower()

    if value in OPTIONS_TRUE:
        return True

    if value in OPTIONS_FALSE:
        return False

    raise argparse.ArgumentTypeError('Boolean value expected. Options: {}'.format(OPTIONS_ALL))

if __name__ == '__main__':
    run_example(CrateExample)