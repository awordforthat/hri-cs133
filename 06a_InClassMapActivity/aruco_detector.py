import cv2
from matplotlib import pyplot as plt
from aruco_obj import Aruco
import asyncio


class ArucoDetector:
    def __init__(self):
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50) #6x6?
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

        self.aruco_tags = {}

        self.visualizing = False
        self.cap = None
        self._task = None  # asyncio task handle

    async def visualize(self):
        """Async loop for visualization"""
        self.cap = cv2.VideoCapture(0)

        while self.visualizing and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                await asyncio.sleep(0.01)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = self.detector.detectMarkers(gray)

            if corners: # if we detect a tag within the image frame
                cur_id = ids[0][0]
                if cur_id not in self.aruco_tags: # create a new aruco object for the tag if it doesn't exist
                    self.aruco_tags[cur_id] = Aruco() 
                self.aruco_tags[cur_id].update_corners(corners) # update the aruco object with the last-detected corners
                
                print("detected")

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            cv2.imshow("Detected markers", frame)

            # # Use waitKey in a non-blocking way
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.visualizing = False

            await asyncio.sleep(0)  # yield to loop

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    async def begin_visualization(self):
        """Start visualization if not already running"""
        if not self.visualizing:
            self.visualizing = True
            self._task = asyncio.create_task(self.visualize())

    async def end_visualization(self):
        """Stop visualization cleanly"""
        self.visualizing = False
        if self._task:
            await self._task
            self._task = None

    # takes a picture using the connected camera and saves it to a file.
    def take_pic(self, save_file="captured_image.jpg"):
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        cv2.imshow("Captured Image", frame)
        cv2.waitKey(0) # Wait indefinitely until a key is pressed
        cv2.imwrite(save_file, frame)
        self.cap.release()
        cv2.destroyAllWindows()
        
    # returns a dictionary of the markers which have been detected. The key represents the unique ID of the marker and the value is the ArUco tag object.
    def get_tags(self):
        return self.aruco_tags
    
    # returns a dictionary of the last corner coordinates where each marker was identified.
    def get_last_tag_corners(self):
        return {k: v.get_corners() for k, v in self.aruco_tags.items()} 
    
    # returns a dictionary of the last center coordinates where each marker was identified.
    def get_last_tag_centers(self):
        return {k: v.get_center() for k, v in self.aruco_tags.items()} 
    
    # returns a dictionary of all the corner coordinates where each marker was previously identified
    def get_all_tag_corners(self):
        return {k: v.get_all_corners() for k, v in self.aruco_tags.items()} 
    
    # returns a dictionary of all the center coordinates where each marker was previously identified
    def get_all_tag_centers(self):
        return {k: v.get_all_centers() for k, v in self.aruco_tags.items()} 
    
    