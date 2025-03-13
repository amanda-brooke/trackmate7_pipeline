# plotting/plotter.py
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from pathlib import Path
from plotting.themes import PlotTheme  # Import your theme class

class Plotter:
    def __init__(self, output_dir: Path, theme: PlotTheme = None):
        """
        Parameters:
            output_dir (Path): Directory where plots will be saved.
            theme (PlotTheme, optional): An instance of PlotTheme. If provided,
                                         it will be applied to all plots.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.theme = theme 
        if theme is not None:
            theme.apply()  # Apply the theme (updates rcParams globally)

    def plot_trajectory(self, edge_table: pd.DataFrame, 
                        title: str = "", 
                        filename: str = "trajectory.png", 
                        cmap=None,
                        facecolor=None,
                        save: bool = True):
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Use provided cmap or fallback to the global default
        if cmap is None:
            cmap = cm.get_cmap('magma')
        # Use provided facecolor or fallback to the current rcParams value
        if facecolor is None:
            facecolor = plt.rcParams['axes.facecolor']
        
        q = ax.quiver(edge_table['source_x'], edge_table['source_y'], 
                      edge_table['u'], edge_table['v'], 
                      edge_table['EDGE_TIME'], angles='xy', scale_units='xy', scale=0.8, 
                      cmap=cmap, alpha=0.95, headlength=0, headaxislength=0, headwidth=0, width=0.003)
        
        ax.set_title(title, fontsize=34)
        ax.set_xlabel('X (µm)', fontsize=20)
        ax.set_ylabel('Y (µm)', fontsize=20)
        ax.tick_params(axis='both', which='both', labelsize=20)
        ax.grid(False)
        ax.set_aspect('equal', adjustable='box')
        ax.set_facecolor(facecolor)
        
        cbar = fig.colorbar(q, ax=ax, orientation='vertical', pad=0.02, aspect=10, shrink=0.6)
        cbar.set_label('Time (Hours)', rotation=270, labelpad=20, fontsize=20)
        cbar.ax.tick_params(labelsize=20)
        for spine in cbar.ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)
        
        if save:
            output_path = self.output_dir / filename
            plt.savefig(output_path)
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
        plt.close()

    def plot_radial_velocity(self, 
                             control_mean: pd.Series, control_sem: pd.Series, 
                             treatment_mean: pd.Series = None, treatment_sem: pd.Series = None, 
                             title: str = "Radial Velocity",
                             filename: str = "radial_velocity.png",
                             style: str = "light",
                             single_group: bool = False,
                             save: bool = True):
        plt.figure(figsize=(8, 6))
        plt.axhline(y=0, color='gray', linestyle='--', linewidth=2)
        
        # Get a custom palette from the theme if available; otherwise, set a default.
        if self.theme is not None:
            custom_palette = self.theme.get_custom_palette()
        else:
            import seaborn as sns
            rocket_palette = sns.color_palette("rocket", n_colors=9)
            custom_palette = [rocket_palette[3], rocket_palette[7]]
        
        if single_group or treatment_mean is None or treatment_sem is None:
            plt.errorbar(
                control_mean.index,
                control_mean.values,
                yerr=control_sem.values,
                color=custom_palette[0],
                label='Wildtype',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
        else:
            plt.errorbar(
                control_mean.index,
                control_mean.values,
                yerr=control_sem.values,
                color=custom_palette[0],
                label='Control',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
            plt.errorbar(
                treatment_mean.index,
                treatment_mean.values,
                yerr=treatment_sem.values,
                color=custom_palette[1],
                label='Treatment',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
        
        plt.ylim(-0.75, 0.6)
        plt.xlim(27, 45)
        plt.xlabel('Time (hr) post BMP4', fontsize=26)
        plt.ylabel('Radial velocity (µm/min)', fontsize=26)
        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        plt.legend(loc='upper left', fontsize=22)
        plt.grid(False)
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / f"radial_velocity_{style}_style.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
        plt.close()
        
    def plot_speed(self, 
                control_mean: pd.Series, control_sem: pd.Series, 
                treatment_mean: pd.Series = None, treatment_sem: pd.Series = None, 
                title: str = "Speed",
                filename: str = "speed.png",
                style: str = "light",
                single_group: bool = False,
                save: bool = True):
        plt.figure(figsize=(8, 6))
        
        # Get a custom palette from the theme if available; otherwise, use a default palette.
        if self.theme is not None:
            custom_palette = self.theme.get_custom_palette()
        else:
            import seaborn as sns
            rocket_palette = sns.color_palette("rocket", n_colors=9)
            custom_palette = [rocket_palette[3], rocket_palette[7]]
        
        # Plot error bars for the control group (or wildtype)
        if single_group or treatment_mean is None or treatment_sem is None:
            plt.errorbar(
                control_mean.index,
                control_mean.values,
                yerr=control_sem.values,
                color=custom_palette[0],
                label='Wildtype',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
        else:
            # Plot error bars for both control and treatment groups
            plt.errorbar(
                control_mean.index,
                control_mean.values,
                yerr=control_sem.values,
                color=custom_palette[0],
                label='Control',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
            plt.errorbar(
                treatment_mean.index,
                treatment_mean.values,
                yerr=treatment_sem.values,
                color=custom_palette[1],
                label='Treatment',
                linewidth=3,
                capsize=4,
                elinewidth=1
            )
        
        # Set plot titles and labels; adjust these as needed based on your data.
        plt.title(title, fontsize=28)
        plt.xlabel('Time (hr) post BMP4', fontsize=26)
        plt.ylabel('Speed (µm/min)', fontsize=26)
        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        plt.legend(loc='upper left', fontsize=22)
        plt.grid(False)
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / f"speed_{style}_style.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
        plt.close()
        
        
    def plot_speed_from_raw(self, edges_data: pd.DataFrame, 
                            bin_size: float = 0.5,
                            title: str = "Speed (TC)",
                            filename: str = "speed_tc.png",
                            style: str = "light",
                            single_group: bool = False,
                            save: bool = True):
        """
        Processes raw edge data to compute binned speed statistics (mean and SEM)
        for Control and Treatment groups, then plots the speed with error bars.
        
        Parameters:
            edges_data (pd.DataFrame): Raw edge data that includes columns 'EDGE_TIME', 'SPEED', and 'Group'.
            bin_size (float): The bin width for EDGE_TIME.
            title (str): Title for the plot.
            filename (str): Filename to save the plot.
            style (str): Plot style indicator.
            single_group (bool): Whether to plot a single group.
            save (bool): Whether to save the plot to a file (True) or display interactively (False).
        """
        # Bin the EDGE_TIME values
        edges_data['EDGE_TIME_BINNED'] = (edges_data['EDGE_TIME'] // bin_size) * bin_size
        
        # Split data into Control and Treatment groups
        control_group = edges_data[edges_data['Group'] == 'Control']
        treatment_group = edges_data[edges_data['Group'] == 'Treatment']
        
        # Group by the binned time and compute mean and standard error for the SPEED column
        control_grouped = control_group.groupby('EDGE_TIME_BINNED')['SPEED']
        treatment_grouped = treatment_group.groupby('EDGE_TIME_BINNED')['SPEED']
        
        control_mean = control_grouped.mean()
        control_sem = control_grouped.sem()
        treatment_mean = treatment_grouped.mean()
        treatment_sem = treatment_grouped.sem()
        
        # Now call the existing plot_speed method using the computed statistics
        self.plot_speed(control_mean, control_sem, treatment_mean, treatment_sem,
                        title=title,
                        filename=filename,
                        style=style,
                        single_group=single_group,
                        save=save)


    def plot_speed_vs_intensity(self, edges_data: pd.DataFrame, spots_data: pd.DataFrame,
                                time_bin_size: float = 0.5,
                                title: str = "Speed vs Fluorescence Intensity",
                                filename: str = "speed_vs_intensity.png",
                                style: str = "light",
                                save: bool = True):
        import numpy as np
        import matplotlib.pyplot as plt

        # Only include treatment group
        edges_data = edges_data[edges_data['Group'] == 'Treatment']
        spots_data = spots_data[spots_data['Group'] == 'Treatment']
        # Merge the spots data into the edges data using SPOT_SOURCE_ID (from edges) and ID (from spots)
        merged = edges_data.merge(
            spots_data[['File_ID', 'ID', 'MEAN_INTENSITY_CH1']],
            left_on=['File_ID', 'SPOT_SOURCE_ID'],
            right_on=['File_ID', 'ID'],
            how='left'
        )
        
        # Bin the EDGE_TIME values
        merged['EDGE_TIME_BINNED'] = (merged['EDGE_TIME'] // time_bin_size) * time_bin_size
        
        # Group by the binned time and compute mean speed and mean fluorescence intensity
        binned_speed = merged.groupby('EDGE_TIME_BINNED')['SPEED'].mean()
        binned_intensity = merged.groupby('EDGE_TIME_BINNED')['MEAN_INTENSITY_CH1'].mean()
        
        # Apply log1p transformation to intensity (log(x+1))
        binned_intensity = np.log1p(binned_intensity)
        
        # Create a scatter plot (x: intensity, y: speed)
        plt.figure(figsize=(8, 6))
        
        # Get a color from the theme if available
        if self.theme is not None:
            custom_palette = self.theme.get_custom_palette()
            color = custom_palette[0]
        else:
            color = 'blue'
        
        plt.scatter(binned_intensity, binned_speed, color=color, s=50)
        plt.xlabel("log1p(Mean Fluorescence Intensity Ch2)", fontsize=16)
        plt.ylabel("Mean Speed (µm/min)", fontsize=16)
        plt.title(title, fontsize=18)
        plt.grid(True)
        plt.tight_layout()
        
        if save:
            output_path = self.output_dir / f"{filename}"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
        plt.close()

    def plot_speed_vs_intensity_simple(self, edges_data: pd.DataFrame, spots_data: pd.DataFrame,
                                    title: str = "Speed vs Fluorescence Intensity",
                                    filename: str = "speed_vs_intensity.png",
                                    style: str = "light",
                                    save: bool = True):
        import numpy as np
        import matplotlib.pyplot as plt

        # Only include treatment group
        edges_data = edges_data[edges_data['Group'] == 'Treatment']
        spots_data = spots_data[spots_data['Group'] == 'Treatment']

        # Merge the spots data into the edges data using SPOT_SOURCE_ID (from edges) and ID (from spots)
        merged = edges_data.merge(
            spots_data[['File_ID', 'ID', 'MEAN_INTENSITY_CH1']],
            left_on=['File_ID', 'SPOT_SOURCE_ID'],
            right_on=['File_ID', 'ID'],
            how='left'
        )

        # Apply log1p transformation directly to each intensity value
        merged['LOG_INTENSITY'] = np.log1p(merged['MEAN_INTENSITY_CH1'])

        # Create a scatter plot (x: log-transformed intensity, y: speed)
        plt.figure(figsize=(8, 6))

        # Get a color from the theme if available
        if self.theme is not None:
            custom_palette = self.theme.get_custom_palette()
            color = custom_palette[0]
        else:
            color = 'blue'

        plt.scatter(merged['LOG_INTENSITY'], merged['SPEED'], color=color, s=50)
        plt.xlabel("log1p(Mean Fluorescence Intensity Ch1)", fontsize=16)
        plt.ylabel("Speed (µm/min)", fontsize=16)
        plt.title(title, fontsize=18)
        plt.grid(True)
        plt.tight_layout()
        
        # ADD THIS LINE TO FORCE X-AXIS LIMITS:
        plt.xlim(8, 10)

        if save:
            output_path = self.output_dir / f"{filename}"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
        plt.close()

