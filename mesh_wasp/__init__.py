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

# -------------------------------- WASPmed ------------------------------------#
#-------------------------------- version 0.1 ---------------------------------#
#                                                                              #
#                                    WASP                                      #
#                                   (2018)                                     #
#                                                                              #
# http://http://www.wasproject.it/                                             #
#                                                                              #
################################################################################


if "bpy" in locals():
    import importlib
    importlib.reload(waspmed_scan)
    importlib.reload(waspmed_sculpt)
    importlib.reload(waspmed_generate)
    importlib.reload(waspmed_deform)
    importlib.reload(waspmed_crop)
    importlib.reload(waspmed_generate)
    importlib.reload(waspmed_print)

else:
    from . import waspmed_scan
    from . import waspmed_sculpt
    from . import waspmed_generate
    from . import waspmed_deform
    from . import waspmed_crop
    from . import waspmed_generate
    from . import waspmed_print

import bpy

bl_info = {
	"name": "Waspmed",
	"author": "WASP",
	"version": (0, 0, 1),
	"blender": (2, 7, 9),
	"location": "",
	"description": "Tools for medical devices",
	"warning": "",
	"wiki_url": (""),
	"tracker_url": "",
	"category": "Mesh"}


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.waspmed_prop = bpy.props.PointerProperty(
        type=waspmed_scan.waspmed_object_prop)
    bpy.types.Scene.waspmed_prop = bpy.props.PointerProperty(
        type=waspmed_scan.waspmed_scene_prop)


def unregister():
    waspmed_scan.unregister()
    waspmed_sculpt.unregister()
    waspmed_generate.unregister()
    waspmed_deform.unregister()
    waspmed_crop.unregister()
    waspmed_generate.unregister()
    waspmed_print.unregister()


if __name__ == "__main__":
    register()
