import pathlib
from typing import List, Union, Optional, Sequence
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import ffmpeg

from asi.load import get_frames
import asi.config as config


def plot_movie(time_range: Sequence[Union[datetime, str]], mission: str, station: str, **kwargs):
    """
    A warpper for plot_movie_generator() generator function. This function calls 
    plot_movie_generator() in a for loop, nothing more. The two function's arguments
    and keyword arguments are identical.
    
    To make movies, you'll need to install ffmpeg in your operating system. 

    Parameters
    ----------
    time_range: List[Union[datetime, str]]
        A list with len(2) == 2 of the start and end time to get the
        frames. If either start or end time is a string, 
        dateutil.parser.parse will attempt to parse it into a datetime
        object. The user must specify the UT hour and the first argument
        is assumed to be the start_time and is not checked.
    mission: str
        The mission id, can be either THEMIS or REGO.
    station: str
        The station id to download the data from.
    force_download: bool (optional)
        If True, download the file even if it already exists.
    add_label: bool
        Flag to add the "mission/station/frame_time" text to the plot.
    color_map: str
        The matplotlib colormap to use. If 'auto', will default to a 
        black-red colormap for REGO and black-white colormap for THEMIS. 
        For more information See 
        https://matplotlib.org/3.3.3/tutorials/colors/colormaps.html
    color_bounds: List[float] or None
        The lower and upper values of the color scale. If None, will 
        automatically set it to low=1st_quartile and 
        high=min(3rd_quartile, 10*1st_quartile)
    ax: plt.subplot()
        The optional subplot that will be drawn on.
    color_norm: str
        Sets the 'lin' linear or 'log' logarithmic color normalization.
    movie_format: str
        The movie format: mp4 has better compression but avi can be 
        opened by the VLC player.
    clean_pngs: bool
        Remove the intermediate png files created for the ffmpeg library.

    Returns
    -------
    """
    movie_generator = plot_movie_generator(time_range, mission, station, **kwargs)

    for frame_time, im, ax in movie_generator:
        pass
    return


def plot_movie_generator(time_range: Sequence[Union[datetime, str]], mission: str, station: str, 
            force_download: bool=False, add_label: bool=True, color_map: str='auto',
            color_bounds: Union[List[float], None]=None, color_norm: str='log', 
            ax: plt.subplot=None, movie_format: str='mp4', clean_pngs: bool=True):
    """
    A generator function that yields ASI images, frame by frame.

    Parameters
    ----------
    time_range: List[Union[datetime, str]]
        A list with len(2) == 2 of the start and end time to get the
        frames. If either start or end time is a string, 
        dateutil.parser.parse will attempt to parse it into a datetime
        object. The user must specify the UT hour and the first argument
        is assumed to be the start_time and is not checked.
    mission: str
        The mission id, can be either THEMIS or REGO.
    station: str
        The station id to download the data from.
    force_download: bool (optional)
        If True, download the file even if it already exists.
    add_label: bool
        Flag to add the "mission/station/frame_time" text to the plot.
    color_map: str
        The matplotlib colormap to use. If 'auto', will default to a 
        black-red colormap for REGO and black-white colormap for THEMIS. 
        For more information See 
        https://matplotlib.org/3.3.3/tutorials/colors/colormaps.html
    color_bounds: List[float] or None
        The lower and upper values of the color scale. If None, will 
        automatically set it to low=1st_quartile and 
        high=min(3rd_quartile, 10*1st_quartile)
    ax: plt.subplot()
        The optional subplot that will be drawn on.
    movie_format: str
        The movie format: mp4 has better compression but avi can be 
        opened by the VLC player.
    color_norm: str
        Sets the 'lin' linear or 'log' logarithmic color normalization.
    clean_pngs: bool
        Remove the intermediate png files created for the ffmpeg library.

    Yields
    ------
    frame_time: datetime.datetime
        The time of the current frame.
    im: plt.imshow
        The plt.imshow object. Common use for im is to add a colorbar.
    ax: plt.subplot
        The subplot object to modify the axis, labels, etc.
    """
    frame_times, frames = get_frames(time_range, mission, station, 
                                    force_download=force_download)
    if ax is None:
        _, ax = plt.subplots()

    # Create the movie directory inside config.ASI_DATA_DIR if it does 
    # not exist.
    save_dir = config.ASI_DATA_DIR / 'movies' / 'temp'
    if not save_dir.is_dir():
        save_dir.mkdir(parents=True)
        print(f'Created a {save_dir} directory')

    if (color_map == 'auto') and (mission.lower() == 'themis'):
        color_map = 'Greys_r'
    elif (color_map == 'auto') and (mission.lower() == 'rego'):
        color_map = colors.LinearSegmentedColormap.from_list('black_to_red', ['k', 'r'])
    else:
        raise NotImplementedError('color_map == "auto" but the mission is unsupported')

    save_paths = []

    for frame_time, frame in zip(frame_times, frames):
        ax.clear()
        plt.axis('off')
        # Figure out the color_bounds from the frame data.
        if color_bounds is None:
            lower, upper = np.quantile(frame, (0.25, 0.98))
            color_bounds = [lower, np.min([upper, lower*10])]

        if color_norm == 'log':
            norm=colors.LogNorm(vmin=color_bounds[0], vmax=color_bounds[1])
        elif color_norm == 'lin':
            norm=colors.Normalize(vmin=color_bounds[0], vmax=color_bounds[1])
        else:
            raise ValueError('color_norm must be either "log" or "lin".')

        im = ax.imshow(frame, cmap=color_map, norm=norm)
        if add_label:
            ax.text(0, 0, f"{mission}/{station}\n{frame_time.strftime('%Y-%m-%d %H:%M:%S')}", 
                    va='bottom', transform=ax.transAxes, color='white')
        
        # Give the user the control of the subplot, image object, and return the frame time
        # so that the user can manipulate the image to add, for example, the satellite track. 
        yield frame_time, im, ax

        # Save the file and clear the subplot for next frame.
        save_name = (f'{frame_time.strftime("%Y%m%d_%H%M%S")}_{mission.lower()}_'
                     f'{station.lower()}.png')
        plt.savefig(save_dir / save_name)
        save_paths.append(save_dir / save_name)

    # Make the movie
    movie_file_name = (f'{frame_times[0].strftime("%Y%m%dT%H%M%S")}_'
                       f'{frame_times[1].strftime("%Y%m%dT%H%M%S")}_'
                       f'{mission.lower()}_{station.lower()}.{movie_format}')
    movie_obj = ffmpeg.input(str(save_dir) + f'/*{mission.lower()}_{station.lower()}.png', 
                pattern_type='glob', framerate=10)
    movie_obj.output(str(save_dir.parent / movie_file_name)).run()
    # Clean up.
    if clean_pngs:
        for path in save_paths:
            path.unlink()
    return

    
if __name__ == "__main__":
    plot_movie((datetime(2017, 9, 15, 2, 34, 0), datetime(2017, 9, 15, 2, 36, 0)), 
                'THEMIS', 'RANK', color_norm='log')