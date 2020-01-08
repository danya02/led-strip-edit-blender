import bpy
import sys
# Replace the path with your own site-packages and dist-packages paths
sys.path = ['/usr/lib/python3/dist-packages', '/home/danya/.local/lib/python3.7/site-packages'] + sys.path
import serial
import traceback
import time
import threading

PORT_ADDR = '/dev/ttyUSB0'
IMAGE_NAME = 'LED strip texture'
SERIAL_HANDLE = None

class ArduinoProperties(bpy.types.PropertyGroup):
    port_address: bpy.props.StringProperty(
                    name='Port',
                    description='Path to TTY connected to Arduino',
                    default='/dev/ttyUSB0',
                    subtype='FILE_PATH')
    
    port_baudrate: bpy.props.IntProperty(
                    name='Baudrate',
                    default=115200,
                    min=1)
    
    pixel_len: bpy.props.IntProperty(
                name='Number of pixels',
                default=60,
                min=1)
    
    texture: bpy.props.PointerProperty(
                name='Image',
                description='Image whose pixels will be transmitted over the wire',
                type=bpy.types.Image)
                



class ArduinoTextureUploadOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.arduino_texture_upload_operator"
    bl_label = "Upload texture to Arduino"

    _timer = None

    @property
    def img(self):
        return bpy.context.scene.arduino_props.texture

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            self.report({'WARNING'}, 'Transmission cancelled before it was completed!')
            return {'CANCELLED'}

        if event.type == 'TIMER':
            print('Timer tick!')
            self.write_pixel(self.index)
            self.index += 1
            if self.index >= self.img.size[1]:
                self.serial_handle.write(b'-1       0  0   0\n')
                self.serial_handle.close()
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        props = context.scene.arduino_props
        self.lock = threading.Lock()
        try:
            self.serial_handle = serial.Serial(props.port_address, props.port_baudrate)
        except:
            self.report({'ERROR'}, 'Error opening serial: \n'+traceback.format_exc())
            return {'CANCELLED'}
        if self.img is None:
            self.report({'ERROR'}, 'Texture loading error, has it not been inited?')
            return {'CANCELLED'}
        if False: # do send entire texture at once or with a timer? 
            try:
                for i in range(self.img.size[1]):
                    self.write_pixel(i)
                return {'FINISHED'}
            except:
                self.report({'ERROR'}, 'Error while transmitting texture:\n'+traceback.format_exc())
                return {'CANCELLED'}
        else:
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.001, window=context.window)
            self.index = 0
            wm.modal_handler_add(self)
            return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
    
    def get_at(self, x, y):
        index = (y*self.img.size[1] + x)*4
        pixel = [
                 self.img.pixels[index],   # Red
                 self.img.pixels[index+1], # Green
                 self.img.pixels[index+2], # Blue
                 self.img.pixels[index+3]  # Alpha
                ]
        print(pixel)
        pixel = [int(255*i) for i in pixel]
        return pixel
    
    def to_bytes(self, position, color):
        return bytes(str(position), 'ascii') + b'      ' + bytes('         '.join(map(str, color[:-1])), 'ascii')+ b'                          \n'
    def write_pixel(self, pos):
        pix = self.get_at(pos,0)
        write = self.to_bytes(pos, pix)
        print(write)
        with self.lock:
            self.serial_handle.write(write)

class ArduinoCreateImage(bpy.types.Operator):
    bl_label = "Create Image from size"
    bl_idname = "scene.arduino_create_img"

    def execute(self, context):
        scene = context.scene
        props = scene.arduino_props
        name = 'Arduino upload texture'
        try:
            bpy.data.images.remove(bpy.data.images[name])
        except:pass
        bpy.ops.image.new(name=name, height=props.pixel_len, width=1)
        props.texture = bpy.data.images[name]

        return {'FINISHED'}

class ArduinoCreateLEDStrip(bpy.types.Operator):
    bl_label = "Create LED strip object"
    bl_idname = "scene.arduino_create_leds"

    def execute(self, context):
        scene = context.scene
        props = scene.arduino_props
        bpy.ops.mesh.primitive_plane_add()
        object = context.active_object
        object.name="Arduino LED strip model"
        bpy.ops.object.modifier_add(type='ARRAY')
        object.modifiers['Array'].count = props.pixel_len
        object.modifiers['Array'].use_merge_vertices = True
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Array')
        bpy.ops.uv.smart_project()
        mat = bpy.data.materials.new("Arduino LED strip material")
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        while nodes: nodes.remove(nodes[0])
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = props.texture
        texture.interpolation = 'Closest'
        uvmap = nodes.new("ShaderNodeUVMap")
        links.new(texture.inputs['Vector'], uvmap.outputs['UV'])
        links.new(texture.outputs['Color'], emission.inputs['Color'])
        links.new(output.inputs['Surface'], emission.outputs['Emission'])
        
        
        object.data.materials.append(mat)
        

        return {'FINISHED'}

        
class ArduinoUploaderPanel(bpy.types.Panel):
    """Panel with settings for Arduino texture uploading."""
    bl_label = "Arduino Uploader config"
    bl_idname = "SCENE_PT_arduino_uploader"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"



    def draw(self, context):
        layout = self.layout

        scene = context.scene
        myprops = scene.arduino_props

        layout.label(text="Texture config:")
        row = layout.row(align=True)
        row.prop(myprops, "pixel_len")
        row.operator("scene.arduino_create_img")
        row.prop(myprops, "texture")
        layout.operator("scene.arduino_create_leds")

        layout.label(text="Arduino connection config:")
        layout.prop(myprops, "port_address")
        layout.prop(myprops, "port_baudrate")

        row = layout.row()
        row.scale_y=4.0
        row.operator("wm.arduino_texture_upload_operator")



def register():
    bpy.utils.register_class(ArduinoTextureUploadOperator)
    bpy.utils.register_class(ArduinoUploaderPanel)
    bpy.utils.register_class(ArduinoProperties)
    bpy.utils.register_class(ArduinoCreateImage)
    bpy.utils.register_class(ArduinoCreateLEDStrip)
    bpy.types.Scene.arduino_props = bpy.props.PointerProperty(type=ArduinoProperties)



def unregister():
    bpy.utils.unregister_class(ArduinoTextureUploadOperator)
    bpy.utils.unregister_class(ArduinoUploaderPanel)
    bpy.utils.unregister_class(ArduinoCreateImage)
    bpy.utils.unregister_class(ArduinoCreateLEDStrip)
    bpy.utils.unregister_class(ArduinoProperties)
    


if __name__ == "__main__":
    register()

    # test call
#    bpy.ops.wm.arduino_texture_upload_operator()
