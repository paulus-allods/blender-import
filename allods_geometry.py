import bpy
import bpy_extras
import mathutils

import io
import itertools
import pathlib
import re
import zlib

import distutils.util as du

from enum import Enum
from xml.etree import ElementTree
from struct import pack, unpack, unpack_from

## Geometry structures

class Vertex:
    
    def __init__(self, position, normal, color, texcoord0, texcoord1, weights, indices):
        self.position = position
        self.normal = normal
        self.color = color
        self.texcoord0 = texcoord0
        self.texcoord1 = texcoord1
        self.weights = weights
        self.indices = indices

class VertexDeclaration:

    def __init__(self, position, normal, color, texcoord0, texcoord1, weights, indices, stride):
        self.position = position
        self.normal = normal
        self.color = color
        self.texcoord0 = texcoord0
        self.texcoord1 = texcoord1
        self.weights = weights
        self.indices = indices
        self.stride = stride

class VertexComponent:

    def __init__(self, type, offset):
        self.type = type
        self.offset = offset

class VertexElementType(Enum):
    FLOAT1 = 1
    FLOAT2 = 2
    FLOAT3 = 3
    FLOAT4 = 4
    SHORT2 = 5
    SHORT4 = 6
    COLOR4 = 7
    UBYTE4 = 8
    USHORT2 = 9
    USHORT4 = 10
    HALF4 = 11
    UNUSED = 12

class Bone:

    def __init__(self, inverted_world_matrix, parent, id, name, local_matrix):
        self.inverted_world_matrix = inverted_world_matrix
        self.parent = parent
        self.id = id
        self.name = name
        self.local_matrix = local_matrix

class Blob:

    def __init__(self, localId, size):
        self.localId = localId
        self.size = size

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

## File parsers

class XdbParser:

    def __init__(self, path):
        self.content = ElementTree.parse(path).getroot()
        self._vertex_declarations = None
        self._index_buffer = None
        self._vertex_buffer = None
        self._model_elements = None
        self._skeleton = None
    
    def get_vertex_declarations(self):
        if self._vertex_declarations == None:
            self._vertex_declarations = []
            for item in self.content.findall('vertexDeclarations/Item'):
                position = XdbParser._parse_vertex_component(item.find('position'))
                normal = XdbParser._parse_vertex_component(item.find('normal'))
                color = XdbParser._parse_vertex_component(item.find('color'))
                texcoord0 = XdbParser._parse_vertex_component(item.find('texcoord0'))
                texcoord1 = XdbParser._parse_vertex_component(item.find('texcoord1'))
                weights = XdbParser._parse_vertex_component(item.find('weights'))
                indices = XdbParser._parse_vertex_component(item.find('indices'))
                stride = int(item.find('stride').text)
                self._vertex_declarations.append(VertexDeclaration(position, normal, color, texcoord0, texcoord1, weights, indices, stride))
        return self._vertex_declarations

    def get_index_buffer(self):
        if self._index_buffer == None:
            localID = int(self.content.find('indexBuffer/localID').text)
            size = int(self.content.find('indexBuffer/size').text)
            self._index_buffer = Blob(localID, size)
        return self._index_buffer

    def get_vertex_buffer(self):
        if self._vertex_buffer == None:
            localID = int(self.content.find('vertexBuffer/localID').text)
            size = int(self.content.find('vertexBuffer/size').text)
            self._vertex_buffer = Blob(localID, size)
        return self._vertex_buffer

    def get_skeleton(self):
        if self._skeleton == None:
            localID = int(self.content.find('skeleton/localID').text)
            size = int(self.content.find('skeleton/size').text)
            self._skeleton = Blob(localID, size)
        return self._skeleton

    def get_model_elements(self):
        if self._model_elements == None:
            self._model_elements = []
            for item in self.content.findall('modelElements/Item'):
                lods = []
                for lod in item.findall('lods/Item'):
                    lods.append(XdbParser._parse_geometry_fragment(lod))
                material = None #XdbParser._parse_material(item.find('material'))
                material_name = item.find('materialName').text
                name = item.find('name').text
                skin_index = int(item.find('skinIndex').text)
                vertex_buffer_offset = int(item.find('vertexBufferOffset').text)
                vertex_declaration_id = int(item.find('vertexDeclarationID').text)
                virtual_offset = float(item.find('virtualOffset').text)
                self._model_elements.append(ModelElement(lods, name, material_name, vertex_declaration_id, vertex_buffer_offset, material, skin_index, virtual_offset))
        return self._model_elements

    def get_binary_file(self):
        return XdbParser._find_href(self.content, 'binaryFile')

    @staticmethod
    def _parse_material(xml):
        blend_effect = BlendEffect[xml.find('BlendEffect').text]
        diffuse_texture = XdbParser._find_href(xml, 'diffuseTexture')
        scroll_alpha = bool(du.strtobool(xml.find('scrollAlpha').text))
        scroll_rgb =  bool(du.strtobool((xml.find('ScrollRGB') or xml.find('scrollRGB')).text))
        transparency_texture = XdbParser._find_href(xml, 'transparencyTexture')
        transparent = bool(du.strtobool(xml.find('transparent').text))
        use_fog = bool(du.strtobool(xml.find('useFog').text))
        u_translate_speed = float(xml.find('uTranslateSpeed').text)
        visible = bool(du.strtobool(xml.find('visible').text))
        v_translate_speed = float(du.strtobool(xml.find('vTranslateSpeed').text))
        return Material(blend_effect, diffuse_texture, scroll_alpha, scroll_rgb, transparency_texture, transparent, use_fog, u_translate_speed, visible, v_translate_speed)

    @staticmethod
    def _parse_geometry_fragment(xml):
        index_buffer_begin = int(xml.find('indexBufferBegin').text)
        index_buffer_end = int(xml.find('indexBufferEnd').text)
        vertex_buffer_begin = int(xml.find('vertexBufferBegin').text)
        vertex_buffer_end = int(xml.find('vertexBufferEnd').text)
        return GeometryFragment(vertex_buffer_begin, vertex_buffer_end, index_buffer_begin, index_buffer_end)

    @staticmethod
    def _parse_vertex_component(xml):
        offset = int(xml.find('offset').text)
        type = VertexElementType[xml.find('type').text]
        return VertexComponent(type, offset)

    @staticmethod
    def _find_href(xml, key):
        el = xml.find(key)
        if el == None:
            return None
        else:
            return el.attrib['href']

class BinParser:

    def __init__(self, path):
        self.path = path
        self._blobs = []
        self._read_blobs()

    def _read_blobs(self):
        content = io.BytesIO(zlib.decompress(open(self.path, 'rb').read()))
        while True:
            try:
                localId, size = unpack('II',content.read(8))
                assert localId == len(self._blobs)
                value = content.read(size)
                self._blobs.append(value)
            except:
                break
        content.close()

    def get_buffer(self, blob):
        assert(len(self._blobs[blob.localId]) == blob.size)
        return self._blobs[blob.localId]

class BoneBinParser:

    def __init__(self, buffer):
        self.buffer = buffer
        self.bones = None
        

    def get_bones(self):
        if self.bones == None:
            self.bones = []
            bone_list_offset, bone_list_size, bone_names_offset, bone_names_size, bone_ids_offset, bone_ids_size, bone_local_offset, bone_local_size = unpack_from('IIIIIIII', self.buffer)
            
            assert bone_list_size == bone_names_size == bone_ids_size == bone_local_size
            
            bone_names_offset += 8
            bone_ids_offset += 16
            bone_local_offset += 24

            bone_list_buffer = self.buffer[bone_list_offset:bone_names_offset]
            bone_names_buffer = self.buffer[bone_names_offset:]
            bone_ids_buffer = self.buffer[bone_ids_offset:]
            bone_world_buffer = self.buffer[bone_local_offset:bone_ids_offset]

            for i in range(bone_list_size):
                coefficients_w = unpack_from('ffffffffffff', bone_list_buffer, i*52)
                inverted_world_matrix = mathutils.Matrix([  [*coefficients_w[0:3], 0], [*coefficients_w[3:6], 0], [*coefficients_w[6:9], 0], [*coefficients_w[9:12], 1] ])
                parent = unpack_from('I', bone_list_buffer, i*52 + 48)[0]
                offset, length = unpack_from('II', bone_names_buffer, i*8)
                name = bone_names_buffer[offset + i*8:offset + i*8 + length].decode('utf-8').rstrip('\x00')
                id = unpack_from('H', bone_ids_buffer, i*2)[0]
                coefficients_l = unpack_from('ffffffffffff', bone_world_buffer, i*48)
                local_matrix = mathutils.Matrix([  [*coefficients_l[0:3], 0], [*coefficients_l[3:6], 0], [*coefficients_l[6:9], 0], [*coefficients_l[9:12], 1] ])
                self.bones.append(Bone(inverted_world_matrix, parent, id, name, local_matrix))

        return self.bones

class VertexBinConverter:

    def __init__(self, vertex_declaration):
        self.vertex_declaration = vertex_declaration

    def vertex_to_bin(self, vertex):
        buffer = [0] * self.vertex_declaration.stride
        VertexBinConverter._write_vertex_component(self.vertex_declaration.position, buffer, vertex.position)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.normal, buffer, vertex.normal)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.color, buffer, vertex.color)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.texcoord0, buffer, vertex.texcoord0)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.texcoord1, buffer, vertex.texcoord1)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.weights, buffer, vertex.weights)
        VertexBinConverter._write_vertex_component(self.vertex_declaration.indices, buffer, vertex.indices)
        return buffer

    def bin_to_vertex(self, buffer):
        assert len(buffer) == self.vertex_declaration.stride
        return Vertex(
            VertexBinConverter._read_vertex_component(self.vertex_declaration.position, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.normal, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.color, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.texcoord0, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.texcoord1, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.weights, buffer),
            VertexBinConverter._read_vertex_component(self.vertex_declaration.indices, buffer)
        )
    
    def bin_to_vertices(self, buffer):
        assert len(buffer) % self.vertex_declaration.stride == 0
        count = len(buffer) // self.vertex_declaration.stride
        vertices = []
        for i in range(count):
            offset = i * self.vertex_declaration.stride
            vertices.append(self.bin_to_vertex(buffer[offset:offset + self.vertex_declaration.stride]))
        return vertices
        

    @staticmethod
    def _read_vertex_component(vertex_component, buffer):
        if vertex_component.type == VertexElementType.FLOAT1:
            return unpack('f', buffer[vertex_component.offset:vertex_component.offset+4])[0]
        elif vertex_component.type == VertexElementType.FLOAT2:
            return unpack('ff', buffer[vertex_component.offset:vertex_component.offset+8])
        elif vertex_component.type == VertexElementType.FLOAT3:
            return unpack('fff', buffer[vertex_component.offset:vertex_component.offset+12])
        elif vertex_component.type == VertexElementType.FLOAT4:
            return unpack('ffff', buffer[vertex_component.offset:vertex_component.offset+16])
        elif vertex_component.type == VertexElementType.SHORT2:
            return unpack('hh', buffer[vertex_component.offset:vertex_component.offset+4])
        elif vertex_component.type == VertexElementType.SHORT4:
            return unpack('hhhh', buffer[vertex_component.offset:vertex_component.offset+8])
        elif vertex_component.type == VertexElementType.COLOR4:
            return unpack('BBBB', buffer[vertex_component.offset:vertex_component.offset+4])
        elif vertex_component.type == VertexElementType.UBYTE4:    
            return unpack('BBBB', buffer[vertex_component.offset:vertex_component.offset+4])
        elif vertex_component.type == VertexElementType.USHORT2:    
            return unpack('HH', buffer[vertex_component.offset:vertex_component.offset+4])
        elif vertex_component.type == VertexElementType.USHORT4:
            return unpack('HHHH', buffer[vertex_component.offset:vertex_component.offset+8])     
        elif vertex_component.type == VertexElementType.HALF4:
            return unpack('eeee', buffer[vertex_component.offset:vertex_component.offset+8])
        elif vertex_component.type == VertexElementType.UNUSED:
            return None
        else:
            raise Exception('Unknown value type: {}'.format(vertex_component.type))

    @staticmethod
    def _write_vertex_component(vertex_component, buffer, value):
        if vertex_component.type == VertexElementType.FLOAT1:
            buffer[vertex_component.offset:vertex_component.offset+4] = pack('f', value)
        elif vertex_component.type == VertexElementType.FLOAT2:
            buffer[vertex_component.offset:vertex_component.offset+8] = pack('ff', *value)
        elif vertex_component.type == VertexElementType.FLOAT3:
            buffer[vertex_component.offset:vertex_component.offset+12] = pack('fff', *value)
        elif vertex_component.type == VertexElementType.FLOAT4:
            buffer[vertex_component.offset:vertex_component.offset+16] = pack('ffff', *value)
        elif vertex_component.type == VertexElementType.SHORT2:
            buffer[vertex_component.offset:vertex_component.offset+4] = pack('hh', *value)
        elif vertex_component.type == VertexElementType.SHORT4:
            buffer[vertex_component.offset:vertex_component.offset+8] = pack('hhhh', *value)
        elif vertex_component.type == VertexElementType.COLOR4:
            buffer[vertex_component.offset:vertex_component.offset+4] = pack('BBBB', *value)
        elif vertex_component.type == VertexElementType.UBYTE4:    
            buffer[vertex_component.offset:vertex_component.offset+4] = pack('BBBB', *value)
        elif vertex_component.type == VertexElementType.USHORT2:    
            buffer[vertex_component.offset:vertex_component.offset+4] = pack('HH', *value)
        elif vertex_component.type == VertexElementType.USHORT4:
            buffer[vertex_component.offset:vertex_component.offset+8] = pack('HHHH', *value)     
        elif vertex_component.type == VertexElementType.HALF4:
            buffer[vertex_component.offset:vertex_component.offset+8] = pack('eeee', *value)
        elif vertex_component.type == VertexElementType.UNUSED:
            pass
        else:
            raise Exception('Unknown value type: {}'.format(vertex_component.type))

## Addon main code

class ImportGeometry(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Load geometry files from Allods Online"""
    bl_idname = "allods.import_geometry"
    bl_label = "Import geometry"

    filter_glob: bpy.props.StringProperty(
        default="*.xdb",
        options={'HIDDEN'},
    )

    import_lods: bpy.props.BoolProperty(
        name="Import LODs",
        description="Import all LOD models",
        default=False,
    )

    def execute(self, context):
        path = pathlib.Path(self.filepath)

        parser = XdbParser(path)
        bin_parser = BinParser(path.with_suffix('.bin'))

        vertex_bin_converters = []
        for vertex_declaration in parser.get_vertex_declarations():
            vertex_bin_converters.append(VertexBinConverter(vertex_declaration))

        vertex_bin_converter = vertex_bin_converters[0]
        vertex_buffer = bin_parser.get_buffer(parser.get_vertex_buffer())
        vertices = vertex_bin_converter.bin_to_vertices(vertex_buffer)
        index_buffer = bin_parser.get_buffer(parser.get_index_buffer())
        indices = [(unpack('HHH', index_buffer[i*6:i*6+6])) for i in range(len(index_buffer) // 6)]
        skeleton_buffer = bin_parser.get_buffer(parser.get_skeleton())
        skeleton_parser = BoneBinParser(skeleton_buffer)
        bones = skeleton_parser.get_bones()

        model_name = re.sub('(\.\(.*\))?\.xdb', '', path.name)

        root_collection =  bpy.data.collections.new(model_name)
        bpy.context.scene.collection.children.link(root_collection)

        for model_element in parser.get_model_elements():
            collection = bpy.data.collections.new(model_element.name)
            root_collection.children.link(collection)
            for i, lod in enumerate(model_element.lods):
                if not self.import_lods and i > 0:
                    break
                lod_indices = indices[lod.index_buffer_begin//3:lod.index_buffer_end//3]
                lod_vertices = [vertices[i] for i in set(itertools.chain.from_iterable(lod_indices))]
                lod_indices_vertex = [(lod_vertices.index(vertices[i[0]]), lod_vertices.index(vertices[i[1]]), lod_vertices.index((vertices[i[2]]))) for i in lod_indices] 	
                mesh = bpy.data.meshes.new(model_element.name + '_lod' + str(i))
                mesh.from_pydata([v.position for v in lod_vertices], [], lod_indices_vertex)
                mesh.update()
                uv_layer = mesh.uv_layers.new()
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        uv_layer.data[loop_idx].uv = lod_vertices[vert_idx].texcoord0
                obj = bpy.data.objects.new(model_element.name + '_lod' + str(i), mesh)
                collection.objects.link(obj)
                obj.hide_set(i != 0)
        
        return {'FINISHED'}

## Addon registration

bl_info = {
    'name': 'Allods Online geometry',
    'category': 'Import-Export',
    'version': (0, 0, 2),
    'blender': (2, 90, 0)
}

moduleNames = ['import']
moduleFullNames = []

def menu_func_import(self, context):
    self.layout.operator(ImportGeometry.bl_idname, text="Allods Geometry (.bin)")

def register():
    bpy.utils.register_class(ImportGeometry)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportGeometry)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
