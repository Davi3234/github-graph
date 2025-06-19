import requests
import gzip
import io
import json
import networkx as nx
from datetime import datetime
import matplotlib.pyplot as plt

DATABASE_URL = "https://data.gharchive.org/2023-06-10-0.json.gz"

def download_and_parse(url):
    print(f"$ Compilando dados de: \"{url}\"...")

    r = requests.get(url)
    r.raise_for_status()

    compressed_file = io.BytesIO(r.content)

    with gzip.GzipFile(fileobj=compressed_file) as f:
        for line in f:
            yield json.loads(line)

def build_graph(events):
    G = nx.Graph()
    repo_to_users = {}

    print(f"$ Construindo grafo...")

    for e in events:
        if e.get("type") == "PushEvent":
            repo_name = e["repo"]["name"]
            user = e["actor"]["login"]

            if repo_name not in repo_to_users:
                repo_to_users[repo_name] = set()
            repo_to_users[repo_name].add(user)

    for repo, users in repo_to_users.items():
        users_list = list(users)

        for i in range(len(users_list)):
            for j in range(i+1, len(users_list)):
                u1 = users_list[i]
                u2 = users_list[j]

                if G.has_edge(u1, u2):
                    G[u1][u2]['weight'] += 1
                else:
                    G.add_edge(u1, u2, weight=1)
    return G

def interprete_graph(graph, degree_users):
    print(f"--\nNúmero de nós mapeados (desenvolvedores): {graph.number_of_nodes()}")
    print(f"Número de arestas mapeados (colaborações): {graph.number_of_edges()}")

    top_degrees = sorted(degree_users.items(), key=lambda x: x[0], reverse=True)[:5]

    print("Top 5 graus distintos (usuários com maior número de conexões):")

    for degree, users in top_degrees:
        print(f"  Grau {degree}: \"{users[0]}\" e mais {len(users) - 1} desenvolvedor(es)")

def draw_graph(graph, degrees):
    plt.figure(figsize=(12, 12))

    pos = nx.spring_layout(graph, k=0.1)

    nx.draw_networkx_nodes(graph, pos, node_size=[degrees[n] for n in graph.nodes()], node_color="blue", alpha=0.7)
    nx.draw_networkx_edges(graph, pos, alpha=0.3)
    nx.draw_networkx_labels(graph, pos, font_size=8)

def save_graph():
    NAME = f"/app/assets/grafo_colaboracao-{datetime.today().strftime('%Y-%m-%d')}.png"

    plt.title("Rede de Colaboração entre Desenvolvedores (PushEvent)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(NAME)

    print(f"--\nVisualização salva em '{NAME}'")

def main():
    events = download_and_parse(DATABASE_URL)

    G = build_graph(events)

    degrees = dict(G.degree())

    degree_to_users = {}

    for user, degree in degrees.items():
        if degree not in degree_to_users:
            degree_to_users[degree] = []

        degree_to_users[degree].append(user)

    interprete_graph(G, degree_to_users)
    draw_graph(G, degrees)
    save_graph()

if __name__ == "__main__":
    main()
