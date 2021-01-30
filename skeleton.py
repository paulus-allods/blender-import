import mathutils

from struct import unpack, unpack_from

class Bone:

    def __init__(self, inverted_world_matrix, parent, id, name, local_matrix):
        self.inverted_world_matrix = inverted_world_matrix
        self.parent = parent
        self.id = id
        self.name = name
        self.local_matrix = local_matrix

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
