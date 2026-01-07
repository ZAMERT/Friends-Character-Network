from collections import deque
import re

class Node:
    """
    A class to store each character as a simple graph node. 
    
    Attributes
    ----------
    name : str
    neighbors : dict {neighbor_name: weight}
    degree : int
    weighted_degree : int
    pop_scores : list
    effective_pop_scores: list
    
    Methods
    -------
    add_neighbor(name)
        Add or update a weighted edge. 
    
    add_popularity_score(score)
        Add one episode-level popularity score for this character. 
    
    avg_popularity()
        Calculate and return the average popularity score across all episodes this character appears in. 
    
    add_effective_popularity_score(score)
        Add one episode-level popularity score for this character if this character is a main one. 
    
    avg_effective_popularity()
        Calculate and return the average popularity score across all episodes this character appears effectively in. 
    """
    def __init__(self, name: str):
        self.name = name
        self.neighbors = {}
        self.degree = 0
        self.weighted_degree = 0
        self.pop_scores = []
        self.effective_pop_scores = []
        
    def add_neighbor(self, neighbor: str, weight: int = 1):
        """
        Add or update a weighted edge.
        
        Parameters
        ----------
        neighbor : str
            Another character's name. 
        
        weight : int
            The number of interactions between the node and the neighbor. 
        """
        if neighbor in self.neighbors:
            self.neighbors[neighbor] += weight
            self.weighted_degree += weight
        else:
            self.neighbors[neighbor] = weight
            self.degree += 1
            self.weighted_degree += weight
    
    def add_popularity_score(self, score):
        """Add one episode-level popularity score for this character."""
        if score is not None:
            self.pop_scores.append(score)
    
    def avg_popularity(self):
        """Calculate and return the average popularity score across all episodes this character appears in."""
        if not self.pop_scores:
            return None
        return sum(self.pop_scores) / len(self.pop_scores)

    def add_effective_popularity_score(self, score):
        """Add one episode-level popularity score for this character if the character is one of the main cast in that episode."""
        if score is not None:
            self.effective_pop_scores.append(score)
    
    def avg_effective_popularity(self):
        """Calculate and return the average effective popularity score across all episodes this character appears in."""
        if not self.effective_pop_scores:
            return None
        return sum(self.effective_pop_scores) / len(self.effective_pop_scores)
    
    def __repr__(self):
        avg_pop = self.avg_popularity()
        avg_eff_pop = self.avg_effective_popularity()
        if avg_pop is None and avg_eff_pop is None: 
            return f"{self.name}, degree = {self.degree}, weighted_degree = {self.weighted_degree}"
        elif avg_eff_pop is None: 
            return f"{self.name}, degree = {self.degree}, weighted_degree = {self.weighted_degree}, avg_pop = {avg_pop:.2f}, num_episode_appeared = {len(self.pop_scores)}"
        else:
            return f"{self.name}, degree = {self.degree}, weighted_degree = {self.weighted_degree}, avg_pop = {avg_pop:.2f}, num_episode_appeared = {len(self.pop_scores)}, avg_eff_pop = {avg_eff_pop:.2f}"

class Graph:
    """
    A class of graph to store all the nodes. 
    
    Attributes
    ----------
    nodes : dict {name: Node}
    
    Methods
    -------
    add_node(name)
        Add a node to the graph.
    
    add_edge(a, b, weight)
        Add or update an edge between two nodes.
    
    get_neighbors(character)
        Return sorted list of (neighbor, weight).
    
    build_graph_from_interactions(episode_interactions)
        Build the graph from episode interactions data.
    
    add_popularity_by_presence(episode_characters, episode_popularity)
        Add popularity scores based on episode presence.
    
    add_popularity_by_wordcount(episode_wordcount, episode_popularity, top_k)
        Add popularity scores based on episode word count. 
        Only if the character is in the top-k number of word count, 
        the character is considered as a main cast in that episode, 
        and the episode popularity score is added to his or her effective popularity scores.

    top_k_by_degree(k)
        Return top-k nodes sorted by degree.
    
    top_k_by_weighted_degree(k)
        Return top-k nodes sorted by sum of weights.

    top_k_by_popularity(k, min_episodes)
        Return top-k nodes sorted by average popularity. The nodes must appear in at least min_episodes number of episodes.

    top_k_by_effective_popularity(k, min_episodes)
        Return top-k nodes sorted by average effective popularity. The nodes must appear in at least min_episodes number of episodes.
        
    search_character(character, top_k)
        Output the node information when searching for one character.
    
    shortest_path(start, end)
        Return shortest path between two characters using BFS.
    """
    def __init__(self):
        self.nodes = {}
    
    def add_node(self,name):
        if name not in self.nodes:
            self.nodes[name] = Node(name)
    
    def add_edge(self, a, b, weight = 1):
        self.add_node(a)
        self.add_node(b)
        self.nodes[a].add_neighbor(b, weight)
        self.nodes[b].add_neighbor(a, weight)
    
    def get_neighbors(self, character: str):
        """Return sorted list of (neighbor, weight)."""
        if character not in self.nodes:
            return []
        
        neighbors = []
        for (neighbor, weight) in self.nodes[character].neighbors.items():
            neighbors.append((neighbor, weight))
        
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors
    
    def build_graph_from_interactions(self, episode_interactions):
        """
        Build the graph from episode interactions data.

        Parameters
        ----------
        episode_interactions : dict
            episode_id: {"A-B": weight, ...}
        """
        for epi, interactions in episode_interactions.items():
            for pair, weight in interactions.items():
                a, b = pair.split("-")
                self.add_edge(a, b, weight)
    
    def add_popularity_by_presence(self, episode_characters, episode_popularity):
        """
        For each episode: 
            - Get its popularity score. 
            - Add this score into each character's pop_scores list
                if appearing in that episode. 
        """
        for epi_id, chars in episode_characters.items():
            score = episode_popularity.get(epi_id, None)
            if score is None: 
                continue
            
            for char in chars:
                self.add_node(char)
                self.nodes[char].add_popularity_score(score)
    
    def add_popularity_by_wordcount(self, episode_wordcount, episode_popularity, top_k = 5):
        """
        Add popularity score only to characters who are main cast in that episode, 
        based on the top-k word count in each episode.

        Parameters
        ----------
        episode_wordcount : dict[episode_id -> {char: wordcount}]
        episode_popularity: dict[episode_id -> popularity_score]
        top_k: int
        """
        for episode_id, wc_dict in episode_wordcount.items():
            score = episode_popularity.get(episode_id)
            if score is None:
                continue
            sorted_chars = sorted(wc_dict.items(), key=lambda x: x[1], reverse=True)
            top_chars = [char for char, wordcount in sorted_chars[:top_k]]

            for char in top_chars:
                self.add_node(char)
                self.nodes[char].add_effective_popularity_score(score)
    
    def top_k_by_degree(self, k=3):
        """Return top-k nodes sorted by degree."""
        return sorted(self.nodes.values(), key=lambda n: n.degree, reverse=True)[:k]

    def top_k_by_weighted_degree(self, k=3):
        """Return top-k nodes sorted by sum of weights."""
        return sorted(self.nodes.values(), key=lambda n: n.weighted_degree, reverse=True)[:k]
    
    def top_k_by_popularity(self, k=5, min_episodes = 5):
        """Return top-k nodes sorted by average popularity."""
        candidates = [
            n for n in self.nodes.values()
            if len(n.pop_scores) >= min_episodes and n.avg_popularity() is not None
        ]
        return sorted(candidates, key=lambda n: n.avg_popularity(), reverse=True)[:k]

    def top_k_by_effective_popularity(self, k=5, min_episodes = 3):
        """Return top-k nodes sorted by average effective popularity."""
        candidates = [
            n for n in self.nodes.values()
            if len(n.effective_pop_scores) >= min_episodes and n.avg_effective_popularity() is not None
        ]
        return sorted(candidates, key=lambda n: n.avg_effective_popularity(), reverse=True)[:k]
    
    def search_character(self, character: str, top_k:int = 5):
        """
        Output the node information when searching for one character.

        Parameters
        ----------
        character : str
            The character name to search for.
        top_k : int
            The number of top interaction partners to return.
        """
        if character not in self.nodes:
            return {
                "Error": f"Sorry, character {character} is not found."
            }
        
        # Information about interaction partners. 
        node = self.nodes[character]
        neighbors = self.get_neighbors(character)
        top_interactions = neighbors[:top_k]

        # Information about popularity. 
        pop_scores = node.pop_scores
        avg_pop = node.avg_popularity()
        effective_pop_scores = node.effective_pop_scores
        effective_avg_pop = node.avg_effective_popularity()

        return {
            "Character": character, 
            "Degree": node.degree, 
            "Weighted Degree": node.weighted_degree, 
            "Top Interaction Partners": [
                {"Name": neighbor, "Weight": weight}
                for neighbor, weight in top_interactions
            ], 
            "Popularity": {
                "Average": round(avg_pop, 2) if avg_pop is not None else None, 
                "Num of Episodes": len(pop_scores), 
                "Effective Episode Average": round(effective_avg_pop, 2) if effective_avg_pop is not None else None, 
                "Num of Effective Episodes": len(effective_pop_scores)
            }, 
        }
    
    def shortest_path(self, start, end):
        """Return shortest path between two characters using BFS."""
        if start not in self.nodes or end not in self.nodes:
            return None
        
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            curr, path = queue.popleft()
            if curr == end:
                return path
            
            for neighbor in self.nodes[curr].neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

def build_graph_by_seasons(episode_interactions, seasons) -> Graph:
    """
    Build a Graph containing only edges from the specified seasons. 
    
    Parameters
    ----------
    episode_interaction: dict
        episode_id: {"A-B": weight, ...}
    
    seasons: list[int]
        List of season numbers
    
    Returns
    -------
    Graph
        A new graph containing only edges from the specified seasons. 
    """
    g = Graph()
    
    for episode_id, interaction_dict in episode_interactions.items():
        match = re.search(r"S(\d+)E", episode_id)
        if not match: 
            continue
        
        season_num = int(match.group(1))
        if season_num not in seasons:
            continue
        
        for pair, weight in interaction_dict.items():
            a, b = pair.split("-")
            g.add_edge(a, b, weight)
    
    return g