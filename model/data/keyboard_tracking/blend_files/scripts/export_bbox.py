import os
import math
import bpy
import bpy_extras
from mathutils import Vector
import csv

def get_2d_bbox_in_camera(scene, camera, obj):
    """
    Returns (min_x, min_y, max_x, max_y) for 'obj' as seen by 'camera' 
    in pixel coordinates, for the current frame.
    """
    # Project each 3D bounding-box corner into 2D camera space
    corners_2d = []
    for corner_local in obj.bound_box:
        corner_world = obj.matrix_world @ Vector(corner_local)
        # world_to_camera_view returns a normalized (0..1) coordinate in the camera frame,
        # but can be outside [0..1] if the point is outside the camera's viewing region.
        co_2d = bpy_extras.object_utils.world_to_camera_view(scene, camera, corner_world)
        corners_2d.append(co_2d)

    # Convert normalized coordinates to pixel coordinates
    render = scene.render
    res_x = render.resolution_x * render.resolution_percentage / 100
    res_y = render.resolution_y * render.resolution_percentage / 100
    
    # Compute min and max *in the camera view*
    min_x = min(pt.x for pt in corners_2d) * res_x
    max_x = max(pt.x for pt in corners_2d) * res_x
    min_y = (1 - max(pt.y for pt in corners_2d)) * res_y
    max_y = (1 - min(pt.y for pt in corners_2d)) * res_y
    # min_y = (1 - min(pt.y for pt in corners_2d)) * res_y
    # max_y = (1 - max(pt.y for pt in corners_2d)) * res_y

    return (min_x, min_y, max_x, max_y)

def get_collection_2d_bbox_in_camera(scene, camera, collection):
    """
    Returns an aggregate bounding box (min_x, min_y, max_x, max_y)
    for all objects in 'collection' as seen by 'camera'.
    """
    all_coords_x = []
    all_coords_y = []
    
    for obj in collection.objects:
        bbox = get_2d_bbox_in_camera(scene, camera, obj)
        all_coords_x.extend([bbox[0], bbox[2]])  # min_x, max_x
        all_coords_y.extend([bbox[1], bbox[3]])  # min_y, max_y
    
    if not all_coords_x or not all_coords_y:
        # Collection empty or something unexpected
        return (0.0, 0.0, 0.0, 0.0)
    
    return (min(all_coords_x), min(all_coords_y),
            max(all_coords_x), max(all_coords_y))

def save_bboxes_to_csv(csv_filepath):
    """
    Writes the 2D bounding box (in pixel coordinates) for each animation frame.
    If 'object_or_collection_name' matches an Object, get its bounding box.
    If it matches a Collection, get the bounding box enclosing all objects in that Collection.
    The bounding box is computed as seen by the camera named 'camera_name'.
    """
    # Specify the camera
    camera = bpy.context.scene.camera
    if camera is None:
        print("No active camera in the scene. Please add a camera.")
        return

    # Attempt to get an Object or a Collection by the given name
    target_name = "keyboard-track"
    obj = next((obj for obj in bpy.context.scene.objects if obj.name.startswith(target_name)), None)
    coll = next((coll for coll in bpy.data.collections if coll.name.startswith(target_name) and bpy.context.scene.user_of_id(coll)), None)
    if not obj and not coll:
        print(f"ERROR: Could not find an Object or Collection named '{target_name}'.")
        return

    scene = bpy.context.scene
    start_frame = scene.frame_start
    end_frame   = scene.frame_end
    step = scene.frame_step

    with open(csv_filepath, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Write CSV header
        writer.writerow(["Frame", "min_x", "min_y", "max_x", "max_y"])

        # Iterate over each frame in the animation range
        for frame in range(start_frame, end_frame + 1, step):
            scene.frame_set(frame)

            if obj:
                min_x, min_y, max_x, max_y = get_2d_bbox_in_camera(scene, camera, obj)
            else:
                min_x, min_y, max_x, max_y = get_collection_2d_bbox_in_camera(scene, camera, coll)

            # Write one row per frame
            writer.writerow([frame, min_x, min_y, max_x, max_y])

    print(f"2D bounding box data (camera view) written to: {csv_filepath}")

if __name__ == '__main__':
    # Specify directories
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "../raw"))
    label_dir = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "../labels_bbox"))

    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(label_dir, exist_ok=True)

    label_files = os.listdir(label_dir)
    base_name = bpy.context.scene.name
    name_collisions = [f for f in label_files if f.startswith(base_name)]
    if name_collisions:
        print(f"Warning: {len(name_collisions)} files with the same scene name already exist in the labels directory.")
        base_name += f"-{len(name_collisions) + 1}"

    raw_filepath = f"{raw_dir}/{base_name}/{base_name}-#####.png"
    label_filepath = f"{label_dir}/{base_name}.csv"

    # print(f"Rendering frames to {raw_filepath}")
    # bpy.context.scene.filepath = raw_filepath
    # bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

    print(f"Saving 2D coordinates to {label_filepath}")
    save_bboxes_to_csv(label_filepath)
