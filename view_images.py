#!/usr/bin/python

import os
import sys
import json
import cv2
import copy
import numpy as np
import open3d as o3d
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLineEdit,
)
from PyQt5.QtGui import QImage, QPixmap

IMAGE_FOLDER_UNDIST = "undist_images"
IMAGE_FOLDER_RECT = "rect_images"

CLASS_COLOR_LOOKUP = {"ship": (0, 255, 0), "buoy": (255, 0, 0), "other": (0, 0, 255)}
OVERLAY_AFTER_FILE_SWITCH = True




def box_center_to_corner(box):
    """
    Args:
        box = [h,w,l,x,y,z,rot]

    reference: https://stackoverflow.com/questions/62938546/how-to-draw-bounding-boxes-and-update-them-real-time-in-python
    """
    translation = box[3:6]
    h, w, l = box[0], box[1], box[2]
    rotation = box[6]

    # consistent with 3dbat label (w, l flip)
    bounding_box = np.array(
        [
            [-w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2],
            [-l / 2, -l / 2, l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2],
            [h / 2, h / 2, h / 2, h / 2, -h / 2, -h / 2, -h / 2, -h / 2],
        ]
    )

    # Standard 3x3 rotation matrix around the Z axis
    rotation_matrix = np.array(
        [
            [np.cos(rotation), -np.sin(rotation), 0.0],
            [np.sin(rotation), np.cos(rotation), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    # Repeat the [x, y, z] eight times
    eight_points = np.tile(translation, (8, 1))

    # Translate the rotated bounding box by the
    # original center position to obtain the final box
    corner_box = np.dot(rotation_matrix, bounding_box) + eight_points.transpose()
    # print(corner_box.transpose())

    return corner_box.transpose()

def visualize_pcd_and_bb(label_file, points_v):
    """
    visualize point clouds and bounding boxes in open 3d
    visualize minimal bounding boxes to make sharper touch

    Args:
        - label_file: (json) annotated file for each frame
        - points_v: (np.array) vector of point clouds

    Returns:
        - box_entity: (list) of o3d.geometry.OrientedBoundingBox or o3d.geometry.AxisAlignedBoundingBox
    """
    
    # 0. prerequsite for visualization
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_v)  # np_arracy -> o3d pcd

    # Set a fixed color for the point cloud (e.g., gray)
    fixed_color = [0, 0, 1]
    pcd.paint_uniform_color(fixed_color)

    # Create a visualization
    vis = o3d.visualization.Visualizer()
    vis.create_window()

    # Add point cloud
    vis.add_geometry(pcd)

    # ------------------------------------------------------------------------------
    content_exist = False
    # 1. bounding boxes label
    with open(label_file, "r", encoding="utf-8") as f:
        try:
            label_data = json.load(f)
            content_exist = True
        except:
            print("no content in lidar label data -- test split")
        
    # json_file = open(label_file)
    # label_data = json.load(json_file)

    # ------------------------------------------------------------------------------
    if content_exist and label_data:
        # 2. reading annotated bounding box in our annotated json file
        for label in label_data["labels"]:
            box_info = label["box3d"]
            box = [
                box_info["dimension"]["height"],
                box_info["dimension"]["width"],
                box_info["dimension"]["length"],
                box_info["location"]["x"],
                box_info["location"]["y"],
                box_info["location"]["z"],
                box_info["orientation"]["rotationYaw"],
            ]
            # print("old_box", box)
            # 1) box corner points
            boxes3d_pts = box_center_to_corner(box)
            boxes3d_pts = boxes3d_pts.T
            boxes3d_pts = o3d.utility.Vector3dVector(boxes3d_pts.T)

            # 2) create box from corner points
            box = o3d.geometry.OrientedBoundingBox.create_from_points(boxes3d_pts)  # using

            # 3) visualization added #Box color would be red box.color = [R,G,B]
            if label["category"] == "ship":
                box.color = [0, 1, 0]  # green
            elif label["category"] == "buoy":
                box.color = [1, 0.8, 0]  # yellow
            elif label["category"] == "others":
                box.color = [1, 0, 0]  # red

            # entities_to_draw.append(box)
            vis.add_geometry(box)


    # ------------------------------------------------------------------------------
    # 3. Draw
    # Set a custom viewpoint
    view_control = vis.get_view_control()

    # Adjust the camera to achieve a bird's-eye view
    view_control.set_front([-10.0, -0.0, 2.62068021233921933])  # behind of lidar
    view_control.set_lookat(
        [2.4615, 2.1331, 1.338]  # where look
    )  # [-0.97243714332580566, -0.1751408576965332, 0.51464511454105377])
    view_control.set_up(
        [4.1781, 0, 90.0]  # tiltied angle
    )  # [-0.36828927493940194, 0.49961995188329117, 0.78405542766104697])
    view_control.set_zoom(0.15999999999999961)

    # Access rendering options
    render_option = vis.get_render_option()
    render_option.point_size = 3.0  # Smaller value for smaller points (default is typically 5.0)
    # render_option.background_color = [0.1, 0.1, 0.1]  # Dark gray background
    render_option.line_width = 20.0  # Thicker bounding box lines

    # Run visualization and take a snapshot
    vis.poll_events()
    vis.update_renderer()
    vis.run()



class ImageViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image = None
        self.lidar_points = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Viewer with groundtruth label")
        self.setGeometry(100, 100, 1000, 800)

        # Main layout
        layout = QVBoxLayout()

        # ---------------------------------------
        # Buttons to load images data
        self.loadFolderButton = QPushButton("Load Folder")
        self.upButton = QPushButton("Up")
        self.downButton = QPushButton("Down")
        self.fileNumberDisplay = QLineEdit()
        self.fileNumberDisplay.setPlaceholderText("File Number")
        self.fileNumberDisplay.setReadOnly(False)  # Allow typing

        # Add components to layout
        layout.addWidget(self.loadFolderButton)
        layout.addWidget(self.fileNumberDisplay)
        layout.addWidget(self.upButton)
        layout.addWidget(self.downButton)
        # ---------------------------------------

        # ---------------------------------------
        # Buttons to load image individually
        self.loadImageButton = QPushButton("Load Camera Image")
        self.overlayButton = QPushButton("Overlay Bounding Box on Image")
        # layout.addWidget(self.loadImageButton)
        # layout.addWidget(self.overlayButton)
        # ---------------------------------------


        self.show3DButton = QPushButton("Show 3D View")
        layout.addWidget(self.show3DButton)

        # Image display label
        self.imageLabel = QLabel("Camera Image Here")
        layout.addWidget(self.imageLabel)

        # ---------------------------------------
        # Main container
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # ---------------------------------------
        # Connect buttons to actions
        self.loadFolderButton.clicked.connect(self.load_folder)
        self.upButton.clicked.connect(self.iterate_files_up)
        self.downButton.clicked.connect(self.iterate_files_down)
        self.loadImageButton.clicked.connect(self.load_image)
        self.fileNumberDisplay.editingFinished.connect(self.jump_to_file)
        self.overlayButton.clicked.connect(self.overlay_bounding_box_on_image)
        self.show3DButton.clicked.connect(self.on_show_3d)


    def overlay_bounding_box_on_image(self):
        """main overlay function"""
        if self.image is None:
            return
        # Reset to the original image
        self.image = self.original_image.copy()
        img_arr = self.image
        content_exist = False

        # load label
        label_file = os.path.join(self.label_folder, self.label_files[self.current_index])
        with open(label_file, "r", encoding="utf-8") as f:
            try:
                label_data = json.load(f)
                content_exist = True
            except:
                print("no content in image label data -- test split")
        
        if content_exist and label_data:
            for shape in label_data["shapes"]:
                coords = shape["points"]
                class_ = shape["label"]

                (x1, y1) = tuple([int(a) for a in coords[0]])
                (x2, y2) = tuple([int(b) for b in coords[-1]])

                cv2.rectangle(
                    img_arr,
                    (x1, y1),
                    (x2, y2),
                    color=CLASS_COLOR_LOOKUP[class_],
                    thickness=2,
                )

                (w, h), _ = cv2.getTextSize(class_, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

        # img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR) # not using as I don't use PIL

        # finish displaying image
        self.image = img_arr
        self.display_image()


    def on_show_3d(self):
        if self.lidar_points is None:
            return
        
        # load label
        pcd_label_file = os.path.join(self.pc_label_folder, self.pc_label_files[self.current_index])
        visualize_pcd_and_bb(pcd_label_file, self.lidar_points)
        

    def load_folder(self):
        """
        select the folder to load image and lidar point cloud numerically samely increasing
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.loaded_folder = folder
            self.image_folder = os.path.join(folder, "{}/CAM_FRONT".format(IMAGE_FOLDER_UNDIST))
            self.lidar_folder = os.path.join(folder, "point_clouds")
            self.label_folder = os.path.join(folder, "camera_label")
            self.pc_label_folder = os.path.join(folder, "annotations")
            try:
                self.image_files = sorted(
                    [
                        f
                        for f in os.listdir(self.image_folder)
                        if f.lower().endswith((".png", ".jpg", ".bmp"))
                    ]
                )
                self.label_files = sorted(
                    [
                        f
                        for f in os.listdir(self.label_folder)
                        if f.lower().endswith((".json"))
                    ]
                )
                self.lidar_files = sorted(
                    [
                        f
                        for f in os.listdir(self.lidar_folder)
                        if f.lower().endswith((".pcd"))
                    ]
                )
                self.pc_label_files = sorted(
                    [
                        f
                        for f in os.listdir(self.pc_label_folder)
                        if f.lower().endswith((".json"))
                    ]
                )
            except FileNotFoundError:
                self.image_folder = os.path.join(folder, "{}/CAM_FRONT".format(IMAGE_FOLDER_RECT))
                self.image_files = sorted(
                    [
                        f
                        for f in os.listdir(self.image_folder)
                        if f.lower().endswith((".png", ".jpg", ".bmp"))
                    ]
                )
                self.label_files = sorted(
                    [
                        f
                        for f in os.listdir(self.label_folder)
                        if f.lower().endswith((".json"))
                    ]
                )
                self.lidar_files = sorted(
                    [
                        f
                        for f in os.listdir(self.lidar_folder)
                        if f.lower().endswith((".pcd"))
                    ]
                )
                self.pc_label_files = sorted(
                    [
                        f
                        for f in os.listdir(self.pc_label_folder)
                        if f.lower().endswith((".json"))
                    ]
                )
            self.current_index = 0  # Start with the first file
            print("Loaded folder:", folder)
            print("Image files {}: {}".format(self.image_folder, len(self.image_files)))
            print("LiDAR files {}: {}".format(self.lidar_folder, len(self.lidar_files)))
            self.load_files_by_index()


    def iterate_files_down(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_files_by_index()

    def iterate_files_up(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_files_by_index()

    def load_files_by_index(self):
        # assume image and lidar file number same
        if self.current_index < 0 or self.current_index >= len(self.image_files):
            print("Index out of bounds.")
            return

        # Extract number from image file name
        image_file = self.image_files[self.current_index]
        number = "".join(filter(str.isdigit, image_file))

        # Find corresponding LiDAR file with the same number
        lidar_file = next((f for f in self.lidar_files if number in f), None)

        if image_file and lidar_file:
            self.load_image(os.path.join(self.image_folder, image_file))
            self.load_lidar_data(os.path.join(self.lidar_folder, lidar_file))

            self.fileNumberDisplay.setText(
                f"{self.current_index} / {len(self.image_files)-1}"
            )  # Update file number display
            if OVERLAY_AFTER_FILE_SWITCH:
                self.overlay_bounding_box_on_image()

            # finish check
            print(f"Loaded image: {image_file}")
            print(f"Loaded point cloud: {lidar_file}")

        else:
            print("No matching image file found for number:", number)


    def jump_to_file(self):
        try:
            # Parse the file number and adjust to zero-based index
            file_number = int(self.fileNumberDisplay.text().split("/")[0].strip()) - 1
            if 0 <= file_number < len(self.image_files):
                self.current_index = file_number
                self.load_files_by_index()
            else:
                print("File number out of range.")
        except ValueError:
            print("Invalid file number entered.")

    def load_image(self, file_given=False):
        """file_given: file already selected"""
        if file_given is False:
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Open Image File", "", "Images (*.png *.jpg *.bmp)"
            )
        else:
            file_name = file_given
        if file_name:
            self.original_image = cv2.imread(file_name)
            self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            self.image = self.original_image.copy()  # Work with a copy of the original image
            self.display_image()



    def display_image(self):
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.imageLabel.setPixmap(QPixmap.fromImage(q_img))


    def load_lidar_data(self, file_given=False):
        if file_given is False:
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Open LiDAR File", "", "Point Cloud Files (*.pcd *.ply *.las)"
            )
        else:
            file_name = file_given

        if file_name:
            lidar_cloud = o3d.io.read_point_cloud(file_name)
            self.lidar_points = np.asarray(lidar_cloud.points)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = ImageViewerApp()
    mainWin.show()
    sys.exit(app.exec_())
