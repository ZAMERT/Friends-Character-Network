import sys
import os

# add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import FriendsCLI
from flask import Flask, render_template, request, redirect

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx


app = Flask(__name__)

# Load the graph. 
cli = FriendsCLI()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    name = None
    result = None
    if request.method == "POST":
        raw_name = request.form.get("name", "").strip()
        if raw_name:
            name = raw_name.title()
            result = cli.graph.search_character(name)
        else:
            result = {"error": "Please enter a character name."}

    return render_template("search.html", name = name, result = result)

@app.route("/path", methods=["GET", "POST"])
def shortest_path():
    result = None
    if request.method == "POST":
        start = request.form.get("start")
        end = request.form.get("end")
        result = cli.graph.shortest_path(start.title(), end.title())
    
    return render_template("path.html", result=result)

@app.route("/season")
def season_filter():
    season = request.args.get("season")

    if season == "all":
        cli.reset_graph()

    elif season:
        try:
            cli.filter_season(int(season))
        except:
            pass
    return redirect(request.referrer or "/")

@app.route("/rankings", methods=["GET", "POST"])
def rankings():
    result = None

    if request.method == "POST":
        k = int(request.form.get("k", 5))
        result = {
            "degree": cli.graph.top_k_by_degree(k),
            "weighted": cli.graph.top_k_by_weighted_degree(k),
            "popularity": cli.graph.top_k_by_popularity(k),
            "effective": cli.graph.top_k_by_effective_popularity(k)
        }

    return render_template("rankings.html", rankings=result)

def generate_graph_image(graph, save_path="Friends_UI/static/graph.png"):
    """Generate and save a visualization of the graph using NetworkX and Matplotlib."""
    G = nx.Graph()

    for name, node in graph.nodes.items():
        G.add_node(name)

    for name, node in graph.nodes.items():
        for neighbor, weight in node.neighbors.items():
            if G.has_edge(name, neighbor):
                continue
            G.add_edge(name, neighbor, weight=weight)

    plt.figure(figsize=(10, 8))

    # Determine positions using spring layout. 
    pos = nx.spring_layout(G, k=0.5, seed=42)  

    node_sizes = [
    min(node.weighted_degree * 20, 300) 
    for node in graph.nodes.values()
    ]

    nx.draw_networkx(
        G, 
        pos,
        with_labels=True,
        node_size=node_sizes,
        font_size=8,
        node_color="#86bff1",
        edge_color="#888"
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

@app.route("/graph")
def graph_page():
    generate_graph_image(cli.graph)

    return render_template("graph.html")



if __name__ == "__main__":
    app.run(debug=True)