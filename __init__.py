import bpy
import numpy as np

bl_info = {
    "name": "Master Shapeshifter",
    "author": "00004707",
    "version": (0, 0, 1),
    "blender": (3, 1, 0),
    "location": "Properties Panel > Data Properties > Shape Keys",
    "description": "Extra tools to control shape keys",
    "warning": "",
    "doc_url": "",
    "category": "Interface",
    "support": "COMMUNITY",
    "tracker_url": "",
}


def get_mesh_selected_domain_indexes(obj, domain, spill=False):
    """Gets the indexes of selected domain entries in edit mode. (Vertices, edges, faces or Face Corners)

    Args:
        obj (Reference): 3D Object Reference
        domain (str): Mesh Domain
        spill (bool, optional): Enables selection spilling to nearby face corners from selected verts/faces/edges. Defaults to False.

    Raises:
        etc.MeshDataReadException: If domain is unsupported

    Returns:
        list: List of indexes
    """

    if domain == 'POINT': 
        storage = np.zeros(len(obj.data.vertices), dtype=bool)
        obj.data.vertices.foreach_get('select', storage)
        return np.arange(0, len(obj.data.vertices))[storage]
    
    elif domain == 'EDGE': 
        storage = np.zeros(len(obj.data.edges), dtype=bool)
        obj.data.edges.foreach_get('select', storage)
        return np.arange(0, len(obj.data.edges))[storage]
    
    elif domain == 'FACE': 
        storage = np.zeros(len(obj.data.polygons), dtype=bool)
        obj.data.polygons.foreach_get('select', storage)
        return np.arange(0, len(obj.data.polygons))[storage]


SOLO_SHAPEKEY_TIMER_REF = None

def gui_shapekeys_menu(self, context):
    col = self.layout.column()
    row = col.row(align=False)
    row.operator('object.shape_key_insert')
    
    col.label(text="Solo")
    solo_row = col.row(align=True)
    global SOLO_SHAPEKEY_TIMER_REF
    sr = solo_row.row(align=True)
    sr.enabled = SOLO_SHAPEKEY_TIMER_REF is None
    sr.operator('object.shape_key_active_solo')
    
    
    sr = solo_row.row(align=True)
    sr.alert = SOLO_SHAPEKEY_TIMER_REF is not None
    sr.operator('object.shape_key_active_solo_automatic', text= "Autosolo ON" if SOLO_SHAPEKEY_TIMER_REF is not None else "Autosolo OFF")
    
    
    
    col.label(text="Update Position From Selected")
    row = col.row(align=False)
    
    replace_row = col.row(align=True)
    sr = replace_row.row(align=True)
    x = sr.operator('object.shape_key_position_update', text="Replace Lower")
    x.b_higher = False
    
    sr = replace_row.row(align=True)
    x = sr.operator('object.shape_key_position_update', text="Replace Higher")
    x.b_higher = True
    
    global ED_WD_LAST_OBJ
    col.label(text="Auto Toggle Absolute")
    absolute_toggle_row = col.row(align=True)
    sr = absolute_toggle_row.row(align=True)
    sr.alert = ED_WD_LAST_OBJ is not None
    sr.operator('object.shape_key_absolute_mode_watchdog', text= "AutoAbsolute ON" if ED_WD_LAST_OBJ is not None else "AutoAbsolute OFF")
    
    col.label(text="Utility")
    sr = col.row()
    sr.operator('object.shape_key_name_set_to_id')
    
    col.label(text="Utility")
    sr = col.row(align=True)
    sr.operator('object.shape_key_toggle_lower')
    sr.operator('object.shape_key_toggle_higher')
    
    
    
    
    
def solo_active_shape_key():
    obj = bpy.context.active_object
    for some_sk in obj.data.shape_keys.key_blocks:
        if some_sk.name == obj.active_shape_key.name:
            some_sk.value = 1.0
        else:
            some_sk.value = 0.0


class InsertNewShapeKey(bpy.types.Operator):
    bl_label = 'Insert'
    bl_idname = 'object.shape_key_insert'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Inserts a new shape key above current and enables solo"
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        
        obj = bpy.context.active_object
        mode = obj.mode
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        

        sk = obj.shape_key_add(name="Shape Key", from_mix=True)

        sk_id = obj.data.shape_keys.key_blocks.find(sk.name)

        if obj.active_shape_key_index +1 < sk_id:
            times = sk_id - obj.active_shape_key_index -1
            print(times)
            obj.active_shape_key_index = sk_id
            for i in range(0, times):
                bpy.ops.object.shape_key_move(type='UP')
            
            sk_id = obj.data.shape_keys.key_blocks.find(sk.name)
            

        for some_sk in obj.data.shape_keys.key_blocks:
            if some_sk.name == sk.name:
                some_sk.value = 1.0
            else:
                some_sk.value = 0.0
                
                
                
        obj.active_shape_key_index = sk_id

        bpy.ops.object.shape_key_retime()
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}

class SoloActiveShapeKey(bpy.types.Operator):
    bl_label = 'Solo'
    bl_idname = 'object.shape_key_active_solo'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sets the weight of active shape key to 1.0 and others to 0.0"

    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        solo_active_shape_key()
        return {'FINISHED'}

def solo_every_second():
    obj = bpy.context.active_object
    if obj is None or not len(obj.data.shape_keys.key_blocks):
        return
    
    solo_active_shape_key()
    return 0.1

class AutoSoloActiveShapeKey(bpy.types.Operator):
    bl_label = 'Autosolo'
    bl_idname = 'object.shape_key_active_solo_automatic'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sets the weight of active shape key to 1.0 and others to 0.0"

    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        global SOLO_SHAPEKEY_TIMER_REF
        if SOLO_SHAPEKEY_TIMER_REF is None: 
            SOLO_SHAPEKEY_TIMER_REF = True
            bpy.app.timers.register(solo_every_second)
        else:
            SOLO_SHAPEKEY_TIMER_REF = None
            bpy.app.timers.unregister(solo_every_second)
            
        return {'FINISHED'}

class UpdateHigherShapeKeys(bpy.types.Operator):
    bl_label = 'Update Pos'
    bl_idname = 'object.shape_key_position_update'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Replaces position of selected vertices in higher/lower shape keys"
    
    b_higher: bpy.props.BoolProperty(name="Higher", default=True)
    #b_relative: bpy.props.BoolProperty(name="Higher", default=False)
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        obj = bpy.context.active_object
        sk_id = obj.active_shape_key_index

        mode = obj.mode
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
                    
        if self.b_higher:
            min_sk_id = sk_id+1
            max_sk_id = len(obj.data.shape_keys.key_blocks)
        else:
            min_sk_id = 1
            max_sk_id = sk_id
        
        v_pos_storage = np.zeros(len(obj.data.shape_keys.key_blocks[sk_id].data)*3, dtype=float)
        v_pos = obj.data.shape_keys.key_blocks[sk_id].data.foreach_get('co', v_pos_storage)
        
        selected_vert_ids = get_mesh_selected_domain_indexes(obj, 'POINT')
        print(selected_vert_ids)
        
        indices_to_replace = []
        for i in selected_vert_ids:
            for j in range(0,3):
                indices_to_replace +=[i*3+j]
                
        print(indices_to_replace)
        print(v_pos_storage)
        for i in range(min_sk_id, max_sk_id):
            print("source")
            print(v_pos_storage)
            
            v_pos_storage_higher = np.zeros(len(obj.data.shape_keys.key_blocks[i].data)*3, dtype=float)
            obj.data.shape_keys.key_blocks[i].data.foreach_get('co', v_pos_storage_higher)
            print("pre-replace")
            print(v_pos_storage_higher)
            
            print(indices_to_replace)
            
            np.put(v_pos_storage_higher, indices_to_replace, np.take(v_pos_storage, indices_to_replace))
            
            print("pre-write read")
            print(v_pos_storage_higher)
            obj.data.shape_keys.key_blocks[i].data.foreach_set('co', v_pos_storage_higher)
            
            print("post read")
            obj.data.shape_keys.key_blocks[i].data.foreach_get('co', v_pos_storage_higher)
            print(v_pos_storage_higher)

        obj.data.update()
        
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}

class RenameShapeKeysToIndex(bpy.types.Operator):
    bl_label = 'Rename to index'
    bl_idname = 'object.shape_key_name_set_to_id'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Renames shape keys to index"
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        obj = bpy.context.active_object
        for i, some_sk in enumerate(obj.data.shape_keys.key_blocks):
            if i == 0:
                some_sk.name = "Basis"
            else:
                some_sk.name = f"Key {i}"
        return {'FINISHED'}

class ToggleToHigherShapeKey(bpy.types.Operator):
    bl_label = 'Toggle To Higher Shape Key'
    bl_idname = 'object.shape_key_toggle_higher'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        obj = bpy.context.active_object
        if obj.active_shape_key_index +1 < len(obj.data.shape_keys.key_blocks):
            obj.active_shape_key_index = obj.active_shape_key_index +1
            return bpy.ops.object.shape_key_active_solo()
        else:
            return bpy.ops.object.shape_key_insert()

class ToggleToLowerShapeKey(bpy.types.Operator):
    bl_label = 'Toggle To Lower Shape Key'
    bl_idname = 'object.shape_key_toggle_lower'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""
    
    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        obj = bpy.context.active_object
        if obj.active_shape_key_index > 0:
            obj.active_shape_key_index = obj.active_shape_key_index -1
            return bpy.ops.object.shape_key_active_solo()
        return {'FINISHED'}

ED_WD_LAST_OBJ = None

def edit_mode_watchdog():
    obj = bpy.context.active_object

        
    global ED_WD_LAST_OBJ
    if obj != ED_WD_LAST_OBJ:
        ED_WD_LAST_OBJ = None
        return
    obj.data.shape_keys.use_relative = obj.mode != 'OBJECT'
    return 0.1

class AbsoluteEditmodeWatchdog(bpy.types.Operator):
    bl_label = 'Edit Watchdog'
    bl_idname = 'object.shape_key_absolute_mode_watchdog'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Preview absolute frames in object mode and relative in edit mode"

    @classmethod
    def poll(self, context):
        return True
    
    def execute(self, context): 
        global ED_WD_LAST_OBJ
        if ED_WD_LAST_OBJ is not None: 
            try:
                bpy.app.timers.unregister(edit_mode_watchdog)   
            except ValueError:
                pass
                
            ED_WD_LAST_OBJ = None
        else:
            ED_WD_LAST_OBJ = bpy.context.active_object
            bpy.app.timers.register(edit_mode_watchdog)
            
        return {'FINISHED'}


class ShapeKeyFloatingMenu(bpy.types.Operator):
    bl_label = 'Shape Keys Floating Menu'
    bl_idname = 'object.shape_key_floating_menu_open'
    bl_options = {'REGISTER'}
    bl_description = "Shows floating menu of shape keys"
    
    # Width of the message box
    width: bpy.props.IntProperty(default=400)
    
    # trick to make the dialog box open once and not again after pressing ok
    times = 0
    
    
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    @classmethod
    def poll(cls, context):
        engine = context.engine
        obj = context.object
        return (obj and obj.type in {'MESH', 'LATTICE', 'CURVE', 'SURFACE'} and (engine in cls.COMPAT_ENGINES))
    
    def execute(self, context):
        self.times += 1
        if self.times < 2:
            return context.window_manager.invoke_props_dialog(self, width=self.width)
        return {'FINISHED'}
    
    draw = bpy.types.DATA_PT_shape_keys.draw
    #def draw(self, context):
        #data.types.DATA_PT_shape_keys.draw(self, context)
        

        

classes = [InsertNewShapeKey,
            SoloActiveShapeKey,
            AutoSoloActiveShapeKey,
            UpdateHigherShapeKeys,
            RenameShapeKeysToIndex,
            ShapeKeyFloatingMenu,
            ToggleToHigherShapeKey,
            ToggleToLowerShapeKey,
            AbsoluteEditmodeWatchdog
            ]

def register():
    bpy.types.DATA_PT_shape_keys.append(gui_shapekeys_menu)
    
    for c in classes:
        bpy.utils.register_class(c)
        
    


def unregister():
    bpy.types.DATA_PT_shape_keys.remove(gui_shapekeys_menu)
    for c in classes:
            bpy.utils.unregister_class(c)
    
    
    
if __name__ == "__main__":
    register()