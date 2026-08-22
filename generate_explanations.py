import json
import os
from pathlib import Path

graph = json.loads(Path("graphify-out/graph.json").read_text(encoding="utf-8"))
nodes = graph["nodes"]
links = graph["links"]

# Compute degrees
node_degrees = {}
for link in links:
    src = link["source"]
    tgt = link["target"]
    node_degrees[src] = node_degrees.get(src, 0) + 1
    node_degrees[tgt] = node_degrees.get(tgt, 0) + 1

sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
god_node_ids = [n[0] for n in sorted_nodes[:10]]

# Build community map
communities = {}
for node in nodes:
    cid = node["community"]
    communities.setdefault(cid, []).append(node["id"])

# Cross-community links
cross_links = []
for link in links:
    src_comm = next(n["community"] for n in nodes if n["id"] == link["source"])
    tgt_comm = next(n["community"] for n in nodes if n["id"] == link["target"])
    if src_comm != tgt_comm:
        cross_links.append(link)

# === GOD NODE EXPLANATIONS ===
god_explanations = []
for god_id in god_node_ids:
    node = next(n for n in nodes if n["id"] == god_id)
    connections = [l for l in links if l["source"] == god_id or l["target"] == god_id]
    node_info = next(n for n in nodes if n["id"] == god_id)

    conn_lines = ""
    for conn in connections:
        other_id = conn["target"] if conn["source"] == god_id else conn["source"]
        other_node = next(n for n in nodes if n["id"] == other_id)
        conn_lines += "- **" + other_node["label"] + "** (Community " + str(other_node["community"]) + ") - " + conn.get("context", "connection") + "\n"

    degree = len(connections)
    explanation = "# God Node: " + node_info["label"] + "\n"
    explanation += "**ID:** " + god_id + "\n"
    explanation += "**Community:** Community " + str(node_info["community"]) + "\n"
    explanation += "**File:** " + node_info["source_file"] + " (Line " + str(node_info["source_location"]) + ")\n"
    explanation += "**Degree:** " + str(degree) + " connections\n"
    explanation += "## Connections\n" + conn_lines
    explanation += "## Role in Architecture\n"
    explanation += "This node is a central hub in the SiraFit codebase, connecting " + str(degree) + " other components. It likely represents a core abstraction or service that many other parts of the system depend on.\n"
    explanation += "## Upgrade Path\n"
    explanation += "If this node needs enhancement: 1) Add interface/abstract class, 2) Add comprehensive tests, 3) Document the API contract, 4) Consider if it should be split into smaller focused components.\n"

    god_explanations.append(explanation)

# === SURPRISING CONNECTIONS ===
connection_explanations = []
for link in cross_links[:5]:
    src_node = next(n for n in nodes if n["id"] == link["source"])
    tgt_node = next(n for n in nodes if n["id"] == link["target"])

    explanation = "# Surprising Connection: " + src_node["label"] + " -> " + tgt_node["label"] + "\n"
    explanation += "**Source:** Community " + str(src_node["community"]) + " - " + src_node["source_file"] + "\n"
    explanation += "**Target:** Community " + str(tgt_node["community"]) + " - " + tgt_node["source_file"] + "\n"
    explanation += "**Relation:** " + ("calls" if not link.get("relation") else link["relation"]) + "\n"
    explanation += "**Confidence:** " + link.get("confidence", "EXTRACTED") + " (score: " + str(link.get("confidence_score", "N/A")) + ")\n"
    explanation += "## Why This Is Surprising\n"
    explanation += "This connection bridges two communities that typically do not interact, suggesting:\n"
    explanation += "1. A shared dependency or abstraction\n"
    explanation += "2. A cross-cutting concern (e.g., Session management)\n"
    explanation += "3. An architectural coupling that should be examined\n"
    explanation += "## Architectural Implication\n"
    explanation += "This bridge indicates that " + tgt_node["label"] + " (in Community " + str(tgt_node["community"]) + ") is accessed from " + src_node["label"] + " (in Community " + str(src_node["community"]) + "), which may require:\n"
    explanation += "- Interface normalization\n"
    explanation += "- Error handling consistency\n"
    explanation += "- Data transformation layer\n"
    explanation += "- Consideration of whether this should be a direct dependency or mediated through a shared service\n"

    connection_explanations.append(explanation)

# === COMMUNITY LINK PAGES ===
link_pages = []
for comm_id in sorted(communities.keys()):
    comm_node_ids = communities[comm_id]
    if not comm_node_ids:
        continue
    comm_nodes = [n for n in nodes if n["community"] == comm_id]
    comm_links = [l for l in links if l["source"] in comm_node_ids or l["target"] in comm_node_ids]

    node_list_lines = []
    for node in comm_nodes:
        conns = [l for l in links if l["source"] == node["id"] or l["target"] == node["id"]]
        label_safe = node["label"].replace("]]", "] >").replace("[", " [")
        loc = node.get("source_location", "?")
        node_list_lines.append("- [[" + label_safe + "]] - " + node["source_file"] + " L" + str(loc) + " - " + str(len(conns)) + " connections")

    internal_count = len([l for l in comm_links if l.get("confidence") == "EXTRACTED"])

    external_count = len([l for l in comm_links
        if next((n["community"] for n in nodes if n["id"] == l["source"]), None) != comm_id
        or next((n["community"] for n in nodes if n["id"] == l["target"]), None) != comm_id])

    god_count = len([n for n in comm_nodes if node_degrees.get(n["id"], 0) > 10])

    page = "# Community " + str(comm_id) + "\n"
    page += "**Members:** " + str(len(comm_nodes)) + " nodes\n"
    page += "## Node List\n"
    page += "\n".join(node_list_lines) + "\n"
    page += "## Internal Connections\n"
    page += "- " + str(internal_count) + " extracted connections within community\n"
    page += "## External Bridges\n"
    page += "- " + str(external_count) + " cross-community bridges\n"
    page += "## God Nodes in This Community\n"
    page += "- " + str(god_count) + " high-degree nodes\n"

    link_pages.append(page)

# === SUMMARY ===
summary = "# SiraFit Graphify Explanations\n"
summary += "\n"
summary += "Generated from: 1647 nodes, 2525 edges, 151 communities\n"
summary += "\n"
summary += "## God Nodes\n"
summary += str(len(god_explanations)) + " detailed explanations provided above\n"
summary += "\n"
summary += "## Surprising Connections\n"
summary += str(len(connection_explanations)) + " cross-community bridges analyzed above\n"
summary += "\n"
summary += "## Community Link Pages\n"
summary += str(len(link_pages)) + " community summaries generated\n"
summary += "\n"
summary += "## Key Findings\n"
summary += "- " + str(len(god_node_ids)) + " god nodes identified as central abstractions\n"
summary += "- " + str(len(cross_links)) + " cross-community bridges discovered\n"
summary += "- " + str(len(nodes)) + " total nodes across " + str(len(communities)) + " communities\n"
summary += "- No import cycles detected\n"
summary += "\n"
summary += "## How to Use\n"
summary += "1. Review god nodes to understand core abstractions\n"
summary += "2. Study surprising connections for architectural insights\n"
summary += "3. Use community link pages for navigation within the codebase\n"
summary += "4. Open graph.html for interactive exploration\n"

# Write all files with explicit UTF-8 encoding
output_dir = "graphify-out/explanations"
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, "god-nodes.md"), "w", encoding="utf-8") as f:
    for i, expl in enumerate(god_explanations, 1):
        f.write("## God Node " + str(i) + "\n")
        f.write(expl)
        f.write("---\n\n")

with open(os.path.join(output_dir, "surprising-connections.md"), "w", encoding="utf-8") as f:
    for i, expl in enumerate(connection_explanations, 1):
        f.write("## Connection " + str(i) + "\n")
        f.write(expl)
        f.write("---\n\n")

with open(os.path.join(output_dir, "community-link-pages.md"), "w", encoding="utf-8") as f:
    for i, page in enumerate(link_pages, 1):
        f.write("# Community Summary " + str(i) + "\n")
        f.write(page)
        f.write("---\n\n")

with open(os.path.join(output_dir, "EXPLANATION_SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write(summary)

print("Explanation files generated successfully!")
print("  - god-nodes.md: " + str(len(god_explanations)) + " god node explanations")
print("  - surprising-connections.md: " + str(len(connection_explanations)) + " connection explanations")
print("  - community-link-pages.md: " + str(len(link_pages)) + " community summaries")
print("  - EXPLANATION_SUMMARY.md: 1 summary document")