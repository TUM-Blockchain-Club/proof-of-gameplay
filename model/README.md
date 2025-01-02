# Training Data

## Setup

To store the raw video files, we use [DVC](https://dvc.org/doc) for version control and a [Google Drive folder](https://drive.google.com/drive/folders/0APuRyssmqP4NUk9PVA) as storage bucket.

1. Follow the [DVC installation instructions](https://dvc.org/doc/install) to install DVC.
2. Request the `.dvc/config.local` file from [@LucasAschenbach](https://github.com/LucasAschenbach) to get API access to the Google Drive folder.
3. To download all raw video files to your system run `dvc pull`. (optional)

## Data Collection

1. Choose a text-blob from `data/text-blobs/` to type out
2. Go to `data/raw/` directory and run
   ```bash
   python key_logger.py
   ```
3. After completing, terminate the key logger with `Ctrl+C` and rename the `"key_log.csv"` file to `"{text-blob-name}_{your-name}_{number}_{optional-descriptor}.csv"`. Example: `"typing_mixed_1_lucas_1.csv"`
4. Save the video recording of the typing session in `data/raw/` directory with the same name as the csv file. Example: `"typing_mixed_1_lucas_1.mp4"`
5. To track the video in source control, run
   ```bash
   dvc add <file-name>.mp4
   dvc push
   ```
   This will upload the video file to the Google Drive folder and create a `.dvc` file to represent the video file in source control.
   ```bash
   git add <file-name>.mp4.dvc
   git commit -m "Add video file <file-name>.mp4"
   git push
   ```

> **Note:** It is crucial to keep the csv and video file names consistent for data processing in the next step.

## Data Preprocessing

1. Go to `data/` directory and run
   ```bash
   python process_data.py <file-name-1> <file-name-2> ... <file-name-n>
   ```
   Example:
   ```bash
   python process_data.py typing_mixed_1_lucas_1 typing_mixed_1_lucas_2 typing_mixed_1_lucas_3
   ```
2. For each file, a window will pop up asking you to select the frame where the first key press occurs. This is to match the key press events with the video frames.
3. Three new files will be created in the `data/processed/` directory: 
   - `<file-name>.npy`: Inputs
   - `<file-name>_labels.npy`: Labels
   - `<file-name>_config.yaml`: Syncronization info for inputs and labels

   <br>
   Example: `typing_mixed_1_lucas_1.npy`, `typing_mixed_1_lucas_1_labels.npy`, and `typing_mixed_1_lucas_1_config.yaml`. Furthermore, the `keys.names` file will be updated with any new keys found in the data.

<p align="center" style="max-width: 400px;">
    <img src="./docs/assets/video_preprocessing_preview.png" alt="Video Preprocessing Preview" width="300px">
    <p align="center">
        <i>Example of a Preprocessed Video Frame</i>
    </p>
</p>

# Training

TODO

# Evaluation

TODO

---

# Notes

- Key-press detection
- Features
    1. Detect Motion of object pressing down the key
    2. Detect change in shadow of key
- Invariants
    - Motion Duration ~100-200 milliseconds
    - Essentially Stateless
        - Keypress should be treated independent of previous key presses
        - Only memory: key-down event will be followed by key-up event, likely in the next 100 milliseconds.
