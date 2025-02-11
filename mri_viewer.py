import os
import numpy as np
import pydicom
import PySimpleGUI as sg

from PIL import Image
from io import BytesIO

def normalize_array(arr):
    """Normalize array values to range [0, 1], avoiding division by zero."""
    arr_min = np.min(arr)
    arr_max = np.max(arr)
    if arr_max - arr_min == 0:
        return arr
    return (arr - arr_min) / (arr_max - arr_min)

def Contrast(r1_map, r2_map, TE, TI, TR, min_value, max_value):
    """
    Custom function to compute 'Contrast_value' from R1/R2 maps.
    Adapted from your original code.
    """
    TI1 = 500
    TI2 = TI
    Tao = TE / 2.0

    # Example from your code:
    Contrast_value = abs(
        1 - 2 * np.exp(-TI1 * r1_map)
        + 2 * np.exp(-TI1 * r1_map) * np.exp(-TI2 * r1_map)
        - np.exp(-TR * r1_map) * (2 / np.exp(-Tao * r1_map) - 1)
    ) * np.exp(-TE * r2_map)

    return np.clip(Contrast_value, min_value, max_value)

def open_and_display_mri(r1_data_path, r2_data_path, slice_id, TE, TI, TR, min_value, max_value):
    """
    Reads the specified DICOM slice from R1_map and R2_map folders,
    applies the Contrast function, normalizes the resulting array,
    and returns a displayable numpy array.
    """
    # Format the slice index (similar to your code)
    if slice_id < 100:
        formatted_slice_index = f"{slice_id + 1:02d}"
    else:
        formatted_slice_index = f"{slice_id + 1:03d}"

    # ---- Read R1 ----
    r1_dicom_path = os.path.join(r1_data_path, f"SLICE_{formatted_slice_index}.dcm")
    r1_dicom_data = pydicom.dcmread(r1_dicom_path)
    r1_pixel_array = r1_dicom_data.pixel_array.astype(float)

    # Rescale for R1
    r1_slope = float(getattr(r1_dicom_data, 'RescaleSlope', 1.0))
    r1_intercept = float(getattr(r1_dicom_data, 'RescaleIntercept', 0.0))
    r1_map = (r1_pixel_array * r1_slope + r1_intercept) / 1000.0
    r1_non_zero_mask = (r1_map != 0)

    # ---- Read R2 ----
    r2_dicom_path = os.path.join(r2_data_path, f"SLICE_{formatted_slice_index}.dcm")
    r2_dicom_data = pydicom.dcmread(r2_dicom_path)
    r2_pixel_array = r2_dicom_data.pixel_array.astype(float)

    # Rescale for R2
    r2_slope = float(getattr(r2_dicom_data, 'RescaleSlope', 1.0))
    r2_intercept = float(getattr(r2_dicom_data, 'RescaleIntercept', 0.0))
    r2_map = (r2_pixel_array * r2_slope + r2_intercept) / 1000.0

    # ---- Calculate Contrast Value ----
    contrast_val = np.where(
        r1_non_zero_mask,
        Contrast(r1_map, r2_map, TE, TI, TR, min_value, max_value),
        r1_map  # if R1 is zero, keep original
    )

    contrast_val = normalize_array(contrast_val)
    return contrast_val

def main():
    """
    Main function: PySimpleGUI app for reading user inputs
    and displaying the resulting MRI contrast image.
    """

    # 1) Disable default PySimpleGUI icon to fix `_tkinter.TclError` on macOS
    sg.theme("DarkBlue3")  # or any other theme
    # 2) Define UI Layout
    layout = [
        [sg.Text("Path to folder containing R1_map:"), sg.Input(key="-R1_PATH-"), sg.FolderBrowse()],
        [sg.Text("Path to folder containing R2_map:"), sg.Input(key="-R2_PATH-"), sg.FolderBrowse()],
        [sg.Text("Slice index:"), sg.Input("0", size=(10, 1), key="-SLICE_ID-")],
        [sg.Text("TE:"), sg.Input("10", size=(10, 1), key="-TE-")],
        [sg.Text("TI:"), sg.Input("100", size=(10, 1), key="-TI-")],
        [sg.Text("TR:"), sg.Input("6000", size=(10, 1), key="-TR-")],
        [sg.Text("Min value:"), sg.Input("-1", size=(10, 1), key="-MIN_VAL-")],
        [sg.Text("Max value:"), sg.Input("1", size=(10, 1), key="-MAX_VAL-")],
        [sg.Button("Compute"), sg.Button("Exit")],
        [sg.Text("Result Image:")],
        [sg.Image(key="-IMAGE-", size=(400, 400))]
    ]

    # 3) Create the window
    window = sg.Window("MRI Contrast Viewer", layout, resizable=True)

    # 4) Event Loop
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == "Compute":
            try:
                # Extract user inputs
                r1_path = values["-R1_PATH-"]
                r2_path = values["-R2_PATH-"]
                slice_id = int(values["-SLICE_ID-"])
                TE = float(values["-TE-"])
                TI = float(values["-TI-"])
                TR = float(values["-TR-"])
                min_value = float(values["-MIN_VAL-"])
                max_value = float(values["-MAX_VAL-"])

                # Compute the resulting numpy array
                result_array = open_and_display_mri(
                    r1_data_path=r1_path,
                    r2_data_path=r2_path,
                    slice_id=slice_id,
                    TE=TE,
                    TI=TI,
                    TR=TR,
                    min_value=min_value,
                    max_value=max_value
                )

                # Convert numpy array to a displayable image
                #  -- scale [0,1] -> [0,255] for 8-bit
                result_8bit = (result_array * 255).astype(np.uint8)
                img = Image.fromarray(result_8bit)

                # Convert to PNG in memory
                bio = BytesIO()
                img.save(bio, format="PNG")
                window["-IMAGE-"].update(data=bio.getvalue())

            except Exception as e:
                sg.popup_error(f"Error: {e}", title="Computation Error")

    window.close()

if __name__ == "__main__":
    main()
