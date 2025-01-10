import os
import uuid
import json
from PIL import Image, ImageDraw
from constants import SM_BLOCK_INFO
from tkinter import messagebox

def get_blueprints_directory():
    blueprint_dir = os.path.join(os.getenv('APPDATA'), 'Axolot Games', 'Scrap Mechanic', 'User')
    if not os.path.exists(blueprint_dir):
        return None

    user_dirs = [d for d in os.listdir(blueprint_dir) if d.startswith('User_')]
    if not user_dirs:
        return None

    blueprint_dir = os.path.join(blueprint_dir, user_dirs[0], 'Blueprints')
    if os.path.exists(blueprint_dir):
        return blueprint_dir
    else:
        return None

def export_blueprint(rects, wedges, diameter, material_choice, thickness, name, real_radius, sides, circularity, uniformity, output_directory=None):
    """
    Exports the blueprint based on rects and wedges.
    """
    # Validate material_choice
    if material_choice not in SM_BLOCK_INFO:
        raise ValueError(f"Invalid material choice: {material_choice}")

    block_info = SM_BLOCK_INFO[material_choice]
    block_id = block_info["block_id"]
    wedge_id = block_info["wedge_id"]
    color = block_info["color"]

    # Generate UUID
    blueprint_uuid = str(uuid.uuid4())

    # Determine output directory
    if output_directory is None:
        blueprint_folder = get_blueprints_directory()
        if blueprint_folder is None:
            # Fallback to default "output" directory if Scrap Mechanic Blueprints directory not found
            blueprint_folder = os.path.join(os.getcwd(), "output")
    else:
        blueprint_folder = output_directory

    # Create output folder
    blueprint_folder = os.path.join(blueprint_folder, blueprint_uuid)
    os.makedirs(blueprint_folder, exist_ok=True)

    # Initialize blueprint.json
    blueprint_data = {
        "bodies": [
            {
                "childs": []
            }
        ],
        "version": 4
    }

    # Define scaling and center shift for PNG image
    scale = 10  # 10 pixels per unit
    image_size = diameter * scale  # Image size based on diameter
    center_shift_x = image_size / 2
    center_shift_y = image_size / 2

    # Adjust center based on diamater. If odd diameter, center is at (0.5, 0.5), else (0, 0)
    odd_center = diameter % 2 == 1
    center_x = 0.5 if odd_center else 0
    center_y = 0.5 if odd_center else 0

    # Adjust center_shift based on new center
    center_shift_x -= center_x * scale
    center_shift_y -= center_y * scale

    # Create Image
    image = Image.new("RGBA", (image_size, image_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Insert Rects
    for rect in rects:
        x = rect["x"]  # Position relative to center
        y = rect["y"]
        width = rect["width"]
        height = rect["height"]

        # Draw rectangle on image (blue fill, no border)
        draw.rectangle([
            (x * scale) + center_shift_x,
            (y * scale) + center_shift_y,
            (x + width) * scale + center_shift_x,
            (y + height) * scale + center_shift_y
        ], fill=(0, 0, 255, 255), outline=None)

        # Create blueprint child
        child = {
            "bounds": {
                "x": int(width),        # Width of the rectangle
                "y": int(height),       # Height of the rectangle
                "z": int(thickness)     # Thickness from user input
            },
            "color": color,
            "pos": {
                "x": int(x),
                "y": int(y),
                "z": 0
            },
            "shapeId": block_id,
            "xaxis": 1,
            "zaxis": 3
        }

        blueprint_data["bodies"][0]["childs"].append(child)

    # Insert Wedges
    for wedge in wedges:
        point_a = wedge["point_a"]
        point_b = wedge["point_b"]
        point_c = wedge["point_c"]
        rotation = wedge["rotation"]
        quadrant = wedge["quadrant"]

        # Calculate width and height based on quadrants
        bounds_x = thickness
        if quadrant in ["tl", "br"]: # For tl and br, bounds_y is height and bounds_z is width
            bounds_y = abs(point_a.y - point_b.y)  # Height
            bounds_z = abs(point_a.x - point_c.x)  # Width
        elif quadrant in ["tr", "bl"]: # For tr and bl, bounds_y is width and bounds_z is height
            bounds_y = abs(point_a.x - point_b.x)  # Width
            bounds_z = abs(point_a.y - point_c.y)  # Height

        # Draw triangle on image (red fill, no border)
        draw.polygon([
            (point_a.x * scale + center_shift_x, point_a.y * scale + center_shift_y),
            (point_b.x * scale + center_shift_x, point_b.y * scale + center_shift_y),
            (point_c.x * scale + center_shift_x, point_c.y * scale + center_shift_y)
        ], fill=(255, 0, 0, 255), outline=None)

        # Create blueprint child
        child = {
            "bounds": {
                "x": int(bounds_x),
                "y": int(bounds_y),
                "z": int(bounds_z)
            },
            "color": color,
            "pos": {
                "x": int(point_c.x),
                "y": int(point_c.y),
                "z": 0
            },
            "shapeId": wedge_id,
            "xaxis": rotation["xaxis"],
            "zaxis": rotation["zaxis"]
        }

        blueprint_data["bodies"][0]["childs"].append(child)

    # Save blueprint.json
    blueprint_path = os.path.join(blueprint_folder, "blueprint.json")
    with open(blueprint_path, "w") as f:
        json.dump(blueprint_data, f, indent=4)

    # Resize image to 128x128 and save as icon.png
    icon = image.resize((128, 128), Image.LANCZOS)
    icon_path = os.path.join(blueprint_folder, "icon.png")
    icon.save(icon_path, "PNG")

    # Create description.json with detailed information
    description = {
        "description": (
            f"Real Radius: {real_radius}\n"
            f"Diameter: {diameter}\n"
            f"Thickness: {thickness}\n"
            f"Sides: {sides}\n"
            f"Circularity: {circularity}\n"
            f"Uniformity: {uniformity}"
        ),
        "localId": blueprint_uuid,
        "name": name,
        "type": "Blueprint",
        "version": 0
    }
    description_path = os.path.join(blueprint_folder, "description.json")
    with open(description_path, "w") as f:
        json.dump(description, f, indent=4)

    return blueprint_uuid  # Return the UUID for confirmation
