# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
from mathutils import Vector
import numpy as np
from math import sqrt, radians
import random

status_list = ["scan", "remesh", "sculpt", "deform", "crop", "generate", "print"]

#def store_parameters(operator, ob):
#    ob.tissue_tessellate.generator = operator.generator
#    return ob

def update_smooth(self, context):
    ob = context.object
    try:
        mod = ob.modifiers["CorrectiveSmooth"]
    except:
        ob.modifiers.new(type='CORRECTIVE_SMOOTH', name="CorrectiveSmooth")
        mod = ob.modifiers["CorrectiveSmooth"]
        bpy.ops.object.modifier_move_up(modifier = mod.name)
    mod.vertex_group = "Smooth"
    mod.invert_vertex_group = True
    mod.use_only_smooth = True
    mod.use_pin_boundary = True
    mod.iterations = ob.waspmed_prop.smooth_iterations
    mod.factor = 1
    mod.show_viewport = ob.waspmed_prop.bool_smooth


def update_trim_bottom(self, context):
    if True:
        margin = 10
        ob = context.object
        if ob.waspmed_prop.status < 6: return
        min_x, min_y, min_z = max_x, max_y, max_z = ob.matrix_world * ob.data.vertices[0].co
        init_z = True
        for v in ob.data.vertices:
            # store vertex world coordinates
            world_co = ob.matrix_world * v.co
            min_x = min(min_x, world_co[0])-margin
            min_y = min(min_y, world_co[1])-margin
            max_x = max(max_x, world_co[0])+margin
            max_y = max(max_y, world_co[1])+margin
            try:
                if ob.vertex_groups["Smooth"].weight(v.index) > 0.5:
                    if init_z:
                        min_z = max_z = world_co[2]
                        init_z = False
                    else:
                        min_z = min(min_z, world_co[2])
                        max_z = max(max_z, world_co[2])
            except:
                pass
        loc = (
            (min_x + max_x)/2,
            (min_y + max_y)/2,
            (min_z + max_z)/2,
            )
        try:
            box = bpy.data.objects["Crop_Box"]
            box.location = loc
        except:
            bpy.ops.mesh.primitive_cube_add(location=loc,
                radius = max(max_x - min_x, max_y - min_y)/2 + 2)
            box = bpy.context.object
        box.dimensions[2] = max_z - min_z + ob.waspmed_prop.trim_bottom*2
        box.name = "Crop_Box"
        bpy.context.scene.objects.active = ob
        ob.select = True
        box.draw_type = 'WIRE'
        box.parent = ob
        box.hide_select = True
        box.select = False
        try:
            mod = ob.modifiers["Crop"]
        except:
            ob.modifiers.new(type="BOOLEAN", name="Crop")
            mod = ob.modifiers["Crop"]
        mod.object = box
        mod.operation = 'INTERSECT'
        mod.solver = 'CARVE'
        if ob.waspmed_prop.bool_trim_bottom:
            mod.show_viewport = False
            context.scene.update()
        mod.show_viewport = ob.waspmed_prop.bool_trim_bottom

    #except:
    #    pass

def update_thickness(self, context):
    try:
        ob = bpy.context.object
        mod = ob.modifiers['Solidify']
        min_t = ob.waspmed_prop.min_thickness
        max_t = ob.waspmed_prop.max_thickness
        if min_t == 0:
            ob.modifiers['Mask'].vertex_group = "Smooth"
            ob.modifiers['Mask'].show_viewport = True
            ob.modifiers["Mask"].show_render = True
        else:
            ob.modifiers['Mask'].show_viewport = False
            ob.modifiers["Mask"].show_render = False
        mod.thickness = max_t
        mod.thickness_vertex_group = min_t / max_t
        mod.use_even_offset = True
    except:
        pass

def update_crop(self, context):
    try:
        bpy.ops.object.crop_geometry()
    except:
        pass

class waspmed_object_prop(bpy.types.PropertyGroup):
    patientID = bpy.props.StringProperty()
    status = bpy.props.IntProperty(default=0)
    zscale = bpy.props.FloatProperty(default=1)
    merge = bpy.props.BoolProperty()
    min_thickness = bpy.props.FloatProperty(
        name="Min", default=3, min=0.0, soft_max=10,
        description="Max Thickness",
        unit = 'LENGTH',
        update = update_thickness
        )
    max_thickness = bpy.props.FloatProperty(
        name="Max", default=6, min=0.01, soft_max=10,
        description="Max Thickness",
        unit = 'LENGTH',
        update = update_thickness
        )
    bool_trim_bottom = bpy.props.BoolProperty(
        name = "Trim",
        description = "Create a flat bottom",
        default = False,
        update = update_trim_bottom
        )
    trim_bottom = bpy.props.FloatProperty(
        name="Distance", default=5, min=0.01, soft_max=50,
        description="Trim distance for the bottom",
        unit = 'LENGTH',
        update = update_trim_bottom
        )
    bool_smooth = bpy.props.BoolProperty(
        name = "Smooth",
        description = "Smooth body",
        default = False,
        update = update_smooth
        )
    smooth_iterations = bpy.props.IntProperty(
        name="Iterations", default=100, min=0, soft_max=1000,
        description="Corrective Smooth Iterations",
        update = update_smooth
        )
    plane_cap = bpy.props.BoolProperty(
        name="Cap", default=False,
        description="Fill the section area",
        update = update_crop
        )




class waspmed_scene_prop(bpy.types.PropertyGroup):
    do_setup = bpy.props.BoolProperty(default=True)

class cap_holes(bpy.types.Operator):
    bl_idname = "mesh.cap_holes"
    bl_label = "Cap Holes"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try: return not context.object.hide
        except: return False

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_non_manifold(
            extend=False, use_wire=False, use_multi_face=False,
            use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.quads_convert_to_tris(
            quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


class waspmed_next(bpy.types.Operator):
    bl_idname = "object.waspmed_next"
    bl_label = "Next"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            ob = context.object
            if ob.type != 'MESH' and ob.parent != None:
                ob = ob.parent
            if ob.type == 'MESH' and ob.waspmed_prop.status < len(status_list)-1:
                return True
            else: return False
        except:
            return False

    def execute(self, context):
        old_ob = context.object

        bpy.ops.object.mode_set(mode='OBJECT')

        # if crop planes are selected
        if old_ob.waspmed_prop.status == 4 and old_ob.parent != None:
            old_ob.hide = True
            old_ob.select = False
            old_ob = old_ob.parent
            context.scene.objects.active = old_ob

        if old_ob.type != 'MESH' and old_ob.parent != None:
            old_ob.hide = True
            old_ob.select = False
            old_ob = old_ob.parent
            context.scene.objects.active = old_ob

        old_ob.hide = False
        bpy.ops.object.mode_set(mode='OBJECT')

        init_object = False
        if old_ob.waspmed_prop.patientID == "":
            init_object = True
            old_ob.waspmed_prop.patientID = old_ob.name
        status = old_ob.waspmed_prop.status
        patientID = old_ob.waspmed_prop.patientID

        ob = None
        # check for existing nex step and eventually delete them
        for o in bpy.data.objects:
            if o.waspmed_prop.patientID == patientID and status+1 == o.waspmed_prop.status:
                if status+1 != 3:
                    for child in o.children: bpy.data.objects.remove(child)
                    bpy.data.objects.remove(o)
                else:
                    for child in o.children: child.hide = False
                    o.data = old_ob.data
                    context.scene.objects.active = o
                    o.select = True
                    o.hide = False
                    ob = o

        # generate new next status
        new_ob = ob
        if ob == None:
            ob = context.object
            ob.select = True
            context.scene.objects.active = ob
            old_status = status_list[status]
            next_status = status_list[status+1]
            if status == 0 and init_object:
                ob.name = "00_" + patientID + "_" + old_status
            if status == 5:
                bpy.ops.object.weight_thickness()
                new_ob = context.object
                update_smooth(new_ob, context)
                new_ob.modifiers.new(type='MASK', name="Mask")
                bpy.ops.object.modifier_move_up(modifier = "Mask")
                #new_ob.modifiers["Mask"].vertex_group = "Smooth"

                #new_ob.modifiers.new(type='CORRECTIVE_SMOOTH', name="CorrectiveSmooth")
                #bpy.ops.object.modifier_move_up(modifier = new_ob.modifiers[-1].name)
                new_ob.modifiers.new(type="BOOLEAN", name="Crop")

                bpy.context.object.waspmed_prop.patientID = patientID
            else:
                bpy.ops.object.duplicate_move()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            new_ob = context.object
            new_ob.waspmed_prop.status = status + 1
            new_ob.name = str(status+1).zfill(2) + "_" + patientID + "_" + next_status
        for o in bpy.data.objects:
            if o != new_ob and o not in new_ob.children: o.hide = True

        # change mode
        if new_ob.waspmed_prop.status == 2:
            bpy.ops.object.mode_set(mode='SCULPT')
            bpy.context.scene.tool_settings.sculpt.use_symmetry_x = False
        elif new_ob.waspmed_prop.status == 5:
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        else: bpy.ops.object.mode_set(mode='OBJECT')

        if status != 5:
            for vg in new_ob.vertex_groups: new_ob.vertex_groups.remove(vg)
            for mod in new_ob.modifiers:
                #new_ob.modifiers.remove(mod)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
        return {'FINISHED'}

class waspmed_back(bpy.types.Operator):
    bl_idname = "object.waspmed_back"
    bl_label = "Back"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            visible = context.object.waspmed_prop.status > 0
            if not visible:
                try: visible = context.object.parent.waspmed_prop.status > 0
                except: pass
            return visible
        except: return False

    def execute(self, context):
        ob = context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        if ob.type == 'LATTICE':
            try:
                ob.hide = True
                ob = context.object.parent
            except:
                return {'FINISHED'}
        patientID = ob.waspmed_prop.patientID
        status = ob.waspmed_prop.status - 1
        for o in bpy.data.objects:
            if o.waspmed_prop.patientID == patientID and status == o.waspmed_prop.status:
                bpy.context.scene.objects.active = o
                o.select = True
                o.hide = False
                ob = o
                if o.waspmed_prop.status == 2:
                    bpy.ops.object.mode_set(mode='SCULPT')
                elif o.waspmed_prop.status == 5:
                    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
                else: bpy.ops.object.mode_set(mode='OBJECT')
            else:
                o.select = False
                o.hide = True
            for child in ob.children: child.hide = False

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        if context.object.waspmed_prop.status != 3:
            col.label("This will delete changes to the model.", icon="ERROR")
            col.label("Do you want to continue?")

    def invoke(self, context, event):
        if context.object.waspmed_prop.status == 3:
            return self.execute(context)
        #return context.window_manager.invoke_confirm(self, event)
        else: return context.window_manager.invoke_props_dialog(self)

class rebuild_mesh(bpy.types.Operator):
    bl_idname = "object.rebuild_mesh"
    bl_label = "Rebuild Mesh"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    detail = bpy.props.IntProperty(
        name="Detail", default=7, soft_min=3, soft_max=10,
        description="Octree Depth")

    @classmethod
    def poll(cls, context):
        try: return not context.object.hide
        except: return False

    def execute(self, context):
        '''
        ob = context.object
        patientID = ob.waspmed_prop.patientID
        status = ob.waspmed_prop.status
        if status > 0:
            for o in bpy.data.objects:
                if o.waspmed_prop.patientID == patientID:
                    if o.waspmed_prop.status == 0:
                        o.hide = False
                        o.select = True
                        context.scene.objects.active = o
        '''
        bpy.ops.object.waspmed_back()
        bpy.ops.object.waspmed_next()

        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].mode = 'SMOOTH'
        bpy.context.object.modifiers["Remesh"].octree_depth = self.detail
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")
        return {'FINISHED'}


class auto_origin(bpy.types.Operator):
    bl_idname = "object.auto_origin"
    bl_label = "Center Model"
    bl_description = ("Center the 3D model automatically")
    bl_options = {'REGISTER', 'UNDO'}

    rotx = bpy.props.FloatProperty(
        name="Rotation X", default=90, soft_min=-180, soft_max=180,
        description="Rotation X")
    roty = bpy.props.FloatProperty(
        name="Rotation Y", default=0.00, soft_min=-180, soft_max=180,
        description="Rotation Y")
    rotz = bpy.props.FloatProperty(
        name="Rotation Z", default=-45.00, soft_min=-180, soft_max=180,
        description="Rotation Z")

    @classmethod
    def poll(cls, context):
        try: return not context.object.hide
        except: return False

    def execute(self, context):
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
        bpy.ops.object.location_clear(clear_delta=False)
        bpy.ops.view3d.view_selected(use_all_regions=False)
        rx = radians(self.rotx)
        ry = radians(self.roty)
        rz = radians(self.rotz)
        ob = context.object
        ob.rotation_euler = (rx, ry, rz)
        #ob.waspmed_prop.patientID = ob.name
        return {'FINISHED'}


def delete_all():
    for o in bpy.data.objects:
        bpy.data.objects.remove(o)

def set_mm():
    for s in bpy.data.screens:
        for a in s.areas:
            if a.type == 'OUTLINER':
                a.spaces[0].display_mode = 'VISIBLE_LAYERS'
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.001
    bpy.context.space_data.lens = 50
    bpy.context.space_data.clip_start = 1
    bpy.context.space_data.clip_end = 1e+006

def set_clipping_planes():
    bpy.context.space_data.lens = 50
    bpy.context.space_data.clip_start = 1
    bpy.context.space_data.clip_end = 1e+006

class check_differences(bpy.types.Operator):
    bl_idname = "object.check_differences"
    bl_label = "Check Differences"
    bl_description = ("Check the differences with the original model")
    bl_options = {'REGISTER', 'UNDO'}

    max_dist = bpy.props.FloatProperty(
        name="Max Distance (mm)", default=5, soft_min=0, soft_max=50,
        description="Max Distance")

    @classmethod
    def poll(cls, context):
        try: return context.object.waspmed_prop.status != 0
        except: return False

    def execute(self, context):
        ob = context.object
        patientID = ob.waspmed_prop.patientID
        status = ob.waspmed_prop.status
        try:
            vg = ob.vertex_groups["Proximity"]
        except:
            vg = ob.vertex_groups.new(name="Proximity")
        for i in range(len(ob.data.vertices)):
            vg.add([i], 1, 'ADD')
        mod = None
        for m in ob.modifiers:
            if m.type == "VERTEX_WEIGHT_PROXIMITY":
                mod = m
        if mod == None: mod = ob.modifiers.new(
                                name="Differences",
                                type="VERTEX_WEIGHT_PROXIMITY"
                                )
        mod.vertex_group = vg.name
        mod.max_dist = self.max_dist
        for o in bpy.data.objects:
            o_patientID = o.waspmed_prop.patientID
            o_status = o.waspmed_prop.status
            if o_patientID == patientID and o_status == 0:
                mod.target = o
        if mod.target == None:
            self.report({'ERROR'}, "Can't find original scan model")
            return {'CANCELLED'}
        mod.proximity_mode = 'GEOMETRY'
        mod.proximity_geometry = {'FACE'}
        bpy.ops.paint.weight_paint_toggle()
        if context.mode == 'OBJECT' and status == 2:
            bpy.ops.object.mode_set(mode='SCULPT')
        return {'FINISHED'}



class wasp_setup(bpy.types.Operator):
    bl_idname = "scene.wasp_setup"
    bl_label = "Setup"
    bl_description = ("Reset the scene")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        delete_all()
        set_mm()
        set_clipping_planes()
        context.scene.waspmed_prop.do_setup = False
        return {'FINISHED'}

### Sculpt Tools ###
from bl_ui.properties_paint_common import (
        UnifiedPaintPanel,
        brush_texture_settings,
        brush_texpaint_common,
        brush_mask_texture_settings,
        )

class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

class View3DPaintPanel(UnifiedPaintPanel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

### END Sculpt Tools ###


class waspmed_progress_panel(View3DPaintPanel, bpy.types.Panel):
#class waspmed_scan_panel(, bpy.types.View3DPaintPanel):
    bl_label = "Waspmed Progress"
    bl_category = "Waspmed"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_options = {}
    #bl_context = "objectmode"

    '''
    @classmethod
    def poll(cls, context):
        try: return context.object.waspmed_prop.status == 0
        except: return False
    '''
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        if context.scene.waspmed_prop.do_setup:
            col.operator("scene.wasp_setup", icon="NEW", text="Start")
            col.separator()
        try: col.label(text="" + context.object.waspmed_prop.patientID,
            icon="ARMATURE_DATA")
        except: col.label(text="Import new Patient",
            icon="INFO")
        col.separator()
        row = col.row(align=True)
        row.operator("object.waspmed_back", icon='BACK')#, text="")
        if context.object != None:
            if context.object.waspmed_prop.status == 6:
                row.operator("export_mesh.stl", icon='EXPORT')#, text="")
            else:
                row.operator("object.waspmed_next", icon='FORWARD')#, text="")

class waspmed_scan_panel(View3DPaintPanel, bpy.types.Panel):
#class waspmed_scan_panel(, bpy.types.View3DPaintPanel):
    bl_label = "3D Scan"
    bl_category = "Waspmed"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_options = {}
    #bl_context = "objectmode"


    @classmethod
    def poll(cls, context):
        try:
            ob = context.object
            status = ob.waspmed_prop.status
            is_mesh = ob.type == 'MESH'
            return (status < 2 and is_mesh) and not context.object.hide
        except: return True


    def draw(self, context):
        try:
            status = context.object.waspmed_prop.status
        except:
            status = 0
        layout = self.layout
        col = layout.column(align=True)

        if status != 1:
            col.label(text="Import Patient:", icon="OUTLINER_OB_ARMATURE")
            row = col.row(align=True)
            row.operator("import_scene.obj", text="OBJ")
            row.operator("import_mesh.stl", text="STL")
            col.separator()
            col.operator("object.auto_origin", icon='BBOX')
            col.separator()
        #col.label(text="Fix model", icon='ZOOM_SELECTED')
        #col.operator("mesh.cap_holes", text="Cap Holes")
        if status == 1:
            col.operator("object.rebuild_mesh", icon="MOD_REMESH", text="Auto Remesh")
            col.separator()
        '''
        try:
            settings = self.paint_settings(context)
            col.template_ID_preview(settings, "brush", rows=3, cols=8)
            brush = settings.brush
            self.prop_unified_size(col, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_strength(col, context, brush, "strength", text="Strength")
        except: pass
        '''
        #col.template_preview(bpy.data.textures['.hidden'], show_buttons=False)
        col.separator()


        box = layout.box()
        col = box.column(align=True)
        #col.label(text="Utils:")
        col.operator("view3d.ruler", text="Ruler", icon="ARROW_LEFTRIGHT")
        col.separator()
        if context.mode == 'PAINT_WEIGHT':
            col.operator("object.check_differences",
                            icon="ZOOM_SELECTED",
                            text="Check Differences Off")
        else:
            col.operator("object.check_differences",
                            icon="ZOOM_SELECTED",
                            text="Check Differences On")
        col.separator()
        col.operator("screen.region_quadview", text="Toggle Quad View", icon='SPLITSCREEN')
        col.separator()
        row = col.row(align=True)
        row.operator("ed.undo", icon='LOOP_BACK')
        row.operator("ed.redo", icon='LOOP_FORWARDS')

def register():
    bpy.utils.register_class(waspmed_prop)
    bpy.utils.register_class(waspmed_progress_panel)
    bpy.utils.register_class(waspmed_scan_panel)
    bpy.utils.register_class(scene.wasp_setup)
    bpy.utils.register_class(object.auto_origin)
    bpy.utils.register_class(object.rebuild_mesh)
    bpy.utils.register_class(mesh.cap_holes)
    bpy.utils.register_class(object.waspmed_next)
    bpy.utils.register_class(object.waspmed_back)
    bpy.utils.register_class(check_differences)


def unregister():
    bpy.utils.unregister_class(waspmed_object_prop)
    bpy.utils.unregister_class(waspmed_scene_prop)
    bpy.utils.unregister_class(waspmed_scan_panel)
    bpy.utils.unregister_class(waspmed_progress_panel)
    bpy.utils.unregister_class(wasp_setup)
    bpy.utils.unregister_class(auto_origin)
    bpy.utils.unregister_class(rebuild_mesh)
    bpy.utils.unregister_class(cap_holes)
    bpy.utils.unregister_class(waspmed_next)
    bpy.utils.unregister_class(waspmed_back)
    bpy.utils.unregister_class(check_differences)


if __name__ == "__main__":
    register()
