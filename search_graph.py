import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote

ua = UserAgent()

def search_bing(query, max_results=10):
    headers = {'User-Agent': ua.random}
    urls = []
    for start in range(0, max_results, 10):
        search_url = f"https://www.bing.com/search?q={quote(query)}&first={start}"
        resp = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        for h2 in soup.find_all("h2"):
            a = h2.find("a")
            if a and a.get("href").startswith("http"):
                urls.append((a.get_text(), a["href"]))
    return urls

def visualize_graph(center_keyword, edges):
    G = nx.Graph()
    G.add_node(center_keyword)

    for title, url in edges:
        G.add_node(title)
        G.add_edge(center_keyword, title)

    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.6)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=3000, font_size=10)
    plt.title(f"Crawler Radar: {center_keyword}")
    plt.show()

def main():
    keyword = input("Enter search keyword: ")
    print("[+] Searching...")
    results = search_bing(keyword, 10)
    print(f"[+] Found {len(results)} results.")

    for i, (title, link) in enumerate(results, 1):
        print(f"{i}. {title}\n   {link}\n")
        time.sleep(1)

    visualize_graph(keyword, results)

if __name__ == "__main__":
    main()
