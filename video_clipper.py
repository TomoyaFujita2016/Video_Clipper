import os, sys
from tqdm import tqdm
from more_itertools import chunked
from datetime import datetime
import cv2
import skvideo.io
import subprocess
from scipy.signal import argrelmax
import numpy as np
import configparser as cnf
# darknet yolo
sys.path.append("./darknet_/python/")
import darknet

root_dir = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(root_dir, "./config.conf")
SAVE_PATH = os.path.join(root_dir, "./saves/")

def read_config(path):
    config = cnf.ConfigParser()
    config.read(path, "UTF-8")
    return config

def read_video(path):
    return skvideo.io.vreader(path)

def get_frame_rate(path):
    part_of_fps = skvideo.io.ffprobe(path)["video"]["@avg_frame_rate"].split("/")
    return round(int(part_of_fps[0]) / int(part_of_fps[1]))

def get_amount_of_frame(path):
    return int(skvideo.io.ffprobe(path)["video"]["@nb_frames"])

def get_video_info(path):
    return skvideo.io.ffprobe(path)

def array_to_image(array):
    array = array.transpose(2,0,1)
    c = array.shape[0]
    h = array.shape[1]
    w = array.shape[2]
    array = (array/255.0).flatten()
    data = darknet.c_array(darknet.c_float, array)
    image = darknet.IMAGE(w,h,c,data)
    return image

def detect_by_frame(net, meta, frame):
    image = array_to_image(frame)
    res = darknet.detect(net, meta, image)
    return res

def detect_by_video(input_path, config):
    #net = darknet.get_net("darknet_/cfg/yolov3.cfg", "darknet_/weights/yolov3.weights")
    net = darknet.get_net("darknet_/cfg/yolov3-tiny.cfg", "darknet_/weights/yolov3-tiny.weights")
    meta = darknet.get_meta("darknet_/cfg/coco.data")
    skipping_frame = int(config.get("video_clipper", "skipping_frame"))
    
    object_num = []

    cap = read_video(input_path)
    total_frames = get_amount_of_frame(input_path)
    pbar = tqdm(total=total_frames, ncols=80)
    for i, frame in enumerate(cap):
        pbar.update(1)
        
        # skip frames
        if not i % skipping_frame == 0:
            continue
        
        r = detect_by_frame(net, meta, frame)
        pbar.set_description("object_count = {}".format(len(r)))
        object_num.append(len(r))
        
        ## test
        #if len(object_num) > 150:
        #    break
    pbar.close() 
    return object_num

def calc_cutting_point(object_num, video_path, config):
    # read config
    search_range = int(config.get("video_clipper", "search_range"))
    clip_num = int(config.get("video_clipper", "clip_num"))

    chunk_obj_num = [sum(x) for x in list(chunked(object_num, search_range))]

    max_points = (argrelmax(np.array(chunk_obj_num))[0]).tolist()
    print("object_num")
    print(object_num)
    print("chunk_obj_num")
    print(chunk_obj_num)
    print("max_points")
    print(max_points)
    # [frame idx, object number]
    object_num_max = [[idx*search_range, chunk_obj_num[idx]] for idx in max_points]
    sorted_obj_num_max = sorted(
            object_num_max,
            key=lambda x: x[1],
            reverse=True
        )
    
    picked_frames = sorted_obj_num_max[:clip_num]
    
    sorted_picked_frames = sorted(
            picked_frames,
            key=lambda x: x[0],
        )

    return sorted_picked_frames

def calc_clip_length(object_nums, video_file, config):
    output_video_length = int(config.get("video_clipper", "output_video_length"))
    skipping_frame = int(config.get("video_clipper", "skipping_frame"))
    fps = get_frame_rate(video_file)
    total_obj = np.sum(object_nums, axis=0)[1]

    for i, object_num in enumerate(object_nums):
        print(object_num)
        print(fps)
        print(skipping_frame)
        object_nums[i].extend(
                [round(skipping_frame*object_num[0]/fps, 3),
                round(output_video_length * object_num[1]/total_obj, 3)] # clip length(sec)
            )

    # [frame idx, object number, length(sec)]
    return object_nums

def make_concat_cmd(inputs, output):
    cmd = "ffmpeg -f concat -safe 0 -i {0} -c copy {1}"
    filename = "clip_name_list.txt"
    list_dir = os.path.dirname(output)
    list_path = os.path.join(list_dir, filename)
    with open(list_path, "w") as f:
        for ipt in inputs:
            f.write("file {}\n".format(ipt))
    return cmd.format(list_path, output)

def make_trim_cmd(ipt, ss, t, out):
    return "ffmpeg -ss {0} -i {1} -t {2} {3}".format(ss, ipt, t, out)

def run_shell(cmd):
    subprocess.call(cmd, shell=True)

def trim_concat_video(input_video, cutting_point_sec, config):
    file_path = make_file_path_dir(input_video, config)
    # trim
    for cutting_info, clip_path in zip(cutting_point_sec, file_path["clips"]):
        cmd = make_trim_cmd(input_video, max(0, cutting_info[2]-(round(cutting_info[3]/2, 3))), cutting_info[3], clip_path)
        run_shell(cmd)
    # concat
    cmd = make_concat_cmd(file_path["clips"][:len(cutting_point_sec)], file_path["output"])
    run_shell(cmd)

def get_now_str():
    return datetime.now().strftime('%Y%m%d%H%M%S%f')

def make_file_path_dir(video_path, config):
    file_path = {"clips":[], "output":None}
    clip_num = int(config.get("video_clipper", "clip_num"))
    filename, ext = os.path.splitext(os.path.basename(video_path))
    dirname = SAVE_PATH + filename + get_now_str() 
    
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    for i in range(1, clip_num+1):
        file_path["clips"].append("{0}/part_of_{1}{2:05}{3}".format(dirname, filename, i, ext))
           
    file_path["output"] = "{0}/clipped_{1}{2}".format(dirname, filename, ext)
    
    return file_path

def check_video_ext(path):
    return "MOV" == os.path.splitext(os.path.basename(path))[1][1:]

def main():
    video_path = sys.argv[1]
    if check_video_ext(video_path):
        print("This extention is not allowed.")
        exit()

    video_info = get_video_info(video_path)
    print(str(video_info))
    config = read_config(CONFIG_PATH)
    print(video_path)

    object_num = detect_by_video(video_path, config)
    cutting_point_frame = calc_cutting_point(object_num, video_path, config)
    print("cutting_point_frame")
    print(cutting_point_frame)
    
    if len(cutting_point_frame) == 0:
        print("[***FAILED TO MAKE THE CLIPPING VIDEO***]")
        print("It couldn't make the clipping video. Make sure config file.")
        print("Reason: There was no highlight scenes")
        print("Recommended: Decrease the values of skipping_frame and search_range.")
        exit()

    cutting_point_sec = calc_clip_length(cutting_point_frame, video_path, config)
    print("cutting_point_sec")
    print(cutting_point_sec)
    
    trim_concat_video(video_path, cutting_point_sec, config)

if __name__=="__main__":
    main()
