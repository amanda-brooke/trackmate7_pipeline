import pickle
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from data_loader import BaseDataLoader, CombinedDataLoader, discover_group_folders
from radial_analyzer import RadialAnalyzer

load_dotenv()

# Retrieve the variables as strings
base_path_str = os.getenv("BASE_PATH")
pickles_path_str = os.getenv("PICKLES_PATH")
base_output_str = os.getenv("BASE_OUTPUT")

# Convert them to Path objects
BASE_PATH = Path(base_path_str)
PICKLES_PATH = Path(pickles_path_str)
BASE_OUTPUT = Path(base_output_str)

# Now you can create directories if needed
PICKLES_PATH.mkdir(parents=True, exist_ok=True)
BASE_OUTPUT.mkdir(parents=True, exist_ok=True)

print("BASE_PATH:", BASE_PATH)
print("Directories in BASE_PATH:", list(BASE_PATH.iterdir()))

class TrackingPipeline:
    """
    Integrated pipeline to load pre-processed tracking data,
    perform radial analysis (if desired), and output final results.
    Automatically discovers offset folders.
    """
    def __init__(self, base_data_path: Path, output_path: Path):
        """
        Parameters:
            base_data_path (Path): Base path where the raw data (CSV files) are stored.
            output_path (Path): Path where final processed results will be saved.
        """
        self.base_data_path = base_data_path
        self.output_path = output_path
        self.results = {}

    def discover_offsets(self) -> list[Path]:
        """Automatically discover offset directories (e.g., offset_29, offset_30, etc.) under the base_data_path."""
        return sorted(self.base_data_path.glob("offset_*"))
    
    def run_single_replicate(self, offset_folder: Path, data_type: str, group: str = "Wildtype") -> pd.DataFrame:
        if group.lower() == "wildtype":
            folder = offset_folder / data_type
        else:
            # For treatment/control, assume the folder structure is:
            # offset_folder/group/data_type
            folder = offset_folder / group.lower() / data_type
        if not folder.exists():
            raise FileNotFoundError(f"Folder {folder} does not exist.")
        offset_str = offset_folder.name.split("_")[-1]
        time_offset = float(offset_str)
        loader = BaseDataLoader(folder=folder,
                                group_label=group.capitalize(),
                                data_type=data_type,
                                time_offset=time_offset)
        return loader.load_all()


    def run_wildtype(self) -> dict:
        offset_folders = self.discover_offsets()
        if not offset_folders:
            raise FileNotFoundError("No offset folders found.")
        
        all_data = {}
        for data_type in ['spots', 'edges', 'tracks']:
            df_list = []
            for offset_folder in offset_folders:
                try:
                    df = self.run_single_replicate(offset_folder, data_type)
                    df_list.append(df)
                except Exception as e:
                    print(f"Error processing {offset_folder} for {data_type}: {e}")
            if df_list:
                combined_df = pd.concat(df_list, ignore_index=True)
            else:
                combined_df = pd.DataFrame()
            all_data[data_type] = combined_df
            save_path = self.output_path / f"wildtype_{data_type}.pkl"
            with open(save_path, 'wb') as f:
                pickle.dump(combined_df, f)
            print(f"Saved {data_type} pickle to {save_path}")
        return all_data

    def run_treatment_control(self) -> dict:
        """
        Processes treatment/control data. For each offset folder, it discovers group subfolders
        (e.g., Treatment and Control), loads data for each group, combines them, and saves the results.
        Returns a dict with keys 'spots', 'edges', 'tracks'.
        """
        offset_folders = self.discover_offsets()
        if not offset_folders:
            raise FileNotFoundError("No offset folders found.")
        
        all_data = { 'spots': [], 'edges': [], 'tracks': [] }
        for offset_folder in offset_folders:
            groups = discover_group_folders(offset_folder)  # returns a dict for this offset folder
            for group, dt_dict in groups.items():
                for data_type in ['spots', 'edges', 'tracks']:
                    if data_type in dt_dict:
                        try:
                            offset_str = offset_folder.name.split("_")[-1]
                            time_offset = float(offset_str)
                            loader = BaseDataLoader(
                                folder=dt_dict[data_type],
                                group_label=group,
                                data_type=data_type,
                                time_offset=time_offset
                            )
                            df = loader.load_all()
                            all_data[data_type].append(df)
                        except Exception as e:
                            print(f"Error processing {dt_dict[data_type]} for {group} {data_type}: {e}")
        combined_data = {}
        for data_type in ['spots', 'edges', 'tracks']:
            if all_data[data_type]:
                combined_df = pd.concat(all_data[data_type], ignore_index=True)
            else:
                combined_df = pd.DataFrame()
            combined_data[data_type] = combined_df
            save_path = self.output_path / f"treatment_control_{data_type}.pkl"
            with open(save_path, 'wb') as f:
                pickle.dump(combined_df, f)
            print(f"Saved {data_type} pickle to {save_path}")
        return combined_data

    def run_radial_analysis_combined(self, combined_spots: pd.DataFrame, combined_edges: pd.DataFrame) -> pd.DataFrame:
        """
        Runs radial analysis on combined data that has already been loaded and combined,
        grouping by File_ID (and optionally by Group if needed). This method processes
        the entire combined dataset in one go.
        
        Assumes the combined_spots and combined_edges DataFrames contain a 'File_ID' column.
        
        Returns:
            A combined edge DataFrame with radial metrics computed per file.
        """
        # Create an instance of RadialAnalyzer using the combined data
        analyzer = RadialAnalyzer(spot_table=combined_spots, edge_table=combined_edges)
        
        # Process each file by grouping on File_ID.
        processed_edges = analyzer.process_all_files()
        
        # Calculate radial persistence and add it to the DataFrame
        analyzer.calculate_radial_persistence(processed_edges)
        
        # Save the processed radial analysis DataFrame to a pickle file
        save_path = self.output_path / "radial_edges.pkl"
        with open(save_path, 'wb') as f:
            pickle.dump(processed_edges, f)
        print(f"Final radial processed data saved to {save_path}")

        return processed_edges

    def run_radial_analysis(self, offset_folder: Path) -> pd.DataFrame:
        """
        Loads spots and edges data for a given offset folder, runs radial analysis,
        and returns the processed edge DataFrame.
        """
        spot_data = self.run_single_replicate(offset_folder, "spots")
        edge_data = self.run_single_replicate(offset_folder, "edges")
        analyzer = RadialAnalyzer(spot_table=spot_data, edge_table=edge_data)
        processed_edges = analyzer.process_all_files()  # Group by File_ID
        analyzer.calculate_radial_persistence(processed_edges)
        return processed_edges

    def run_radial_analysis_all(self) -> pd.DataFrame:
        """
        Runs radial analysis over all offset folders and combines the results.
        """
        offset_folders = self.discover_offsets()
        all_edges = []
        for offset_folder in offset_folders:
            print(f"Processing radial analysis for replicate from folder: {offset_folder}")
            try:
                processed_edges = self.run_radial_analysis(offset_folder)
                all_edges.append(processed_edges)
            except Exception as e:
                print(f"Error processing {offset_folder} for radial analysis: {e}")
        if all_edges:
            combined_edges = pd.concat(all_edges, ignore_index=True)
            self.results['edges'] = combined_edges
            save_path = self.output_path / "radial_edges.pkl"
            with open(save_path, 'wb') as f:
                pickle.dump(combined_edges, f)
            print(f"Final radial processed data saved to {save_path}")
            return combined_edges
        else:
            print("No edge data processed for radial analysis.")
            return pd.DataFrame()

    
if __name__ == "__main__":
    PICKLES_PATH.mkdir(parents=True, exist_ok=True)
    
    pipeline = TrackingPipeline(base_data_path=BASE_PATH, output_path=PICKLES_PATH)
    
    # For wildtype experiments:
    #wildtype_results = pipeline.run_wildtype()
    
    # For treatment/control experiments:
    #tc_results = pipeline.run_treatment_control()
    #radial_edges_tc = pipeline.run_radial_analysis_combined(tc_results['spots'], tc_results['edges'])

    # For wildtype experiments:
    wt_results = pipeline.run_wildtype()
    radial_edges_wt = pipeline.run_radial_analysis_combined(wt_results['spots'], wt_results['edges'])

    # For radial analysis:
    #radial_edges = pipeline.run_radial_analysis_all()