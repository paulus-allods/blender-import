import zlib
from enum import Enum

class ModelElement:

    def __init__(self, lods, name, material_name, vertex_declaration_id, vertex_buffer_offset, material, skin_index, virtual_offset):
        self.lods = lods
        self.name = name
        self.material_name = material_name
        self.vertex_declaration_id = vertex_declaration_id
        self.vertex_buffer_offset = vertex_buffer_offset
        self.material = material
        self.skin_index = skin_index
        self.virtual_offset = virtual_offset

class GeometryFragment:

    def __init__(self, vertex_buffer_begin, vertex_buffer_end, index_buffer_begin, index_buffer_end):
        self.vertex_buffer_begin = vertex_buffer_begin
        self.vertex_buffer_end = vertex_buffer_end
        self.index_buffer_begin = index_buffer_begin
        self.index_buffer_end = index_buffer_end

class Material:

    def __init__(self, blend_effect, diffuse_texture, scroll_alpha, scroll_rgb, transparency_texture, transparent, use_fog, u_translate_speed, visible, v_translate_speed):
        self.blend_effect = blend_effect
        self.diffuse_texture = diffuse_texture
        self.scroll_alpha = scroll_alpha
        self.scroll_rgb = scroll_rgb
        self.transparency_texture = transparency_texture
        self.transparent = transparent
        self.use_fog = use_fog
        self.u_translate_speed = u_translate_speed
        self.visible = visible
        self.v_translate_speed = v_translate_speed

class BlendEffect(Enum):

    BLEND_EFFECT_ADD =0 
    BLEND_EFFECT_ALPHA = 1
    BLEND_EFFECT_ALPHA_ADD = 2
    BLEND_EFFECT_COLOR = 3
    BLEND_EFFECT_COLOR_ADD = 4   
