from enum import Enum
from struct import pack, unpack

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
