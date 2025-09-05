import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Your generate_spacer_scad function here
import os
import shutil
import subprocess
import math

def generate_spacer_scad(
    filename="battery_spacer.scad",
    stl_filename="battery_spacer.stl",
    cell_type="21700",
    diameter_adjustment=0.2,
    series_cells=4,
    parallel_cells=5,
    slanted=True
):
    # Cell specs
    cell_dimensions = {
        "18650": {"diameter": 18.6, "height": 65.0},
        "21700": {"diameter": 21.3, "height": 70.0},
    }

    if cell_type not in cell_dimensions:
        raise ValueError("Invalid cell_type. Use '18650' or '21700'.")

    d = cell_dimensions[cell_type]["diameter"] + diameter_adjustment
    spacing = 22.4
    radius = d / 2
    spacer_thickness = 12
    padding = 4.0
    corner_radius = 8.0

    insulator_thickness = 0.4
    insulator_depth = 0
    insulator_outer_d = 22.0
    insulator_inner_d = 12.9

    row_height = spacing * 0.866 if slanted else spacing  # Ensure this handles non-slanted rows
    col_offset = spacing / 2 if (slanted and parallel_cells > 1) else 0

    body_width = (series_cells - 1) * spacing + d + col_offset + 2 * padding
    body_height = (parallel_cells - 1) * row_height + d + 2 * padding

    lines = ["// Battery Spacer with Flush Insulator Rings"]

    # Modules
    lines.append(f"""
module cell_hole() {{
    cylinder(h={spacer_thickness + 2}, d={d:.3f}, $fn=100);
}}

module cell_insulator() {{
    difference() {{
        cylinder(h={insulator_thickness}, d={insulator_outer_d}, $fn=100);
        cylinder(h={insulator_thickness}, d={insulator_inner_d}, $fn=100);
    }}
}}

module rounded_spacer_body() {{
    offset(r={corner_radius})
        offset(delta=-{corner_radius})
            square([{body_width:.3f}, {body_height:.3f}], center=false);
}}
    """.strip())

    # Spacer + holes
    lines.append("difference() {")
    lines.append(f"    linear_extrude(height={spacer_thickness}) rounded_spacer_body();")

    for y in range(parallel_cells):
        for x in range(series_cells):
            offset_x = spacing / 2 if (slanted and (y % 2 == 1)) else 0
            pos_x = x * spacing + offset_x + radius + padding
            pos_y = y * row_height + radius + padding
            lines.append(f"    translate([{pos_x:.3f}, {pos_y:.3f}, -1]) cell_hole();")
    lines.append("}")

    # Flush insulator rings — protruding into holes
    for y in range(parallel_cells):
        for x in range(series_cells):
            offset_x = spacing / 2 if (slanted and (y % 2 == 1)) else 0
            pos_x = x * spacing + offset_x + radius + padding
            pos_y = y * row_height + radius + padding
            z_pos = -insulator_depth
            lines.append(f"translate([{pos_x:.3f}, {pos_y:.3f}, {z_pos:.3f}]) cell_insulator();")

    # Save SCAD
    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ SCAD file written: {filename}")

    # Render STL
    openscad_cmd = "openscad.exe" if os.name == "nt" else "openscad"
    if shutil.which(openscad_cmd):
        try:
            subprocess.run([openscad_cmd, "-o", stl_filename, filename], check=True)
            print(f"✅ STL generated: {stl_filename}")
        except subprocess.CalledProcessError as e:
            print(f"❌ OpenSCAD rendering failed: {e}")
    else:
        print("⚠️ OpenSCAD not found in PATH.")

# Create the GUI
class SpacerGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Battery Spacer Generator")

        # Cell type
        self.cell_type_label = tk.Label(root, text="Cell Type:")
        self.cell_type_label.grid(row=0, column=0, padx=10, pady=5)
        self.cell_type = ttk.Combobox(root, values=["18650", "21700"])
        self.cell_type.set("21700")
        self.cell_type.grid(row=0, column=1, padx=10, pady=5)

        # Diameter adjustment
        self.diameter_adjustment_label = tk.Label(root, text="Diameter Adjustment (mm):")
        self.diameter_adjustment_label.grid(row=1, column=0, padx=10, pady=5)
        self.diameter_adjustment = tk.DoubleVar(value=0.2)
        self.diameter_adjustment_entry = tk.Entry(root, textvariable=self.diameter_adjustment)
        self.diameter_adjustment_entry.grid(row=1, column=1, padx=10, pady=5)

        # Series cells
        self.series_cells_label = tk.Label(root, text="Series Cells:")
        self.series_cells_label.grid(row=2, column=0, padx=10, pady=5)
        self.series_cells = tk.IntVar(value=4)
        self.series_cells_entry = tk.Entry(root, textvariable=self.series_cells)
        self.series_cells_entry.grid(row=2, column=1, padx=10, pady=5)

        # Parallel cells
        self.parallel_cells_label = tk.Label(root, text="Parallel Cells:")
        self.parallel_cells_label.grid(row=3, column=0, padx=10, pady=5)
        self.parallel_cells = tk.IntVar(value=5)
        self.parallel_cells_entry = tk.Entry(root, textvariable=self.parallel_cells)
        self.parallel_cells_entry.grid(row=3, column=1, padx=10, pady=5)

        # Slanted option
        self.slanted_label = tk.Label(root, text="Slanted:")
        self.slanted_label.grid(row=4, column=0, padx=10, pady=5)
        self.slanted_var = tk.BooleanVar(value=True)
        self.slanted_check = tk.Checkbutton(root, variable=self.slanted_var)
        self.slanted_check.grid(row=4, column=1, padx=10, pady=5)

        # Output file names
        self.filename_label = tk.Label(root, text="SCAD File Name:")
        self.filename_label.grid(row=5, column=0, padx=10, pady=5)
        self.filename_entry = tk.Entry(root)
        self.filename_entry.grid(row=5, column=1, padx=10, pady=5)
        self.filename_entry.insert(0, "battery_spacer_final.scad")

        self.stl_filename_label = tk.Label(root, text="STL File Name:")
        self.stl_filename_label.grid(row=6, column=0, padx=10, pady=5)
        self.stl_filename_entry = tk.Entry(root)
        self.stl_filename_entry.grid(row=6, column=1, padx=10, pady=5)
        self.stl_filename_entry.insert(0, "battery_spacer_final.stl")

        # Generate button
        self.generate_button = tk.Button(root, text="Generate Spacer", command=self.generate)
        self.generate_button.grid(row=7, column=0, columnspan=2, pady=10)

    def generate(self):
        filename = self.filename_entry.get()
        stl_filename = self.stl_filename_entry.get()
        cell_type = self.cell_type.get()
        diameter_adjustment = self.diameter_adjustment.get()
        series_cells = self.series_cells.get()
        parallel_cells = self.parallel_cells.get()
        slanted = self.slanted_var.get()

        try:
            generate_spacer_scad(
                filename=filename,
                stl_filename=stl_filename,
                cell_type=cell_type,
                diameter_adjustment=diameter_adjustment,
                series_cells=series_cells,
                parallel_cells=parallel_cells,
                slanted=slanted
            )
            messagebox.showinfo("Success", f"SCAD and STL files generated: {filename}, {stl_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = SpacerGeneratorApp(root)
    root.mainloop()
