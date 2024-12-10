import os
import json
from PIL import Image
import zipfile

# Folder containing your images
image_folder = 'S:/Image Resources/360 Panoramic/Product Images/Sample'

# Output .tirf file name
output_file = 'output.tirf'

# Function to combine images and metadata into a .tirf file
def create_tirf(image_folder, output_file):
    images = []
    metadata = []

    # Iterate over files in the image folder
    for file_name in os.listdir(image_folder):
        if file_name.endswith(('.png', '.jpg', '.jpeg')):  # Add more image formats if needed
            file_path = os.path.join(image_folder, file_name)
            image = Image.open(file_path)
            images.append(file_path)

            # Add metadata (for now just file name, can be extended)
            metadata.append({
                'file_name': file_name,
                'size': image.size,
                'mode': image.mode
            })

    # Create a .zip file to store images and metadata
    with zipfile.ZipFile(output_file, 'w') as zipf:
        # Add all images to the .tirf file (as a zip)
        for image_path in images:
            zipf.write(image_path, os.path.basename(image_path))

        # Add metadata as a JSON file inside the .tirf (zip) file
        metadata_file = 'metadata.json'
        with open(metadata_file, 'w') as meta_file:
            json.dump(metadata, meta_file)

        zipf.write(metadata_file)

    print(f'.tirf file created: {output_file}')

# Run the function to create the .tirf file
create_tirf(image_folder, output_file)