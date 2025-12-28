#!/usr/bin/env python3

"""
This script demonstrates how to preprocess a new dataset for transfer learning.
It focuses on ensuring compatibility with a pre-trained model, including
handling image resizing, normalization, and label encoding.
"""

import os
import sys
from PIL import Image
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


def load_and_preprocess_images(image_dir, target_size=(224, 224), grayscale=False):
    """
    Loads images from a directory, resizes them, and optionally converts them to grayscale.

    Args:
        image_dir (str): Path to the directory containing the images.
        target_size (tuple): The desired size (width, height) of the images.
        grayscale (bool): Whether to convert images to grayscale.

    Returns:
        tuple: A tuple containing a list of preprocessed image arrays and a list of corresponding filenames.
               Returns None, None if an error occurs.
    """

    images = []
    filenames = []
    try:
        for filename in os.listdir(image_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(image_dir, filename)
                try:
                    img = Image.open(image_path)
                    if grayscale:
                        img = img.convert('L')  # Convert to grayscale
                    img = img.resize(target_size)
                    img_array = np.array(img)

                    # Ensure images are 3-channel even if grayscale
                    if grayscale and len(img_array.shape) == 2:
                        img_array = np.stack([img_array] * 3, axis=-1)
                    elif len(img_array.shape) == 2:
                        img_array = np.stack([img_array] * 3, axis=-1)


                    images.append(img_array)
                    filenames.append(filename)
                except (IOError, OSError) as e:
                    print(f"Error processing image {filename}: {e}")
        return images, filenames
    except OSError as e:
        print(f"Error accessing image directory {image_dir}: {e}")
        return None, None


def normalize_images(images):
    """
    Normalizes pixel values of images to the range [0, 1].

    Args:
        images (list): A list of image arrays.

    Returns:
        list: A list of normalized image arrays.
    """
    normalized_images = [img / 255.0 for img in images]
    return normalized_images


def encode_labels(labels):
    """
    Encodes categorical labels into numerical values using LabelEncoder.

    Args:
        labels (list): A list of categorical labels.

    Returns:
        numpy.ndarray: An array of encoded labels.
    """
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    return encoded_labels


def create_dataframe(images, labels, filenames):
    """
    Creates a pandas DataFrame from the preprocessed images, labels, and filenames.

    Args:
        images (list): A list of preprocessed image arrays.
        labels (numpy.ndarray): An array of encoded labels.
        filenames (list): A list of filenames.

    Returns:
        pandas.DataFrame: A DataFrame containing the image data, labels, and filenames.
    """
    df = pd.DataFrame({'image': images, 'label': labels, 'filename': filenames})
    return df


def split_data(df, test_size=0.2, random_state=42):
    """
    Splits the data into training and testing sets.

    Args:
        df (pandas.DataFrame): The DataFrame containing the data.
        test_size (float): The proportion of the data to use for testing.
        random_state (int): The random state for reproducibility.

    Returns:
        tuple: A tuple containing the training and testing DataFrames.
    """
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    return train_df, test_df


def main(image_dir):
    """
    Main function to demonstrate the data preprocessing steps.

    Args:
        image_dir (str): Path to the directory containing the images.
    """
    images, filenames = load_and_preprocess_images(image_dir)

    if images is None or filenames is None:
        print("Error loading images.  Exiting.")
        return

    # Example labels (replace with your actual labels)
    labels = [filename.split('_')[0] for filename in filenames]  # Assuming filename format: label_image_id.jpg
    encoded_labels = encode_labels(labels)

    normalized_images = normalize_images(images)

    df = create_dataframe(normalized_images, encoded_labels, filenames)

    train_df, test_df = split_data(df)

    print("Training DataFrame shape:", train_df.shape)
    print("Testing DataFrame shape:", test_df.shape)
    print("First 5 rows of training DataFrame:")
    print(train_df.head())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_directory = sys.argv[1]
        main(image_directory)
    else:
        print("Please provide the image directory as a command-line argument.")
        print("Example: python data_preprocessing_example.py path/to/images")