import requests
import gzip
import io
import json
import networkx as nx
import matplotlib.pyplot as plt

URL = "https://data.gharchive.org/2023-06-10-0.json.gz"

def download_and_parse(url):
    print(f"Baixando dados de: {url}")
    r = requests.get(url)
    r.raise_for_status()
    compressed_file = io.BytesIO(r.content)
    contador = 0
    with gzip.GzipFile(fileobj=compressed_file) as f:
        for line in f:
            yield json.loads(line)

def build_graph(events):
    G = nx.Graph()
    repo_to_users = {}

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

def main():
    events = download_and_parse(URL)
    print("Construindo grafo...")
    G = build_graph(events)

    print(f"Número de nós (desenvolvedores): {G.number_of_nodes()}")
    print(f"Número de arestas (colaborações): {G.number_of_edges()}")

    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
    print(f"Grau médio dos nós: {avg_degree:.2f}")

    centrality = nx.degree_centrality(G)
    top5 = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 desenvolvedores por centralidade de grau:")
    for user, cent in top5:
        print(f"  {user}: {cent:.4f}")

    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, k=0.1)
    nx.draw_networkx_nodes(G, pos, node_size=[v * 1000 for v in centrality.values()], node_color="blue", alpha=0.7)
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.title("Rede de Colaboração entre Desenvolvedores (PushEvent)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("/app/grafo_colaboracao.png")
    print("Visualização salva em 'grafo_colaboracao.png'")

if __name__ == "__main__":
    main()
