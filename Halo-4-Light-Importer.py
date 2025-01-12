bl_info = {
    "name": "Halo 4 Light Importer",
    "author": "Brooen",
    "version": (1, 0),
    "blender": (4, 1, 1),  # Update to your Blender version
    "location": "View3D > Sidebar > Halo Light Importers",
    "description": "Imports Halo 4 light data into Blender",
    "category": "Import-Export",
}

import bpy
import os
import struct
import math
from bpy.props import StringProperty
from bpy.types import Operator, Panel, AddonPreferences
from mathutils import Matrix, Vector, Color

# Define enums for lighttype, shape, and bungie_light_type
LIGHTTYPE = {0: 'point', 1: 'spot', 2: 'directional', 3: 'area', 4: 'sun'}

# Addon Preferences for global settings
class Halo4LightImporterPreferences(AddonPreferences):
    bl_idname = __name__

    tags_base_directory: StringProperty(
        name="Tags Base Directory",
        subtype='DIR_PATH',
        default=""
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "tags_base_directory")

# Operator to import lights
class IMPORT_OT_halo_4_lights(Operator):
    bl_idname = "import_scene.halo_4_lights"
    bl_label = "Import Halo 4 Lights"
    bl_description = "Import Halo 4 lighting data files"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the lights",
        maxlen=1024,
        subtype='FILE_PATH',
    )
    directory: StringProperty(
        name="Directory",
        description="Directory of the files",
        maxlen=1024,
        subtype='DIR_PATH',
    )
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        for file_elem in self.files:
            filepath = os.path.join(self.directory, file_elem.name)
            read_binary_file(filepath, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        tags_dir = prefs.tags_base_directory if prefs.tags_base_directory else "//"

        context.window_manager.fileselect_add(self)
        self.directory = bpy.path.abspath(tags_dir)
        self.filter_glob = "*.scenario_structure_lighting_info"
        return {'RUNNING_MODAL'}

# Panel in the 3D Viewport Sidebar
class VIEW3D_PT_halo_4_light_importer(Panel):
    bl_label = "Halo 4 Light Importer"
    bl_idname = "VIEW3D_PT_halo_4_light_importer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Halo Lights"

    def draw(self, context):
        layout = self.layout
        layout.operator(IMPORT_OT_halo_4_lights.bl_idname, text="Import Lights")



# Function to read and import binary files
def read_binary_file(file_path, context):
    with open(file_path, 'rb') as file:
        # 1. Skip 184 bytes
        file.seek(184)
        
        # 2. Read a u32, then skip that many bytes
        skip_size, = struct.unpack('I', file.read(4))
        file.seek(skip_size, 1)
        
        # 3. Skip 8 bytes, read a u32, then skip that many bytes (11 times)
        for _ in range(11):
            file.seek(8, 1)
            skip_size, = struct.unpack('I', file.read(4))
            file.seek(skip_size, 1)

        # Skip 132 bytes after completing the first part
        file.seek(144, 1)

        # Read u32 reference count
        reference_count, = struct.unpack('I', file.read(4))
        print(f"Reference count: {reference_count}")

        # Store references in a list
        references = []
        
        file.seek(12, 1)

        # Read each reference
        for _ in range(reference_count):
            # Skip the initial padding
            file.seek(8, 1)

            # Read lighttype (u32)
            lighttype, = struct.unpack('I', file.read(4))

            # Read color (3 floats: r, g, b)
            color = struct.unpack('fff', file.read(12))

            # Skip padding (36 bytes)
            file.seek(36, 1)

            # Read lighting_mode (u32)
            lighting_mode, = struct.unpack('I', file.read(4))

            # Read distance_attenuation_start (float)
            distance_attenuation_start, = struct.unpack('f', file.read(4))

            # Skip padding (36 bytes)
            file.seek(36, 1)

            # Read data (4 floats)
            data = struct.unpack('ffff', file.read(16))

            # Read inner_cone_angle (float)
            inner_cone_angle, = struct.unpack('f', file.read(4))

            # Skip padding (332 bytes)
            file.seek(332, 1)


            # Store the parsed reference data
            reference = {
                'lighttype': LIGHTTYPE.get(lighttype, 'unknown'),
                'color': color,
                'intensity': 0.0,  # Placeholder for intensity from block2
            }
            references.append(reference)
            
            print(f"Lighttype: {lighttype}")
            print(f"Color: {color}")
            print(f"Lighting Mode: {lighting_mode}")
            print(f"Distance Attenuation Start: {distance_attenuation_start}")
            print(f"Data: {data}")
            print(f"Inner Cone Angle: {inner_cone_angle}")

        file.seek(4, 1)
        
        for ref_index in range(reference_count):
            # Skip padding (8 bytes)
            file.seek(8, 1)

            # Read blocksize (u32)
            blocksize, = struct.unpack('I', file.read(4))

            # Skip padding (8 bytes)
            file.seek(8, 1)

            # Read stringsize (u32)
            stringsize, = struct.unpack('I', file.read(4))

            # Read the string (chars)
            string = file.read(stringsize).decode('ascii').strip('\x00')

            # Skip padding (76 bytes)
            file.seek(76, 1)

            # Read intensity (float)
            intensity, = struct.unpack('f', file.read(4))

            # Skip remaining padding (blocksize - (80 + stringsize))
            remaining_padding = blocksize - (80 + stringsize)
            if remaining_padding > 0:
                file.seek(remaining_padding, 1)
            
            
            references[ref_index]['intensity'] = intensity
            print(f"Blocksize: {blocksize}")
            print(f"String Size: {stringsize}")
            print(f"String: {string}")
            print(f"Intensity: {intensity}")      
            
        # Skip 16 bytes of padding after references
        file.seek(12, 1)

        # Create a collection named after the file (minus extension)
        collection_name = os.path.splitext(os.path.basename(file_path))[0] + "_lights"
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)

        # Create a dictionary to store light data blocks for each reference index
        light_data_blocks = {}

        # Read each instance block
        for instance_index in range(reference_count):
            # Skip initial padding (36 bytes)
            file.seek(36, 1)

            # Read lightmode (u32)
            lightmode, = struct.unpack('I', file.read(4))

            # Read origin (xyz: 3 floats)
            origin = struct.unpack('fff', file.read(12))

            # Read forward (xyz: 3 floats)
            forward = struct.unpack('fff', file.read(12))

            # Read up (xyz: 3 floats)
            up = struct.unpack('fff', file.read(12))

            # Skip padding (20 bytes)
            file.seek(20, 1)

            # Map the lighttype to Blender's light types
            blender_light_type = {
                'point': 'POINT',
                'spot': 'SPOT',
                'directional': 'SUN',
                'area': 'AREA',
                'sun': 'SUN'
            }.get(references[instance_index]['lighttype'], 'POINT')  # Default to POINT if unknown

            # Create the light data block
            light_data = bpy.data.lights.new(name=f"{string}", type=blender_light_type)

            # Set light properties
            light_data.color = references[instance_index]['color']
            light_data.energy = references[instance_index]['intensity'] * 10

            # Create the light object using the light data
            light_object = bpy.data.objects.new(name=f"{string}", object_data=light_data)
            collection.objects.link(light_object)

            # Set light radius and spot size
            if light_data.type == 'POINT':
                light_data.shadow_soft_size = 0.15  # Set the radius for point lights
            elif light_data.type == 'SPOT':
                light_data.spot_size = math.radians(120)  # Convert 120 degrees to radians
            light_data.shadow_soft_size = 0.15  # Set the radius for spot lights
            
            # Multiply location by 3.048
            scaled_origin = Vector(origin) * 3.048
            light_object.location = scaled_origin

            # Convert tuples to mathutils.Vector and normalize
            forward_vector = Vector(forward).normalized()
            up_vector = Vector(up).normalized()

            # Compute the right vector
            right_vector = forward_vector.cross(up_vector).normalized()

            # Recompute the up vector to ensure orthogonality
            up_vector = right_vector.cross(forward_vector).normalized()

            # Create rotation matrix (3x3)
            rotation_matrix = Matrix((
                right_vector,
                up_vector,
                -forward_vector,  # Adjust for Blender's coordinate system
            )).transposed()

            # Invert Y rotation by rotating 180 degrees around Y-axis (3x3)
            invert_y_rotation = Matrix.Rotation(math.pi, 3, 'Y')  # 180 degrees in radians

            # Rotate -90 degrees around local X-axis (3x3)
            rotate_neg_90_x = Matrix.Rotation(-math.pi / 2, 3, 'X')  # -90 degrees in radians

            # Apply the rotations
            rotation_matrix = rotation_matrix @ invert_y_rotation @ rotate_neg_90_x

            # Convert rotation matrix to 4x4
            rotation_matrix_4x4 = rotation_matrix.to_4x4()

            # Apply rotation and location to the light object
            light_object.matrix_world = Matrix.Translation(scaled_origin) @ rotation_matrix_4x4


# Registration
classes = (
    Halo4LightImporterPreferences,
    IMPORT_OT_halo_4_lights,
    VIEW3D_PT_halo_4_light_importer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("Halo 4 Light Importer registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Halo 4 Light Importer unregistered")

if __name__ == "__main__":
    register()
