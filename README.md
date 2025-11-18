# SeePerSea
Welcome to the SeePerSea Dataset from the Dartmouth Reality and Robotics Lab!
Our paper is currently under review for IEEE Transaction on Field Robotics (T-FR)!

__our dataset website__:  https://seepersea.github.io/


This paper introduces the first publicly accessible labeled multi-modal perception dataset 
for autonomous maritime navigation, focusing on in-water obstacles within the aquatic environment to enhance situational awareness for Autonomous Surface Vehicles (ASVs). This dataset, collected over 4 years and consisting of diverse objects encountered under varying environmental conditions, aims to bridge the research gap in ASVs by providing a multi-modal, annotated, and ego-centric perception dataset, for object detection and classification. We also show the applicability of the proposed dataset by training deep learning-based open-source perception algorithms that have shown success in the autonomous ground vehicle domain. We expect that our dataset will contribute to the development of future marine autonomy pipelines and marine (field) robotics.


![image info](./img/t-fr-busan.gif)


## Authors
Jeong, Mingi* and Chadda, Arihant* and Ren, Ziang and Zhao, Luyang and Liu, Haowen and Roznere, 
Monika and Zhang, Aiwei and Jiang, Yitao and Achong, Sabriel and Lensgraf, Samuel and Alberto Quattrini Li

\* these authors equally contributed.

## Maintainer
* Mingi Jeong: mingi.jeong.gr@dartmouth.edu
* Arihant Chadda: ari.chadda@gmail.com

## Contribution
* SeePerSea, the first LiDAR-camera dataset in aquatic environments with object labels across two modalities, will foster the development of robust fusion perception pipelines for ASV autonomy.
* SeePerSea, covering various environments and day conditions, will help ensure that developed perception pipelines are increasingly generalizable.

## Dependencies
The following environment is tested for the GUI viewer for the sample dataset.
* Ubuntu >= 20.04 (tested environment)
* PyQt5 5.14.1
* Open3D 0.13.0
* Numpy 1.24.4
* openCV-python 4.10.0.84
* python 3.8.10

## Folder Explanation
__NOTE__: evaluation is based on `interected` objects for LiDAR only and fusion approach, i.e., lidar not trained on `annotations` but `kitti_label`, to be consistent with what other literature did when comparing together with fusion approaches. 

### Individual 
* __camera_label__ (.json): object labels based on camera ( [AnyLabeling](https://github.com/vietanhdev/anylabeling)
) -- 6 digit file name per frame number 
* __annotations__ (.json): object labels based on LiDAR ( [3d-bat](https://github.com/walzimmer/3d-bat)
) -- 6 digit file name per frame number
* __calib__ (.txt): camera intrinsic and lidar extrinsic calibbration info -- 6 digit file name per frame number
    * P2: camera matrix (3 by 3)
    * Tr_velo_to_cam: extrinsic from LiDAR to camera (3 by 4)
* __timestamp__ (.txt): camera and LiDAR data's timestamp as synched. each frame's timestamp
* __point_clouds__ (.pcd): point clouds data -- 6 digit file name per frame number
* __undist_images__ (.png): undistorted camera images -- 6 digit file name per frame number
* __motion_data__ (.csv): gps and imu data, respectively. Each sensor contains its own timestamp and correspondingly recorded data.
* __kitti_label__ (.txt): contains objects (`intersection` of image and lidar point cloud) and label mapped {Ship: Car, Buoy: Pedestrian, Other: Cyclist}

### Aggregated
If you are running for an algorithm following KiTTi input (mmdetection3d, OpenPCDET), you need to use this. 
```
├── calib (.txt): camera intrinsic and lidar extrinsic calibbration info -- 6 digit file name per frame number
├── image (.png):  undistorted camera images 
├── ImageSets (.txt): train, val, test split
├── label (.txt): contains objects (intersection of image and lidar point cloud) and label mapped {Ship: Car, Buoy: Pedestrian, Other: Cyclist}
├── points (.pdf):  point clouds data
```

__Note__: labels for testsplit are empty.

## How to explore our dataset with sample data
1. Please download sample data from the following link: ([ Google-drive](https://drive.google.com/drive/folders/1KuhWh7KSmzg62b88LVoL_3oEM5HWLCfe?usp=sharing)
)
2. git clone the current repo
3. install dependencies (we recommend [Poetry](https://python-poetry.org/) and have included a `pyproject.toml` for convenience; run `poetry shell` and then `poetry install`). 
4. `python view_images.py`
5. Click the `Load Folder` button to load a sample sequence (_mascoma-20221007-1560_)
6. You can see a sample image with groudtruth bounding boxes overlaid.
7. Click `Show 3D View` to visualize point clouds also with groudtruth bounding boxes. Open3D window will pop-up.
8. If you want to move to the next frame, close the Open3D window and click the `Up` button.
9. You are welcome to explore the dataset using the `Up`, `Down`, and `Show 3D View` as well as load other sequences to explore the dataset. 

![instruction](./img/instruction.gif)

## Sample data explain
* _mascoma-20221007-1560_: many boats and buoys
* _sunapee-20210916-1440_: 3 kayaks, near and moving, overlapping
* _barbados-202302220530-200_: lots of buoys in line (more than 20)

## Full data explain
* _sunapee-20210827-910_: 2 buoys passing. one on the right side of ASV
* _sunapee-20210916-152_: 3 kayaks, distant
* _sunapee-20210916-1440_: 3 kayaks, near and moving, overlapping
* _sunapee-20210916-1950_: 3 distant kayaks moving away to the left side of ASV
* _sunapee-20210916-3671_: 3 kayaks near, one person approaching from behind
* _mascoma-20221007-880_: 2 boats passing by, then another boat appears, and the first one fade away
* _mascoma-20221007-1560_: many boats and buoys
* _mascoma-20221012-2000_: raft with 4 people on board, ahead of ASV, and move to the left
* _mascoma-20221012-3250_: raft boat near, but images have many sailing boat in front
* _mascoma-20221012-4100_: raft behind, sailing boats detected far, sparse
* _mascoma-20221012-5940_: many boats and buoys
* _mascoma-20221007-67_: raft nearby
* _mascoma-20221007-134_: raft nearby
* _busan-20221102-360_: 2 ships docked on the left
* _busan-20221102-2220_: 3 boats passing, large cargoship on the right side with stern detected
* _busan-20221102-3200_: Yellow, black buoy on the left front side
* _busan-20221102-3270_: after buoy passing, barge ships and cranes on the front right
* _busan-20221102-3530_: 2 buoys passing 
* _busan-20221102-3720_: boat stay on the left side and buoy passing from the front
* _busan-20221102-4000_: 1 boat passing
* _busan-20221102-4440_: 1 buoy passing, followed by one boat
* _busan-20221102-4520_: 1 green buoy passing on the left front side
* _barbados-202302220530-200_: lots of buoys in line (more than 20)
* _barbados-202302220530-430_: boats and buoy
* _barbados-202302220530-740_: boats in far distance, sun glare
* _barbados-202302220530-1815_: boat, buoy, sunset
* _barbados-20230223-240_: boat, buoy
* _barbados-20230223-360_: 3 boats daytime
* _barbados-20230223-1420_: boats, wind surfing boat
* _barbados-20230223-1570_: different type of boats and other objects
* _barbados-20230223-1680_: boay and buoy, wind surfing boat

## License
All datasets and benchmarks on this page are copyright by us.
https://creativecommons.org/licenses/by-nc-sa/4.0/
