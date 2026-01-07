import os
import re
import json
import pandas as pd
from DataProcessing import parse_episode_file, parse_episode_file_with_wordcount

def save_parsed_data_as_json(scripts_folder, output_folder):
    """
    Batch-parse all Friends script files in scripts_folder,
    and save the structured data as JSON into output_folder.

    Output JSON files:
        - episode_scenes.json
        - episode_interactions.json
        - episode_characters.json
        - episode_meta.json
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    episode_scenes = {}          # episode_id -> list of scenes (each scene is a list)
    episode_interactions = {}    # episode_id -> { "A-B": weight }
    episode_characters = {}      # episode_id -> list of unique characters
    episode_meta = {}            # episode_id -> metadata (scenes, chars, etc.)
    episode_wordcount = {}

    # Collect all .txt scripts
    script_files = sorted(f for f in os.listdir(scripts_folder) if f.endswith(".txt"))

    for file in script_files:
        file_path = os.path.join(scripts_folder, file)

        # Extract episode_id from filename (e.g., S02E12-S02E13)
        match = re.search(r"S\d+E\d+(?:-S?\d*E?\d+)?", file, flags=re.IGNORECASE)
        if not match:
            print(f"Skipping file (no episode id found): {file}")
            continue

        episode_id = match.group().upper()

        # Parse the episode
        # scenes, interactions = parse_episode_file(file_path)
        scenes, interactions, word_count = parse_episode_file_with_wordcount(file_path)

        # Prepare structures
        episode_scenes[episode_id] = [sorted(list(scene)) for scene in scenes]

        # Convert (A,B) tuples → "A-B" JSON-friendly keys
        inter_json = {}
        for (a, b), w in interactions.items():
            key = f"{a}-{b}"
            inter_json[key] = w
        episode_interactions[episode_id] = inter_json

        # characters list (union of all scenes)
        char_set = set()
        for scene in scenes:
            char_set |= scene
        episode_characters[episode_id] = sorted(list(char_set))

        # WordCount for each character per episode. 
        episode_wordcount[episode_id] = word_count

        # meta info
        episode_meta[episode_id] = {
            "file": file,
            "num_scenes": len(scenes),
            "num_characters": len(char_set),
            "num_edges": len(interactions)
        }

        print(f"Parsed {episode_id}  | scenes: {len(scenes)}, chars: {len(char_set)}, edges: {len(interactions)}")
        
        def save_json(data, name):
            path = os.path.join(output_folder, name)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Saved {name} ({len(data)} items)")
        
        save_json(episode_scenes, "episode_scenes.json")
        save_json(episode_interactions, "episode_interactions.json")
        save_json(episode_characters, "episode_characters.json")
        save_json(episode_meta, "episode_meta.json")
        save_json(episode_wordcount, "episode_wordcount.json")

        print("\nAll JSON cache files generated successfully!")


def build_and_save_episode_popularity(csv_path, output_json_path):
    """
    Read the Friends episode score CSV, build an episode_popularity dict,
    and save it to a JSON file.

    Parameters
    ----------
    csv_path : str
        Path to friends_episodes_scores.csv.
    output_json_path : str
        JSON file path to save the episode_id → Stars mapping.

    Returns
    -------
    dict
        The generated episode_popularity dictionary.
    """

    # Load CSV
    episode_score = pd.read_csv(csv_path, encoding='iso-8859-1')

    # Build an episode_id column like "S01E03"
    episode_score["episode_id"] = (
        "S" + episode_score["Season"].astype(int).astype(str).str.zfill(2)
        + "E" + episode_score["Episode Number"].astype(int).astype(str).str.zfill(2)
    )

    episode_popularity = {
        row["episode_id"]: row["Stars"]
        for _, row in episode_score.iterrows()
    }

    # Save JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(episode_popularity, f, ensure_ascii=False, indent=4)

    print(f"Saved episode popularity JSON to {output_json_path}")


def load_json(path):
    """Load a JSON file and return its Python object. """
    with open(path, "r", encoding = "utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    scripts_folder = "./Scripts"
    output_folder = "./Friends_json"
    save_parsed_data_as_json(scripts_folder, output_folder)
    csv_path = "./data/friends_episodes_scores.csv"
    output_json_path = os.path.join(output_folder, "episode_popularity.json")
    build_and_save_episode_popularity(csv_path, output_json_path)