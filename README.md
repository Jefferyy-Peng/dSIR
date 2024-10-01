# dSIR

# My Python Program

## Overview
This Python program uses `Gradio` to provide an interactive interface and includes libraries such as `numpy` and `pydicom` for data processing. The interface will provide a link once you run the program, allowing you to interact with it in your browser.

## Prerequisites
Before running the program, make sure you have Python installed on your system (Python 3.9 or later is recommended).

## Installation

To get started, you'll need to install the required Python libraries: `numpy`, `gradio`, and `pydicom`.

### Install dependencies using pip:
1. Open your terminal or command prompt.
2. Run the following command to install the required packages:

```bash
pip install numpy gradio pydicom
```

## Run
Run the program named `mri_app.py`, the program will generate an url link. E.g.:`Running on local URL:  http://127.0.0.1:7860`

Copy the url and open it in your web browser.

After open the link, fill in the path to your R1 Map dicom files. For example, `/Users/amadeus/Downloads/SyMRI_processed_DL/HD_1_DL/1202_R1_MAP_AX`. Then you can tune the parameters and click on the `Submit` button.
