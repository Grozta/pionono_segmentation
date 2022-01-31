import os
import imageio
import errno
import csv
import torch
import mlflow
import numpy as np

import src.utils.globals as globals

def save_model(model):
    model_dir = 'models'
    dir = os.path.join(globals.config['logging']['experiment_folder'], model_dir)
    os.makedirs(dir, exist_ok=True)
    out_path = os.path.join(dir, 'best_model.pth')
    torch.save(model, out_path)
    print('Best Model saved!')

def save_test_images(test_preds: np.array, test_labels: np.array, test_name: np.array, mode: str):
    visual_dir = 'qualitative_results/' + mode
    dir = os.path.join(globals.config['logging']['experiment_folder'], visual_dir)
    os.makedirs(dir, exist_ok=True)

    b, h, w = np.shape(test_labels)
    test_preds = np.asarray(test_preds, dtype=np.uint8)
    test_labels = np.asarray(test_labels, dtype=np.uint8)

    for i, test_pred in enumerate(test_preds):
        test_pred_rgb = convert_classes_to_rgb(test_pred, h, w)
        out_path = os.path.join(dir, 'pred_' + test_name[i])
        imageio.imsave(out_path, test_pred_rgb)

    for i, test_label in enumerate(test_labels):
        test_label_rgb = convert_classes_to_rgb(test_label, h, w)
        out_path = os.path.join(dir, 'gt_' + test_name[i])
        imageio.imsave(out_path, test_label_rgb)
    mlflow.log_artifacts(dir)

def convert_classes_to_rgb(seg_classes, h, w):

    seg_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    class_no = globals.config['data']['class_no']
    if globals.config['data']['ignore_last_class']:
        class_no = class_no - 1

    colors = [[153,0,0], [255,102,204], [0,153,51], [153,0,204], [0,179,255]]

    for class_id in range(class_no):
        seg_rgb[:, :, 0][seg_classes == class_id] = colors[class_id][0]
        seg_rgb[:, :, 1][seg_classes == class_id] = colors[class_id][1]
        seg_rgb[:, :, 2][seg_classes == class_id] = colors[class_id][2]

    return seg_rgb


def save_results(results):
    results_dir = 'quantitative_results'
    dir = os.path.join(globals.config['logging']['experiment_folder'], results_dir)
    os.makedirs(dir, exist_ok=True)
    out_path = os.path.join(dir, 'results.csv')

    with open(out_path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in results.items():
            writer.writerow([key, value])