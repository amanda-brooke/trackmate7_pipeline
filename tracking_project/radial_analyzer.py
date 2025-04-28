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
        # --- slice tables ----------------------------------------------------
        spots = self.spot_table[self.spot_table['File_ID'] == file_id]
        edges = self.edge_table[self.edge_table['File_ID'] == file_id].copy()
        if spots.empty or edges.empty:
            print(f"Warning: No data for File_ID {file_id}")
            return edges

        # drop TrackMate’s zero-length “edge 0→0”
        edges = edges[~((edges['SPOT_SOURCE_ID'] == edges['SPOT_TARGET_ID']) &
                        (edges['SPOT_SOURCE_ID'] == 0))].copy()

        # --- dynamic centre --------------------------------------------------
        center_x = spots['POSITION_X'].mean()
        center_y = spots['POSITION_Y'].mean()
        print(f"File {file_id}: Dynamic Center: ({center_x:.2f}, {center_y:.2f})")

        # --- collectors ------------------------------------------------------
        u_vals, v_vals = [], []
        sx_vals, sy_vals, tx_vals, ty_vals = [], [], [], []
        r_vals, rv_vals, theta_vals = [], [], []
        cx_vals, cy_vals = [], []

        frame_interval_s = 600  # only used if FRAME fallback is needed

        # ---------------------------------------------------------------------
        for _, row in edges.iterrows():
            src = spots[spots['ID'] == row['SPOT_SOURCE_ID']]
            tgt = spots[spots['ID'] == row['SPOT_TARGET_ID']]
            if src.empty or tgt.empty:
                continue

            sx, sy = src[['POSITION_X', 'POSITION_Y']].values[0]
            tx, ty = tgt[['POSITION_X', 'POSITION_Y']].values[0]
            u, v   = tx - sx, ty - sy                        # µm

            # time step (minutes) ---------------------------------------------
            if 'POSITION_T' in spots.columns:                # POSITION_T is in **seconds**
                ts_min = float(src['POSITION_T'].iloc[0]) / 60   # sec → min
                tt_min = float(tgt['POSITION_T'].iloc[0]) / 60
                dt = tt_min - ts_min
            else:                                            # FRAME fallback
                dt = ((int(tgt['FRAME'].iloc[0]) -
                    int(src['FRAME'].iloc[0])) * frame_interval_s) / 60
            if dt == 0:
                continue

            # radial unit vector ----------------------------------------------
            dx, dy   = center_x - sx, center_y - sy
            r_source = np.hypot(dx, dy)
            if r_source == 0:
                continue
            ux, uy = dx / r_source, dy / r_source            # inward

            # signed radial velocity (µm min⁻¹) -------------------------------
            rv = -(u * ux + v * uy) / dt                     # + inward

            # save -------------------------------------------------------------
            u_vals.append(u);            v_vals.append(v)
            sx_vals.append(sx);          sy_vals.append(sy)
            tx_vals.append(tx);          ty_vals.append(ty)
            r_vals.append(r_source)
            rv_vals.append(rv)
            theta_vals.append(np.arctan2(uy, ux))
            cx_vals.append(center_x);    cy_vals.append(center_y)

        # --- write lists back to the same DataFrame --------------------------
        edges['u']  = u_vals;  edges['v']  = v_vals
        edges['source_x'] = sx_vals;  edges['source_y'] = sy_vals
        edges['target_x'] = tx_vals;  edges['target_y'] = ty_vals
        edges['radial_distance'] = r_vals
        edges['radial_velocity'] = rv_vals
        edges['radial_velocity_theta'] = theta_vals
        edges['center_x'] = cx_vals;     edges['center_y'] = cy_vals

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