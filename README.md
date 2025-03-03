# TrackMate Analysis Pipeline

This project provides a comprehensive analysis pipeline for cell tracking data using TrackMate.

## Data Structure
/Your_Base_Data_Path
├── offset_24/          # Offset folder (the number indicates the time offset in hours)
│   ├── wildtype/       # (Optional) For wildtype experiments, data are stored directly here.
│   │   ├── spots/      # CSV files with spot data (e.g., c1_spots.csv)
│   │   ├── edges/      # CSV files with edge data (e.g., c1_edges.csv)
│   │   └── tracks/     # CSV files with track data (e.g., c1_tracks.csv)
│   ├── treatment/      # For treatment/control experiments, group subfolder.
│   │   ├── spots/
│   │   ├── edges/
│   │   └── tracks/
│   └── control/        # For treatment/control experiments, group subfolder.
│       ├── spots/
│       ├── edges/
│       └── tracks/
├── offset_27/
│   └── ...
└── offset_29/
    └── ...

## Classes
- **BaseDataLoader**
    - Purpose: Loads and preprocesses a single type of CSV data (spots, edges, or tracks) from a specified folder.
    - Features:
    Reads CSV files, converts columns to numeric types, fills missing values.
    Performs necessary unit conversions (e.g., converting seconds to hours).
    Generates a unique File_ID for each file by combining the file’s base name with its parent folder (replicate) name.
    Adds a Group column (e.g., "Wildtype", "Treatment", or "Control") based on the provided group label.

- **CombinedDataLoader**
    - Purpose: Aggregates data from multiple BaseDataLoader instances (e.g., multiple replicates) and concatenates them into one DataFrame.
    - Features:
    Collects and combines DataFrames for a given data type.
    Saves the combined DataFrame as a pickle file.

- **TrackingPipeline**
    - Purpose: Orchestrates the overall workflow by:
    Discovering offset folders automatically.
    Loading data for each replicate using BaseDataLoader.
    Supporting both wildtype and treatment/control workflows.
    Optionally performing radial analysis.
    - Usage:
    For wildtype experiments, call run_wildtype() to load data directly from offset folders.
    For treatment/control experiments, call run_treatment_control() to load data from group subdirectories.
    Optionally, call run_radial_analysis_all() to perform advanced radial analysis.

- **RadialAnalyzer (Optional)**
    - Purpose: Performs radial calculations (e.g., computing a dynamic center and radial persistence) on preprocessed spot and edge data on a per‑file basis.
    - Features:
    Groups data by File_ID to compute the centroid for each imaging file.
    Calculates movement vectors and radial metrics for each edge.
    Computes radial persistence as the ratio of the radial velocity to overall movement.