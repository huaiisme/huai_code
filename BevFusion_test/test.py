from my_nuscenes import MyNuScenes

VERSION = 'v1.0-mini'
NUSCENES_ROOT = "/mnt/Ddisk/data/nuscenes"
nusc = MyNuScenes(version=VERSION, dataroot=NUSCENES_ROOT, verbose=True)
