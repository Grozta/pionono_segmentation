import os
import torch
import mlflow
import warnings
import numpy as np

import utils.globals as globals
from utils.saving import save_model, save_results, save_test_images, save_image_color_legend, save_crowd_images, \
    save_grad_flow, save_test_image_variability, save_model_distributions
from utils.test_helpers import segmentation_scores
from utils.mlflow_logger import log_results, log_results_list, probabilistic_model_logging, set_epoch_output_dir, set_test_output_dir
from utils.initialize_optimization import init_optimization
from utils.initialize_model import init_model

eps=1e-7


class ModelHandler():
    def __init__(self, annotators):
        config = globals.config
        self.train_img_vis = []
        self.train_label_vis = []
        self.train_pred_vis = []
        self.train_img_name = []
        self.epoch = 0
        self.model = init_model(annotators)
        self.model.cuda()
        if torch.cuda.is_available():
            print('Running on GPU')
            self.device = torch.device('cuda')
        else:
            warnings.warn("Running on CPU because no GPU was found!")
            self.device = torch.device('cpu')

    def train(self, trainloader, validate_data):
        config = globals.config
        model = self.model
        epochs = config['model']['epochs']
        batch_s = config['model']['batch_size']

        save_image_color_legend()

        optimizer, loss_fct = init_optimization(model)

        # Training loop
        for i in range(0, epochs):
            print('\nEpoch: {}'.format(i))
            model.train()
            set_epoch_output_dir(i)
            self.epoch = i

            # Training in batches
            for j, (images, labels, imagename, ann_ids) in enumerate(trainloader):
                # Loading data to GPU
                images = images.cuda().float()
                labels = labels.cuda().long()
                ann_ids = ann_ids.cuda().float()

                # zero the parameter gradients
                optimizer.zero_grad()

                _, labels = torch.max(labels, dim=1)
                loss, y_pred = model.train_step(images, labels, loss_fct, ann_ids)

                if config['model']['method'] != 'conf_matrix':
                    if j % int(config['logging']['interval']) == 0:
                        print("Iter {}/{} - batch loss : {:.4f}".format(j, len(trainloader), loss))
                        self.log_training_metrics(y_pred, labels, loss, model, i * len(trainloader) * batch_s + j)
                    self.store_train_imgs(imagename, images, labels, y_pred)
                elif config['model']['method'] == 'conf_matrix' and i == config['model']['conf_matrix_config']['activate_min_trace_epoch']:  # 10 for cr_image_dice // 5 rest of the methods
                    optimizer = model.activate_min_trace()

                # Backprop
                if not torch.isnan(loss):
                    loss.backward()
                    optimizer.step()

            mlflow.log_metric('finished_epochs', self.epoch + 1, int((i + 1) * len(trainloader) * batch_s))

            if i % int(config['logging']['artifact_interval']) == 0:
                val_results = self.evaluate(validate_data, mode='val')
                log_results_list(val_results, mode='val', step=int((i + 1) * len(trainloader) * batch_s))
                save_model_distributions(model)
                save_grad_flow(model.named_parameters())
                self.save_train_imgs()

            mlflow.log_artifacts(globals.config['logging']['experiment_folder'])

            # LR decay
            if i > config['model']['lr_decay_after_epoch']:
                for g in optimizer.param_groups:
                    g['lr'] = g['lr'] / (1 + config['model']['lr_decay_param'])
        save_model(model)

    def test(self, test_data):
        set_test_output_dir()
        save_image_color_legend()
        results = self.evaluate(test_data)
        log_results_list(results, mode='test', step=None)
        mlflow.log_artifacts(globals.config['logging']['experiment_folder'])

    def evaluate(self, data, mode='test'):
        config = globals.config
        class_no = config['data']['class_no']
        vis_images = config['data']['visualize_images'][mode]

        if mode=='test':
            print("Testing the best model")
            model_dir = 'models'
            dir = os.path.join(globals.config['logging']['experiment_folder'], model_dir)
            model_path = os.path.join(dir, 'best_model.pth')
            model = torch.load(model_path)
        else:
            model = self.model

        device = self.device
        model.eval()
        annotator_list = data[0]
        loader_list = data[1]

        with torch.no_grad():
            results_list = []
            for e in range(len(loader_list)):
                labels = []
                preds = []
                for j, (test_img, test_label, test_name, ann_id) in enumerate(loader_list[e]):
                    test_img = test_img.to(device=device, dtype=torch.float32)
                    if config['model']['method'] == 'pionono':
                        model.forward(test_img)
                        if 'STAPLE' in annotator_list[e] or 'MV' in annotator_list[e]:
                            test_pred, _ = model.get_gold_predictions()
                        else:
                            test_pred = model.sample(use_z_mean=True, annotator_ids=ann_id, annotator_list=annotator_list)
                    elif config['model']['method'] == 'prob_unet':
                        model.forward(test_img, None, training=False)
                        test_pred = model.sample(testing=True)
                    elif config['model']['method'] == 'conf_matrix':
                        test_pred = model(test_img)[0]
                    else:
                        test_pred = model(test_img)
                    _, test_pred = torch.max(test_pred[:, 0:class_no], dim=1)
                    test_pred_np = test_pred.cpu().detach().numpy()
                    test_label = test_label.cpu().detach().numpy()
                    test_label = np.argmax(test_label, axis=1)

                    preds.append(test_pred_np.astype(np.int8).copy().flatten())
                    labels.append(test_label.astype(np.int8).copy().flatten())

                    # We only want to execute the code below once for each image.
                    if e == 0:
                        if self.epoch % int(config['logging']['artifact_interval']) == 0 or mode == 'test':
                            for k in range(len(test_name)):
                                if test_name[k] in vis_images or vis_images == 'all':
                                    img = test_img[k]
                                    save_test_images(img, test_pred_np[k], test_label[k], test_name[k], mode)
                                    save_test_image_variability(model, test_name, k, mode)

                preds = np.concatenate(preds, axis=0, dtype=np.int8).flatten()
                labels = np.concatenate(labels, axis=0, dtype=np.int8).flatten()
                if e == 0:
                    shortened = False
                else:
                    shortened = True
                results = self.get_results(preds, labels, shortened)

                print('RESULTS for ' + mode + ' Annotator: ' + str(annotator_list[e]))
                print(results)
                results_list.append(results)
        return results_list

    def get_results(self, pred, label, shortened=False):
        if torch.is_tensor(pred):
            pred = pred.cpu().detach().numpy().copy().flatten()
        if torch.is_tensor(label):
            label = label.cpu().detach().numpy().copy().flatten()

        results = segmentation_scores(label, pred, shortened)

        return results

    def log_training_metrics(self, y_pred, labels, loss, model, step):
        config = globals.config
        _, y_pred = torch.max(y_pred[:, 0:config['data']['class_no']], dim=1)
        mlflow.log_metric('loss',float(loss.cpu().detach().numpy()), step=step)
        train_results = self.get_results(y_pred, labels)
        log_results(train_results, mode='train', step=step)
        probabilistic_model_logging(model, step)

    def store_train_imgs(self, imagenames, images, labels, y_pred):
        config = globals.config
        vis_train_images = config['data']['visualize_images']['train']

        for k in range(len(imagenames)):
            if imagenames[k] in vis_train_images:
                _, y_pred_argmax = torch.max(y_pred[:, 0:config['data']['class_no']], dim=1)
                self.train_img_vis.append(images[k])
                self.train_label_vis.append(labels[k].cpu().detach().numpy())
                self.train_pred_vis.append(y_pred_argmax[k].cpu().detach().numpy())
                self.train_img_name.append(imagenames[k])

                # if len(y_pred[k].cpu().detach().numpy().shape) == 1:
                #     print(y_pred[k])

    def save_train_imgs(self):
        for i in range(len(self.train_img_vis)):
            save_test_images(self.train_img_vis[i], self.train_pred_vis[i],
                             self.train_label_vis[i], self.train_img_name[i], 'train')
        self.train_img_vis = []
        self.train_label_vis = []
        self.train_pred_vis = []
        self.train_img_name = []