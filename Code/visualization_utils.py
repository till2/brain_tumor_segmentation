import torch
import torch.nn as nn

import matplotlib.pyplot as plt
from matplotlib.colors import from_levels_and_colors
from matplotlib.animation import FuncAnimation
import matplotlib.cm as cm
from matplotlib.gridspec import GridSpec
from dataset_utils import segment_entire_3d_cube, predict_whole_cube_2d, Labels


def plot_batch(batch, num_rows=2, height=70):
    
    # plt.clf()
    fig, ax_array = plt.subplots(num_rows, 4, figsize=(12,6), 
                                 gridspec_kw = {'wspace':0, 'hspace':0})
    
    for i, ax in enumerate(fig.axes):
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        for row in range(num_rows):
            x = batch['image'][row]
            
            # modalities
            indices = [col_idx + (4*row) for col_idx in range(4)]
            if i in indices:
                ax.imshow(x[i%4, height, :, :], cmap="gray", origin="lower")
                
    plt.show()
    #plt.close()


def _plot_slice(pred_slice, label_slice):
    colors = [(0.3,0.4,0.7),(0.1, 0.9, 0.5),(0.9,0.7,0.2), (0.9,0.4,0.0)]
    
    plt.rcParams.update({'axes.labelsize': 14})
    
    cmap, norm = from_levels_and_colors([0,1,2,3,4], colors)
    slice_labels = ['prediction', 'label']
    fig, axes = plt.subplots(ncols=2)
    fig.set_size_inches(10, 5)

    
    for ax, data, slice_label in zip(axes, [pred_slice, label_slice], slice_labels):
        im = ax.imshow(data, 
                       cmap = cmap,
                       norm = norm, 
                       interpolation ='none')
        ax.set(xlabel=slice_label)
        ax.tick_params(labelsize=12)
    
    cbar = fig.colorbar(im, ticks=[0, 1, 2, 3], orientation='vertical')
    cbar.ax.set_yticklabels([Labels[i] for i in range(4)], fontsize=12)
    plt.show()
    plt.close()

def animate_cube(model, batch, add_context, device, is_3d=True):
    """
    Plots a horizontal slice of the MRI-Image for every fourth image starting from the bottom.
    All four input channels, the segmentation and the label is plotted.
    """
    if is_3d:
        pred_cube = segment_entire_3d_cube(model, batch, add_context, device).cpu()
    else:
        pred_cube = predict_whole_cube_2d(model, batch, device)
    label_slice = batch['label'][0, 0, :, :, :].cpu()
    image_height = len(pred_cube)
    colors = [(0.3, 0.4, 0.7), (0.1, 0.9, 0.5), (0.9, 0.7, 0.2), (0.9, 0.4, 0.0)]
    cmap, norm = from_levels_and_colors([0, 1, 2, 3, 4], colors)

    fig = plt.figure(tight_layout=True)
    gs = GridSpec(2, 4, figure=fig)
    fig.add_subplot(gs[0, 0])
    fig.add_subplot(gs[0, 1])
    fig.add_subplot(gs[0, 2])
    fig.add_subplot(gs[0, 3])
    fig.add_subplot(gs[1, :2])
    fig.add_subplot(gs[1, 2:])
    axes = fig.axes
    fig.set_size_inches(10, 10)
    plt.rcParams.update({'axes.labelsize': 14})

    def animation_step_slice(height):
        height = height*4
        current_pred_slice = pred_cube[height]
        current_label_slice = label_slice[height]

        for i, ax in enumerate(axes[:4]):
            ax.clear()
            ax.imshow(batch['image'][0, i, height, :, :], cmap="gray")

        slice_labels = ['prediction', 'label']
        for ax, data, slice_label in zip(axes[4:], [current_pred_slice, current_label_slice], slice_labels):
            ax.clear()
            ax.imshow(data, cmap=cmap, norm=norm, interpolation='none')
            ax.set(xlabel=slice_label)
            ax.tick_params(labelsize=12)

    cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ticks=[0, 1, 2, 3], orientation='vertical')
    cbar.ax.set_yticklabels([Labels[i] for i in range(4)], fontsize=12)

    ani = FuncAnimation(fig, animation_step_slice, frames=int(image_height/4)-2, interval=100, repeat=True)
    return ani




def plot_minicube_pred_label(model, minicube_batch, device, minicube_idx, height=70):
    """
    Takes a batch of minicubes as input and outputs a comparison plot between a slice 
    of the prediction on a minicube and the label of the minicube
    at the given height of the minicube at the given index in the batch.
    """
    
    # make prediction for minicube
    voxel_logits_batch = model.forward(minicube_batch['image'][None, minicube_idx,:,:,:,:].to(device))
    
    sm = nn.Softmax(dim=1)
    voxel_probs_batch = sm(voxel_logits_batch)
    _ , out = torch.max(voxel_probs_batch, dim=1)
    
    pred_slice = out[0, height, :, :].cpu()
    label_slice = minicube_batch['label'][minicube_idx, 0, height, :, :].cpu()
    
    _plot_slice(pred_slice, label_slice, height)


def plot_cube_pred_label(model, batch, add_context, device, height=70):
    """
    Takes a raw 3d batch as input and outputs a comparison plot between 
    a slice of the prediction and the label at the given height.
    """
    # make prediction on entire cube
    segmented_cube = segment_entire_3d_cube(model, batch, add_context, device)
    
    pred_slice = segmented_cube[height, :, :].cpu()
    label_slice = batch['label'][0, 0, height, :, :].cpu()
    
    _plot_slice(pred_slice, label_slice, height)


def plot_loss(train_losses, test_losses):
    plt.plot(train_losses, label='training loss')
    if test_losses is not None:
        plt.plot(test_losses, label='test loss')
    plt.xlabel('epoch', fontsize=14)
    plt.ylabel('loss', fontsize=14)
    plt.legend()
    plt.show()
    plt.close()
