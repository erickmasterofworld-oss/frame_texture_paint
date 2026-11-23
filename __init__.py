import bpy
import os
import re
import shutil
from bpy.app.handlers import persistent

bl_info = {
    "name": "Frame Texture Paint",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N-Panel > Frame Paint",
    "category": "Paint",
}

def sanitize_name(name):
    clean = re.sub(r'[^\w\-_]', '_', name)
    return clean.strip('_') or "seq"

def get_node_seq_dir(node, mat_name="Mat", create=True):
    if not bpy.data.filepath or not node:
        return None
    
    if "seq_folder" in node and node["seq_folder"].strip():
        raw_name = node["seq_folder"]
    else:
        raw_name = f"{sanitize_name(mat_name)}_{sanitize_name(node.name)}"
        # Записываем в ноду ТОЛЬКО если разрешено изменение данных (create=True)
        if create:
            node["seq_folder"] = raw_name

    folder_name = sanitize_name(raw_name)
    base_dir = os.path.dirname(bpy.data.filepath)
    seq_dir = os.path.join(base_dir, "tex_sequences", folder_name)
    
    if create:
        os.makedirs(seq_dir, exist_ok=True)
    return seq_dir


def get_active_tex_node(context):
    obj = context.view_layer.objects.active
    if not obj or not obj.active_material or not obj.active_material.use_nodes:
        return None, None
    nodes = obj.active_material.node_tree.nodes
    active = nodes.active
    if active and active.type == 'TEX_IMAGE':
        return active, obj.active_material.name
    return None, None

def get_bg_color(bg_mode):
    if bg_mode == 'WHITE':
        return (1.0, 1.0, 1.0, 1.0)
    elif bg_mode == 'BLACK':
        return (0.0, 0.0, 0.0, 1.0)
    return (0.0, 0.0, 0.0, 0.0)

def update_single_node(context, node, mat_name, create_new=False, duplicate=False):
    seq_dir = get_node_seq_dir(node, mat_name, create=create_new)
    if not seq_dir:
        return "Save your .blend file first!"

    folder_tag = sanitize_name(node["seq_folder"])
    frame = context.scene.frame_current
    disk_filename = f"frame_{frame:04d}.png"
    blender_img_name = f"{folder_tag}_{disk_filename}"
    target_path = os.path.join(seq_dir, disk_filename)

    if node.image and node.image.is_dirty:
        if node.image.filepath:
            abs_p = bpy.path.abspath(node.image.filepath)
            if os.path.exists(abs_p):
                node.image.save()

    if create_new:
        if duplicate and node.image and node.image.filepath:
            src_path = bpy.path.abspath(node.image.filepath)
            if os.path.exists(src_path):
                if os.path.normpath(src_path) != os.path.normpath(target_path):
                    shutil.copy2(src_path, target_path)
                
                existing = bpy.data.images.get(blender_img_name)
                if existing:
                    bpy.data.images.remove(existing)
                img = bpy.data.images.load(target_path)
                img.name = blender_img_name
            else:
                return "Source image file not found!"
        else:
            existing = bpy.data.images.get(blender_img_name)
            if existing:
                bpy.data.images.remove(existing)
            
            res = int(context.scene.fp_resolution)
            bg_col = get_bg_color(context.scene.fp_bg_color)
            
            img = bpy.data.images.new(name=blender_img_name, width=res, height=res, alpha=True)
            img.generated_color = bg_col
            img.filepath_raw = target_path
            img.file_format = 'PNG'
            img.save()
            img.filepath = target_path
            img.source = 'FILE'
            img.reload()

        node.image = img
        node["tex_key"] = frame
        node.keyframe_insert(data_path='["tex_key"]', frame=frame)
    else:
        if not os.path.exists(seq_dir):
            return "OK"
            
        best_num = -1
        best_file = None
        
        for f in os.listdir(seq_dir):
            if f.startswith("frame_") and f.endswith(".png"):
                digits = re.findall(r"\d+", f)
                if digits:
                    num = int(digits.pop(0))
                    if num <= frame and num > best_num:
                        best_num = num
                        best_file = f
        
        if best_file:
            best_path = os.path.join(seq_dir, best_file)
            best_blender_name = f"{folder_tag}_{best_file}"
            if os.path.exists(best_path):
                current_path = bpy.path.abspath(node.image.filepath) if (node.image and node.image.filepath) else ""
                if os.path.normpath(current_path) != os.path.normpath(best_path):
                    img = bpy.data.images.get(best_blender_name)
                    if not img:
                        img = bpy.data.images.load(best_path)
                        img.name = best_blender_name
                    else:
                        img.reload()
                    node.image = img
        else:
            node.image = None

    return "OK"

def delete_current_frame(context):
    node, mat_name = get_active_tex_node(context)
    if not node:
        return "Select a texture node first!"

    seq_dir = get_node_seq_dir(node, mat_name, create=False)
    if not seq_dir:
        return "Save your .blend file first!"

    folder_tag = sanitize_name(node["seq_folder"])
    frame = context.scene.frame_current
    disk_filename = f"frame_{frame:04d}.png"
    blender_img_name = f"{folder_tag}_{disk_filename}"
    target_path = os.path.join(seq_dir, disk_filename)

    if not os.path.exists(target_path):
        return f"No keyframe on frame {frame}!"

    if node.image and node.image.name == blender_img_name:
        node.image = None
    
    existing = bpy.data.images.get(blender_img_name)
    if existing:
        bpy.data.images.remove(existing)

    os.remove(target_path)

    try:
        node.keyframe_delete(data_path='["tex_key"]', frame=frame)
    except RuntimeError:
        pass

    update_single_node(context, node, mat_name, create_new=False)
    
    if node.image:
        context.scene.tool_settings.image_paint.mode = 'IMAGE'
        context.scene.tool_settings.image_paint.canvas = node.image
        
    return "OK"
# --- ОПЕРАТОРЫ ---

class FRAMEPAINT_OT_select_node(bpy.types.Operator):
    bl_idname = "framepaint.select_node"
    bl_label = "Select Texture Node"
    bl_description = "Make this texture node active and switch paint canvas to it"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj or not obj.active_material or not obj.active_material.use_nodes:
            return {'CANCELLED'}
        
        nodes = obj.active_material.node_tree.nodes
        target = nodes.get(self.node_name)
        if target and target.type == 'TEX_IMAGE':
            nodes.active = target
            if "seq_folder" in target:
                update_single_node(context, target, obj.active_material.name, create_new=False)
            if target.image:
                context.scene.tool_settings.image_paint.mode = 'IMAGE'
                context.scene.tool_settings.image_paint.canvas = target.image
        return {'FINISHED'}

class FRAMEPAINT_OT_new_key(bpy.types.Operator):
    bl_idname = "framepaint.new_key"
    bl_label = "New Blank Keyframe"

    def execute(self, context):
        node, mat_name = get_active_tex_node(context)
        if not node:
            self.report({'WARNING'}, "Select a texture node from the list above!")
            return {'CANCELLED'}
        res = update_single_node(context, node, mat_name, create_new=True, duplicate=False)
        if res != "OK":
            self.report({'WARNING'}, res)
        elif node.image:
            context.scene.tool_settings.image_paint.mode = 'IMAGE'
            context.scene.tool_settings.image_paint.canvas = node.image
        return {'FINISHED'}

class FRAMEPAINT_OT_dup_key(bpy.types.Operator):
    bl_idname = "framepaint.dup_key"
    bl_label = "Duplicate Keyframe"

    def execute(self, context):
        node, mat_name = get_active_tex_node(context)
        if not node:
            self.report({'WARNING'}, "Select a texture node from the list above!")
            return {'CANCELLED'}
        res = update_single_node(context, node, mat_name, create_new=True, duplicate=True)
        if res != "OK":
            self.report({'WARNING'}, res)
        elif node.image:
            context.scene.tool_settings.image_paint.mode = 'IMAGE'
            context.scene.tool_settings.image_paint.canvas = node.image
        return {'FINISHED'}

class FRAMEPAINT_OT_del_key(bpy.types.Operator):
    bl_idname = "framepaint.del_key"
    bl_label = "Delete Keyframe"

    def execute(self, context):
        res = delete_current_frame(context)
        if res != "OK":
            self.report({'WARNING'}, res)
        return {'FINISHED'}

def get_action_fcurves(action):
    """Универсальное получение кривых анимации для Blender 4.x и Blender 5.x"""
    if hasattr(action, "fcurves"):
        return action.fcurves
    
    # Новое API для Slotted Actions (Blender 4.4 / 5.x)
    curves = []
    if hasattr(action, "layers"):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for bag in strip.channelbags:
                        curves.extend(bag.fcurves)
    return curves

class FRAMEPAINT_OT_sync_keys(bpy.types.Operator):
    bl_idname = "framepaint.sync_keys"
    bl_label = "Sync Dope Sheet Keys"
    bl_description = "Generate image files for duplicated keyframes on the timeline"

    def execute(self, context):
        node, mat_name = get_active_tex_node(context)
        if not node or not node.id_data.animation_data or not node.id_data.animation_data.action:
            self.report({'WARNING'}, "No keyframes found on timeline!")
            return {'CANCELLED'}

        seq_dir = get_node_seq_dir(node, mat_name, create=True)
        action = node.id_data.animation_data.action
        target_path_str = f'nodes["{node.name}"]["tex_key"]'
        
        copied_count = 0
        for fcurve in get_action_fcurves(action):
            if fcurve.data_path == target_path_str:
                for kp in fcurve.keyframe_points:
                    timeline_frame = int(round(kp.co.x))
                    source_frame = int(round(kp.co.y))
                    
                    dest_file = os.path.join(seq_dir, f"frame_{timeline_frame:04d}.png")
                    src_file = os.path.join(seq_dir, f"frame_{source_frame:04d}.png")
                    
                    if not os.path.exists(dest_file) and os.path.exists(src_file):
                        shutil.copy2(src_file, dest_file)
                        kp.co.y = float(timeline_frame)
                        copied_count += 1

        update_single_node(context, node, mat_name, create_new=False)
        self.report({'INFO'}, f"Synced {copied_count} copied keyframes!")
        return {'FINISHED'}

@persistent
def on_frame_change(scene):
    # Во время многопоточного рендера Cycles нельзя напрямую менять ID-блоки из фонового потока
    if hasattr(bpy.app, "is_job_running") and bpy.app.is_job_running('RENDER'):
        # Безопасно обновляем только если кадр реально изменился, без reload()
        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and "seq_folder" in node:
                        seq_dir = get_node_seq_dir(node, mat.name, create=False)
                        if seq_dir and os.path.exists(seq_dir):
                            folder_tag = sanitize_name(node["seq_folder"])
                            frame = scene.frame_current
                            best_num = -1
                            best_file = None
                            for f in os.listdir(seq_dir):
                                if f.startswith("frame_") and f.endswith(".png"):
                                    digits = re.findall(r"\d+", f)
                                    if digits:
                                        num = int(digits.pop(0))
                                        if num <= frame and num > best_num:
                                            best_num = num
                                            best_file = f
                            if best_file:
                                best_path = os.path.join(seq_dir, best_file)
                                best_name = f"{folder_tag}_{best_file}"
                                img = bpy.data.images.get(best_name)
                                if not img and os.path.exists(best_path):
                                    img = bpy.data.images.load(best_path)
                                    img.name = best_name
                                if img and node.image != img:
                                    node.image = img
        return

    # Обычный режим работы во вьюпорте
    context = bpy.context
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and "seq_folder" in node:
                    update_single_node(context, node, mat.name, create_new=False)

    if getattr(context, "screen", None) and getattr(context, "view_layer", None):
        active_node, _ = get_active_tex_node(context)
        if active_node and active_node.image:
            try:
                context.scene.tool_settings.image_paint.mode = 'IMAGE'
                context.scene.tool_settings.image_paint.canvas = active_node.image
            except Exception:
                pass

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

# --- ИНТЕРФЕЙС ---
def get_sorted_key_frames(seq_dir):
    """Возвращает отсортированный список номеров всех существующих кадров в папке"""
    if not seq_dir or not os.path.exists(seq_dir):
        return []
    frames = []
    for f in os.listdir(seq_dir):
        if f.startswith("frame_") and f.endswith(".png"):
            digits = re.findall(r"\d+", f)
            if digits:
                frames.append(int(digits.pop(0)))
    return sorted(list(set(frames)))

class FRAMEPAINT_OT_jump_key(bpy.types.Operator):
    bl_idname = "framepaint.jump_key"
    bl_label = "Jump to Keyframe"
    bl_description = "Jump to the previous or next existing texture keyframe"

    direction: bpy.props.EnumProperty(
        items=[
            ('PREV', "Prev", "Previous keyframe"),
            ('NEXT', "Next", "Next keyframe"),
        ]
    )

    def execute(self, context):
        node, mat_name = get_active_tex_node(context)
        if not node:
            self.report({'WARNING'}, "Select a texture node first!")
            return {'CANCELLED'}

        seq_dir = get_node_seq_dir(node, mat_name, create=False)
        frames = get_sorted_key_frames(seq_dir)
        
        if not frames:
            self.report({'WARNING'}, "No keyframes found in folder!")
            return {'CANCELLED'}

        cur = context.scene.frame_current
        target_frame = None

        if self.direction == 'PREV':
            prev_frames = [f for f in frames if f < cur]
            if prev_frames:
                target_frame = prev_frames[-1]
        else:
            next_frames = [f for f in frames if f > cur]
            if next_frames:
                target_frame = next_frames[0]

        if target_frame is not None:
            context.scene.frame_set(target_frame)
        else:
            self.report({'INFO'}, "No more keyframes in that direction")

        return {'FINISHED'}

class FRAMEPAINT_PT_main_panel(bpy.types.Panel):
    bl_label = "Frame Texture Paint"
    bl_idname = "FRAMEPAINT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Frame Paint'

    def draw(self, context):
        layout = self.layout
        
        if not bpy.data.filepath:
            layout.label(text="Save your .blend file first!", icon='ERROR')
            return

        obj = context.view_layer.objects.active
        if not obj or not obj.active_material or not obj.active_material.use_nodes:
            layout.label(text="No active material", icon='MATERIAL')
            return

        mat = obj.active_material
        tex_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']

        if not tex_nodes:
            layout.label(text="No Image Texture nodes in material", icon='NODE_TEXTURE')
            return

        # 1. Список нод материала
        box_list = layout.box()
        box_list.label(text=f"Ноды ({mat.name}):", icon='NODETREE')
        col_list = box_list.column(align=True)
        
        active_node = mat.node_tree.nodes.active
        for n in tex_nodes:
            is_selected = (n == active_node)
            label_text = n["seq_folder"] if "seq_folder" in n else (n.label or n.name)
            icon = 'RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF'
            
            op = col_list.operator("framepaint.select_node", text=label_text, icon=icon, depress=is_selected)
            op.node_name = n.name

        # 2. Информация об активной ноде
        node, mat_name = get_active_tex_node(context)
        if not node:
            layout.label(text="Select a node from the list above", icon='INFO')
            return

        box = layout.box()
        if "seq_folder" in node:
            box.prop(node, '["seq_folder"]', text="Folder", icon='FILE_FOLDER')
        else:
            default_name = f"{sanitize_name(mat_name)}_{sanitize_name(node.name)}"
            box.label(text=f"Folder: {default_name}", icon='FILE_FOLDER')

               # Проверяем, стоит ли ползунок ровно на ключевом кадре или это Hold
        cur_f = context.scene.frame_current
        seq_dir = get_node_seq_dir(node, mat_name, create=False)
        all_keys = get_sorted_key_frames(seq_dir)
        is_exact_key = cur_f in all_keys

        status_text = f"Frame: {cur_f} {'[KEY]' if is_exact_key else '(Hold)'}"
        status_icon = 'KEYFRAME_HLT' if is_exact_key else 'KEYFRAME'
        box.label(text=status_text, icon=status_icon)

        if node.image and node.image.filepath:
            box.label(text=f"File: {os.path.basename(node.image.filepath)}", icon='IMAGE_DATA')
        else:
            box.label(text="File: None", icon='IMAGE_DATA')

        # Кнопки быстрой навигации по ключам в один ряд
        row_nav = box.row(align=True)
        op_prev = row_nav.operator("framepaint.jump_key", text="Prev Key", icon='PREV_KEYFRAME')
        op_prev.direction = 'PREV'
        op_next = row_nav.operator("framepaint.jump_key", text="Next Key", icon='NEXT_KEYFRAME')
        op_next.direction = 'NEXT'

        # Настройки нового холста
        box_set = layout.box()
        box_set.prop(context.scene, "fp_resolution", text="Size")
        box_set.prop(context.scene, "fp_bg_color", text="Background")
        
        # Кнопки ключей
        col = layout.column(align=True)
        col.operator("framepaint.new_key", icon='ADD')
        col.operator("framepaint.dup_key", icon='DUPLICATE')
        col.separator()
        col.operator("framepaint.del_key", icon='TRASH')
        col.separator()
        col.operator("framepaint.sync_keys", icon='FILE_REFRESH')


classes = (
    FRAMEPAINT_OT_select_node,
    FRAMEPAINT_OT_new_key,
    FRAMEPAINT_OT_dup_key,
    FRAMEPAINT_OT_del_key,
    FRAMEPAINT_OT_sync_keys,
    FRAMEPAINT_OT_jump_key,
    FRAMEPAINT_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.fp_resolution = bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ('512', "512 x 512", ""),
            ('1024', "1024 x 1024", ""),
            ('2048', "2048 x 2048", ""),
            ('4096', "4096 x 4096", ""),
        ],
        default='1024'
    )
    bpy.types.Scene.fp_bg_color = bpy.props.EnumProperty(
        name="Background",
        items=[
            ('ALPHA', "Transparent", ""),
            ('BLACK', "Black", ""),
            ('WHITE', "White", ""),
        ],
        default='ALPHA'
    )
    
    if on_frame_change not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(on_frame_change)

def unregister():
    if on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(on_frame_change)
        
    del bpy.types.Scene.fp_resolution
    del bpy.types.Scene.fp_bg_color
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


