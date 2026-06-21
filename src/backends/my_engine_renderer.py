# backends/my_engine_renderer.py
from systems.renderer_interface import IRenderer, TextureHandle

class MyEngineRenderer(IRenderer):
    def load_texture(self, path: str) -> TextureHandle:
        pass
        #handle = my_engine.load_image(path)
        #return TextureHandle(id=path, width=handle.w, height=handle.h)

    def draw_texture(self, handle, src, dst, flip_x, color_mod, alpha):
        pass
        #my_engine.blit(handle.id, src, dst, flip_x, color_mod, alpha)

    # ... implement the other 7 methods ...