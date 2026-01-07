import os
import re
from GraphConstruct import Graph, build_graph_by_seasons
from JSONProcessing import load_json

class FriendsCLI:
    """
    A command-line interface for interacting with the Friends Network.
    Allows searching for characters, finding shortest paths, and viewing centrality.
    It can also filter the graph by certain seasons.

    Attributes:
        json_folder (str): Path to the folder containing JSON data files.
        full_graph (Graph): The complete graph of all characters and interactions.
        graph (Graph): The current graph, which may be filtered by seasons.
        current_seasons (str or list): Description of the current seasons represented in the graph.
    
    Methods:
        _load_full_graph(): 
            Loads the full graph from JSON files.
        
        filter_season(seasons):
            Filters the graph to only include data from specified seasons.

        search_character(name):
            Searches for a character and displays their information, interactions, centrality, and popularity.

        shortest_path(start, end):
            Finds and displays the shortest path between two characters.

        top_degree(k):
            Displays the top-k characters by degree centrality.

        top_weighted_degree(k):
            Displays the top-k characters by weighted degree centrality.
        
        top_popularity(k):
            Displays the top-k characters by average episode-level popularity if the character appears in at least 5 episodes.
        
        top_effective_popularity(k):
            Displays the top-k characters by effective average episode-level popularity if the character appears in at least 5 episodes.

        print_interactions_commands():
            Prints the available interaction commands as a manual page.
        
        match_commands(command):
            Parses and executes a given command string.

        reset_graph():
            Resets the current graph to the full graph. In other words, removes any season filters.

        run():
            Starts the command-line interface loop for user interaction.
    """
    def __init__(self, json_folder="./Friends_json"):
        self.json_folder = json_folder
        self.full_graph = None
        self.graph = None
        self.current_seasons = "All 10 seasons"
        self._load_full_graph()
    
    def _load_full_graph(self):
        """Load the full graph from JSON files."""
        print("Loading JSON data...")
        episode_interactions = load_json(os.path.join(self.json_folder, "episode_interactions.json"))
        episode_characters = load_json(os.path.join(self.json_folder, "episode_characters.json"))
        episode_wordcount = load_json(os.path.join(self.json_folder, "episode_wordcount.json"))
        episode_popularity = load_json(os.path.join(self.json_folder, "episode_popularity.json"))

        # Build a new graph. 
        print("Building graph...")
        g = Graph()
        g.build_graph_from_interactions(episode_interactions)
        g.add_popularity_by_presence(episode_characters, episode_popularity)
        g.add_popularity_by_wordcount(episode_wordcount, episode_popularity)

        self.full_graph = g
        self.graph = g
        print(f"FUll graph built successfully! Characters: {len(self.full_graph.nodes)}\n")

    def filter_season(self, seasons):
        """
        Filter the graph to only include data from specified seasons.

        Parameters
        ----------
        seasons: int
        """
        if isinstance(seasons, int):
            seasons = [seasons]

        print(f"Building graph for seasons {seasons}...")

        # Load JSON again
        episode_interactions = load_json(f"{self.json_folder}/episode_interactions.json")
        episode_characters = load_json(f"{self.json_folder}/episode_characters.json")
        episode_popularity = load_json(f"{self.json_folder}/episode_popularity.json")
        try:
            episode_wordcount = load_json(f"{self.json_folder}/episode_wordcount.json")
        except:
            episode_wordcount = {}
        
        def filter_by_season(d):
            new_d = {}
            for epi, value in d.items():
                match = re.search(r"S(\d+)E", epi)
                if not match:
                    continue
                season_num = int(match.group(1))
                if season_num in seasons:
                    new_d[epi] = value
            return new_d

        episode_interactions = filter_by_season(episode_interactions)
        episode_characters = filter_by_season(episode_characters)
        episode_popularity = filter_by_season(episode_popularity)
        episode_wordcount = filter_by_season(episode_wordcount)

        # Use your build_graph_by_seasons
        g = build_graph_by_seasons(episode_interactions, seasons)

        # Add popularity fields
        g.add_popularity_by_presence(episode_characters, episode_popularity)
        if episode_wordcount:
            g.add_popularity_by_wordcount(episode_wordcount, episode_popularity)

        self.graph = g
        self.current_seasons = seasons
        print(f"Season graph built! Characters: {len(self.graph.nodes)}\n")
    
    def search_character(self, name: str):
        """
        Search for a certain character to find his or her information 
            about popularity and connections as well as top interaction partners. 
        
        Parameters
        ----------
        name: str
            The name of the character to search for.
        """
        result = self.graph.search_character(name.title())
        print("Seasons contained: ", self.current_seasons)
        for key, value in result.items():
            print(key, ":", value)


    def shortest_path(self, start: str, end: str):
        """
        Find the shortest path between two characters. 
        """
        path = self.graph.shortest_path(start.title(), end.title())
        if path:
            print(" ->".join(path))
        else:
            print("Sorry! No path found!")
    
    def top_degree(self, k: int=5):
        """Display the top-k characters by degree centrality."""
        results = self.graph.top_k_by_degree(k)
        print(f"The {k} characters with most interaction partners are:\n")
        for n in results:
            print(n, "\n")
    
    def top_weighted_degree(self, k: int=5):
        """Display the top-k characters by weighted degree centrality."""
        results = self.graph.top_k_by_weighted_degree(k)
        print(f"The {k} characters with highest counts of interactions are:\n")
        for n in results:
            print(n, "\n")
    
    def top_popularity(self, k: int=5):
        """Display the top-k characters by average episode-level popularity 
            if the character appears in at least 5 episodes."""
        results = self.graph.top_k_by_popularity(k)
        print(f"The {k} characters with highest average episode-level scores are:\n")
        for n in results:
            print(n, "\n")
    
    def top_effective_popularity(self, k: int=5):
        """Display the top-k characters by effective average episode-level popularity
            if the character appears in at least 5 episodes."""
        results = self.graph.top_k_by_effective_popularity(k)
        print(f"The {k} characters with highest effective average episode-level scores are:\n")
        for n in results:
            print(n, "\n")
    
    def print_interactions_commands(self):
        """Print the available interaction commands as a manual page."""
        print("""
Here are the available interactions commands:

    1. Search <name>             - Search character info.
    2. Path <start> <end>        - Find the shortest path. 
    3. Top_degree <k>            - Top-k degree.
    4. Top_weighted_degree <k>   - Top-k weighted degree.
    5. Popularity <k>            - Top-k popular characters if one appears in at least 5 episodes. 
    6. Effective_popularity <k>  - Top-k popular characters if one is a main in a episode and appears in at least 5.
    7. Season <n>                - Filter graph to only season n. 
    8. Manual                    - Show the interactions commands manual. 
    9. Exit / Q                  - Exit the program. 

Please enter the interaction command! 
E.g. Search Monica / 1 Monica
        """)
    
    def match_commands(self, command):
        """Parse and execute a given command string."""
        command = command.split()
        interaction = command[0]

        if (interaction == "search" or interaction == "1") and len(command) >= 2:
            self.search_character(command[1])
        elif (interaction == "path" or interaction == "2") and len(command) >= 3:
            self.shortest_path(command[1], command[2])
        elif interaction == "top_degree" or interaction == "3":
            k = int(command[1]) if len(command) >= 2 else 5
            self.top_degree(k)
        elif interaction == "top_weighted_degree" or interaction == "4":
            k = int(command[1]) if len(command) >= 2 else 5
            self.top_weighted_degree(k)
        elif interaction == "popularity" or interaction == "5":
            k = int(command[1]) if len(command) >= 2 else 5
            self.top_popularity(k)
        elif interaction == "effective_popularity" or interaction == "6":
            k = int(command[1]) if len(command) >= 2 else 5
            self.top_effective_popularity(k)
        elif interaction == "season" or interaction == "7":
            if len(command) == 2:
                if command[1] == "all":
                    self.reset_graph()
                else:
                    try:
                        season_num = int(command[1])
                        self.filter_season(season_num)
                    except ValueError:
                        print("Invalid season number.")
            else:
                print("Usage: season <n> or season all")
        else:
            print("Command not found. Type 'interactions' to see the manual page or try again!")

    def reset_graph(self):
        """Reset the current graph to the full graph. In other words, removes any season filters."""
        self.graph = self.full_graph
        self.current_seasons = "All 10 seasons"
        print("Graph reset to full graph.\n")

    def run(self):
        """Start the command-line interface loop for user interaction."""
        print("Welcome to the Friends Network!\n")
        print("Type 'Manual' for available interactions commands!\n")
        print("Type 'Exit' or 'Q' for exiting the program.\n")

        while True:
            command = input(">>").strip().lower()
            if command == "exit" or command == 'q' or command == "9":
                print("Bye!")
                break
            elif command == "manual" or command == "8":
                self.print_interactions_commands()
            else:
                self.match_commands(command)


if __name__ == "__main__":
    cli = FriendsCLI()
    cli.run()
