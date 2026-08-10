import math

class Tracker:
    def __init__(self):
        self.center_points = {}
        self.id_count = 0
        self.distance_threshold = 50   # Increased for boat movement stability

    def update(self, objects_rect):
        objects_bbs_ids = []

        for rect in objects_rect:
            x1, y1, x2, y2 = rect
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            same_object_detected = False

            for object_id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < self.distance_threshold:
                    self.center_points[object_id] = (cx, cy)
                    objects_bbs_ids.append([x1, y1, x2, y2, object_id])
                    same_object_detected = True
                    break

            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x1, y1, x2, y2, self.id_count])
                self.id_count += 1

        # Clean unused IDs
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id = obj_bb_id
            new_center_points[object_id] = self.center_points[object_id]

        self.center_points = new_center_points.copy()

        return objects_bbs_ids
