import json

def export_for_web(graph, filename="graph_data.json"):
    """Export graph data in a clean format for frontend JS visualization."""
    nodes = []
    for node_id, data in graph.nodes(data=True):
        nodes.append({
            "id": node_id,
            "label": data.get("name") or data.get("title") or node_id,
            "group": data.get("type", "unknown"),
            "title": f"<b>{data.get('name', node_id)}</b><br>Type: {data.get('type')}"
        })
    
    edges = []
    for source, target, data in graph.edges(data=True):
        edges.append({
            "from": source,
            "to": target,
            "label": data.get("relationship", ""),
            "arrows": "to"
        })
    
    web_data = {"nodes": nodes, "edges": edges}
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(web_data, f, indent=4)
    print(f"Web graph data exported to {filename}")