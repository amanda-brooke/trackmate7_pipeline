import numpy as np
import pandas as pd

class RadialAnalyzer:
    """
    Performs radial calculations on pre-processed spot and edge data.
    Processes the data on a per-file basis (grouped by File_ID), so that each 
    imaging file (each circular colony) gets its own dynamic center.
    
    Assumes that the data loader has already:
      - Converted time units (e.g., seconds → hours) and applied the appropriate time offset.
      - Added a 'File_ID' column identifying the source CSV.
    """
    def __init__(self, spot_table: pd.DataFrame, edge_table: pd.DataFrame):
        """
        Parameters:
            spot_table (pd.DataFrame): Pre-processed DataFrame of spot data.
            edge_table (pd.DataFrame): Pre-processed DataFrame of edge data.
        """
        self.spot_table = spot_table
        self.edge_table = edge_table.copy()  # work on a copy so the original data remains intact

    def process_file(self, file_id: str) -> pd.DataFrame:
        """
        Processes the data for a single File_ID.
        Computes the dynamic center based on the spots for that file,
        and then calculates the radial metrics for the corresponding edges.
        
        Parameters:
            file_id (str): The identifier for the file.
            
        Returns:
            A processed edge DataFrame for that file with added columns for:
              - Movement vectors (u, v)
              - Source and target positions
              - Radial distance, radial velocity, and radial velocity angle
              - The dynamic center (center_x, center_y)
        """
        # Filter spots and edges for the given file_id
        spots = self.spot_table[self.spot_table['File_ID'] == file_id]
        edges = self.edge_table[self.edge_table['File_ID'] == file_id].copy()
        
        if spots.empty or edges.empty:
            print(f"Warning: No data for File_ID {file_id}")
            return edges  # returns an empty DataFrame if no data

        # Compute dynamic center (centroid) for this file
        center_x = spots['POSITION_X'].mean()
        center_y = spots['POSITION_Y'].mean()
        print(f"File {file_id}: Dynamic Center: ({center_x:.2f}, {center_y:.2f})")
        
        # Initialize lists to store computed values for each edge row
        u_values, v_values = [], []
        source_x_values, source_y_values = [], []
        target_x_values, target_y_values = [], []
        radial_distances, radial_velocities = [], []
        radial_velocity_thetas = []
        centers_x, centers_y = [], []

        # Process each edge row for this file
        for _, row in edges.iterrows():
            source_id = row['SPOT_SOURCE_ID']
            target_id = row['SPOT_TARGET_ID']

            # Get the corresponding source and target spot rows
            source_spot = spots[spots['ID'] == source_id]
            target_spot = spots[spots['ID'] == target_id]
            if source_spot.empty or target_spot.empty:
                continue  # Skip if either spot is missing

            source_x = source_spot['POSITION_X'].values[0]
            source_y = source_spot['POSITION_Y'].values[0]
            target_x = target_spot['POSITION_X'].values[0]
            target_y = target_spot['POSITION_Y'].values[0]

            # Movement vector components
            u = target_x - source_x
            v = target_y - source_y

            # Compute radial distance from source to dynamic center
            r_source = np.sqrt((source_x - center_x) ** 2 + (source_y - center_y) ** 2)
            if r_source != 0:
                radial_direction_x = (center_x - source_x) / r_source
                radial_direction_y = (center_y - source_y) / r_source
                radial_direction = np.arctan2(radial_direction_y, radial_direction_x)
                radial_velocity = - (u * radial_direction_x + v * radial_direction_y)
            else:
                radial_direction = 0
                radial_velocity = 0

            # Store computed values
            u_values.append(u)
            v_values.append(v)
            source_x_values.append(source_x)
            source_y_values.append(source_y)
            target_x_values.append(target_x)
            target_y_values.append(target_y)
            radial_distances.append(r_source)
            radial_velocities.append(radial_velocity)
            radial_velocity_thetas.append(radial_direction)
            centers_x.append(center_x)
            centers_y.append(center_y)

        # Add computed columns to the edges DataFrame for this file
        edges.loc[:, 'u'] = u_values
        edges.loc[:, 'v'] = v_values
        edges.loc[:, 'source_x'] = source_x_values
        edges.loc[:, 'source_y'] = source_y_values
        edges.loc[:, 'target_x'] = target_x_values
        edges.loc[:, 'target_y'] = target_y_values
        edges.loc[:, 'radial_distance'] = radial_distances
        edges.loc[:, 'radial_velocity'] = radial_velocities
        edges.loc[:, 'radial_velocity_theta'] = radial_velocity_thetas
        edges.loc[:, 'center_x'] = centers_x
        edges.loc[:, 'center_y'] = centers_y

        return edges

    def process_all_files(self) -> pd.DataFrame:
        """
        Processes all files by grouping the data by 'File_ID', running the radial analysis
        for each file, and concatenating the results.
        
        Returns:
            A combined edge DataFrame with radial analysis columns for all files.
        """
        file_ids = self.spot_table['File_ID'].unique()
        processed_edges_list = []
        for fid in file_ids:
            processed_edges = self.process_file(fid)
            if not processed_edges.empty:
                processed_edges_list.append(processed_edges)
        if processed_edges_list:
            return pd.concat(processed_edges_list, ignore_index=True)
        else:
            return pd.DataFrame()

    def calculate_radial_persistence(self, edge_data: pd.DataFrame) -> pd.Series:
        """
        Calculates radial persistence as the ratio of radial velocity to the overall movement vector magnitude
        for a given edge DataFrame.
        
        Parameters:
            edge_data (pd.DataFrame): Processed edge data.
            
        Returns:
            A pandas Series of radial persistence values.
        """
        velocity_magnitude = np.sqrt(edge_data['u']**2 + edge_data['v']**2)
        radial_persistence = np.where(
            velocity_magnitude != 0,
            edge_data['radial_velocity'] / velocity_magnitude,
            0
        )
        edge_data['radial_persistence'] = radial_persistence
        return edge_data['radial_persistence']