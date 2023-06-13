import numpy as np
import nibabel as nib
from PIL import Image

def convert_nifti_to_png(nifti_file_path, output_folder):
    # Load NIfTI file
    nifti_image = nib.load(nifti_file_path)

    # Get the image data as a 3D numpy array
    image_data = np.array(nifti_image.get_fdata())

    # Normalize the image data to 0-255 range
    image_data = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data)) * 255

    # Convert to uint8 and transpose axes if necessary
    image_data = np.uint8(image_data)
    if image_data.ndim == 3:
        image_data = np.transpose(image_data, (1, 0, 2))

    # Save each slice as a colored PNG image
    for slice_idx in range(image_data.shape[2]):
        slice_data = image_data[:, :, slice_idx]

        # Create a grayscale PIL Image from the slice
        image_gray = Image.fromarray(slice_data, mode='L')

        # Convert grayscale image to RGB
        image_rgb = image_gray.convert('RGB')

        # Save the image as PNG
        output_path = f"{output_folder}/slice_{slice_idx}.png"
        image_rgb.save(output_path)

# Usage example
nifti_file_path = '/content/drive/MyDrive/Colab Notebooks/liver_54.nii.gz'
output_folder = '/content/drive/MyDrive/Colab Notebooks'
convert_nifti_to_png(nifti_file_path, output_folder)
