import datetime
import glob
from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
import pywebcoos 
import random
import re
from sklearn.neural_network import MLPClassifier
import warnings
import cv2
import json

import moviepy
if moviepy.__version__ == '1.0.3':
    from moviepy.video.compositing.concatenate import concatenate_videoclips
    from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
else:
    from moviepy import *

from .CoopsApi import CoopsApi
from .CoopsApiTwo import CoopsApiTwo

warnings.filterwarnings('ignore')


def get_cameras(token):
    api = pywebcoos.API(token)
    return api.get_cameras()


def get_products(camera, token):
    api = pywebcoos.API(token)
    return api.get_products(camera)


def get_inventory(camera, product, token):
    api = pywebcoos.API(token)
    return api.get_inventory(camera, product)


def synch(station, camera, data_product, camera_product, value, time_start, time_end, interval, cutoff, sep_model, token, save_dir):
    _check_date_format(time_start, 'start', token)
    _check_date_format(time_end, 'end', token)
    _check_date_range(camera, camera_product, time_start, time_end, token)
    
    datas = _synch_init(station, data_product, value, time_start, time_end, interval, cutoff)
        
    print(f"Synchronizing {len(datas)} timestamps. Fetching corresponding WebCOOS images...") # --- DEBUG PRINT ---
        
    datas['image'] = ''
    for i in range(len(datas)):
        
        # --- DEBUG PRINT ---
        if i % 10 == 0 or i == len(datas) - 1:
            print(f"   -> Fetching WebCOOS image {i+1} of {len(datas)}...") 
        # -------------------
        
        time_start = _dt2datestr(datas['date_time'].iloc[i])
        time_end = _dt2datestr(datas['date_time'].iloc[i]+datetime.timedelta(minutes=1))
        filename = _call_WebcoosApi(camera=camera,
                                    product=camera_product,
                                    time_start=time_start,
                                    time_end=time_end,
                                    token=token,
                                    save_dir=save_dir)
        if filename:
            datas.loc[i,'image'] = filename[0]
        else:
            datas.loc[i,'image'] = ''
            
    if sep_model is not None:
        vs = ViewSeparator(camera, token, n_views=7)
        f = open(sep_model, 'rb')
        modell = pickle.load(f)
        model = modell[0]
        decim_fac = modell[1]
        pred = []
        for i in range(len(datas)):
            imf = datas.iloc[i]['image']
            if len(imf) > 0:
                im = plt.imread(imf)
                prediction = vs.predict(model, im, decim_fac=decim_fac)[0]
                pred.append(prediction)
            else:
                pred.append(np.nan)
        datas['view'] = pred
    else:
        datas['view'] = list(np.zeros(len(datas))*np.nan)
       
    return datas


def synch_local(station, camera, data_product, local_dir, value, time_start, time_end, interval, cutoff):
    _check_local_dir(local_dir)
    
    datas = _synch_init(station, data_product, value, time_start, time_end, interval, cutoff)
    
    datas['image'] = 0
    for i in range(len(datas)):
        time_start = _dt2datestr(datas['date_time'].iloc[i])
        time_end = _dt2datestr(datas['date_time'].iloc[i]+datetime.timedelta(minutes=1))
        filename = _get_local_image(local_dir, time_start)
        if filename:
            datas['image'].iloc[i] = filename[0]
        else:
            datas['image'].iloc[i] = ''
    
    return datas
    

import os
import glob
import cv2
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import moviepy.video.io.ImageSequenceClip

def make_movie(synchro, camera, station=None, save_dir='.', extra_csv_dir='.', gap_threshold_hours=1.0, local_timezone='UTC'):
    """
    Takes the synchronized data dictionary, creates stacked plots, generates a video, 
    and outputs an interactive HTML dashboard. Automatically aligns CSV UTC data 
    to the requested local timezone to match NOAA timestamps.
    """
    print("Generating frames and compiling video...")
    
    dates = synchro['date_time'] if 'date_time' in synchro else []
    image_paths = synchro['image'] if 'image' in synchro else []
    water_levels = synchro['value'] if 'value' in synchro else []
    
    has_tide = station is not None and len(water_levels) > 0
    
    csv_files = sorted(glob.glob(os.path.join(extra_csv_dir, "*.csv")))
    extra_datasets = []
    threshold = pd.Timedelta(hours=gap_threshold_hours)

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            col_map = {'datetime (timezone=UTC)': 'datetime', 'datetime(timezone=UTC)': 'datetime', 'date_time': 'datetime', 'Date Time': 'datetime', 'time': 'datetime'}
            df.rename(columns=lambda x: col_map.get(x, x), inplace=True)
            
            if 'datetime' not in df.columns:
                continue
                
            # Parse the CSV timestamps as UTC first
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
            
            # Automatically calculate and apply the correct local UTC offset for each row's specific date
            if local_timezone != 'UTC':
                df['datetime'] = df['datetime'].dt.tz_convert(local_timezone)
                
            # Strip timezone awareness so it aligns with NOAA's naive local timestamps
            df['datetime'] = df['datetime'].dt.tz_localize(None)
            
            df = df.sort_values('datetime')
            
            # Graph Gap Break Logic
            gaps = df['datetime'].diff() > threshold
            if gaps.any():
                break_times = df['datetime'].shift(1)[gaps] + pd.Timedelta(seconds=1)
                dummy_df = pd.DataFrame({'datetime': break_times})
                df = pd.concat([df, dummy_df]).sort_values('datetime').reset_index(drop=True)

            y_col = 'value'
            if y_col not in df.columns:
                num_cols = df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    y_col = num_cols[0]
                else:
                    continue 
            
            extra_datasets.append({'name': os.path.basename(file_path).replace('.csv', ''), 'df': df, 'plot_col': y_col})
        except Exception as e:
            print(f"Warning: Could not process {os.path.basename(file_path)}: {e}")

    num_graphs = (1 if has_tide else 0) + len(extra_datasets)
    time_markers = []
    
    if num_graphs > 0:
        fig, axes = plt.subplots(nrows=num_graphs, ncols=1, sharex=True, figsize=(10, 3 * num_graphs))
        if num_graphs == 1: axes = [axes]
        ax_index = 0

        if has_tide:
            axes[ax_index].plot(dates, water_levels, color='blue', linewidth=2, label='Water Level')
            axes[ax_index].set_ylabel('Water Level (m)')
            axes[ax_index].set_title(f"Station: {station} | Camera: {camera}")
            axes[ax_index].grid(True, alpha=0.3)
            axes[ax_index].legend(loc='upper right')
            ax_index += 1

        for dataset in extra_datasets:
            df = dataset['df']
            axes[ax_index].plot(df['datetime'], df[dataset['plot_col']], color='green', linewidth=1.5, marker='o', markersize=4, linestyle='-', label=dataset['name'])
            axes[ax_index].set_ylabel(dataset['plot_col'].title())
            if not has_tide and ax_index == 0:
                axes[ax_index].set_title(f"Camera: {camera}")
            axes[ax_index].grid(True, alpha=0.3)
            axes[ax_index].legend(loc='upper right')
            ax_index += 1
            
        if num_graphs > 1:
            plt.setp([a.get_xticklabels() for a in axes[:-1]], visible=False)
        plt.xticks(rotation=45)
        plt.tight_layout()

        for ax in axes:
            initial_time = dates[0] if len(dates) > 0 else 0
            marker = ax.axvline(x=initial_time, color='red', linewidth=2, linestyle='--')
            time_markers.append(marker)

    combined_frames = []
    relative_frame_paths = []
    frame_save_dir = os.path.join(save_dir, 'frames')
    os.makedirs(frame_save_dir, exist_ok=True)

    for i, (img_path, current_time) in enumerate(zip(image_paths, dates)):
        if not os.path.exists(img_path):
            continue

        cam_img = cv2.imread(img_path)
        if cam_img is None:
            continue

        if num_graphs > 0:
            for marker in time_markers:
                marker.set_xdata([current_time, current_time])
            fig.canvas.draw()
            plot_img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            plot_img = plot_img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plot_img = cv2.cvtColor(plot_img, cv2.COLOR_RGB2BGR)
            
            target_width = cam_img.shape[1]
            aspect_ratio = plot_img.shape[0] / plot_img.shape[1] 
            target_height = int(target_width * aspect_ratio)
            plot_img_resized = cv2.resize(plot_img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            combined_frame = cv2.vconcat([cam_img, plot_img_resized])
        else:
            combined_frame = cam_img
            
        frame_filename = os.path.join(frame_save_dir, f"frame_{i:04d}.jpg")
        cv2.imwrite(frame_filename, combined_frame)
        combined_frames.append(frame_filename)
        relative_frame_paths.append(f"frames/frame_{i:04d}.jpg")

    if num_graphs > 0:
        plt.close(fig)

    if not combined_frames:
        print("Error: No frames were generated.")
        return None

    prefix = station if station else camera
    video_name = os.path.join(save_dir, f"{prefix}_sync_movie.mp4")
    print(f"Encoding video to {video_name}...")
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(combined_frames, fps=5)
    clip.write_videofile(video_name, logger=None)
    
    print("Generating HTML dashboard...")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebCOOS Synch Dashboard</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; background: #121212; color: white; margin: 0; padding: 20px; }}
            #viewer-container {{ max-width: 1200px; margin: 0 auto; }}
            img#frame-display {{ width: 100%; height: auto; border: 2px solid #333; border-radius: 8px; }}
            .controls {{ margin-top: 20px; display: flex; align-items: center; justify-content: center; gap: 15px; }}
            input[type=range] {{ width: 60%; cursor: pointer; }}
            button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div id="viewer-container">
            <h2>{prefix} Timeline Dashboard</h2>
            <img id="frame-display" src="{relative_frame_paths[0]}" alt="Synchronized Frame">
            <div class="controls">
                <button id="playBtn">Play</button>
                <button id="pauseBtn">Pause</button>
                <input type="range" id="slider" min="0" max="{len(relative_frame_paths) - 1}" value="0">
                <span id="frameCounter">1 / {len(relative_frame_paths)}</span>
            </div>
        </div>

        <script>
            const frames = {json.dumps(relative_frame_paths)};
            const img = document.getElementById('frame-display');
            const slider = document.getElementById('slider');
            const counter = document.getElementById('frameCounter');
            let playing = false;
            let timer;

            function updateFrame(idx) {{
                img.src = frames[idx];
                slider.value = idx;
                counter.innerText = (parseInt(idx) + 1) + " / " + frames.length;
            }}

            slider.addEventListener('input', (e) => {{
                if (playing) {{
                    playing = false;
                    clearInterval(timer);
                }}
                updateFrame(e.target.value);
            }});

            document.getElementById('playBtn').addEventListener('click', () => {{
                if (playing) return;
                playing = true;
                timer = setInterval(() => {{
                    let idx = parseInt(slider.value) + 1;
                    if (idx >= frames.length) idx = 0;
                    updateFrame(idx);
                }}, 200);
            }});

            document.getElementById('pauseBtn').addEventListener('click', () => {{
                playing = false;
                clearInterval(timer);
            }});
        </script>
    </body>
    </html>
    """
    
    html_filename = os.path.join(save_dir, f"{prefix}_dashboard.html")
    with open(html_filename, "w") as f:
        f.write(html_content)

    print("Done!")
    return video_name

def _synch_init(station, data_product, value, time_start, time_end, interval, cutoff):
    if station is None or str(station).lower() == 'none':
        print("Skipping NOAA CO-OPS API fetch. Generating dummy timeline...")
        # Create naive timestamps without UTC enforcement to match local NOAA data
        start_dt = pd.to_datetime(time_start) 
        end_dt = pd.to_datetime(time_end) + pd.Timedelta(days=1)
        dummy_dates = pd.date_range(start=start_dt, end=end_dt, freq='6min')
        return pd.DataFrame({'date_time': dummy_dates, 'value': 0.0})
    
    print("Fetching NOAA CO-OPS data...") # --- DEBUG PRINT ---
    data = _call_CoopsApi(station, data_product, time_start, time_end)
    print("NOAA data fetch complete. Interpolating timelines...") # --- DEBUG PRINT ---
    
    data = data[data['date_time'] >= _datestr2dt(time_start)]
    data = data[data['date_time'] <= _datestr2dt(time_end)]
    
    data_dates = pd.date_range(_datestr2dt(time_start), _datestr2dt(time_end), freq=str(interval)+'min')      
    datai_v = data['value']
    datai_v = np.interp(data_dates, data['date_time'], data['value'])
    datai = pd.DataFrame({'date_time': data_dates, 'value': datai_v})
    data = datai
    
    if value == 'all':
        datas = data.dropna()
    elif isinstance(value, str) and value != 'all':
        raise ValueError("value argument must be either 'all' or a float/integer value.")
    elif isinstance(value, int) or isinstance(value, float):
        tol = 0.01
        datas = data
        datas = datas[datas['value'] >= value-tol]
        datas = datas[datas['value'] <= value+tol]
        datas = datas.sample(frac=1)
        datas = datas.iloc[0:cutoff]
    else:
        raise ValueError("value argument must be either 'all' or a float/integer value.")
    return datas    

    
def _call_CoopsApi(station, data_product, time_start, time_end):
    coopsapi = CoopsApi()
    start_date = _datestr2dt(time_start)
    end_date = _datestr2dt(time_end)
    [data, data_errors] = coopsapi.get_data(str(station), [start_date, end_date], product=data_product, datum='MHHW', timeZone='lst_ldt')
    return data


def _get_flood_thresh(station):
    lvls = CoopsApiTwo(station, '20240101', '20240102', product='floodlevels').run()['floodlevels']
    datums = CoopsApiTwo(station, '20240101', '20240102', product='datums').run()['datums']['datums']
    mhhw = np.array(datums)[np.array([datums[i]['name'] for i in range(len(datums))]) == 'MHHW'][0]['value']

    for k in lvls.keys():
        try:
            lvls[k] = lvls[k]-mhhw
        except:
            pass
    return lvls


def _call_WebcoosApi(camera, product, time_start, time_end, token, save_dir):
    api = pywebcoos.API(token)
    filenames = api.download(camera_name=camera,
                             product_name=product,
                             start=time_start,
                             stop=time_end,
                             interval=1,
                             save_dir=save_dir)
    return filenames


def _get_local_image(local_dir, time):
    dt_want = _datestr2dt(time)
    ims = sorted(os.listdir(local_dir))
    ims = [im for im in ims if '.png' in im or '.jpg' in im]
    datestrs = [im.split('.')[0] for im in ims]
    dts = np.array([_datestr2dt(datestr) for datestr in datestrs])
    i_want = np.where(dts == dt_want)[0]
    if len(i_want) > 0:
        return [os.path.join(local_dir, str(np.array(ims)[i_want][0]))]
    else:
        return None


def _datestr2dt(datestr):
    dt = datetime.datetime(int(datestr[0:4]),
                           int(datestr[4:6]),
                           int(datestr[6:8]),
                           int(datestr[8:10]),
                           int(datestr[10:12]),
                           0)
    return dt


def _dt2datestr(dt):
    mo = dt.month
    day = dt.day
    hr = dt.hour
    mn = dt.minute
    if mo < 10:
        smo = '0'
    else:
        smo = ''
    if day < 10:
        sday = '0'
    else:
        sday = ''
    if hr < 10:
        shr = '0'
    else:
        shr = ''
    if mn < 10:
        smn = '0'
    else:
        smn = ''
    return str(dt.year)+smo+str(mo)+sday+str(day)+shr+str(hr)+smn+str(mn)


def _check_date_format(date, date_name, token):
    api = pywebcoos.API(token)
    api._check_date_format(date, date_name)

    
def _check_date_range(camera_name, product_name, start, stop, token):
    api = pywebcoos.API(token)
    api._check_date_range(camera_name, product_name, start, stop)

    
def _check_local_dir(local_dir):
    files = os.listdir(local_dir)
    exts = [file.split('.')[-1] for file in files]
    pats = [re.match(r'^\d{12}\.*', f) for f in files]

    if len(files) == 0:
        raise ValueError("The input image directory is empty!")
    elif not all(np.array([ext in {'png', 'jpg', 'jpeg', 'tif', 'tiff'} for ext in exts])):
        raise ValueError("At least one file in the image directory does not have a png, jpg, or tif extension.")
    elif not all(pats):
        raise ValueError("At least one file in the image directory is not named with the format yyyymmddHHMM.png/jpg/tif.")


def _save_frames(datas, camera, station, view_num):
    datas['frame'] = ''
    
    if datas['date_time'].diff().dropna().nunique() == 1:
        ts = True
    else:
        ts = False 
        
    lens = np.array([len(datas['image'].iloc[i]) for i in range(len(datas))])
    datas = datas[lens > 0]                     
                     
    if view_num is not None:
        ii = np.where(datas['view'] == view_num)[0]
    else:
        ii = range(len(datas))
               
    for i in ii:
        if ts:
            fig, ax_img, ax_data = _FrameTemplates().ts(datas)            
            ax_data.plot(datas['date_time'].iloc[0:i+1].dt.to_pydatetime(), datas['value'].iloc[0:i+1], color='cornflowerblue')
            ax_data.scatter(datas['date_time'].iloc[i].to_pydatetime(), datas['value'].iloc[i], 150, 
                            color='cornflowerblue', edgecolor='darkgray', linewidth=2, alpha=1)
        else:
            fig, ax_img, ax_data = _FrameTemplates().bar(datas, station)
            ax_data.bar(1, datas['value'].iloc[i], width=0.5, color='cornflowerblue', edgecolor='darkgray')
            
        ax_img.set_xticklabels([])
        ax_img.set_yticklabels([])
        ax_img.set_xticks([])
        ax_img.set_yticks([])
        ax_data.grid('on')
        ax_data.set_ylabel('Height in meters (MHHW)')
        ax_img.set_title('Camera: '+camera+'\nGauge: '+str(station), fontsize=10, fontweight='normal', loc='left')

        mhhw = 0
        if ax_data.get_ylim()[0] < mhhw < ax_data.get_ylim()[1]:
            ax_data.plot(ax_data.get_xlim(), [mhhw, mhhw], 'k--')
            ax_data.text(ax_data.get_xlim()[0], mhhw, 'MHHW', color='k', fontsize=12)
        minor = _get_flood_thresh(station)['nws_minor']
        if minor is not None:
            if ax_data.get_ylim()[0] < minor < ax_data.get_ylim()[1]:
                ax_data.plot(ax_data.get_xlim(), [minor, minor], 'y--')
                ax_data.text(ax_data.get_xlim()[0], minor, 'Minor flooding', color='y', fontsize=12)
        moderate = _get_flood_thresh(station)['nws_moderate']
        if moderate is not None:
            if ax_data.get_ylim()[0] < moderate < ax_data.get_ylim()[1]:
                ax_data.plot(ax_data.get_xlim(), [moderate, moderate], 'r--')
                ax_data.text(ax_data.get_xlim()[0], moderate, 'Moderate flooding', color='r', fontsize=12)        
        major = _get_flood_thresh(station)['nws_major']
        if major is not None:
            if ax_data.get_ylim()[0] < major < ax_data.get_ylim()[1]:
                ax_data.plot(ax_data.get_xlim(), [major, major], 'm--')
                ax_data.text(ax_data.get_xlim()[0], major, 'Major flooding', color='m', fontsize=12)

        im = plt.imread(datas['image'].iloc[i])
        ax_img.imshow(im)

        savename = datas['image'].iloc[i] + '_frame.png'            
        plt.savefig(savename, dpi=450)
        datas.loc[i,'frame'] = savename
        plt.close()
        
    return datas


def _produce_movie(datas_mov, fps):
    datas_mov = datas_mov[~(datas_mov['frame'] == 0)]
        
    clips = []
    for i in range(len(datas_mov)):
        frame_path = datas_mov['frame'].iloc[i]
        clip = ImageSequenceClip([frame_path], fps=fps)            
        clips.append(clip)

    final_clip = concatenate_videoclips(clips)
    
    lens = np.array([len(datas_mov['image'].iloc[i]) for i in range(len(datas_mov))])
    good = np.where(lens > 0)[0]
    if len(good) > 0:
        out_file_name = os.path.basename(datas_mov['image'].iloc[good[0]]).split('.')[0]+'--'+os.path.basename(datas_mov['image'].iloc[good[-1]]).split('.')[0]+'--'+'Video.mp4'
        out_file = os.path.join(os.path.dirname(datas_mov['image'].iloc[good[0]]), out_file_name)
    else:
        out_file = 'Video.mp4'                                                                               
    final_clip.write_videofile(out_file, codec='libx264')
    return out_file


class _FrameTemplates():
    @staticmethod
    def ts(datas):
        fig = plt.figure(figsize = (9, 8)) 
        ax_img = plt.subplot2grid((20, 19), (0, 0), colspan=19, rowspan=11)
        ax_data = plt.subplot2grid((20, 19), (12, 0), colspan=19, rowspan=9)
        plt.subplots_adjust(hspace=0)
        ax_data.set_xlim(datas['date_time'].iloc[0].to_pydatetime(), datas['date_time'].iloc[-1].to_pydatetime())
        ax_data.set_ylim(np.min(datas['value'])-0.1, np.max(datas['value'])+0.1)
        ax_data.xaxis.set_major_formatter(DateFormatter('%m/%d/%y\n%H:%M'))      
        return fig, ax_img, ax_data
    
    @staticmethod
    def bar(datas, station):
        fig = plt.figure(figsize=(9, 4)) 
        ax_img = plt.subplot2grid((11, 19), (0, 0), colspan=12, rowspan=11)
        ax_data = plt.subplot2grid((11, 19), (1, 13), colspan=6, rowspan=9)
        ax_data.yaxis.tick_right()
        ax_data.yaxis.set_label_position("right")
        plt.subplots_adjust(wspace=0)
        ax_data.set_ylim(min([np.min(datas['value']), 0])-0.05, _get_flood_thresh(station)['nws_major']+0.1)
        ax_data.set_xlim(0.5, 1.5)
        ax_data.set_xticks([1])
        ax_data.set_xticklabels([])
        return fig, ax_img, ax_data
    
                
class ViewSeparator():
    def __init__(self, camera, token, n_views):
        self.camera = camera
        self.token = token
        self.n_views = n_views
        
    def get_random_images(self, time_start, time_stop, n, direc):
        times = self._get_random_images_times(time_start, time_stop, n)
        for i in range(len(times)):
            time_start = _dt2datestr(times[i])
            time_end = _dt2datestr(times[i]+datetime.timedelta(minutes=1))
            _call_WebcoosApi(camera=self.camera,
                             product='one-minute-stills',
                             time_start=time_start,
                             time_end=time_end,
                             token=self.token,
                             save_dir=direc)
    
    def label(self, direc):
        ims = os.listdir(direc) 
        for imf in ims:
            imff = os.path.join(direc, imf)
            try:
                im = plt.imread(imff)
            except:
                pass
            else:
                if not os.path.exists(imff.split('.')[0]+'_label'+'.pkl'):
                    plt.imshow(im)   
                    plt.axis('off')
                    plt.show()
                    user_input = input("You specified that this camera has "+str(self.n_views)+" views. Enter the number of this view  (note that entering 0 will place this image in the 'other' category). ")
                    print("Your input:", user_input)
                    label = int(user_input)
                    with open(imff.split('.')[0]+'_label'+'.pkl', 'wb') as f:
                        pickle.dump(label, f)
                    plt.close('all')
    
    def train(self, direc, decim_fac=10):
        dset = self._make_dataset(direc, decim_fac)
        model = self._do_train(dset)
        return model
    
    def predict(self, model, direc_or_image, decim_fac=10):
        dset_pred = self._make_dataset(direc_or_image, decim_fac)
        prediction = self._do_predict(model, dset_pred)
        return prediction     
    
    def inspect_prediction(self, direc, prediction):
        files = glob.glob(direc+'/*.jpg')
        c = -1
        for f in files:
            c += 1
            im = plt.imread(f)
            plt.imshow(im)    
            plt.title('Predicted label = '+str(prediction[c]))
            plt.show()

            input("Press Enter to continue to the next image...")    
            plt.close('all')
            
    def save_model(self, model, decim_fac, direc, fname):
        with open(direc+'/'+fname+'.pkl', 'wb') as f:
            pickle.dump([model, decim_fac], f)
       
    @staticmethod
    def _get_random_images_times(time_start, time_stop, n):
        dt_start = _datestr2dt(time_start)
        dt_stop = _datestr2dt(time_stop)
        r = pd.date_range(dt_start, dt_stop, freq='min')
        i_take = [random.randint(0, len(r)) for _ in range(n)]
        return r[i_take].to_pydatetime()
    
    @staticmethod
    def _make_dataset(direc_or_image, decim_fac):
        if isinstance(direc_or_image, str):
            files = glob.glob(direc_or_image+'/*.jpg')
            dset = pd.DataFrame({'label': [], 'image': []})
            for f in files:
                ims = f
                labs = f.split('.')[0]+'_label.pkl'
                im = plt.imread(ims)
                try:
                    f = open(labs, 'rb')
                    lab = pickle.load(f)
                except:
                    lab = 1000
                dset = pd.concat([dset, pd.DataFrame({'label': int(lab), 'image': [im]}, index=[0])], ignore_index=True)
            dset['image vec'] = dset.apply(lambda row: np.array(row.image).flatten()[0:-1:decim_fac] , axis = 1).tolist()
        else:
            dset = pd.DataFrame({'image': [direc_or_image]})
            dset['image vec'] = dset.apply(lambda row: np.array(row.image).flatten()[0:-1:decim_fac] , axis = 1).tolist()
        return dset
    
    @staticmethod
    def _do_train(dset):
        X = np.vstack(dset['image vec'].tolist()) / 255.0
        y = dset['label']
        mlp_model = MLPClassifier(hidden_layer_sizes=[300, 100], 
                                  activation='relu', 
                                  early_stopping=True,
                                  random_state=13, 
                                  verbose= True)

        mlp_model.fit(X, y)
        return mlp_model
    
    @staticmethod
    def _do_predict(model, dset_pred):
        X = np.vstack(dset_pred['image vec'].tolist()) / 255.0
        pred = model.predict(X)
        return pred
