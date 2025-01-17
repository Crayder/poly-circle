import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import math
import threading
from constants import DEFAULT_CONFIG, SM_BLOCK_INFO
import database
import plot
import poly
import blueprint
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import ImageTk, Image

def on_row_selected(event, tree, canvas_frame, difference_threshold, min_radius, max_radius):
    selected_item = tree.focus()
    if not selected_item:
        return
    data_tuple = tree.item_data.get(selected_item)
    if not data_tuple:
        return

    # The DB row returns the columns in the order: (tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, odd_center, uniformity)
    tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_str, db_odd_center, uniformity = data_tuple

    # Reconstruct the polygon from grid_points text
    points_str = grid_str.strip()
    point_pairs = points_str.split(')')
    points = []
    for p in point_pairs:
        p = p.strip().strip(',')
        if p.startswith('('):
            p = p[1:]
        if p:
            try:
                x_str, y_str = p.split(',')
                x, y = float(x_str), float(y_str)
                points.append((x, y))
            except ValueError:
                continue
    polygon = tuple(points)

    # Determine odd_center for plotting based on row's odd_center value
    if db_odd_center == 1:
        odd_center_for_plot = "Odd"
    else:
        odd_center_for_plot = "Even"

    # Calculate center based on odd_center
    if odd_center_for_plot == "Odd":
        center_x, center_y = 0.5, 0.5
    else:
        center_x, center_y = 0.0, 0.0

    # Convert polygon to rects and wedges
    rects, wedges = poly.convert_polygon_to_blueprint(polygon, center_x, center_y)

    for widget in canvas_frame.winfo_children():
        widget.destroy()

    toolbar_frame = ttk.Frame(canvas_frame)
    toolbar_frame.pack(side=tk.TOP, fill=tk.X)

    plot_frame = ttk.Frame(canvas_frame)
    plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    fig, ax = plot.create_plot(
        odd_center=odd_center_for_plot,
        tested_radius=tested_radius,
        sides=sides,
        real_radius=real_radius,
        max_diff=max_diff,
        max_width=max_width,
        diameter=diameter,
        circularity=circularity,
        uniformity=uniformity,
        grid_points=polygon
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

    # Create overlay based on odd_center
    plot.create_overlay(ax, center_x, center_y, polygon)

    # Set overlay visibility based on checkbox state
    visible = tree.overlay_var.get()
    plot.set_overlay_visibility(ax, canvas, visible)

    # Store current Axes, Canvas, rects, and wedges for export
    tree.current_ax = ax
    tree.current_canvas = canvas
    tree.current_rects = rects
    tree.current_wedges = wedges

def sort_treeview(tree, col, reverse, sort_order):
    l = [(tree.set(k, col), k) for k in tree.get_children('')]
    if not l:
        return

    try:
        # Attempt to convert to float for numeric sorting
        float(l[0][0].replace(',', ''))
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
    tree.heading(col, text=tree.heading(col)['text'], command=lambda: sort_treeview(tree, col, sort_order[col], sort_order))

def create_gui():
    root = tk.Tk()
    root.title("Polygon Radius App (Database Edition)")
    root.geometry("1200x900")

    input_frame = ttk.Frame(root)
    input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # --- Normal Mode Frames ---

    # Thresholds Frame
    thresholds_frame = ttk.LabelFrame(input_frame, text="Thresholds")
    thresholds_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Radius Range Frame
    radius_frame = ttk.LabelFrame(input_frame, text="Radius Range")
    radius_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Diameter Range Frame
    diameter_frame = ttk.LabelFrame(input_frame, text="Diameter Range")
    diameter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # We'll hold these frames in a list so we can hide/show them in custom mode
    normal_mode_frames = [thresholds_frame, radius_frame, diameter_frame]

    # --- Buttons Frame (always visible) ---
    buttons_frame = ttk.Frame(input_frame)
    buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Thresholds Frame Inputs ---
    entries_thresholds = {}
    
    # Difference Threshold
    label_diff = ttk.Label(thresholds_frame, text="Difference Threshold:")
    label_diff.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    entry_diff = ttk.Entry(thresholds_frame, width=15)
    entry_diff.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    entry_diff.insert(0, str(DEFAULT_CONFIG["DIFFERENCE_THRESHOLD"]))
    entries_thresholds["DIFFERENCE_THRESHOLD"] = entry_diff

    # Circularity Threshold Entry
    label_circ_thresh = ttk.Label(thresholds_frame, text="Circularity Threshold:")
    label_circ_thresh.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    entry_circ_thresh = ttk.Entry(thresholds_frame, width=15)
    entry_circ_thresh.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    entry_circ_thresh.insert(0, str(DEFAULT_CONFIG["CIRCULARITY_THRESHOLD"]))
    entries_thresholds["CIRCULARITY_THRESHOLD"] = entry_circ_thresh

    # Uniformity Threshold Entry
    label_uniform_thresh = ttk.Label(thresholds_frame, text="Uniformity Threshold:")
    label_uniform_thresh.grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
    entry_uniform_thresh = ttk.Entry(thresholds_frame, width=15)
    entry_uniform_thresh.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    entry_uniform_thresh.insert(0, str(DEFAULT_CONFIG["UNIFORMITY_THRESHOLD"]))
    entries_thresholds["UNIFORMITY_THRESHOLD"] = entry_uniform_thresh

    # Max Width
    label_max_width = ttk.Label(thresholds_frame, text="Max Width:")
    label_max_width.grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
    spin_max_width = ttk.Spinbox(thresholds_frame, from_=1, to=8, width=13)
    spin_max_width.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
    spin_max_width.set(str(DEFAULT_CONFIG["MAX_WIDTH"]))
    entries_thresholds["MAX_WIDTH"] = spin_max_width

    # Min Radius Entry
    entries_radius = {}
    label_min_radius = ttk.Label(radius_frame, text="Min Radius:")
    label_min_radius.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    entry_min_radius = ttk.Entry(radius_frame, width=15)
    entry_min_radius.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    entry_min_radius.insert(0, str(DEFAULT_CONFIG["MIN_RADIUS"]))
    entries_radius["MIN_RADIUS"] = entry_min_radius

    # Max Radius Entry
    label_max_radius = ttk.Label(radius_frame, text="Max Radius:")
    label_max_radius.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    entry_max_radius = ttk.Entry(radius_frame, width=15)
    entry_max_radius.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    entry_max_radius.insert(0, str(DEFAULT_CONFIG["MAX_RADIUS"]))
    entries_radius["MAX_RADIUS"] = entry_max_radius

    # Min Diameter Entry (Spinbox)
    entries_diameter = {}
    label_min_diameter = ttk.Label(diameter_frame, text="Min Diameter:")
    label_min_diameter.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    spin_min_diameter = ttk.Spinbox(diameter_frame, from_=1, to=400, width=13)
    spin_min_diameter.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    spin_min_diameter.set(str(DEFAULT_CONFIG["MIN_DIAMETER"]))
    entries_diameter["MIN_DIAMETER"] = spin_min_diameter

    # Max Diameter Entry (Spinbox)
    label_max_diameter = ttk.Label(diameter_frame, text="Max Diameter:")
    label_max_diameter.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    spin_max_diameter = ttk.Spinbox(diameter_frame, from_=1, to=400, width=13)
    spin_max_diameter.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    spin_max_diameter.set(str(DEFAULT_CONFIG["MAX_DIAMETER"]))
    entries_diameter["MAX_DIAMETER"] = spin_max_diameter

    # Odd Center Selection
    label_odd_center = ttk.Label(diameter_frame, text="Odd Center:")
    label_odd_center.grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
    odd_center_var = tk.StringVar(value=DEFAULT_CONFIG["ODD_CENTER"])
    combo_odd_center = ttk.Combobox(diameter_frame, textvariable=odd_center_var, state="readonly",
                                    values=["Both", "Odd", "Even"], width=11)
    combo_odd_center.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

    # --- Load / Run Query Button ---
    load_button = ttk.Button(buttons_frame, text="Load / Run Query",
                             command=lambda: on_load_click(odd_center_var,
                                                           entries_thresholds,
                                                           entries_radius,
                                                           entries_diameter,
                                                           tree,
                                                           canvas_frame))
    load_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Define Treeview Columns (match the DB exactly excluding the grid_points column)
    columns = (
        "tested_radius", "sides", "real_radius", "max_diff",
        "max_width", "diameter", "circularity", "uniformity", "odd_center"
    )

    # Overlay Checkbox
    overlay_var = tk.BooleanVar(value=False)
    overlay_check = ttk.Checkbutton(buttons_frame, text="Show Overlay", variable=overlay_var,
                                    command=lambda: on_overlay_toggle(
                                        tree, 
                                        overlay_var.get()
                                    ))
    overlay_check.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # --- Export Blueprint Button ---
    export_button = ttk.Button(buttons_frame, text="Export Blueprint",
                               command=lambda: on_export_click(
                                   tree
                               ))
    export_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Bottom Frame for Treeview and Plot
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Treeview Frame
    table_frame = ttk.Frame(bottom_frame)
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

    # Define Treeview with Updated Columns and Horizontal Scrollbar
    tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, anchor=tk.CENTER, width=80)
    scrollbar_vertical = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar_horizontal = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)  # Added horizontal scrollbar
    tree.configure(yscroll=scrollbar_vertical.set, xscroll=scrollbar_horizontal.set)
    scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)  # Pack horizontal scrollbar
    tree.pack(fill=tk.BOTH, expand=True)

    tree.item_data = {}
    tree.current_ax = None
    tree.current_canvas = None
    tree.current_rects = []
    tree.current_wedges = []
    tree.overlay_var = overlay_var  # Assign the overlay_var to tree for easy access

    # Plot Frame
    plot_frame = ttk.Frame(bottom_frame)
    plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    canvas_frame = ttk.Frame(plot_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    # Sorting Order Dictionary
    sort_order = {col: False for col in columns}
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title(), command=lambda _col=col: sort_treeview(tree, _col, sort_order[_col], sort_order))

    # Bind Row Selection
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_selected(
        event,
        tree,
        canvas_frame,
        float(entries_thresholds["DIFFERENCE_THRESHOLD"].get() or 0),
        float(entries_radius["MIN_RADIUS"].get() or 0),
        float(entries_radius["MAX_RADIUS"].get() or 0)
    ))

    return root, tree, canvas_frame, overlay_var

def on_overlay_toggle(tree, visible):
    if tree.current_ax and tree.current_canvas:
        plot.set_overlay_visibility(tree.current_ax, tree.current_canvas, visible)

def on_load_click(odd_center_var, entries_thresholds, entries_radius, entries_diameter, 
                  tree, canvas_frame):
    """
    Load data based on the user inputs and display in the TreeView.
    """
    try:
        # Normal mode
        difference_threshold = float(entries_thresholds["DIFFERENCE_THRESHOLD"].get())
        if difference_threshold < 0:
            raise ValueError("Difference Threshold cannot be negative.")

        circularity_threshold = float(entries_thresholds["CIRCULARITY_THRESHOLD"].get())
        if not (0.0 <= circularity_threshold <= 1.0):
            raise ValueError("Circularity Threshold must be between 0.0 and 1.0.")

        uniformity_threshold = float(entries_thresholds["UNIFORMITY_THRESHOLD"].get())
        if not (0.0 <= uniformity_threshold <= 1.0):
            raise ValueError("Uniformity Threshold must be between 0.0 and 1.0.")

        max_width_threshold = int(entries_thresholds["MAX_WIDTH"].get())
        if not (1 <= max_width_threshold <= 8):
            raise ValueError("Max Width must be between 1 and 8.")

        min_radius = float(entries_radius["MIN_RADIUS"].get())
        max_radius = float(entries_radius["MAX_RADIUS"].get())
        if min_radius < 0 or min_radius > 200:
            raise ValueError("Min Radius must be between 0 and 200.")
        if max_radius < 0 or max_radius > 200:
            raise ValueError("Max Radius must be between 0 and 200.")
        if min_radius > max_radius:
            raise ValueError("Min Radius cannot be greater than Max Radius.")

        min_diameter = int(entries_diameter["MIN_DIAMETER"].get())
        max_diameter = int(entries_diameter["MAX_DIAMETER"].get())
        if not (1 <= min_diameter <= 400):
            raise ValueError("Min Diameter must be between 1 and 400.")
        if not (1 <= max_diameter <= 400):
            raise ValueError("Max Diameter must be between 1 and 400.")
        if min_diameter > max_diameter:
            raise ValueError("Min Diameter cannot be greater than Max Diameter.")

        odd_center_val = odd_center_var.get()  # "Odd", "Even", or "Both"

        # Start a new thread to avoid freezing the GUI
        threading.Thread(target=fetch_and_display, args=(
            difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold,
            odd_center_val, min_radius, max_radius, min_diameter, max_diameter,
            tree, canvas_frame
        ), daemon=True).start()

    except ValueError as ve:
        messagebox.showerror("Invalid Input", str(ve))
        return
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

def fetch_and_display(difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold,
                     odd_center_val, min_radius, max_radius, min_diameter, max_diameter,
                     tree, canvas_frame):
    rows = database.load_results_from_db(difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold,
                                        odd_center_val, min_radius, max_radius, min_diameter, max_diameter)

    # Schedule the insertion of rows in the main thread
    tree.after(0, insert_rows, tree, rows, canvas_frame)

def insert_rows(tree, rows, canvas_frame):
    # Clear the tree
    tree.delete(*tree.get_children())
    tree.item_data.clear()

    if not rows:
        messagebox.showinfo("No Results", "No polygons found for the query.")
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        return

    # Sort by sides ascending (column index 1 is sides)
    sorted_rows = sorted(rows, key=lambda x: x[1])  # x[1] = sides

    # Insert into the TreeView
    # columns = ("tested_radius", "sides", "real_radius", "max_diff", "max_width", "diameter", "circularity", "uniformity", "odd_center")
    for row in sorted_rows:
        # row is (tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, oc_val, uniformity)
        tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, oc_val, uniformity = row

        # Insert into the tree
        # We'll show them in the exact order as columns, excluding grid_points
        tree_vals = (
            f"{tested_radius:.4f}",  # tested_radius
            f"{sides}",              # sides
            f"{real_radius:.4f}",    # real_radius
            f"{max_diff:.4f}",       # max_diff
            f"{max_width}",          # max_width
            f"{diameter}",           # diameter
            f"{circularity:.4f}",    # circularity
            f"{uniformity:.4f}",     # uniformity
            "Yes" if oc_val else "No"  # odd_center as string
        )
        # Insert row
        iid = tree.insert("", tk.END, values=tree_vals)
        tree.item_data[iid] = row  # store raw tuple for on_row_selected

    # Auto-select first row
    if tree.get_children():
        first_id = tree.get_children()[0]
        tree.selection_set(first_id)
        tree.focus(first_id)
        # Force on_row_selected to parse/plot the first row
        tree.event_generate("<<TreeviewSelect>>")

def on_export_click(tree):
    """
    Handles the Export Blueprint button click.
    """
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror("No Selection", "Please select a polygon to export.")
        return

    data_tuple = tree.item_data.get(selected_item)
    if not data_tuple:
        messagebox.showerror("Error", "Selected item data is unavailable.")
        return

    # Ensure that rects and wedges are available
    rects = getattr(tree, 'current_rects', [])
    wedges = getattr(tree, 'current_wedges', [])

    # Create a new top-level window for export options
    export_window = tk.Toplevel()
    export_window.title("Export Blueprint")

    # Material Choice Dropdown
    label_material = ttk.Label(export_window, text="Select Material:")
    label_material.grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
    material_var = tk.StringVar()
    material_dropdown = ttk.Combobox(export_window, textvariable=material_var, state="readonly",
                                     values=list(SM_BLOCK_INFO.keys()), width=30)
    material_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
    material_dropdown.set(list(SM_BLOCK_INFO.keys())[0])  # Set default to first material

    # Thickness Spinbox
    label_thickness = ttk.Label(export_window, text="Select Thickness (1-8):")
    label_thickness.grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
    thickness_var = tk.IntVar(value=1)
    thickness_spin = ttk.Spinbox(export_window, from_=1, to=8, textvariable=thickness_var, width=28)
    thickness_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

    # Name Entry
    label_name = ttk.Label(export_window, text="Blueprint Name:")
    label_name.grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
    # Set default name with diameter and sides
    diameter = data_tuple[5]
    sides = data_tuple[1]
    default_name = f"Wedge Circle - {diameter} Diameter / {sides} Sides"
    name_var = tk.StringVar(value=default_name)
    name_entry = ttk.Entry(export_window, textvariable=name_var, width=30)
    name_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

    # --- New: Place Center Marker Checkbox ---
    center_marker_var = tk.BooleanVar(value=False)
    center_marker_check = ttk.Checkbutton(export_window, text="Place Center Marker", variable=center_marker_var)
    center_marker_check.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # Export Button
    export_btn = ttk.Button(export_window, text="Export",
                            command=lambda: perform_export(export_window, rects, wedges, diameter=data_tuple[5],
                                material_choice=material_var.get(),
                                thickness=thickness_var.get(),
                                name=name_var.get(),
                                real_radius=data_tuple[2],
                                sides=data_tuple[1],
                                circularity=data_tuple[6],
                                uniformity=data_tuple[8],
                                center_marker=center_marker_var.get()  # new parameter
                            ))
    export_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=20)

def perform_export(export_window, rects, wedges, diameter, material_choice, thickness, name, real_radius, sides, circularity, uniformity, center_marker):
    """
    Performs the export after user has provided options.
    """
    try:
        blueprint_uuid = blueprint.export_blueprint(rects, wedges, diameter, material_choice, thickness, name, real_radius, sides, circularity, uniformity, center_marker)
        messagebox.showinfo("Success", f"Blueprint exported successfully!\nUUID: {blueprint_uuid}")
        export_window.destroy()
    except Exception as e:
        messagebox.showerror("Export Failed", f"An error occurred during export:\n{str(e)}")
