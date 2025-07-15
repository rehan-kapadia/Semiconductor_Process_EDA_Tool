import cv2
import numpy as np

class ImageRegistrar:
    """
    Handles the alignment of two images using feature-based registration.
    """

    def __init__(self, n_features=5000):
        """
        Initializes the registrar with an ORB feature detector.

        Args:
            n_features (int): The maximum number of features to detect.
        """
        self.orb = cv2.ORB_create(nfeatures=n_features)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def align_images(self, im1_path: str, im2_path: str) -> np.ndarray:
        """
        Aligns image 2 to image 1.

        Args:
            im1_path (str): Path to the reference image (e.g., step_N.png).
            im2_path (str): Path to the image to be aligned (e.g., step_N+1.png).

        Returns:
            np.ndarray: The aligned version of image 2.
        """
        print(f"PERCEPTION: Aligning '{im2_path}' to '{im1_path}'...")

        # Read images
        im1 = cv2.imread(im1_path, cv2.IMREAD_COLOR)
        im2 = cv2.imread(im2_path, cv2.IMREAD_COLOR)
        
        if im1 is None or im2 is None:
            raise FileNotFoundError("One or both image paths are invalid.")

        im1_gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        im2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

        # Find keypoints and descriptors
        kp1, des1 = self.orb.detectAndCompute(im1_gray, None)
        kp2, des2 = self.orb.detectAndCompute(im2_gray, None)

        # Match features
        matches = self.matcher.match(des1, des2)
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)

        # Keep top 10% of matches
        num_good_matches = int(len(matches) * 0.15)
        matches = matches[:num_good_matches]

        # Extract location of good matches
        points1 = np.zeros((len(matches), 2), dtype=np.float32)
        points2 = np.zeros((len(matches), 2), dtype=np.float32)

        for i, match in enumerate(matches):
            points1[i, :] = kp1[match.queryIdx].pt
            points2[i, :] = kp2[match.trainIdx].pt

        # Find homography
        h, mask = cv2.findHomography(points2, points1, cv2.RANSAC)

        # Use homography to warp image2
        height, width, channels = im1.shape
        im2_aligned = cv2.warpPerspective(im2, h, (width, height))
        
        print("PERCEPTION: Alignment complete.")
        return im2_aligned
