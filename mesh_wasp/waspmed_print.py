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


class waspmed_print_panel(bpy.types.Panel):
#class waspmed_scan_panel(, bpy.types.View3DPaintPanel):
    bl_label = "Print"
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
            return status == 6 and is_mesh and not context.object.hide
        except: return False

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Utils:")
        col.operator("view3d.ruler", text="Ruler", icon="ARROW_LEFTRIGHT")
        col.separator()
        col.operator("screen.region_quadview", text="Toggle Quad View", icon='SPLITSCREEN')
        col.separator()
        row = col.row(align=True)
        row.operator("ed.undo", icon='LOOP_BACK')
        row.operator("ed.redo", icon='LOOP_FORWARDS')


def register():
    bpy.utils.register_class(waspmed_print_panel)


def unregister():
    bpy.utils.unregister_class(waspmed_print_panel)


if __name__ == "__main__":
    register()
