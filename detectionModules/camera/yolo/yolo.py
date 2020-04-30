# USAGE
# python yolo_video.py --input videos/airport.mp4 --output output/airport_output.avi --yolo yolo-coco

# import the necessary packages
import numpy as np
import argparse
import imutils
import time
import cv2
import os
from dotenv import load_dotenv, find_dotenv

# load the .env file
load_dotenv(find_dotenv())

model_path = os.getenv('MODEL_PATH')
# minimum probability to filter weak detections
minimum_probability_for_filtering_weak_detection = 0.6
# threshold when applying non-maxima suppression
# this is the threshold upon which these detections need to be considered for NMS
threshold = 0.1  # float(os.getenv('THRESHOLD'))

# load the COCO class labels our YOLO model was trained on
labelsPath = os.path.sep.join([model_path, "coco.names"])
LABELS = open(labelsPath).read().strip().split("\n")

# initialize a list of colors to represent each possible class label
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                           dtype="uint8")

# derive the paths to the YOLO weights and model configuration
weightsPath = os.path.sep.join([model_path, "yolov3.weights"])
configPath = os.path.sep.join([model_path, "yolov3.cfg"])

# load our YOLO object detector trained on COCO dataset (80 classes)
# and determine only the *output* layer names that we need from YOLO
print("[INFO] loading YOLO from disk...")

# net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
net = cv2.dnn.readNet(weightsPath, configPath)
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# initialize the video stream, pointer to output video file, and
# frame dimensions
input_video = "Inside Google's New Asia Pacific HQ _ CNBC.mp4"
vs = cv2.VideoCapture(input_video)
# vs = cv2.VideoCapture(-1)
# writer = None
(W, H) = (None, None)
frame_id = 0
starting_time = time.time()

# loop over frames from the video file stream
while True:
    # read the next frame from the file
    (grabbed, frame) = vs.read()
    frame_id += 1

    # if the frame was not grabbed, then we have reached the end
    # of the stream
    if not grabbed:
        break

    # if the frame dimensions are empty, grab them
    if W is None or H is None:
        (H, W) = frame.shape[:2]

    # construct a blob from the input frame and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes
    # and associated probabilities
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), (0, 0, 0),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    # initialize our lists of detected bounding boxes, confidences,
    # and class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability)
            # of the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > threshold:
                # scale the bounding box coordinates back relative to
                # the size of the image, keeping in mind that YOLO
                # actually returns the center (x, y)-coordinates of
                # the bounding box followed by the boxes' width and
                # height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top
                # and and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates,
                # confidences, and class IDs
                # check for just person detection (0)
                if classID == np.int64(0):
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)

    print(confidences)

    # apply non-maxima suppression to suppress weak, overlapping
    # bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, threshold,
                            minimum_probability_for_filtering_weak_detection)

    l = 0
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the frame
            color = [int(c) for c in COLORS[classIDs[i]]]
            # color = [int(c) for c in COLORS[0]]
            # print(color)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]],
                                       confidences[i])
            cv2.putText(frame, text, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            l += 1

    # print(l)  # current count of people detected

    elapsed_time = time.time() - starting_time
    fps = frame_id/elapsed_time
    cv2.putText(frame, "FPS:"+str(round(fps, 2)),
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 1)

    cv2.imshow("preview", frame)
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break

    # TODO: CHECK IF THERE IS A NEED FOR THIS OUTPUT WRITER
    # check if the video writer is None
    # if writer is None:
    #     # initialize our video writer
    #     fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    #     writer = cv2.VideoWriter(args["output"], fourcc, 30,
    #                              (frame.shape[1], frame.shape[0]), True)

    #     # some information on processing single frame
    #     if total > 0:
    #         elap = (end - start)
    #         print("[INFO] single frame took {:.4f} seconds".format(elap))
    #         print("[INFO] estimated total time to finish: {:.4f}".format(
    #             elap * total))

    # write the output frame to disk
    # writer.write(frame)

# release the file pointers
print("[INFO] cleaning up...")
# writer.release()
vs.release()
cv2.destroyAllWindows()
