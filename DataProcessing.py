import os
import re
import pandas as pd
from collections import Counter
from itertools import combinations

# Process scripts like: **Phoebe shakes her hand and says: Phoe-Be.**
ACTION_WORDS = {
    "says", "shakes", "walks", "laughs", "enters", "exits",
    "shouts", "yells", "cries", "looks", "stares", "turns",
    "moves", "explains", "asks", "replies", "continues",
    "tells", "answers", "runs", "steps", "smiles", "nods",
    "starts", "storms", "coming", "starting", "raises",
    "have", "screaming", "to", "cutting", "at", "with",
    "opens", "looking", "has", "gets"
}

# Exclude group speakers like "all".
GROUP_SPEAKER_PHRASES = {
    "all", "everyone", "guys", "both",
    "the guys", "girls", "girl", "boys", "boy",
    "guy", "women", "woman", "men", "man"
}

# Exclude group indications like Monica's kid.
GROUP_INDICATORS = {
    "girls", "girl", "boys", "boy", "guys",
    "guy", "crowd", "people", "kids", "kid", "friend",
    "friends", "family", "parents", "neighbors",
    "roommates", "siblings", "child", "children",
    "women", "men", "directed", "extra", "everybody",
    "everyone", "together", "written", "produced", 
    "transcribed", "hosted"
}

# Exclude general roles like "customer".
GENERIC_ROLES = {
    "customer", "customers", "receptionist",
    "receptionists", "nurse", "waiter", "waiters",
    "waitress", "teacher", "clerk", "fireman",
    "detector", "tag", "boss", "tourist", "gambler",
    "dealer", "attendant", "croupier", "guard",
    "lurker", "director", "cashier", "message",
    "critic", "interviewer", "doctor", "tv", "story", 
    "writer", "teleplay", "note"
}

# Construct a dictionary for irregular abbreviation.
NAME_MAP = {
    "Chan": "Chandler",
    "CHAN": "Chandler",
    "Rach": "Rachel",
    "RACH": "Rachel",
    "Rahcel": "Rachel",
    "Mnca": "Monica",
    "MNCA": "Monica",
    "Phoe": "Phoebe",
    "PHOE": "Phoebe"
}

def split_multi_speaker(raw: str) -> list:
    """
    Split multi-speaker strings like "Joey And Chandler" into individual names.  

    Parameters
    ----------
    raw : str
        Raw speaker string that may contain combined names. 
    
    Returns
    -------
    list of str
        A list of individual character names extracted from the string. 
    """
    raw = raw.strip().lower()

    if raw in GROUP_SPEAKER_PHRASES:
        return []
    
    raw_norm = re.sub(r"\band\b|&", ",", raw, flags=re.IGNORECASE)
    parts = [p.strip().title() for p in raw_norm.split(",") if p.strip()]

    return parts

def parse_episode_file(file_path):
    """
    Parse a single Friends script file to extract scene-based character interactions.

    Parameters
    ----------
    file_path : str
        Path to the .txt file for a single episode (e.g. "S01E01 Monica Gets A Roommate.txt")

    Returns
    -------
    scenes : list[set[str]]
        List of sets, where each set contains all characters appearing in one scene.
        Example: [{'Monica', 'Ross', 'Chandler'}, {'Rachel', 'Phoebe', 'Monica'}, ...]

    interactions : dict[(str, str), int]
        Dictionary of pairwise co-occurrence counts across all scenes.
        Example: {('Monica','Ross'): 8, ('Monica','Chandler'): 5, ...}
    """

    scenes = []
    current_scene = set()
    
    MAIN_CHARS = ["Monica", "Rachel", "Phoebe", "Ross", "Chandler", 
                    "Joey", "Ursula", "Carol", "Susan", "Janice"
    ]

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    for line in text.splitlines():
        line = line.strip()
        
        if not line:
            continue
        
        # Skip script information. 
        if line.lower().startswith(("written by", "story by", "teleplay by")): # e.g. Written by: David Crane
            continue
        
        # Action Direction. e.g. (They all stare, bemused.)
        if line.startswith("("): 
            continue
        
        # Change scenes. 
        if re.match(r"^\[(Scene|Time|Cut|Commercial|Closing)", line):
            # Append the latest scene set into the scenes list.
            if current_scene:
                scenes.append(current_scene)
            # Initialize a new scene set.
            current_scene = set()
            continue

        # Normal match e.g. Monica: blah blah blah
        # Mrs. Geller: blah blah blah
        normal_match = re.match(r"^([A-Z][a-zA-Z\s.']+)(?=[:(])", line)
        if normal_match:
            prefix = normal_match.group(1).strip()
            lower_prefix = prefix.lower()
            
            if lower_prefix in GROUP_SPEAKER_PHRASES: # E.g. all, everyone.
                continue
            if lower_prefix in GENERIC_ROLES: # E.g. customer, teacher.
                continue
            
            # Exclude phrases like Phoebe's Friends
            words_no_ap = re.sub(r"'", "", lower_prefix).split()
            if any(w in GROUP_SPEAKER_PHRASES for w in words_no_ap):
                continue
            if any(w in GENERIC_ROLES for w in words_no_ap):
                continue            
            if any(w in GROUP_INDICATORS for w in words_no_ap):
                continue
            
            if any(w in ACTION_WORDS for w in words_no_ap):
                pass # Go to fallback. 
            else:            
                speakers = split_multi_speaker(prefix)
                for speaker in speakers:
                    normalized = NAME_MAP.get(speaker.upper(), speaker.title())
                    current_scene.add(normalized)
                continue
        
        # Fallback. Deal with cases like: 
        # Phoebe shakes her hand and says: Phoe-Be. 
        if ":" in line:
            prefix = line.split(":", 1)[0].strip()
            lower_prefix = prefix.lower()
            
            if lower_prefix in GROUP_SPEAKER_PHRASES:
                continue
            if lower_prefix in GENERIC_ROLES:
                continue
            
            words_no_ap = re.sub(r"'", "", lower_prefix).split()
            if any(w in GROUP_INDICATORS for w in words_no_ap):
                continue
            
            fallback = [name for name in MAIN_CHARS if name.lower() in lower_prefix]
            if len(fallback) == 1:
                current_scene.add(fallback[0])
                continue
            else:
                # No match. Just continue.
                continue
        
        # Nothing match, just continue. 
        continue

    if current_scene:
        scenes.append(current_scene)

    interaction_counter = Counter()
    for scene in scenes:
        for a, b in combinations(sorted(scene), 2):
            interaction_counter[(a, b)] += 1

    return scenes, dict(interaction_counter)

def parse_episode_file_with_wordcount(file_path):
    """
    Enhanced parser: 
    - Extract characters per scene
    - Extract interaction
    - Count how many words each character has said per episode

    Returns
    -------
    scenes : list[set[str]]
        List of sets, where each set contains all characters appearing in one scene.
        Example: [{'Monica', 'Ross', 'Chandler'}, {'Rachel', 'Phoebe', 'Monica'}, ...]

    interactions : dict[(str, str), int]
        Dictionary of pairwise co-occurrence counts across all scenes.
        Example: {('Monica','Ross'): 8, ('Monica','Chandler'): 5, ...}
    
    wordcount: dict[str, int]
        Dictionary of word count for each character in each episode
    """
    scenes = []
    current_scene = set()
    word_count = {}
    
    MAIN_CHARS = ["Monica", "Rachel", "Phoebe", "Ross", "Chandler", 
                    "Joey", "Ursula", "Carol", "Susan", "Janice"
    ]

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Skip script information. 
        if line.lower().startswith(("written by", "story by", "teleplay by")): # e.g. Written by: David Crane
            continue
        
        # Action Direction. e.g. (They all stare, bemused.)
        if line.startswith("("): 
            continue
        
        # Change scenes. 
        if re.match(r"^\[(Scene|Time|Cut|Commercial|Closing)", line):
            # Append the latest scene set into the scenes list.
            if current_scene:
                scenes.append(current_scene)
            # Initialize a new scene set.
            current_scene = set()
            continue

        # Normal match e.g. Monica: blah blah blah
        # Mrs. Geller: blah blah blah
        normal_match = re.match(r"^([A-Z][a-zA-Z\s.']+)(?:\s*\([^)]*\))?\s*:\s*(.*)$", line)

        if normal_match:
            prefix = normal_match.group(1).strip()
            content = normal_match.group(2).strip()
            lower_prefix = prefix.lower()
            
            if lower_prefix in GROUP_SPEAKER_PHRASES: # E.g. all, everyone.
                continue
            if lower_prefix in GENERIC_ROLES: # E.g. customer, teacher.
                continue
            
            # Exclude phrases like Phoebe's Friends
            words_no_ap = re.sub(r"'", "", lower_prefix).split()
            if any(w in GROUP_SPEAKER_PHRASES for w in words_no_ap):
                continue
            if any(w in GENERIC_ROLES for w in words_no_ap):
                continue            
            if any(w in GROUP_INDICATORS for w in words_no_ap):
                continue
            
            if any(w in ACTION_WORDS for w in words_no_ap):
                pass # Go to fallback. 
            else:            
                speakers = split_multi_speaker(prefix)
                for speaker in speakers:
                    normalized = NAME_MAP.get(speaker.upper(), speaker.title())
                    current_scene.add(normalized)
                    words = content.split()
                    word_count[normalized] = word_count.get(normalized, 0) + len(words)
                continue
        
        # Fallback. Deal with cases like: 
        # Phoebe shakes her hand and says: Phoe-Be. 
        if ":" in line:
            prefix = line.split(":", 1)[0].strip()
            lower_prefix = prefix.lower()
            
            if lower_prefix in GROUP_SPEAKER_PHRASES:
                continue
            if lower_prefix in GENERIC_ROLES:
                continue
            
            words_no_ap = re.sub(r"'", "", lower_prefix).split()
            if any(w in GROUP_INDICATORS for w in words_no_ap):
                continue
            
            fallback = [name for name in MAIN_CHARS if name.lower() in lower_prefix]
            if len(fallback) == 1:
                current_scene.add(fallback[0])
                word_count[fallback[0]] = word_count.get(fallback[0], 0) + len(content)
                continue
            else:
                # No match. Just continue.
                continue
        
        # Nothing match, just continue. 
        continue

    if current_scene:
        scenes.append(current_scene)

    interaction_counter = Counter()
    for scene in scenes:
        for a, b in combinations(sorted(scene), 2):
            interaction_counter[(a, b)] += 1

    return scenes, dict(interaction_counter), word_count

def parse_all_scripts(folder_path):
    """
    Batch-parse all Friends script files in a folder.

    Parameters
    ----------
    folder_path : str
        Path to folder containing all .txt episode files.

    Returns
    -------
    all_edges_df : pandas.DataFrame
        DataFrame with columns [episode_id, source, target, weight].
        Each row represents an interaction between two characters within an episode.

    episode_summary : dict[str, dict]
        Meta info per episode: number of scenes, unique characters, total interactions.
    """

    all_edges = []
    episode_summary = {}

    for file in sorted(os.listdir(folder_path)):
        if not file.endswith(".txt"):
            continue

        file_path = os.path.join(folder_path, file)

        match = re.search(r"S\d+E\d+(?:-S?\d*E?\d+)?", file, flags=re.IGNORECASE)
        if not match:
            print(f"Skipping {file} (no episode id found)")
            continue
        episode_id = match.group().upper()

        scenes, interactions = parse_episode_file(file_path)

        for (a, b), w in interactions.items():
            all_edges.append({
                "episode_id": episode_id,
                "source": a,
                "target": b,
                "weight": w
            })

        episode_summary[episode_id] = {
            "file": file,
            "num_scenes": len(scenes),
            "num_characters": len(set().union(*scenes)),
            "num_edges": len(interactions)
        }

    all_edges_df = pd.DataFrame(all_edges)
    print(f"Parsed {len(episode_summary)} episodes, total {len(all_edges_df)} edges.")
    return all_edges_df, episode_summary

