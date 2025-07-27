import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import quote
import math
import re
from collections import defaultdict

ua = UserAgent()

# Common device patterns for detection
DEVICE_PATTERNS = {
    'iPhone': r'\biPhone\s*\d{1,2}\w*\b|\biPhone\s*[1-9][0-9]?\b',
    'iPad': r'\biPad\s*\d{1,2}\w*\b|\biPad\s*[1-9][0-9]?\b',
    'Mac': r'\bMacBook\s*(Pro|Air)?\b|\biMac\b|\bMac\s*mini\b|\bMac\s*Pro\b',
    'Samsung': r'\bGalaxy\s*(S|Note|Tab|Z|A)\s*\d{1,2}\w*\b|\bSamsung\s*Galaxy\b',
    'Google': r'\bPixel\s*\d{1,2}\b|\bPixel\s*[a-zA-Z]+\b',
    'Microsoft': r'\bSurface\s*(Pro|Go|Laptop|Book|Studio)\s*\d*\b',
    'PlayStation': r'\bPS\d\b|\bPlayStation\s*\d\b',
    'Xbox': r'\bXbox\s*(One|Series\s*[SX])\b',
    'Smartwatch': r'\bApple\s*Watch\b|\bGalaxy\s*Watch\b|\bFitbit\b|\bGarmin\b'
}

def detect_devices(text):
    """Detect device mentions in text using predefined patterns"""
    devices_found = defaultdict(int)
    text = text.lower()
    
    for device_type, pattern in DEVICE_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Count unique models (approximate)
            unique_models = set(m.group(0).strip() for m in re.finditer(pattern, text, re.IGNORECASE))
            devices_found[device_type] = list(unique_models)[:3]  # Limit to top 3 models
    
    return dict(devices_found)

def get_page_content(url):
    """Fetch webpage content with error handling"""
    try:
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Check content type to avoid processing non-HTML
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return None
            
        return response.text
    except Exception as e:
        print(f"  - Error fetching {url}: {str(e)}")
        return None

def search_bing(query, max_results=10):
    """Search Bing and return results with device detection"""
    headers = {'User-Agent': ua.random}
    results = []
    
    try:
        search_url = f"https://www.bing.com/search?q={quote(query)}&count={max_results}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        search_items = soup.find_all('li', class_='b_algo')[:max_results]
        
        for item in search_items:
            link = item.find('a')
            if link and link.get('href'):
                title = link.get_text().strip()
                url = link['href']
                
                # Get snippet from Bing results
                snippet_div = item.find('div', class_='b_caption')
                snippet = snippet_div.get_text().strip() if snippet_div else "No description available"
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'devices': {}  # To be populated later
                })
    except Exception as e:
        print(f"[-] Search error: {str(e)}")
    
    return results

def analyze_results(results):
    """Analyze each page to detect devices"""
    print("\n[+] Analyzing pages for device mentions...")
    
    for result in results:
        print(f"  - Processing: {result['title'][:50]}...")
        page_content = get_page_content(result['url'])
        
        if page_content:
            # Extract clean text for device detection
            soup = BeautifulSoup(page_content, 'html.parser')
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            text = main_content.get_text() if main_content else soup.get_text()
            clean_text = re.sub(r'\s+', ' ', text).strip()[:5000]  # Limit to first 5000 chars
            
            # Detect devices in the content
            result['devices'] = detect_devices(clean_text)
            time.sleep(1)  # Be polite to servers
        else:
            result['devices'] = {'Error': ['Page not accessible']}
    
    return results

def visualize_graph(center_keyword, results):
    """Create a radar graph of search results with device insights"""
    plt.figure(figsize=(16, 14))
    G = nx.Graph()
    center_label = f"Search:\n{center_keyword}"
    G.add_node(center_label, size=4000, color='#FF6B6B')
    
    # Device color mapping
    device_colors = {
        'iPhone': '#FF9AA2', 'iPad': '#FFB7B2', 'Mac': '#FFDAC1',
        'Samsung': '#E2F0CB', 'Google': '#B5EAD7', 'Microsoft': '#C7CEEA',
        'PlayStation': '#F8B195', 'Xbox': '#6C5B7B', 'Smartwatch': '#355C7D'
    }
    
    # Create nodes and edges
    node_data = {}
    for i, result in enumerate(results):
        truncated_title = result['title'][:20] + '...' if len(result['title']) > 20 else result['title']
        node_label = f"Site {i+1}\n{truncated_title}"
        
        # Assign color based on dominant device category
        node_color = '#4ECDC4'  # Default color
        if result['devices']:
            primary_device = list(result['devices'].keys())[0]
            node_color = device_colors.get(primary_device, '#4ECDC4')
        
        G.add_node(node_label, size=2500, color=node_color)
        G.add_edge(center_label, node_label)
        node_data[node_label] = result
    
    # Circular layout configuration
    pos = {center_label: (0, 0)}
    angle = 2 * math.pi / len(results) if results else 0
    radius = 3.5
    
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
        font_size=10,
        font_weight='bold',
        width=2,
        with_labels=True,
        alpha=0.95
    )
    
    # Create device legend
    legend_handles = []
    for device, color in device_colors.items():
        legend_handles.append(plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=color, markersize=10, label=device))
    
    plt.legend(handles=legend_handles, loc='upper right', title="Device Categories")
    plt.title(f"Device Detection Radar: {center_keyword}", fontsize=18, pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    return node_data

def print_device_report(results):
    """Print detailed device report"""
    print("\n" + "=" * 80)
    print("DEVICE DETECTION REPORT".center(80))
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{' RESULT ' + str(i) + ' ':-^80}")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\nSummary: {result['snippet']}")
        
        if 'Error' in result['devices']:
            print("\n  !! Page content not accessible for analysis")
        elif not result['devices']:
            print("\n  No devices detected on this page")
        else:
            print("\nDetected Devices:")
            for category, models in result['devices'].items():
                print(f"  - {category}:")
                for model in models:
                    print(f"      • {model}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE".center(80))
    print("=" * 80)

def main():
    print("=" * 70)
    print("ADVANCED DEVICE DETECTION CRAWLER".center(70))
    print("=" * 70)
    
    keyword = input("\nEnter search keyword: ").strip()
    if not keyword:
        print("[-] Please enter a valid keyword")
        return

    print(f"\n[+] Searching Bing for '{keyword}'...")
    start_time = time.time()
    results = search_bing(keyword)
    
    if not results:
        print("[-] No results found or error occurred")
        return
    
    # Analyze pages for device mentions
    results = analyze_results(results)
    elapsed = time.time() - start_time
    
    # Initial results summary
    print(f"\n[+] Analyzed {len(results)} pages in {elapsed:.2f} seconds")
    print("\n" + "=" * 70)
    print(f"TOP {len(results)} RESULTS SUMMARY".center(70))
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        devices = list(result['devices'].keys())
        device_info = ', '.join(devices[:3]) + ('...' if len(devices) > 3 else '') if devices else 'None'
        print(f"{i}. {result['title'][:60]}{'...' if len(result['title']) > 60 else ''}")
        print(f"   Devices: {device_info}")
        print(f"   {result['url']}")
        print("-" * 70)
    
    # Generate visualization
    print("\n[+] Generating device detection radar...")
    node_data = visualize_graph(keyword, results)
    
    # Detailed device report
    print_device_report(results)

if __name__ == "__main__":
    main()
