import nibabel as nib
import matplotlib.pyplot as plt

def convert_nii_to_3d_image(nii_file_path):
    # Load the NIfTI file
    nii_img = nib.load(nii_file_path)
    
    # Get the image data as a NumPy array
    img_data = nii_img.get_fdata()
    
    # Plot the 3D image
    plt.figure()
    plt.imshow(img_data[:, :, img_data.shape[2] // 2], cmap='gray')  # Display the middle slice
    plt.show()

# Provide the path to your NIfTI file
nii_file_path = '/content/drive/MyDrive/Colab Notebooks/liver_54.nii.gz'

# Convert and display the 3D image
convert_nii_to_3d_image(nii_file_path)


