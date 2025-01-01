import os
import math
import bpy
import bpy_extras
import csv

# Function to get 2D coordinates of an object in the rendered image
def get_2d_coordinates(obj, camera, depsgraph):
    # Get the object's world coordinates
    eval_obj = obj.evaluated_get(depsgraph)
    co_world = eval_obj.matrix_world.translation
    
    # Convert the world coordinates to camera view coordinates
    co_camera = bpy_extras.object_utils.world_to_camera_view(bpy.context.scene, camera, co_world)
    
    # Scale to image dimensions
    render = bpy.context.scene.render
    resolution_x = render.resolution_x * render.resolution_percentage / 100
    resolution_y = render.resolution_y * render.resolution_percentage / 100
    
    x = co_camera.x * resolution_x
    y = (1 - co_camera.y) * resolution_y  # Flip Y-axis
    
    return (x, y)

# Function to collect and save 2D coordinates
def save_empty_positions_to_csv(filepath):
    # Specify the camera
    camera = bpy.context.scene.camera
    if camera is None:
        print("No active camera in the scene. Please add a camera.")
        return
    
    # Specify the dependency graph
    depsgraph = bpy.context.evaluated_depsgraph_get()

    # Names of the empties to track
    target_names = [f"keyboard-lt", "keyboard-lb", "keyboard-rt", "keyboard-rb"]

    # Find empties in scene starting with the specified target names
    empties = {name: next((obj for obj in bpy.context.scene.objects if obj.name.startswith(name)), None) for name in target_names}

    if not empties:
        print("None of the specified empties were found in the scene.")
        return

    # Get the frame range
    scene = bpy.context.scene
    start_frame = scene.frame_start
    end_frame = scene.frame_end
    step = scene.frame_step

    # Open CSV file for writing
    with open(filepath, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write header
        header = ['Frame'] + [f'{name}_{coord}' for name in target_names for coord in ['x', 'y']]
        csvwriter.writerow(header)

        # Iterate through all frames in the animation
        for frame in range(start_frame, end_frame + 1, step):
            scene.frame_set(frame)  # Set the current frame
            row = [frame]
            
            # Get 2D coordinates for each target empty
            for name in target_names:
                empty = empties.get(name)
                if empty:
                    coords_2d = get_2d_coordinates(empty, camera, depsgraph)
                    row.extend(coords_2d)
                else:
                    # Fill missing data for non-existent empties
                    row.extend([-1, -1])
            
            # Write frame data to CSV
            csvwriter.writerow(row)
    
    print(f"2D coordinates saved to {filepath}")


if __name__ == '__main__':
    # Specify directories
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "../raw"))
    label_dir = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "../labels"))

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
    save_empty_positions_to_csv(label_filepath)
