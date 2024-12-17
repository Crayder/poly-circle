import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.gridspec import GridSpec
from tkinter import filedialog
import pandas as pd
import os
import threading
import math
from math import gcd
from multiprocessing import Pool, cpu_count
import sqlite3

# Use the TkAgg backend for matplotlib
matplotlib.use("TkAgg")

# Default Configuration Constants
DEFAULT_CONFIG = {
    "ODD_CENTER": False,          # If True, center = (0.5, 0.5); if False, center = (0, 0)
    "INITIAL_RADIUS": 5,
    "RADIUS_INCREMENT": 0.0025,
    "MAX_RADIUS": 40,
    "CHECK_DIMENSIONS": True,
    "DIFFERENCE_THRESHOLD": 0.5
}

overlay_lines = []
overlay_texts = []
overlay_visible = False

def distance_to_center(center_x, center_y, grid_x, grid_y):
    return np.sqrt((grid_x - center_x)**2 + (grid_y - center_y)**2)

def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

def convex_hull(points):
    points = sorted(points)
    if len(points) <= 1:
        return points

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]

def is_collinear(a, b, c):
    return cross(a, b, c) == 0

def is_between(a, b, c):
    return (min(a[0], c[0]) <= b[0] <= max(a[0], c[0])) and \
           (min(a[1], c[1]) <= b[1] <= max(a[1], c[1]))

def remove_collinear_points(points):
    if len(points) < 3:
        return points

    changed = True
    while changed:
        changed = False
        new_points = []
        n = len(points)
        for i in range(n):
            prev_p = points[(i - 1) % n]
            curr_p = points[i]
            next_p = points[(i + 1) % n]

            if is_collinear(prev_p, curr_p, next_p) and is_between(prev_p, curr_p, next_p):
                changed = True
            else:
                new_points.append(curr_p)
        points = new_points
        if len(points) < 3:
            break

    return points

def sort_grid_points(center_x, center_y, grid_points):
    def calculate_angle(point):
        x, y = point
        angle = np.arctan2(y - center_y, x - center_x)
        return angle if angle >= 0 else (2 * np.pi + angle)
    return sorted(grid_points, key=calculate_angle)

def check_dimensions(center_x, center_y, radius, grid_points):
    sorted_points = sort_grid_points(center_x, center_y, grid_points)
    num_points = len(sorted_points)

    for i in range(num_points):
        current_point = sorted_points[i]
        next_point = sorted_points[(i + 1) % num_points]

        delta_x = abs(next_point[0] - current_point[0])
        delta_y = abs(next_point[1] - current_point[1])

        # Condition 1
        if delta_x == 0 or delta_y == 0 or delta_x == delta_y:
            continue

        # Condition 2
        if delta_x <= 8 and delta_y <= 8:
            continue

        # Condition 3
        common_divisor = gcd(delta_x, delta_y)
        if common_divisor > 1:
            simplified_x = delta_x // common_divisor
            simplified_y = delta_y // common_divisor
            if simplified_x <= 8 and simplified_y <= 8:
                continue

        return False

    return True

def create_overlay(ax, center_x, center_y, grid_points):
    global overlay_lines, overlay_texts
    overlay_lines.clear()
    overlay_texts.clear()

    sorted_pts = sort_grid_points(center_x, center_y, grid_points)
    num_points = len(sorted_pts)

    for i in range(num_points):
        A = sorted_pts[i]
        B = sorted_pts[(i + 1) % num_points]
        Ax, Ay = A
        Bx, By = B

        dx = Bx - Ax
        dy = By - Ay

        if dx == 0 or dy == 0:
            line_artist = ax.plot([Ax, Bx], [Ay, By], color="black", zorder=10)
            overlay_lines.extend(line_artist)
            length = abs(dx) if dy == 0 else abs(dy)
            mx, my = (Ax + Bx)/2, (Ay + By)/2
            text_artist = ax.text(mx, my, f"{int(length)}", color="black", fontsize=8, zorder=30,
                                  ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            overlay_texts.append(text_artist)
        else:
            C1 = (Ax, By)
            C2 = (Bx, Ay)
            distC1 = distance_to_center(center_x, center_y, C1[0], C1[1])
            distC2 = distance_to_center(center_x, center_y, C2[0], C2[1])
            C = C1 if distC1 < distC2 else C2
            Cx, Cy = C

            line_artist = ax.plot([Ax, Bx], [Ay, By], color="black", zorder=10)
            overlay_lines.extend(line_artist)
            AC = ax.plot([Ax, Cx], [Ay, Cy], color="red", zorder=10)
            BC = ax.plot([Bx, Cx], [By, Cy], color="red", zorder=10)
            overlay_lines.extend(AC)
            overlay_lines.extend(BC)

            AC_length = round(math.sqrt((Ax - Cx)**2 + (Ay - Cy)**2))
            BC_length = round(math.sqrt((Bx - Cx)**2 + (By - Cy)**2))

            mACx, mACy = (Ax + Cx)/2, (Ay + Cy)/2
            mBCx, mBCy = (Bx + Cx)/2, (By + Cy)/2

            text_AC = ax.text(mACx, mACy, f"{AC_length}", color="black", fontsize=8, zorder=30,
                              ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            text_BC = ax.text(mBCx, mBCy, f"{BC_length}", color="black", fontsize=8, zorder=30,
                              ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            overlay_texts.append(text_AC)
            overlay_texts.append(text_BC)

def toggle_overlay(canvas):
    global overlay_visible
    if canvas is None:
        return
    overlay_visible = not overlay_visible
    for artist in overlay_lines + overlay_texts:
        artist.set_visible(overlay_visible)
    canvas.draw()

def create_plot(center_x, center_y, tested_radius, sides, real_radius, max_diff, diameter, grid_points):
    fig = plt.Figure(figsize=(8, 8))
    gs = GridSpec(1, 1, figure=fig)
    ax = fig.add_subplot(gs[0, 0])

    theta = np.linspace(0, 2 * np.pi, 500)
    circle_x = center_x + tested_radius * np.cos(theta)
    circle_y = center_y + tested_radius * np.sin(theta)
    ax.plot(circle_x, circle_y, color="blue")

    ax.scatter(center_x, center_y, color="red")

    polygon_x = [p[0] for p in grid_points]
    polygon_y = [p[1] for p in grid_points]
    polygon_x.append(grid_points[0][0])
    polygon_y.append(grid_points[0][1])
    ax.plot(polygon_x, polygon_y, color="black")
    ax.scatter([p[0] for p in grid_points], [p[1] for p in grid_points], color="orange")

    approx_radius = max(tested_radius, real_radius)
    grid_min_x = int(np.floor(center_x - approx_radius - 1))
    grid_max_x = int(np.ceil(center_x + approx_radius + 1))
    grid_min_y = int(np.floor(center_y - approx_radius - 1))
    grid_max_y = int(np.ceil(center_y + approx_radius + 1))
    ax.set_xticks(np.arange(grid_min_x, grid_max_x + 1, 1))
    ax.set_yticks(np.arange(grid_min_y, grid_max_y + 1, 1))
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(center_x - approx_radius - 1, center_x + approx_radius + 1)
    ax.set_ylim(center_y - approx_radius - 1, center_y + approx_radius + 1)

    config_text = (
        f"Center: ({center_x}, {center_y})\n"
        f"Tested Radius: {tested_radius:.4f}\n"
        f"Sides: {sides}\n"
        f"Real Radius: {real_radius:.4f}\n"
        f"Max Difference: {max_diff:.4f}\n"
        f"Diameter: {diameter}"
    )
    ax.text(0.02, 0.98, config_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', color="black",
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    ax.set_title(f"Polygon (Sides = {sides}, Real Radius = {real_radius:.4f}, Max Diff = {max_diff:.4f}, Diameter = {diameter})")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    return fig

def on_row_selected(event, tree, canvas_frame, config):
    selected_item = tree.focus()
    if not selected_item:
        return
    data_tuple = tree.item_data.get(selected_item)
    if not data_tuple:
        return

    tested_radius, sides, real_radius, max_diff, diameter, grid_points, odd_center_val = data_tuple

    # Determine center based on ODD_CENTER
    if config["ODD_CENTER"]:
        center_x, center_y = 0.5, 0.5
    else:
        center_x, center_y = 0.0, 0.0

    for widget in canvas_frame.winfo_children():
        widget.destroy()

    toolbar_frame = ttk.Frame(canvas_frame)
    toolbar_frame.pack(side=tk.TOP, fill=tk.X)

    plot_frame = ttk.Frame(canvas_frame)
    plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    fig = create_plot(
        center_x=center_x,
        center_y=center_y,
        tested_radius=tested_radius,
        sides=sides,
        real_radius=real_radius,
        max_diff=max_diff,
        diameter=diameter,
        grid_points=grid_points
    )
    if fig is None:
        return

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    create_overlay(fig.axes[0], center_x, center_y, grid_points)
    for artist in overlay_lines + overlay_texts:
        artist.set_visible(overlay_visible)
    canvas.draw()

    tree.canvas_ref = canvas

def sort_treeview(tree, col, reverse, sort_order):
    l = [(tree.set(k, col), k) for k in tree.get_children('')]
    if not l:
        return

    try:
        # Attempt to convert to float for numeric sorting
        float(l[0][0].replace(',', ''))  # Remove commas if any
        is_numeric = True
    except ValueError:
        is_numeric = False

    if is_numeric:
        l.sort(key=lambda t: float(t[0].replace(',', '')), reverse=reverse)
    else:
        l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        tree.move(k, '', index)

    sort_order[col] = not reverse
    tree.heading(col, command=lambda: sort_treeview(tree, col, sort_order[col], sort_order))

def get_user_inputs(entries_circle, entries_thresholds, check_dimensions_var, odd_center_var):
    try:
        # We no longer read CENTER_X and CENTER_Y from entries, they are determined by odd_center_var
        initial_radius = float(entries_circle["INITIAL_RADIUS"].get())
        max_radius = float(entries_circle["MAX_RADIUS"].get())
        radius_increment = float(entries_thresholds["RADIUS_INCREMENT"].get())
        difference_threshold = float(entries_thresholds["DIFFERENCE_THRESHOLD"].get())

        if not (1 <= initial_radius <= 199):
            raise ValueError("Initial Radius must be between 1 and 199.")
        if not (2 <= max_radius <= 200):
            raise ValueError("Max Radius must be between 2 and 200.")
        if initial_radius > max_radius:
            raise ValueError("Initial Radius cannot be greater than Max Radius.")
        if difference_threshold < 0:
            raise ValueError("Difference Threshold cannot be negative.")
        if radius_increment <= 0:
            raise ValueError("Radius Increment must be positive.")

        # Determine center based on ODD_CENTER
        if odd_center_var.get():
            center_x, center_y = 0.5, 0.5
        else:
            center_x, center_y = 0.0, 0.0

        return {
            "ODD_CENTER": odd_center_var.get(),
            "CENTER_X": center_x,
            "CENTER_Y": center_y,
            "INITIAL_RADIUS": initial_radius,
            "MAX_RADIUS": max_radius,
            "RADIUS_INCREMENT": radius_increment,
            "CHECK_DIMENSIONS": check_dimensions_var.get(),
            "DIFFERENCE_THRESHOLD": difference_threshold
        }
    except ValueError as ve:
        messagebox.showerror("Invalid Input", str(ve))
        return None

def compute_for_radius(args):
    center_x, center_y, radius, check_dimensions_flag, difference_threshold = args

    min_x = int(np.floor(center_x - radius))
    max_x = int(np.ceil(center_x + radius))
    min_y = int(np.floor(center_y - radius))
    max_y = int(np.ceil(center_y + radius))

    inside_points = []
    for gx in range(min_x, max_x+1):
        for gy in range(min_y, max_y+1):
            if distance_to_center(center_x, center_y, gx, gy) <= radius:
                inside_points.append((gx, gy))

    if len(inside_points) < 3:
        return None

    hull = convex_hull(inside_points)
    if len(hull) < 3:
        return None

    simplified = remove_collinear_points(hull)
    if len(simplified) < 3:
        return None

    if check_dimensions_flag:
        if not check_dimensions(center_x, center_y, radius, simplified):
            return None

    # Compute Real Radius (max distance to center)
    real_radius = max(distance_to_center(center_x, center_y, p[0], p[1]) for p in simplified)
    # Compute max difference from Real Radius
    differences = [abs(distance_to_center(center_x, center_y, p[0], p[1]) - real_radius) for p in simplified]
    max_diff = max(differences)

    # Check difference threshold
    if max_diff > difference_threshold:
        return None

    # Compute Diameter: max_x - min_x
    x_values = [p[0] for p in simplified]
    diameter = max(x_values) - min(x_values)

    return (radius, len(simplified), real_radius, max_diff, diameter, tuple(simplified))

def save_results_to_database(results, odd_center_val):
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    # Create table if not exists with diameter as INTEGER
    c.execute("""CREATE TABLE IF NOT EXISTS results (
                    tested_radius REAL,
                    sides INTEGER,
                    real_radius REAL,
                    max_diff REAL,
                    diameter INTEGER,
                    grid_points TEXT,
                    odd_center INTEGER,
                    UNIQUE(grid_points, odd_center)
                )""")
    for r in results:
        tested_radius, sides, real_radius, max_diff, diameter, polygon = r
        polygon_str = ",".join(f"({x},{y})" for x,y in polygon)

        # Check if this polygon with the same odd_center already exists
        c.execute("SELECT tested_radius, sides, real_radius, max_diff, diameter FROM results WHERE grid_points = ? AND odd_center = ?", (polygon_str, odd_center_val))
        existing = c.fetchone()

        if existing is not None:
            # Polygon already in DB with the same odd_center
            existing_tested_radius, existing_sides, existing_real_radius, existing_max_diff, existing_diameter = existing
            # If new tested radius is smaller, replace the old
            if tested_radius < existing_tested_radius:
                c.execute("""UPDATE results SET tested_radius=?, sides=?, real_radius=?, max_diff=?, diameter=? 
                             WHERE grid_points=? AND odd_center=?""",
                          (tested_radius, sides, real_radius, max_diff, diameter, polygon_str, odd_center_val))
            # If not smaller, do nothing (no insert)
        else:
            # Insert the new record with odd_center and diameter
            c.execute("INSERT INTO results (tested_radius, sides, real_radius, max_diff, diameter, grid_points, odd_center) VALUES (?,?,?,?,?,?,?)",
                      (tested_radius, sides, real_radius, max_diff, diameter, polygon_str, odd_center_val))

    conn.commit()
    conn.close()

def on_calculate_click(entries_circle, entries_thresholds, check_dimensions_var, tree, canvas_frame, progress_bar, calculate_button, odd_center_var):
    config = get_user_inputs(entries_circle, entries_thresholds, check_dimensions_var, odd_center_var)
    if config is None:
        return

    calculate_button.config(state=tk.DISABLED)
    progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    progress_bar.config(value=0)

    initial_radius = config["INITIAL_RADIUS"]
    max_radius = config["MAX_RADIUS"]
    radius_increment = config["RADIUS_INCREMENT"]
    center_x = config["CENTER_X"]
    center_y = config["CENTER_Y"]
    check_dimensions_flag = config["CHECK_DIMENSIONS"]
    difference_threshold = config["DIFFERENCE_THRESHOLD"]
    odd_center_val = 1 if config["ODD_CENTER"] else 0  # Convert to integer

    radii = []
    r = initial_radius
    while r <= max_radius:
        radii.append(r)
        r += radius_increment

    total_steps = len(radii)
    progress_bar.config(maximum=total_steps)

    def update_progress(value):
        progress_bar['value'] = value
        progress_bar.update_idletasks()

    def run_computation():
        results = []
        count = 0
        with Pool(processes=cpu_count()) as pool:
            for res in pool.imap_unordered(compute_for_radius, [(center_x, center_y, rad, check_dimensions_flag, difference_threshold) for rad in radii]):
                if res is not None:
                    results.append(res)
                count += 1
                # Update progress in main thread
                root.after(0, update_progress, count)

        # Remove duplicates (based on exact grid points and odd_center)
        seen_polygons = set()
        filtered_results = []
        for res in results:
            tested_radius, sides, real_radius, max_diff, diameter, polygon = res
            if polygon not in seen_polygons:
                seen_polygons.add(polygon)
                filtered_results.append(res)

        # Sort by sides ascending
        filtered_results.sort(key=lambda x: x[1])

        # Save results to database with odd_center_val
        save_results_to_database(filtered_results, odd_center_val)

        def update_gui():
            for item in tree.get_children():
                tree.delete(item)
            tree.item_data.clear()

            if not filtered_results:
                messagebox.showinfo("No Valid Results", "No polygons formed for the given configuration.")
                for widget in canvas_frame.winfo_children():
                    widget.destroy()
                progress_bar.pack_forget()
                calculate_button.config(state=tk.NORMAL)
                return

            for data_tuple in filtered_results:
                tested_radius, sides, real_radius, max_diff, diameter, polygon = data_tuple
                odd_center = "Yes" if odd_center_val else "No"
                iid = tree.insert("", tk.END, values=(
                    f"{tested_radius:.4f}",
                    f"{sides}",
                    f"{real_radius:.4f}",
                    f"{max_diff:.4f}",
                    odd_center,
                    f"{diameter}"
                ))
                tree.item_data[iid] = (tested_radius, sides, real_radius, max_diff, diameter, polygon, odd_center_val)

            sort_order = {col: False for col in ("Tested Radius", "Sides", "Real Radius", "Max Difference", "Odd Center", "Diameter")}
            for col in ("Tested Radius", "Sides", "Real Radius", "Max Difference", "Odd Center", "Diameter"):
                tree.heading(col, text=col, command=lambda _col=col: sort_treeview(tree, _col, sort_order[_col], sort_order))

            if tree.get_children():
                tree.selection_set(tree.get_children()[0])
                tree.focus(tree.get_children()[0])
                on_row_selected(None, tree, canvas_frame, config)

            progress_bar.pack_forget()
            calculate_button.config(state=tk.NORMAL)

        root.after(0, update_gui)

    thread = threading.Thread(target=run_computation)
    thread.start()

def export_to_csv(valid_data):
    if not valid_data:
        messagebox.showinfo("No Data", "There is no data to export.")
        return
    try:
        data = {
            "Tested Radius": [f"{r[0]:.4f}" for r in valid_data],
            "Sides": [f"{r[1]}" for r in valid_data],
            "Real Radius": [f"{r[2]:.4f}" for r in valid_data],
            "Max Difference": [f"{r[3]:.4f}" for r in valid_data],
            "Odd Center": ["Yes" if r[6] else "No" for r in valid_data],
            "Diameter": [f"{r[4]}" for r in valid_data]  # Diameter as integer
        }
        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export data: {e}")

def main():
    global root
    root = tk.Tk()
    root.title("Polygon Radius App")
    root.geometry("1200x800")

    input_frame = ttk.Frame(root)
    input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    circle_params_frame = ttk.LabelFrame(input_frame, text="Circle Parameters")
    circle_params_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    thresholds_frame = ttk.LabelFrame(input_frame, text="Thresholds")
    thresholds_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    options_frame = ttk.LabelFrame(input_frame, text="Options")
    options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    buttons_frame = ttk.Frame(input_frame)
    buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Circle Parameters (No CENTER_X/Y, just INITIAL_RADIUS and MAX_RADIUS)
    inputs_circle = ["INITIAL_RADIUS", "MAX_RADIUS"]
    entries_circle = {}
    for i, key in enumerate(inputs_circle):
        label = ttk.Label(circle_params_frame, text=key.replace("_", " ") + ":")
        label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
        entry = ttk.Entry(circle_params_frame, width=15)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)
        entry.insert(0, str(DEFAULT_CONFIG[key]))
        entries_circle[key] = entry

    # Thresholds
    inputs_thresholds = ["RADIUS_INCREMENT", "DIFFERENCE_THRESHOLD"]
    entries_thresholds = {}
    for i, key in enumerate(inputs_thresholds):
        label = ttk.Label(thresholds_frame, text=key.replace("_", " ") + ":")
        label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
        entry = ttk.Entry(thresholds_frame, width=15)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)
        entry.insert(0, str(DEFAULT_CONFIG[key]))
        entries_thresholds[key] = entry

    # ODD_CENTER Checkbox
    odd_center_var = tk.BooleanVar(value=DEFAULT_CONFIG["ODD_CENTER"])
    odd_center_chk = ttk.Checkbutton(options_frame, text="Odd Center", variable=odd_center_var)
    odd_center_chk.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

    # Check Dimensions Checkbox
    check_dimensions_var = tk.BooleanVar(value=DEFAULT_CONFIG["CHECK_DIMENSIONS"])
    check_dimensions_chk = ttk.Checkbutton(options_frame, text="Check Dimensions", variable=check_dimensions_var)
    check_dimensions_chk.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

    # Calculate Button
    calculate_button = ttk.Button(buttons_frame, text="Calculate")
    calculate_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Define Treeview Columns including "Odd Center" and "Diameter"
    columns = ("Tested Radius", "Sides", "Real Radius", "Max Difference", "Odd Center", "Diameter")

    # Export Button
    export_button = ttk.Button(buttons_frame, text="Export to CSV", command=lambda: export_to_csv(list(tree.item_data.values())))
    export_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Overlay Checkbox
    overlay_var = tk.BooleanVar(value=False)
    overlay_check = ttk.Checkbutton(buttons_frame, text="Show Overlay", variable=overlay_var,
                                    command=lambda: toggle_overlay(getattr(tree, 'canvas_ref', None)))
    overlay_check.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Progress Bar
    progress_bar = ttk.Progressbar(buttons_frame, orient=tk.HORIZONTAL, mode='determinate')

    # Bottom Frame for Treeview and Plot
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Treeview Frame
    table_frame = ttk.Frame(bottom_frame)
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

    # Define Treeview with Updated Columns
    tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER, width=100)
    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    tree.item_data = {}

    # Plot Frame
    plot_frame = ttk.Frame(bottom_frame)
    plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    canvas_frame = ttk.Frame(plot_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    # Sorting Order Dictionary
    sort_order = {col: False for col in columns}
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_treeview(tree, _col, sort_order[_col], sort_order))

    # Bind Row Selection
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_selected(event, tree, canvas_frame, {
        "ODD_CENTER": odd_center_var.get(),
        "INITIAL_RADIUS": float(entries_circle["INITIAL_RADIUS"].get()),
        "MAX_RADIUS": float(entries_circle["MAX_RADIUS"].get()),
        "RADIUS_INCREMENT": float(entries_thresholds["RADIUS_INCREMENT"].get()),
        "CHECK_DIMENSIONS": check_dimensions_var.get(),
        "DIFFERENCE_THRESHOLD": float(entries_thresholds["DIFFERENCE_THRESHOLD"].get())
    }))

    # Configure Calculate Button Command
    calculate_button.config(command=lambda: on_calculate_click(
        entries_circle,
        entries_thresholds,
        check_dimensions_var,
        tree,
        canvas_frame,
        progress_bar,
        calculate_button,
        odd_center_var
    ))

    # No initial run
    root.mainloop()

if __name__ == "__main__":
    main()
