import bpy
import random
import math
from typing import List


###### Pie Chart Data
DATA = [
    {
        'name': 'A',
        'count': 32,
        'color': (1, 0, 0)
    },
    {
        'name': 'B',
        'count': 20,
        'color': (0, 1, 0)
    },
    {
        'name': 'CDE',
        'count': 12,
        'color': (0.9, 0.5, .5)
    },
    {
        'name': 'Other',
        'count': 21,
        'color': (0.1, 0.9, .3)
    }
]

###### User Settings. Feel freely for change settings
FIX_LAMP = False
# Decrease for shallow effect
LAMP_ANGLE = 20
BACKGROUND_COLOR = (.02, .02, .02)
PIECE_NAME_COLOR = (1, 1, 1)
CAM_BORDER_PADDING = 5
CAM_ANGLE = 45
# If you want to use different height by values. Maximum piece height. Default 0.
MAX_DYNAMIC_PIECE_HEIGHT = 5
ANIMATION_FRAME_COUNT = 33


###### Object Names
CAM_NAME = 'Kamera'
CAM_PATH_NAME = 'KameraYolu'
LIGHT_NAME = 'Gunes'


###### Clear Scene
def clearScene():
    if len(bpy.context.scene.objects) > 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()


def createCamera(borderPadding = .2):
    bpy.ops.object.camera_add(rotation=(math.radians(90 - CAM_ANGLE), 0, math.radians(0)))
    bpy.context.object.name = CAM_NAME

    # Select objects that will be rendered
    for obj in bpy.context.scene.objects:
        obj.select = False
        if obj.type == 'CAMERA':
            bpy.context.scene.camera = obj

    for obj in bpy.context.visible_objects:
        if not (obj.hide or obj.hide_render):
            obj.select = True

    bpy.ops.view3d.camera_to_view_selected()
    bpy.context.object.data.sensor_width += borderPadding

    bpy.ops.object.select_all(action='DESELECT')


def createLight():
    bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 3), rotation=(0, math.radians(90 - LAMP_ANGLE), math.radians(-30)))
    bpy.context.object.name = LIGHT_NAME
    bpy.context.object.data.shadow_method = 'RAY_SHADOW'
    bpy.context.object.data.shadow_ray_samples = 3


###### Create Camera and Light
def prepareScene():
    createCamera(CAM_BORDER_PADDING)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                # show backface culling on 3d view
                area.spaces.active.show_backface_culling = True
                # toggle camera perspective
                area.spaces.active.region_3d.view_perspective = 'CAMERA'

    createLight()
    bpy.context.scene.world.light_settings.use_ambient_occlusion = True
    bpy.context.scene.world.light_settings.ao_factor = 0.5
    bpy.context.scene.world.light_settings.samples = 8
    bpy.context.scene.world.horizon_color = BACKGROUND_COLOR
###### End Of Standard Scene Process


###### Chart piece class
class ChartPiece:
    def __init__(self, offset = 0, angle = 60, color = (1, 1, 1), name = None, nameColor = (1, 1, 1), maxDynamicHeight = 0):
        self.offset = offset
        self.angle = angle
        self.color = color
        self.name = name
        self.nameColor = nameColor
        self.maxDynamicHeight = maxDynamicHeight

    def draw(self):
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
        bpy.ops.object.modifier_add(type='SCREW')
        scr = bpy.context.object.modifiers["Screw"]
        scr.axis = 'X'
        scr.steps = self.angle
        scr.render_steps = self.angle
        scr.angle = math.radians(self.angle)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(value=(1, 1, 0))
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Screw")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.fill_holes()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.rotation_euler = [0, math.radians(-90), math.radians(self.offset)]
        height = .5 if self.maxDynamicHeight == 0 else self.angle * (self.maxDynamicHeight / 360)
        bpy.context.object.dimensions[0] = height

        # Set material
        mat = bpy.data.materials.new(name='PieceMaterial')
        bpy.context.active_object.data.materials.append(mat)
        acMat = bpy.context.object.active_material
        acMat.diffuse_color = self.color
        acMat.diffuse_intensity = .6
        acMat.specular_color = (1, 1, 1)
        acMat.specular_intensity = 1
        acMat.emit = 0.35

        if self.name:
            nameAngle = self.offset + (self.angle / 2)
            print(self.name, self.offset, self.angle, nameAngle)
            nameX = 1 * math.sin(-1 * math.radians(nameAngle))
            nameY = 1 * math.cos(-1 * math.radians(nameAngle))
            bpy.ops.object.text_add(location=(nameX, nameY, height))
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.font.select_all()
            bpy.ops.font.delete(type='PREVIOUS_OR_SELECTION')
            bpy.ops.font.text_insert(text=self.name)
            bpy.context.object.data.size = 0.8
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.object.rotation_euler = [math.radians(90), 0, 0]
            bpy.context.object.data.size = .4
            bpy.context.object.data.extrude = 0.05
            bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
            bpy.context.object.data.offset_y = 0

            # Set material
            mat = bpy.data.materials.new(name='PieceNameMaterial')
            bpy.context.active_object.data.materials.append(mat)
            acMat = bpy.context.object.active_material
            acMat.diffuse_color = self.nameColor
            acMat.diffuse_intensity = .6
            acMat.specular_color = (1, 1, 1)
            acMat.specular_intensity = 1
            acMat.emit = 0.35


###### Chart class
class Chart:
    def __init__(self, pieces: List[ChartPiece] = []):
        self.__pieces = pieces

    def addPiece(self, piece: ChartPiece) -> 'Chart':
        self.__pieces.append(piece)
        return self

    def draw(self):
        for piece in self.__pieces:
            piece.draw()


def drawChart(data):
    total = sum([pieceData['count'] for pieceData in data])
    chart = Chart()
    piece = None
    for pieceData in data:
        offset = piece.offset + piece.angle if piece else 0
        angle = pieceData['count'] * 360 / total
        piece = ChartPiece(offset=offset, angle=angle, name=pieceData['name'], nameColor=PIECE_NAME_COLOR, color=pieceData['color'], maxDynamicHeight = MAX_DYNAMIC_PIECE_HEIGHT)
        chart.addPiece(piece)

    chart.draw()


###### Create path follow animation
def createAnimation(fixLamp = False):
    bpy.context.scene.frame_end = ANIMATION_FRAME_COUNT

    cam = bpy.data.objects[CAM_NAME]
    r = math.sqrt(cam.location[0]**2 + cam.location[1]**2)
    bpy.ops.curve.primitive_bezier_circle_add(radius=r, location=(0, 0, cam.location[2]))
    path = bpy.context.object
    path.name = CAM_PATH_NAME
    bpy.context.object.data.path_duration = ANIMATION_FRAME_COUNT

    bpy.ops.object.select_all(action='DESELECT')
    cam.select = True

    if not fixLamp:
        light = bpy.data.objects[LIGHT_NAME]
        light.select = True

    path.select = True

    cam.parent = path
    bpy.ops.object.parent_set(type='FOLLOW')
    bpy.ops.object.select_all(action='DESELECT')


def main():
    clearScene()
    drawChart(DATA)
    prepareScene()
    createAnimation(fixLamp = FIX_LAMP)


if __name__ == "__main__":
    main()
