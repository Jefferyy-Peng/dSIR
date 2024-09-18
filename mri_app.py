import os

import gradio as gr
import pydicom
import numpy as np

def normalize_array(arr):
    arr_min = np.min(arr)
    arr_max = np.max(arr)
    if arr_max - arr_min == 0:
        return arr  # Avoid division by zero if all values are the same
    return (arr - arr_min) / (arr_max - arr_min)

def dSIR(r1_map, TIs, TIi, min_value, max_value):
    dsir_value = (np.exp(-TIs * r1_map) - np.exp(-TIi * r1_map)) / (
            1 - np.exp(-TIs * r1_map) - np.exp(-TIi * r1_map) + np.exp(-15000 * r1_map)
    )
    # dsir_value = (
    #         1 - np.exp(-TIs * r1_map) - np.exp(-TIi * r1_map) + np.exp(-15000 * r1_map)
    # ) / (np.exp(-TIs * r1_map) - np.exp(-TIi * r1_map))
    return np.clip(dsir_value, min_value, max_value)
    # return (np.exp(-TIs * r1_map) - np.exp(-TIi * r1_map))
def open_and_display_mri(data_path, slice_id, TIs, TIi, min_value, max_value):
    if slice_id < 100:
        formatted_slice_index = f"{slice_id+1:02d}"
    else:
        formatted_slice_index = f"{slice_id+1:03d}"
    dicom_path = os.path.join(data_path, f"SLICE_{formatted_slice_index}.dcm")

    dicom_data = pydicom.dcmread(dicom_path)

    # Extract the rescale slope and intercept
    rescale_slope = dicom_data.RescaleSlope
    rescale_intercept = dicom_data.RescaleIntercept

    # Convert pixel data to a numpy array
    pixel_array = dicom_data.pixel_array
    # Apply the rescaling and convert to ms^-1
    r1_map = (pixel_array * rescale_slope + rescale_intercept) / 1000
    non_zero_mask = r1_map != 0
    dSIR_value = np.where(non_zero_mask, dSIR(r1_map, TIs, TIi, min_value, max_value), r1_map)
    #
    dSIR_value = normalize_array(dSIR_value)
    # dSIR_value = normalize_array(pixel_array)
        # pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) if (np.max(
        #     pixel_array) - np.min(pixel_array)) != 0 else pixel_array - np.min(pixel_array)
    return dSIR_value



# Create the Gradio interface
iface = gr.Interface(
    fn=open_and_display_mri,
    inputs=[
        gr.Textbox(label="Path to folder containing 3D array file"),
        gr.Number(label="Slice index"),
        gr.Number(label="TI_s"),
        gr.Number(label="TI_i"),
        gr.Number(label="min_value"),
        gr.Number(label="max_value")
    ],
    outputs=gr.Image(type="numpy", label="dSIR")
)

# Launch the app
iface.launch()