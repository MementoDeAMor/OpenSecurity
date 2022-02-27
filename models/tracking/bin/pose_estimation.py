import cv2
import mediapipe as mp
import numpy as np
from utils import dataprep
import os
import random

dataprep = dataprep.DataPrep()
data_path = dataprep.data_path
sample_dir = os.path.join(data_path, 'samples/')


def head_tracking(cam=0, _record=True, _filename=f'sample{random.randint(9, 9999)}', _format='avi'
                  , _output=sample_dir, _dimensions=(640, 480)):
    # Initialize the mediapipe.solutions face_mesh object and call the FaceMesh Function
    mp_solutions = mp.solutions
    mp_face_mesh = mp_solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.8, min_tracking_confidence=0.3)
    # Access video feed from a selected webcam ,define a codec and create a VideoWriter object
    cap = cv2.VideoCapture(cam)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    _out_ = cv2.VideoWriter(f'{_filename}.{_format}', fourcc, 20.0, _dimensions)

    # loop runs if capturing has been initialized.
    while cap.isOpened():
        # Read frames from a camera
        # success and image returned at each frame
        success, image = cap.read()
        # Flip the image horizontally for a later selfie-view display
        # Also convert the color space from BGR to RGB
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        # Get the result
        results = face_mesh.process(image)
        # To improve performance
        image.flags.writeable = True
        # Convert the color space from RGB to BGR
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        img_h, img_w, img_c = image.shape
        face_3d = []
        face_2d = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                        if idx == 1:
                            nose_2d = (lm.x * img_w, lm.y * img_h)
                            nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 8000)
                        x, y = int(lm.x * img_w), int(lm.y * img_h)
                        # Get the 2D Coordinates
                        face_2d.append([x, y])
                        # Get the 3D Coordinates
                        face_3d.append([x, y, lm.z])
                        # Convert it to the NumPy array
                face_2d = np.array(face_2d, dtype=np.float64)
                # Convert it to the NumPy array
                face_3d = np.array(face_3d, dtype=np.float64)
                # The camera matrix
                focal_length = 1 * img_w
                cam_matrix = np.array([[focal_length, 0, img_h / 2],
                                       [0, focal_length, img_w / 2],
                                       [0, 0, 1]])
                # The Distance Matrix
                dist_matrix = np.zeros((4, 1), dtype=np.float64)
                # Solve PnP
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
                # Get rotational matrix
                rmat, jac = cv2.Rodrigues(rot_vec)
                # Get angles
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
                # Get the y rotation degree
                x = angles[0] * 360
                y = angles[1] * 360
                # See where the user's head tilting
                if y < -20:
                    text = "Looking Left"
                elif y > 20:
                    text = "Looking Right"
                elif x < -20:
                    text = "Looking Down"
                else:
                    text = "Forward"

                # Display the nose direction
                nose_3d_projection, jacobian = cv2.projectPoints(nose_3d, rot_vec, trans_vec, cam_matrix, dist_matrix)
                p1 = (int(nose_2d[0]), int(nose_2d[1]))
                p2 = (int(nose_3d_projection[0][0][0]), int(nose_3d_projection[0][0][1]))
                cv2.line(image, p1, p2, (255, 0, 0), 2)
                # Add the text on the image
                cv2.putText(image, text, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # record the results
        if _record is True:
            # Converts to HSV color space, OCV reads colors as BGR (image is converted to hsv)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            # output the frame
            _out_.write(hsv)
        else:
            pass
        # The original input frame is shown in  window
        cv2.imshow('Head Pose Estimation', image)
        # Wait for '5' key to stop the program
        if cv2.waitKey(5) & 0xFF == 27:
            break
    # Close the window / Release webcam
    cap.release()
    if _out_:
        # After we release our webcam, we also release the output
        _out_.release()
    # De-allocate associated memory usage
    cv2.destroyAllWindows()
