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


import bpy, bmesh, timeit
from mathutils import Vector
import numpy as np
from math import sqrt, radians
import random


class iso_weight_knife(bpy.types.Operator):
    bl_idname = "object.iso_weight_knife"
    bl_label = "Iso Weight Knife"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    use_modifiers = bpy.props.BoolProperty(
        name="Use Modifiers", default=True,
        description="Apply all the modifiers")
    iso = bpy.props.FloatProperty(
        name="Iso Value", default=0.5, soft_min=0, soft_max=1,
        description="Threshold value")
    bool_mask = bpy.props.BoolProperty(
        name="Mask", default=True, description="Trim along isovalue")

    def execute(self, context):
        start_time = timeit.default_timer()
        ob0 = bpy.context.object

        iso_val = self.iso
        group_id = ob0.vertex_groups.active_index
        vertex_group_name = ob0.vertex_groups[group_id].name

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.use_modifiers: me0 = ob0.to_mesh(bpy.context.scene, apply_modifiers=True,
                                         settings = 'PREVIEW')
        else:
            me0 = ob0.data

        # generate new bmesh
        bm = bmesh.new()
        bm.from_mesh(me0)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()


        # store weight values
        weight = []
        ob = bpy.data.objects.new("temp", me0)
        for g in ob0.vertex_groups:
            ob.vertex_groups.new(name=g.name)
        for v in me0.vertices:
            try:
                #weight.append(v.groups[vertex_group_name].weight)
                weight.append(ob.vertex_groups[vertex_group_name].weight(v.index))
            except:
                weight.append(0)

        faces_mask = []
        for f in bm.faces:
            w_min = 2
            w_max = 2
            for v in f.verts:
                w = weight[v.index]
                if w_min == 2:
                    w_max = w_min = w
                if w > w_max: w_max = w
                if w < w_min: w_min = w
                if w_min < iso_val and w_max > iso_val:
                    faces_mask.append(f)
                    break
        print("selected faces:" + str(len(faces_mask)))

        #link_faces = [[f for f in e.link_faces] for e in bm.edges]

        filtered_edges = bm.edges# me0.edges
        faces_todo = [f.select for f in bm.faces]
        verts = []
        edges = []
        delete_edges = []
        delete_faces = []
        edges_id = {}
        _filtered_edges = []
        n_verts = len(bm.verts)
        count = n_verts
        for e in filtered_edges:
            #id0 = e.vertices[0]
            #id1 = e.vertices[1]
            id0 = e.verts[0].index
            id1 = e.verts[1].index
            w0 = weight[id0]
            w1 = weight[id1]

            #edges_id.append(str(id0)+"_"+str(id1))
            #edges_id[str(id0)+"_"+str(id1)] = e.index
            #edges_id[str(id1)+"_"+str(id0)] = e.index

            if w0 == w1: continue
            elif w0 > iso_val and w1 > iso_val:
                #_filtered_edges.append(e)
                continue
            elif w0 < iso_val and w1 < iso_val: continue
            elif w0 == iso_val or w1 == iso_val: continue
            else:
                #v0 = me0.vertices[id0].select = True
                #v1 = me0.vertices[id1].select = True
                v0 = me0.vertices[id0].co
                v1 = me0.vertices[id1].co
                v = v0.lerp(v1, (iso_val-w0)/(w1-w0))
                delete_edges.append(e)
                verts.append(v)
                edges_id[str(id0)+"_"+str(id1)] = count
                edges_id[str(id1)+"_"+str(id0)] = count
                count += 1
            #_filtered_edges.append(e)
        #filtered_edges = _filtered_edges
        print("creating faces")
        del_faces = []
        splitted_faces = []
        #count = 0
        print("new vertices: " + str(len(verts)))
        todo = 0
        for i in faces_todo: todo += i
        print("faces to split: " + str(todo))

        switch = False
        # splitting faces
        for f in faces_mask:
            # create sub-faces slots. Once a new vertex is reached it will
            # change slot, storing the next vertices for a new face.
            build_faces = [[],[]]
            #switch = False
            verts0 = list(me0.polygons[f.index].vertices)
            verts1 = list(verts0)
            verts1.append(verts1.pop(0)) # shift list
            for id0, id1 in zip(verts0, verts1):

                # add first vertex to active slot
                build_faces[switch].append(id0)

                # try to split edge
                try:
                    # check if the edge must be splitted
                    new_vert = edges_id[str(id0)+"_"+str(id1)]
                    # add new vertex
                    build_faces[switch].append(new_vert)
                    # if there is an open face on the other slot
                    if len(build_faces[not switch]) > 0:
                        # store actual face
                        splitted_faces.append(build_faces[switch])
                        # reset actual faces and switch
                        build_faces[switch] = []
                        # change face slot
                    switch = not switch
                    # continue previous face
                    build_faces[switch].append(new_vert)
                except: pass
            if len(build_faces[not switch]) == 2:
                build_faces[not switch].append(id0)
            elif len(build_faces[not switch]) > 2:
                splitted_faces.append(build_faces[not switch])
            # add last face
            splitted_faces.append(build_faces[switch])
            del_faces.append(f)

        print("generate new bmesh")
        # adding new vertices
        for v in verts: bm.verts.new(v)
        bm.verts.ensure_lookup_table()

        # deleting old edges/faces
        #bm.edges.ensure_lookup_table()
        #remove_edges = []
        #for i in delete_edges: remove_edges.append(bm.edges[i])
        #for e in delete_edges: bm.edges.remove(e)

        #bm.faces.ensure_lookup_table()
        #for f in del_faces:
        #    bm.faces.remove(f)

        bm.verts.ensure_lookup_table()
        # adding new faces
        missed_faces = []
        for f in splitted_faces:
            try:
                face_verts = [bm.verts[i] for i in f]
                bm.faces.new(face_verts)
            except:
                missed_faces.append(f)
        print("missed " + str(len(missed_faces)) + " faces")

        select_verts = []
        all_weight = weight + [iso_val+0.0001]*len(verts)
        weight = []
        for w, v in zip(all_weight, bm.verts):
            if w < iso_val:
                select_verts.append(v.index)
            weight.append(w)
            #count = 0
            #remove_verts = []
            #for w in weight:
            #    if w < iso_val: remove_verts.append(bm.verts[count])
            #    count += 1
            #for v in remove_verts: bm.verts.remove(v)
        # Create mesh and object
        name = ob0.name + '_Shell'
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)

        # Link object to scene and make active
        scn = bpy.context.scene
        scn.objects.link(ob)
        scn.objects.active = ob
        ob.select = True
        ob0.select = False

        # generate new vertex group
        for g in ob0.vertex_groups:
            ob.vertex_groups.new(name=g.name)
        #ob.vertex_groups.new(name=vertex_group_name)

        print(len(select_verts))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='TOGGLE')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # delete faces
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for f in del_faces:
            ob.data.polygons[f.index].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        '''
        for i in select_verts:
            ob.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.extrude_region_move()
        bpy.ops.object.mode_set(mode='OBJECT')
        '''

        print("doing weight")
        all_weight = weight + [iso_val]*len(verts)
        mult = 1/(1-iso_val)
        for id in range(len(all_weight)):
            w = all_weight[id] >= iso_val #(all_weight[id]-iso_val)*mult
            try:
                ob.data.vertices[id].select = w
            except:
                pass
            ob.vertex_groups[vertex_group_name].add([id], w, 'REPLACE')
        print("weight done")
        #for id in range(len(weight), len(ob.data.vertices)):
        #    ob.vertex_groups[vertex_group_name].add([id], iso_val*0, 'ADD')


        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.extrude_region_move()
        bpy.ops.object.mode_set(mode='OBJECT')


        ob.vertex_groups.active_index = group_id

        # align new object
        ob.matrix_world = ob0.matrix_world
        ob.data.update()



        # mask
        if self.bool_mask and True:
            #ob.modifiers.new(type='VERTEX_WEIGHT_EDIT', name='Threshold')
            #ob.modifiers['Threshold'].vertex_group = vertex_group_name
            #ob.modifiers['Threshold'].use_remove = True
            #ob.modifiers['Threshold'].remove_threshold = iso_val
            #ob.modifiers.new(type='MASK', name='Mask')
            #ob.modifiers['Mask'].vertex_group = vertex_group_name
            ob.modifiers.new(type='SOLIDIFY', name='Solidify')
            ob.modifiers['Solidify'].thickness = 5
            ob.modifiers['Solidify'].offset = 0
            ob.modifiers["Solidify"].offset = 1

            #ob.modifiers['Solidify'].vertex_group = vertex_group_name

        #bpy.ops.paint.weight_paint_toggle()
        #bpy.context.space_data.viewport_shade = 'WIREFRAME'
        print("time: " + str(timeit.default_timer() - start_time))

        return {'FINISHED'}

class set_weight_paint(bpy.types.Operator):
    bl_idname = "object.set_weight_paint"
    bl_label = "Weight Paint"
    bl_description = ("")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
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

class waspmed_generate_panel(View3DPaintPanel, bpy.types.Panel):
    bl_label = "Generate"
    bl_category = "Waspmed"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_options = {}
    #bl_context = "objectmode"

    #@classmethod
    #def poll(cls, context):
    #    return context.mode in {'OBJECT', 'EDIT_MESH'}

    @classmethod
    def poll(cls, context):
        try:
            ob = context.object
            status = ob.waspmed_prop.status
            is_mesh = ob.type == 'MESH'
            return status == 5 and is_mesh and not context.object.hide
        except: return False

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        if context.mode == 'PAINT_WEIGHT':
            settings = self.paint_settings(context)
            col.template_ID_preview(settings, "brush", rows=3, cols=8)
            brush = settings.brush
            col.separator()
            self.prop_unified_size(col, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_strength(col, context, brush, "strength", text="Strength")
        else:
            col.operator("object.set_weight_paint", icon="BRUSH_DATA")

        col.separator()
        col.operator("object.iso_weight_knife", icon="BRUSH_LAYER")

        col.label(text="Utils:")
        col.operator("view3d.ruler", text="Ruler", icon="ARROW_LEFTRIGHT")
        col.separator()
        col.operator("screen.region_quadview", text="Toggle Quad View", icon='SPLITSCREEN')
        col.separator()
        row = col.row(align=True)
        row.operator("ed.undo", icon='LOOP_BACK')
        row.operator("ed.redo", icon='LOOP_FORWARDS')

def register():
    bpy.utils.register_class(waspmed_generate_panel)
    bpy.utils.register_class(iso_weight_knife)
    bpy.utils.register_class(set_weight_paint)
    #bpy.utils.register_class(object.back)


def unregister():
    bpy.utils.unregister_class(waspmed_generate_panel)
    bpy.utils.unregister_class(iso_weight_knife)
    bpy.utils.unregister_class(set_weight_paint)
    #bpy.utils.unregister_class(back)


if __name__ == "__main__":
    register()
