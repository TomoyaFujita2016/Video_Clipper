git clone https://github.com/pjreddie/darknet
cd darknet
make
cd ..
mv darknet darknet_
mv coco.data darknet_/cfg/
mv darknet.py darknet_/python/
mkdir darknet_/weights
wget https://pjreddie.com/media/files/yolov3-tiny.weights -P darknet_/weights/
