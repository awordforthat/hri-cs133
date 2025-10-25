import cv2
import numpy as np

def generate_aruco_marker(dictionary_type, marker_id, marker_size_pixels, output_filename):
    """
    Generates an ArUco marker and saves it as an image file.

    Args:
        dictionary_type (int): The predefined ArUco dictionary type (e.g., cv2.aruco.DICT_4X4_50).
        marker_id (int): The ID of the marker to generate.
        marker_size_pixels (int): The size of the marker in pixels (width and height).
        output_filename (str): The name of the file to save the marker image.
    """
    # Get the predefined ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_type)

    # Generate the marker image
    marker_image = np.zeros((marker_size_pixels, marker_size_pixels), dtype=np.uint8)
    cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_pixels, marker_image, 1)

    # Save the marker image
    cv2.imwrite(output_filename, marker_image)
    print(f"ArUco marker ID {marker_id} generated and saved as {output_filename}")


if __name__ == "__main__":
    # Example usage:
    # Generate a marker from DICT_4X4_50 dictionary with ID 10 and size 200x200 pixels
    generate_aruco_marker(cv2.aruco.DICT_4X4_50, 10, 200, "aruco_marker_id_10.png")
