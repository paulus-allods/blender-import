import bpy
import mathutils

import argparse
import pathlib
import itertools

from struct import unpack

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ImportGeometry(Operator, ImportHelper):
    """Load geometry files from Allods Online"""
    bl_idname = "allods.import_geometry"
    bl_label = "Import geometry"

    filter_glob: StringProperty(
        default="*.xdb",
        options={'HIDDEN'},
    )

    def execute(self, context):
        path = pathlib.Path(self.filepath)

        parser = XdbParser(path)
        bin_parser = blob.BinParser(path.with_suffix('.bin'))

        vertex_bin_converters = []
        for vertex_declaration in parser.get_vertex_declarations():
            vertex_bin_converters.append(vertex.VertexBinConverter(vertex_declaration))

        vertex_bin_converter = vertex_bin_converters[0]
        vertex_buffer = bin_parser.get_buffer(parser.get_vertex_buffer())
        vertices = vertex_bin_converter.bin_to_vertices(vertex_buffer)
        index_buffer = bin_parser.get_buffer(parser.get_index_buffer())
        indices = [(unpack('HHH', index_buffer[i*6:i*6+6])) for i in range(len(index_buffer) // 6)]
        skeleton_buffer = bin_parser.get_buffer(parser.get_skeleton())
        skeleton_parser = skeleton.BoneBinParser(skeleton_buffer)
        bones = skeleton_parser.get_bones()

        for model_element in parser.get_model_elements():
            collection = bpy.data.collections.new(model_element.name)
            bpy.context.scene.collection.children.link(collection)
            for i, lod in enumerate(model_element.lods):
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
        
        armature = bpy.data.armatures.new("skeleton")
        armature_obj = bpy.data.objects.new("skeleton", armature)
        collection.objects.link(armature_obj)

        bpy.context.view_layer.objects.active = armature_obj

        bpy.ops.object.mode_set(mode='EDIT')

        new_bones = []

        for bone in bones:
            current_bone = bone
            vector = mathutils.Vector((0.0, 0.0, 0.0, 1.0))

            while current_bone.parent != 65535:
                vector = vector @ current_bone.local_matrix
                current_bone = bones[current_bone.parent]

            world = bone.inverted_world_matrix.inverted()

            #o = bpy.data.objects.new( bone.name, None )
            #collection.objects.link(o)
            #o.empty_display_size = 0.01
            #o.empty_display_type = 'PLAIN_AXES'
            #o.location = vector[0:3]

            o = bpy.data.objects.new( bone.name + '_alt', None )
            collection.objects.link(o)
            o.empty_display_size = 0.5
            o.empty_display_type = 'PLAIN_AXES'
            o.location = world[3][0:3]
            o.rotation_euler = world.transposed().to_euler('XYZ')
            new_bones.append(o)

        for index, bone in enumerate(bones):
            d = new_bones[index].location - (new_bones[bone.parent].location if bone.parent != 65535 else mathutils.Vector((0,0,0)))
            axis, roll = bpy.types.Bone.AxisRollFromMatrix(world.transposed().to_3x3(), axis=d)
            print(d, axis, roll)
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportGeometry.bl_idname,
                         text="Allods Geometry (.bin)")


def register():
    bpy.utils.register_class(ImportGeometry)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportGeometry)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
