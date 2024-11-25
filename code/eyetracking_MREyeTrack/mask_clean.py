from pathlib import Path
import json
import ppjson
from importlib import reload  # For debugging purposes

import numpy as np
import pandas as pd

import eyetrackingrun as et

from IPython.display import HTML
from matplotlib import animation
from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import copy
from write_bids_yiwei import EyeTrackingRun, write_bids, write_bids_from_df

def find_mean_position(X_coord, Y_coord):
    print('To find the median coor of the point clouds')
    filtered_X_coord = X_coord[~np.isnan(X_coord) & (X_coord != 0)]
    filtered_Y_coord = Y_coord[~np.isnan(Y_coord) & (Y_coord != 0)]
    med_x = np.nanmedian(filtered_X_coord)
    med_y = np.nanmedian(filtered_Y_coord)
    med_coor = [med_x, med_y]
    print(f'The mean position of the gaze region: {med_coor} (px)')
    return med_coor

def cal_angles(X_coord, Y_coord, med_coor):
    print('To calculate visual angles w.r.t. points')
    # distance from eye to the screen (mm)
    d = 1020
    # radius of the human eye (mm)
    r = 12

    x_hor_mm = np.where(np.isnan(X_coord), np.nan, (X_coord - 400) * 81.3 / 176)
    med_x_hor_mm = (med_coor[0]- 400) * 81.3 / 176
    theta_h_ = np.where(np.isnan(x_hor_mm), np.nan, np.arctan(x_hor_mm / (d+r)))
    theta_h_m = np.arctan(med_x_hor_mm / (d+r))
    
    y_ver_mm = np.where(np.isnan(Y_coord), np.nan, (Y_coord - 300) * 62 / 137)
    med_y_ver_mm = (med_coor[1]- 300) * 62 / 137
    rho_v_ = np.where(np.isnan(y_ver_mm), np.nan, np.arctan(y_ver_mm / (d+r)))
    rho_v_m = np.arctan(med_y_ver_mm / (d+r))

    return theta_h_, theta_h_m, rho_v_, rho_v_m

def cal_disp(theta_h_, theta_h_m, rho_v_, rho_v_m):
    print('To calculate the displacement in both directions (mm)')
    # distance from eye to the screen (mm)
    d = 1020
    # radius of the human eye (mm)
    r = 12

    theta_h_dis = np.where(np.isnan(theta_h_), np.nan, np.abs(theta_h_ - theta_h_m))
    h_dis = np.where(np.isnan(theta_h_dis), np.nan, np.sin(theta_h_dis)*r)

    rho_v_dis = np.where(np.isnan(rho_v_), np.nan, np.abs(rho_v_ - rho_v_m))
    v_dis = np.where(np.isnan(rho_v_dis), np.nan, np.sin(rho_v_dis)*r)

    return h_dis, v_dis

def filter_criteria(h_dis, v_dis, criteria_ratio=0.5):
    # criteria_ratio is the ratio of the voxel size mm
    print('To generate discard masks for x and y direction...')
    voxel_size = 0.5
    disp_criteria = criteria_ratio*voxel_size

    Ms_to_be_discarded_x_mask = (
      (h_dis > disp_criteria) | np.isnan(h_dis)
        )
    Ms_to_be_discarded_y_mask = (
           (v_dis > disp_criteria) | np.isnan(v_dis)
        )
    return Ms_to_be_discarded_x_mask, Ms_to_be_discarded_y_mask
    

def filter_XY_with_mask(coor_data, discarded_x_mask, discarded_y_mask, seq_name=None):
    from matplotlib.font_manager import FontProperties
    title_font = FontProperties(family='Times New Roman', size=20, weight='bold')
    axis_font = FontProperties(family='Times New Roman', size=16)
#     x y coordinate accordingly
    coor_data_clean = copy.deepcopy(coor_data)
    X_coord = coor_data_clean["x_coordinate"].values
    Y_coord = coor_data_clean["y_coordinate"].values
    
    Preserve_mask = ~(discarded_x_mask|discarded_y_mask)
   
    filtered_X_coord = X_coord * Preserve_mask
    filtered_Y_coord = Y_coord * Preserve_mask

    zero_mask = (filtered_X_coord == 0) & (filtered_Y_coord == 0)
    filtered_X_coord[zero_mask] = np.nan
    filtered_Y_coord[zero_mask] = np.nan
    
    Discard_mask = np.where(np.isnan(filtered_X_coord) | np.isnan(filtered_Y_coord), 1, 0)

    # Example data (replace with your actual data)
    fig, ax= plt.subplots(figsize=(8, 6))
    # Plot the data, flipping X coordinates and using dots as markers
    plt.plot(filtered_X_coord, filtered_Y_coord, '.', color='#00468b',markersize=20)
    plt.xlim(0, 800)
    plt.ylim((0, 600))
    # Set plot title
    if seq_name is not None:
        plt.title(f'After filtering: {seq_name}', fontproperties=title_font)
    else:     
        plt.title('After filtering:', fontproperties=title_font)

    # Reverse the direction of the Y-axis
    for label in plt.gca().get_xticklabels():
        label.set_fontproperties(axis_font)

    for label in plt.gca().get_yticklabels():
        label.set_fontproperties(axis_font)
    plt.gca().invert_yaxis()
    plt.gca().invert_xaxis()
    
    coor_data_clean["x_coordinate"] = filtered_X_coord
    coor_data_clean["y_coordinate"] = filtered_Y_coord
    
    return coor_data_clean, Preserve_mask, Discard_mask


def plot_h_v_disp(h_dis, v_dis, discard_x_mask, discard_y_mask, criteria_ratio=0.5):
    
    from matplotlib.font_manager import FontProperties
    title_font = FontProperties(family='Times New Roman', size=20, weight='bold')
    
    start_sample = 0
    end_sample = len(h_dis)
    t_axis_xy = np.arange(start_sample, end_sample, 1)/1000
    criteria_disp = criteria_ratio*0.5

    # Horizontal direction!!!!!
    fig, ax= plt.subplots(figsize=(8, 4))
    ax.plot(
        t_axis_xy,
        h_dis[start_sample:end_sample],
        marker='o', color='green',
        label='Horizontal displacement in mm'
    )

    if len(discard_x_mask) != 0:
        ax.plot(
            t_axis_xy,
            h_dis[start_sample:end_sample] * discard_x_mask[start_sample:end_sample],
            marker='^', color='purple',
            label= 'MS to be discarded'
        )
    ax.axhline(y=criteria_disp, color='r', linestyle='--', label='criterion')
    ax.legend()
    ax.set_title('Filtered Horizontal Displacement', fontproperties=title_font)
    plt.tight_layout()

    # Vertical direction!!!!!
    fig, ax= plt.subplots(figsize=(8, 4))
    ax.plot(
        t_axis_xy,
        v_dis[start_sample:end_sample],
        marker='o', color='blue',
        label="Vertical displacement in mm"
    )


    if len(discard_y_mask) != 0:
        ax.plot(
            t_axis_xy,
            v_dis[start_sample:end_sample] * discard_y_mask[start_sample:end_sample],
            marker='^', color='purple',
            label= 'MS to be discarded'
        )

    ax.axhline(y=criteria_disp, color='r', linestyle='--', label='criterion')

    ax.legend()
    ax.set_title('Filtered Vertical Displacement', fontproperties=title_font)
    plt.tight_layout()


def visualization_func(fig_title,coor_data_raw, coor_data, coor_data_clean):
    from matplotlib.font_manager import FontProperties
    title_font = FontProperties(family='Times New Roman', size=20, weight='bold')
    axis_font = FontProperties(family='Times New Roman', size=16)
    
    fig, ax= plt.subplots(figsize=(8, 6))
    plt.title(fig_title, fontproperties=title_font)
#     -----------------------------------------------------------------------
    # Plot the data, flipping X coordinates and using dots as markers
    X_coord_raw = coor_data_raw['x_coordinate']
    Y_coord_raw = coor_data_raw['y_coordinate']
    plt.scatter(X_coord_raw, Y_coord_raw, s=50, c='coral', alpha=0.1, edgecolors='coral', linewidth=0.2)
#     -----------------------------------------------------------------------
    coor_data_vis = copy.deepcopy(coor_data)
    X_coord_1 = coor_data_vis['x_coordinate']
    Y_coord_1 = coor_data_vis['y_coordinate']

    # plt.plot(X_coord_1, Y_coord_1, '.', color='#728FCE', markersize=15, label='LIBRE w.o. binning')
    plt.scatter(X_coord_1, Y_coord_1, s=50, c='#728FCE', alpha=0.1, edgecolors='#728FCE', linewidth=0.2)
    
#     -----------------------------------------------------------------------
    X_coord = coor_data_clean['x_coordinate']
    Y_coord = coor_data_clean['y_coordinate']
 
    # plt.plot(X_coord, Y_coord, '.', color='#f4d03f', markersize=15, label='LIBRE binning')
    plt.scatter(X_coord, Y_coord, s=50, c='#f4d03f', alpha=0.1, edgecolors='#f4d03f', linewidth=0.2)  # Larger points
#     ----------------------------------------------------------------------------------------------
    # plt.legend(prop={'family': 'Times New Roman', 'size': 20})
    
    plt.tick_params(axis='x', labelsize=10)
    plt.tick_params(axis='y', labelsize=10)
    plt.xlim((0, 800))
    plt.ylim((0, 600))
    # Set plot title
#     plt.title(fig_title, fontproperties=title_font)
    for label in plt.gca().get_xticklabels():
        label.set_fontproperties(axis_font)

    for label in plt.gca().get_yticklabels():
        label.set_fontproperties(axis_font)
    # Reverse the direction of the Y-axis
    plt.gca().invert_yaxis()
    plt.gca().invert_xaxis()
    