import numpy as np
from filterpy.kalman import KalmanFilter


class KalmanBoxTracker:
    """Tracks a single object using Kalman filter"""
    count = 0
    
    def __init__(self, bbox):
        """
        Initialize tracker with bounding box
        Args:
            bbox: [x1, y1, x2, y2]
        """
        # Define Kalman filter with 7 state variables and 4 measurements
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        
        # State transition matrix
        self.kf.F = np.array([
            [1,0,0,0,1,0,0],
            [0,1,0,0,0,1,0],
            [0,0,1,0,0,0,1],
            [0,0,0,1,0,0,0],
            [0,0,0,0,1,0,0],
            [0,0,0,0,0,1,0],
            [0,0,0,0,0,0,1]
        ])
        
        # Measurement matrix
        self.kf.H = np.array([
            [1,0,0,0,0,0,0],
            [0,1,0,0,0,0,0],
            [0,0,1,0,0,0,0],
            [0,0,0,1,0,0,0]
        ])
        
        # Measurement uncertainty
        self.kf.R[2:,2:] *= 10.
        # Process uncertainty
        self.kf.P[4:,4:] *= 1000.
        self.kf.Q[-1,-1] *= 0.01
        self.kf.Q[4:,4:] *= 0.01
        
        # Initialize state
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
    
    def update(self, bbox):
        """Update tracker with new detection"""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
    
    def predict(self):
        """Advance state and return predicted bbox"""
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]
    
    def get_state(self):
        """Return current bounding box estimate"""
        return self._convert_x_to_bbox(self.kf.x)
    
    @staticmethod
    def _convert_bbox_to_z(bbox):
        """Convert [x1, y1, x2, y2] to [x, y, s, r]"""
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w/2
        y = bbox[1] + h/2
        s = w * h
        r = w / float(h)
        return np.array([x, y, s, r]).reshape((4, 1))
    
    @staticmethod
    def _convert_x_to_bbox(x):
        """Convert [x, y, s, r] to [x1, y1, x2, y2]"""
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w
        return np.array([
            x[0] - w/2,
            x[1] - h/2,
            x[0] + w/2,
            x[1] + h/2
        ]).flatten()


class Sort:
    """Simple Online Realtime Tracker (SORT)"""
    
    def __init__(self, max_age=30, min_hits=3, iou_threshold=0.3):
        """
        Args:
            max_age: Max frames to keep alive without detection
            min_hits: Min detections before tracking starts
            iou_threshold: Min IOU for matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers = []
        self.frame_count = 0
    
    def update(self, detections):
        """
        Update tracker with new detections
        
        Args:
            detections: np.array([[x1, y1, x2, y2, score], ...])
        
        Returns:
            np.array([[x1, y1, x2, y2, track_id], ...])
        """
        self.frame_count += 1
        
        # Get predictions from existing trackers
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()  # Returns array directly
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        
        # Match detections to trackers
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(
            detections, trks
        )
        
        # Update matched trackers
        for m in matched:
            self.trackers[m[1]].update(detections[m[0], :])
        
        # Create new trackers for unmatched detections
        for i in unmatched_dets:
            trk = KalmanBoxTracker(detections[i, :4])
            self.trackers.append(trk)
        
        # Return tracked objects that meet criteria
        ret = []
        for trk in self.trackers:
            d = trk.get_state()  # Returns array directly
            if (trk.time_since_update < 1) and (
                trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits
            ):
                ret.append(np.concatenate((d, [trk.id + 1])).reshape(1, -1))
        
        # Remove dead tracklets
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
        
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))
    
    def _associate_detections_to_trackers(self, detections, trackers):
        """Match detections to trackers using IOU"""
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)
        
        iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
        
        for d, det in enumerate(detections):
            for t, trk in enumerate(trackers):
                iou_matrix[d, t] = self._iou(det, trk)
        
        # Use scipy for optimal matching
        matched_indices = self._linear_assignment(-iou_matrix)
        
        unmatched_detections = []
        for d in range(len(detections)):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)
        
        unmatched_trackers = []
        for t in range(len(trackers)):
            if t not in matched_indices[:, 1]:
                unmatched_trackers.append(t)
        
        # Filter out low IOU matches
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < self.iou_threshold:
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))
        
        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)
        
        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)
    
    @staticmethod
    def _iou(bb_test, bb_gt):
        """Calculate Intersection over Union"""
        xx1 = np.maximum(bb_test[0], bb_gt[0])
        yy1 = np.maximum(bb_test[1], bb_gt[1])
        xx2 = np.minimum(bb_test[2], bb_gt[2])
        yy2 = np.minimum(bb_test[3], bb_gt[3])
        w = np.maximum(0., xx2 - xx1)
        h = np.maximum(0., yy2 - yy1)
        wh = w * h
        o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
                  + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
        return o
    
    @staticmethod
    def _linear_assignment(cost_matrix):
        """Optimal assignment using Hungarian algorithm"""
        try:
            from scipy.optimize import linear_sum_assignment
            x, y = linear_sum_assignment(cost_matrix)
            return np.array(list(zip(x, y)))
        except ImportError:
            # Fallback to greedy matching
            matches = []
            used_rows = set()
            used_cols = set()
            for _ in range(min(cost_matrix.shape)):
                min_val = np.inf
                min_pos = None
                for i in range(cost_matrix.shape[0]):
                    if i in used_rows:
                        continue
                    for j in range(cost_matrix.shape[1]):
                        if j in used_cols:
                            continue
                        if cost_matrix[i, j] < min_val:
                            min_val = cost_matrix[i, j]
                            min_pos = (i, j)
                if min_pos is None:
                    break
                matches.append(min_pos)
                used_rows.add(min_pos[0])
                used_cols.add(min_pos[1])
            return np.array(matches) if matches else np.empty((0, 2), dtype=int)
