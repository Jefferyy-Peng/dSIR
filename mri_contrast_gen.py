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


def Contrast(r1_map, r2_map, pd_map, TE, TI, TR, min_value, max_value):
    # T1: TR/TE = 650/10, TI = 0, min/max = -1/1
    # T2: TR/TE = 6000/100, TI = 0, min/max = -1/1
    # STIR: TR/TE = 6000/100, TI = 150 (fat supression), min/max = -1/1
    # IR: TR/TE = 6000/100, TI = 500 (WM supression), TI = 800 (GM supression),  min/max = -1/1
    # Contrast_value = abs(1 - 2 * np.exp(-TI * r1_map) + np.exp(-TR * r1_map)) * np.exp(-TE * r2_map)

    # PSIR: TR/TE = 6000/10, TI = 500, min/max = -1/0.2
    # Contrast_value = (1 - 2 * np.exp(-TI * r1_map) + np.exp(-TR * r1_map)) * np.exp(-TE * r2_map)

    # T2-FLAIR: TR/TE = 15000/100, TI1 = 300, TI2 = 3100, min/max = -1/0.5
    # DIR: TR/TE = 15000/10, TI1 = 500, TI2 = 3350, min/max = -1/0.5
    TI1 = 500
    TI2 = TI
    Tao = TE/2
    Contrast_value = 10 * pd_map * abs(1 - 2 * np.exp(-TI1 * r1_map) + 2 * np.exp(-TI1 * r1_map) * np.exp(-TI2 * r1_map) - np.exp(-TR * r1_map) * (2 / np.exp(-Tao * r1_map) - 1)) * np.exp(-TE * r2_map)

    # dSIR: TR/TE = 15000/10, TIs = 500, TIi = 750, min/max = -1/1
    TIs = TI
    TIi = TR
    TIs1 = 3350
    TIi1 = 3700
    contrast_value1 = abs(1 - 2 * np.exp(-TIs * r1_map) + np.exp(-15000 * r1_map))
    contrast_value2 = abs(1 - 2 * np.exp(-TIi * r1_map) + np.exp(-15000 * r1_map))
    # Had errors using the following fomular
    # Contrast_value1 = abs(1 - 2 * np.exp(-TIs * r1_map) + 2 * np.exp(-TIs * r1_map) * np.exp(-TIs1 * r1_map) - np.exp(-15000 * r1_map))
    # Contrast_value2 = abs(1 - 2 * np.exp(-TIi * r1_map) + 2 * np.exp(-TIi * r1_map) * np.exp(-TIi1 * r1_map) - np.exp(-15000 * r1_map))
    # Contrast_value = (contrast_value1 - contrast_value2) / (contrast_value1 + contrast_value2 + 0.000000000001)

    return np.clip(Contrast_value, min_value, max_value)


def open_and_display_mri(r1_data_path, r2_data_path, pd_data_path, slice_id, TE, TI, TR, min_value, max_value):
    if slice_id < 100:
        formatted_slice_index = f"{slice_id + 1:02d}"
    else:
        formatted_slice_index = f"{slice_id + 1:03d}"
    r1_dicom_path = os.path.join(r1_data_path, f"SLICE_{formatted_slice_index}.dcm")

    r1_dicom_data = pydicom.dcmread(r1_dicom_path)

    # Extract the rescale slope and intercept
    rescale_slope = r1_dicom_data.RescaleSlope
    rescale_intercept = r1_dicom_data.RescaleIntercept

    # Convert pixel data to a numpy array
    r1_pixel_array = r1_dicom_data.pixel_array
    # Apply the rescaling and convert to ms^-1
    r1_map = (r1_pixel_array * rescale_slope + rescale_intercept) / 1000
    r1_non_zero_mask = r1_map != 0

    r2_dicom_path = os.path.join(r2_data_path, f"SLICE_{formatted_slice_index}.dcm")

    r2_dicom_data = pydicom.dcmread(r2_dicom_path)

    # Extract the rescale slope and intercept
    rescale_slope = r2_dicom_data.RescaleSlope
    rescale_intercept = r2_dicom_data.RescaleIntercept

    # Convert pixel data to a numpy array
    r2_pixel_array = r2_dicom_data.pixel_array
    # Apply the rescaling and convert to ms^-1
    r2_map = (r2_pixel_array * rescale_slope + rescale_intercept) / 1000

    pd_dicom_path = os.path.join(pd_data_path, f"SLICE_{formatted_slice_index}.dcm")
    pd_dicom_data = pydicom.dcmread(pd_dicom_path)
    # Extract the rescale slope and intercept
    rescale_slope = pd_dicom_data.RescaleSlope
    rescale_intercept = pd_dicom_data.RescaleIntercept

    # Convert pixel data to a numpy array
    pd_pixel_array = pd_dicom_data.pixel_array
    # Apply the rescaling and convert to ms^-1
    pd_map = (pd_pixel_array * rescale_slope + rescale_intercept) / 1000

    dSIR_value = np.where(r1_non_zero_mask, Contrast(r1_map, r2_map, pd_map, TE, TI, TR, min_value, max_value), r1_map)
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
        gr.Textbox(label="Path to folder containing R1_map"),
        gr.Textbox(label="Path to folder containing R2_map"),
        gr.Textbox(label="Path to folder containing PD_map"),
        gr.Number(label="Slice index"),
        gr.Number(label="TE"),
        gr.Number(label="TI"),
        gr.Number(label="TR"),
        gr.Number(label="min_value"),
        gr.Number(label="max_value")
    ],
    outputs=gr.Image(type="numpy", label="dSIR")
)

# Launch the app
iface.launch()