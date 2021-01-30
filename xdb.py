import xml.etree.ElementTree as ET
import distutils.util as du
from . import blob
from . import geometry
from . import vertex

class XdbParser:

    def __init__(self, path):
        self.content = ET.parse(path).getroot()
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
                self._vertex_declarations.append(vertex.VertexDeclaration(position, normal, color, texcoord0, texcoord1, weights, indices, stride))
        return self._vertex_declarations

    def get_index_buffer(self):
        if self._index_buffer == None:
            localID = int(self.content.find('indexBuffer/localID').text)
            size = int(self.content.find('indexBuffer/size').text)
            self._index_buffer = blob.Blob(localID, size)
        return self._index_buffer

    def get_vertex_buffer(self):
        if self._vertex_buffer == None:
            localID = int(self.content.find('vertexBuffer/localID').text)
            size = int(self.content.find('vertexBuffer/size').text)
            self._vertex_buffer = blob.Blob(localID, size)
        return self._vertex_buffer

    def get_skeleton(self):
        if self._skeleton == None:
            localID = int(self.content.find('skeleton/localID').text)
            size = int(self.content.find('skeleton/size').text)
            self._skeleton = blob.Blob(localID, size)
        return self._skeleton

    def get_model_elements(self):
        if self._model_elements == None:
            self._model_elements = []
            for item in self.content.findall('modelElements/Item'):
                lods = []
                for lod in item.findall('lods/Item'):
                    lods.append(XdbParser._parse_geometry_fragment(lod))
                material = XdbParser._parse_material(item.find('material'))
                material_name = item.find('materialName').text
                name = item.find('name').text
                skin_index = int(item.find('skinIndex').text)
                vertex_buffer_offset = int(item.find('vertexBufferOffset').text)
                vertex_declaration_id = int(item.find('vertexDeclarationID').text)
                virtual_offset = float(item.find('virtualOffset').text)
                self._model_elements.append(geometry.ModelElement(lods, name, material_name, vertex_declaration_id, vertex_buffer_offset, material, skin_index, virtual_offset))
        return self._model_elements

    def get_binary_file(self):
        return self.content.find('binaryFile').attrib['href']

    @staticmethod
    def _parse_material(xml):
        blend_effect = geometry.BlendEffect[xml.find('BlendEffect').text]
        diffuse_texture = xml.find('diffuseTexture').attrib['href']
        scroll_alpha = bool(du.strtobool(xml.find('scrollAlpha').text))
        scroll_rgb = bool(du.strtobool(xml.find('ScrollRGB').text))
        transparency_texture = xml.find('transparencyTexture').attrib['href']
        transparent = bool(du.strtobool(xml.find('transparent').text))
        use_fog = bool(du.strtobool(xml.find('useFog').text))
        u_translate_speed = float(xml.find('uTranslateSpeed').text)
        visible = bool(du.strtobool(xml.find('visible').text))
        v_translate_speed = float(du.strtobool(xml.find('vTranslateSpeed').text))
        return geometry.Material(blend_effect, diffuse_texture, scroll_alpha, scroll_rgb, transparency_texture, transparent, use_fog, u_translate_speed, visible, v_translate_speed)

    @staticmethod
    def _parse_geometry_fragment(xml):
        index_buffer_begin = int(xml.find('indexBufferBegin').text)
        index_buffer_end = int(xml.find('indexBufferEnd').text)
        vertex_buffer_begin = int(xml.find('vertexBufferBegin').text)
        vertex_buffer_end = int(xml.find('vertexBufferEnd').text)
        return geometry.GeometryFragment(vertex_buffer_begin, vertex_buffer_end, index_buffer_begin, index_buffer_end)

    @staticmethod
    def _parse_vertex_component(xml):
        offset = int(xml.find('offset').text)
        type = vertex.VertexElementType[xml.find('type').text]
        return vertex.VertexComponent(type, offset)
