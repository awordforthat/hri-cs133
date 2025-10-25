import numpy as np
# Keeps track of the positions of an aruco tag
class Aruco:
    
    def __init__(self):
        self.corners = []
        self.past_corners = []
        self.center = [] 
        self.past_centers = []
        
    # updates the x,y locations of each corner, then uses this to calculate the center point of the marker
    def update_corners(self, corners): # there's something off here
        self.past_corners.append(self.corners)
        self.corners = corners
        self.update_center()
        
    # calculates and saves the center point of the marker
    def update_center(self):
        # self.corners is [[[x, y], [x,y], [x,y], [x,y]]]
        self.past_centers.append(self.center)
        self.center = np.mean(self.corners[0], axis=1)
                
    # returns the list of x,y coordinates for the last known position of the marker
    def get_corners(self):
        return self.corners
    
    # returns the x,y position of the last known position of the marker's center
    def get_center(self):
        return self.center
    
    # returns every recorded x,y coordinate for the marker's corners
    def get_all_corners(self):
        return self.past_corners
    
    # returns every recorded x,y coordinate for the marker's center
    def get_all_centers(self):
        return self.past_centers