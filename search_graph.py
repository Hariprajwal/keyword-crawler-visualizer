import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote
import math

ua = UserAgent()

def search_bing(query, max_results=10):
    headers = {'User-Agent': ua.random}
    urls = []
    try:
        search_url = f"https://www.bing.com/search?q={quote(query)}&count={max_results}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all('li', class_='b_algo')
        
        for result in results[:max_results]:
            link = result.find('a')
            if link and link.get('href'):
                title = link.get_text().strip()
                urls.append((title, link['href']))
    except Exception as e:
        print(f"[-] Search error: {str(e)}")
    return urls

def visualize_graph(center_keyword, edges):
    plt.figure(figsize=(14, 12))
    G = nx.Graph()
    center_label = f"Search:\n{center_keyword}"
    G.add_node(center_label, size=3000, color='#FF6B6B')
    
    # Create truncated labels for nodes
    node_data = {}
    for i, (title, url) in enumerate(edges):
        truncated_title = title[:20] + '...' if len(title) > 20 else title
        node_label = f"Site {i+1}\n{truncated_title}"
        G.add_node(node_label, size=2000, color='#4ECDC4')
        G.add_edge(center_label, node_label)
        node_data[node_label] = (title, url)  # Store original data

    # Circular layout configuration
    pos = {center_label: (0, 0)}
    angle = 2 * math.pi / len(edges) if edges else 0
    radius = 3
    
    for i, node in enumerate([n for n in G.nodes() if n != center_label]):
        pos[node] = (
            radius * math.cos(i * angle - math.pi/2),
            radius * math.sin(i * angle - math.pi/2)
        )

    # Draw graph with styling
    colors = [G.nodes[n]['color'] for n in G.nodes()]
    sizes = [G.nodes[n]['size'] for n in G.nodes()]
    
    nx.draw_networkx(
        G, pos, 
        node_color=colors, 
        node_size=sizes,
        edge_color='#7E7F9A',
        font_size=9,
        font_weight='bold',
        width=1.5,
        with_labels=True,
        alpha=0.9
    )
    
    plt.title(f"Web Crawler Radar: {center_keyword}", fontsize=16, pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    return node_data

def main():
    print("=" * 60)
    print("WEB CRAWLER RADAR".center(60))
    print("=" * 60)
    
    keyword = input("\nEnter search keyword: ").strip()
    if not keyword:
        print("[-] Please enter a valid keyword")
        return

    print(f"\n[+] Searching Bing for '{keyword}'...")
    start_time = time.time()
    results = search_bing(keyword)
    elapsed = time.time() - start_time
    
    if not results:
        print("[-] No results found or error occurred")
        return

    print(f"[+] Found {len(results)} results in {elapsed:.2f} seconds\n")
    
    # Display results in console
    print("=" * 60)
    print(f"TOP {len(results)} RESULTS".center(60))
    print("=" * 60)
    for i, (title, url) in enumerate(results, 1):
        print(f"{i}. {title}")
        print(f"   {url}")
        print("-" * 60)
        time.sleep(0.2)
    
    # Generate visualization
    print("\n[+] Generating visualization...")
    node_data = visualize_graph(keyword, results)
    
    # Display detailed data after graph
    print("\n" + "=" * 60)
    print("DETAILED PAGE INFORMATION".center(60))
    print("=" * 60)
    for i, node in enumerate(node_data, 1):
        title, url = node_data[node]
        print(f"\nRESULT {i}:")
        print(f"Title: {title}")
        print(f"URL: {url}")

if __name__ == "__main__":
    main()
