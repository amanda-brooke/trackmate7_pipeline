# plotting/themes.py
import seaborn as sns
import matplotlib.pyplot as plt

class PlotTheme:
    def __init__(self, style: str = "light"):
        """
        Initialize the PlotTheme with a style.

        Parameters:
            style (str): The desired theme style. Options: "light" or "dark". 
                         Defaults to "light".
        """
        self.style = style.lower()
        self.light_style = {
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': 'black',
            'axes.labelcolor': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black',
            'text.color': 'black',
            'grid.color': 'gray',
            'legend.facecolor': 'white',
            'legend.edgecolor': 'black',
            'savefig.facecolor': 'white',
            'savefig.edgecolor': 'white'
        }
        self.dark_style = {
            'figure.facecolor': 'black',
            'axes.facecolor': 'black',
            'axes.edgecolor': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'text.color': 'white',
            'grid.color': 'gray',
            'legend.facecolor': 'black',
            'legend.edgecolor': 'white',
            'savefig.facecolor': 'black',
            'savefig.edgecolor': 'black'
        }

    def apply(self):
        """
        Applies the specified theme to matplotlib and seaborn.
        """
        if self.style == "light":
            sns.set_theme(context='paper', font='sans-serif', font_scale=1.2, color_codes=True)
            plt.rcParams.update(self.light_style)
        elif self.style == "dark":
            sns.set_theme(context='paper', font='sans-serif', font_scale=1.2, color_codes=True)
            plt.rcParams.update(self.dark_style)
        else:
            print(f"Unknown style '{self.style}'. Using default light theme.")
            sns.set_theme(context='paper', font='sans-serif', font_scale=1.2, color_codes=True)
            plt.rcParams.update(self.light_style)

    def get_heatmap_style(self) -> dict:
        """
        Returns default parameters for heatmap plots.
        
        You can customize this dictionary as needed.
        """
        heatmap_params = {
            "cmap": "magma",        # Default colormap; can be changed as needed.
            "linewidths": 0.5,
            "linecolor": "white",
            "annot": False,         # If you want annotations on the heatmap.
            "fmt": ".2f",           # Format for annotations.
        }
        return heatmap_params

    def get_custom_palette(self, n_colors: int = 9) -> list:
        """
        Returns a custom color palette from seaborn's "rocket" palette.
        For example, you might want to use specific colors for control and treatment.
        """
        palette = sns.color_palette("rocket", n_colors=n_colors)
        # Customize by picking specific colors. For instance:
        return [palette[3], palette[7]]