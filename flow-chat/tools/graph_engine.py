"""
CIPHER Graph Engine
Native graph operations for the knowledge network.

Provides graph-native querying and algorithms using:
1. PostgreSQL recursive CTEs for path finding
2. In-memory graph algorithms for complex operations
3. Centrality measures for identifying key claims
4. Community detection for finding knowledge clusters
5. Cross-domain bridge analysis

Cross-domain bridge: Math (graph theory) ↔ Neuro (connectomics) ↔ Biology (networks)
"""

import asyncio
import logging
import math
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import heapq

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of connections between claims"""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    ANALOGOUS = "analogous"
    CAUSAL = "causal"
    CORRELATIONAL = "correlational"


@dataclass
class GraphNode:
    """A node in the knowledge graph (represents a claim)"""
    id: int
    claim_text: str
    claim_type: str
    domains: List[int]
    confidence: float
    # Graph metrics (computed)
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    betweenness: float = 0.0
    pagerank: float = 0.0
    clustering_coefficient: float = 0.0
    community_id: Optional[int] = None


@dataclass
class GraphEdge:
    """An edge in the knowledge graph (represents a connection)"""
    source_id: int
    target_id: int
    connection_type: str
    strength: float
    cross_domain: bool
    reasoning: Optional[str] = None


@dataclass
class GraphPath:
    """A path through the knowledge graph"""
    nodes: List[int]
    edges: List[GraphEdge]
    total_weight: float
    path_type: str  # shortest, strongest, cross_domain
    domains_traversed: Set[int] = field(default_factory=set)


@dataclass
class Community:
    """A community/cluster of related claims"""
    id: int
    node_ids: List[int]
    size: int
    density: float
    dominant_domains: List[int]
    bridge_nodes: List[int]  # Nodes connecting to other communities
    coherence: float


@dataclass
class GraphStats:
    """Statistics about the knowledge graph"""
    node_count: int
    edge_count: int
    density: float
    avg_degree: float
    avg_clustering: float
    num_communities: int
    largest_community_size: int
    cross_domain_edge_ratio: float
    diameter: Optional[int] = None


class GraphEngine:
    """
    Graph-native operations for the CIPHER knowledge network.

    Implements graph algorithms optimized for knowledge synthesis:
    - Path finding (shortest, strongest connections)
    - Centrality measures (degree, betweenness, PageRank)
    - Community detection (Louvain-like algorithm)
    - Cross-domain bridge analysis
    """

    # PageRank parameters
    PAGERANK_DAMPING = 0.85
    PAGERANK_ITERATIONS = 100
    PAGERANK_TOLERANCE = 1e-6

    # Community detection parameters
    COMMUNITY_RESOLUTION = 1.0  # Higher = more communities

    def __init__(self, db_connection_string: str):
        """
        Initialize the Graph Engine.

        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
        self._conn = None

        # In-memory graph representation
        self._nodes: Dict[int, GraphNode] = {}
        self._adjacency: Dict[int, List[Tuple[int, GraphEdge]]] = defaultdict(list)
        self._reverse_adjacency: Dict[int, List[Tuple[int, GraphEdge]]] = defaultdict(list)
        self._loaded = False

    async def connect(self):
        """Establish database connection."""
        import asyncpg
        self._conn = await asyncpg.connect(self.db_connection_string)

    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def load_graph(self, min_confidence: float = 0.0):
        """
        Load the knowledge graph into memory.

        Args:
            min_confidence: Minimum claim confidence to include
        """
        logger.info("Loading knowledge graph into memory...")

        # Load nodes (claims)
        rows = await self._conn.fetch("""
            SELECT id, claim_text, claim_type, domains, confidence
            FROM synthesis.claims
            WHERE confidence >= $1
        """, min_confidence)

        for row in rows:
            self._nodes[row['id']] = GraphNode(
                id=row['id'],
                claim_text=row['claim_text'],
                claim_type=row['claim_type'] or 'unknown',
                domains=row['domains'] or [],
                confidence=row['confidence'] or 0.5
            )

        # Load edges (connections)
        edges = await self._conn.fetch("""
            SELECT source_claim_id, target_claim_id, connection_type,
                   strength, cross_domain, reasoning
            FROM synthesis.connections
        """)

        for row in edges:
            source_id = row['source_claim_id']
            target_id = row['target_claim_id']

            if source_id not in self._nodes or target_id not in self._nodes:
                continue

            edge = GraphEdge(
                source_id=source_id,
                target_id=target_id,
                connection_type=row['connection_type'] or 'related',
                strength=row['strength'] or 0.5,
                cross_domain=row['cross_domain'] or False,
                reasoning=row['reasoning']
            )

            self._adjacency[source_id].append((target_id, edge))
            self._reverse_adjacency[target_id].append((source_id, edge))

            # Update degrees
            self._nodes[source_id].out_degree += 1
            self._nodes[target_id].in_degree += 1
            self._nodes[source_id].degree += 1
            self._nodes[target_id].degree += 1

        self._loaded = True
        logger.info(f"Loaded {len(self._nodes)} nodes and {sum(len(adj) for adj in self._adjacency.values())} edges")

    def _ensure_loaded(self):
        """Ensure graph is loaded."""
        if not self._loaded:
            raise RuntimeError("Graph not loaded. Call load_graph() first.")

    # =========================================================================
    # PATH FINDING - Using PostgreSQL Recursive CTEs
    # =========================================================================

    async def find_path_cte(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 10
    ) -> Optional[GraphPath]:
        """
        Find shortest path using PostgreSQL recursive CTE.

        This is efficient for large graphs as it runs in the database.
        """
        rows = await self._conn.fetch("""
            WITH RECURSIVE path_search AS (
                -- Base case: start from source
                SELECT
                    source_claim_id,
                    target_claim_id,
                    ARRAY[source_claim_id] as path,
                    1 as depth,
                    strength as total_strength
                FROM synthesis.connections
                WHERE source_claim_id = $1

                UNION ALL

                -- Recursive case: extend path
                SELECT
                    c.source_claim_id,
                    c.target_claim_id,
                    ps.path || c.source_claim_id,
                    ps.depth + 1,
                    ps.total_strength + c.strength
                FROM synthesis.connections c
                INNER JOIN path_search ps ON c.source_claim_id = ps.target_claim_id
                WHERE NOT c.source_claim_id = ANY(ps.path)  -- Avoid cycles
                AND ps.depth < $3
            )
            SELECT path || target_claim_id as full_path, depth, total_strength
            FROM path_search
            WHERE target_claim_id = $2
            ORDER BY depth ASC, total_strength DESC
            LIMIT 1
        """, source_id, target_id, max_depth)

        if not rows:
            return None

        row = rows[0]
        path_ids = row['full_path']

        # Build path object
        edges = []
        domains = set()

        for i in range(len(path_ids) - 1):
            src, tgt = path_ids[i], path_ids[i + 1]
            # Get edge info
            edge_row = await self._conn.fetchrow("""
                SELECT connection_type, strength, cross_domain, reasoning
                FROM synthesis.connections
                WHERE source_claim_id = $1 AND target_claim_id = $2
            """, src, tgt)

            if edge_row:
                edges.append(GraphEdge(
                    source_id=src,
                    target_id=tgt,
                    connection_type=edge_row['connection_type'] or 'related',
                    strength=edge_row['strength'] or 0.5,
                    cross_domain=edge_row['cross_domain'] or False,
                    reasoning=edge_row['reasoning']
                ))

            # Get domains
            node_row = await self._conn.fetchrow(
                "SELECT domains FROM synthesis.claims WHERE id = $1", src
            )
            if node_row and node_row['domains']:
                domains.update(node_row['domains'])

        return GraphPath(
            nodes=path_ids,
            edges=edges,
            total_weight=row['total_strength'],
            path_type='shortest',
            domains_traversed=domains
        )

    async def find_all_paths_cte(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 5,
        limit: int = 10
    ) -> List[GraphPath]:
        """Find all paths between two nodes (limited)."""
        rows = await self._conn.fetch("""
            WITH RECURSIVE path_search AS (
                SELECT
                    source_claim_id,
                    target_claim_id,
                    ARRAY[source_claim_id] as path,
                    1 as depth,
                    strength as total_strength,
                    cross_domain as has_cross_domain
                FROM synthesis.connections
                WHERE source_claim_id = $1

                UNION ALL

                SELECT
                    c.source_claim_id,
                    c.target_claim_id,
                    ps.path || c.source_claim_id,
                    ps.depth + 1,
                    ps.total_strength + c.strength,
                    ps.has_cross_domain OR c.cross_domain
                FROM synthesis.connections c
                INNER JOIN path_search ps ON c.source_claim_id = ps.target_claim_id
                WHERE NOT c.source_claim_id = ANY(ps.path)
                AND ps.depth < $3
            )
            SELECT path || target_claim_id as full_path, depth, total_strength, has_cross_domain
            FROM path_search
            WHERE target_claim_id = $2
            ORDER BY depth ASC, total_strength DESC
            LIMIT $4
        """, source_id, target_id, max_depth, limit)

        paths = []
        for row in rows:
            paths.append(GraphPath(
                nodes=row['full_path'],
                edges=[],  # Simplified for performance
                total_weight=row['total_strength'],
                path_type='cross_domain' if row['has_cross_domain'] else 'shortest',
                domains_traversed=set()
            ))

        return paths

    # =========================================================================
    # IN-MEMORY GRAPH ALGORITHMS
    # =========================================================================

    def find_shortest_path(
        self,
        source_id: int,
        target_id: int
    ) -> Optional[GraphPath]:
        """
        Find shortest path using BFS (in-memory).

        Args:
            source_id: Starting node ID
            target_id: Target node ID

        Returns:
            GraphPath if path exists, None otherwise
        """
        self._ensure_loaded()

        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        # BFS
        queue = deque([(source_id, [source_id], [])])
        visited = {source_id}

        while queue:
            current, path, edges = queue.popleft()

            if current == target_id:
                domains = set()
                for nid in path:
                    domains.update(self._nodes[nid].domains)

                return GraphPath(
                    nodes=path,
                    edges=edges,
                    total_weight=sum(e.strength for e in edges),
                    path_type='shortest',
                    domains_traversed=domains
                )

            for neighbor, edge in self._adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], edges + [edge]))

        return None

    def find_strongest_path(
        self,
        source_id: int,
        target_id: int
    ) -> Optional[GraphPath]:
        """
        Find path with maximum total strength using Dijkstra (inverted weights).

        Args:
            source_id: Starting node ID
            target_id: Target node ID

        Returns:
            GraphPath with maximum strength
        """
        self._ensure_loaded()

        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        # Dijkstra with inverted weights (1 - strength)
        dist = {source_id: 0}
        prev = {}
        prev_edge = {}
        pq = [(0, source_id)]

        while pq:
            d, current = heapq.heappop(pq)

            if current == target_id:
                break

            if d > dist.get(current, float('inf')):
                continue

            for neighbor, edge in self._adjacency[current]:
                # Invert strength so higher strength = lower cost
                weight = 1.0 - edge.strength
                new_dist = d + weight

                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    prev_edge[neighbor] = edge
                    heapq.heappush(pq, (new_dist, neighbor))

        if target_id not in prev:
            return None

        # Reconstruct path
        path = []
        edges = []
        current = target_id

        while current != source_id:
            path.append(current)
            edges.append(prev_edge[current])
            current = prev[current]
        path.append(source_id)
        path.reverse()
        edges.reverse()

        domains = set()
        for nid in path:
            domains.update(self._nodes[nid].domains)

        return GraphPath(
            nodes=path,
            edges=edges,
            total_weight=sum(e.strength for e in edges),
            path_type='strongest',
            domains_traversed=domains
        )

    def find_cross_domain_path(
        self,
        source_id: int,
        target_id: int
    ) -> Optional[GraphPath]:
        """
        Find path that maximizes domain diversity.

        Prefers paths that cross multiple domains.
        """
        self._ensure_loaded()

        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        # Modified Dijkstra: prefer cross-domain edges
        dist = {source_id: 0}
        prev = {}
        prev_edge = {}
        pq = [(0, source_id, set(self._nodes[source_id].domains))]

        while pq:
            d, current, domains_seen = heapq.heappop(pq)

            if current == target_id:
                break

            if d > dist.get(current, float('inf')):
                continue

            for neighbor, edge in self._adjacency[current]:
                neighbor_domains = set(self._nodes[neighbor].domains)
                new_domains = domains_seen | neighbor_domains

                # Reward crossing into new domains
                domain_bonus = len(new_domains - domains_seen) * 0.5
                weight = (1.0 - edge.strength) - domain_bonus

                new_dist = d + weight

                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    prev_edge[neighbor] = edge
                    heapq.heappush(pq, (new_dist, neighbor, new_domains))

        if target_id not in prev:
            return None

        # Reconstruct path
        path = []
        edges = []
        current = target_id

        while current != source_id:
            path.append(current)
            edges.append(prev_edge[current])
            current = prev[current]
        path.append(source_id)
        path.reverse()
        edges.reverse()

        domains = set()
        for nid in path:
            domains.update(self._nodes[nid].domains)

        return GraphPath(
            nodes=path,
            edges=edges,
            total_weight=sum(e.strength for e in edges),
            path_type='cross_domain',
            domains_traversed=domains
        )

    # =========================================================================
    # CENTRALITY MEASURES
    # =========================================================================

    def compute_pagerank(self) -> Dict[int, float]:
        """
        Compute PageRank for all nodes.

        Identifies the most "important" claims based on connection structure.
        """
        self._ensure_loaded()

        n = len(self._nodes)
        if n == 0:
            return {}

        # Initialize
        pagerank = {nid: 1.0 / n for nid in self._nodes}
        damping = self.PAGERANK_DAMPING

        for _ in range(self.PAGERANK_ITERATIONS):
            new_pagerank = {}
            diff = 0.0

            for node_id in self._nodes:
                # Sum of PageRank from incoming edges
                incoming_sum = 0.0
                for source_id, edge in self._reverse_adjacency[node_id]:
                    out_degree = self._nodes[source_id].out_degree
                    if out_degree > 0:
                        incoming_sum += pagerank[source_id] / out_degree

                new_pr = (1 - damping) / n + damping * incoming_sum
                new_pagerank[node_id] = new_pr
                diff += abs(new_pr - pagerank[node_id])

            pagerank = new_pagerank

            if diff < self.PAGERANK_TOLERANCE:
                break

        # Update nodes
        for node_id, pr in pagerank.items():
            self._nodes[node_id].pagerank = pr

        return pagerank

    def compute_betweenness_centrality(self, sample_size: int = 100) -> Dict[int, float]:
        """
        Compute betweenness centrality (sampled for large graphs).

        Identifies claims that act as bridges between different parts of the network.
        """
        self._ensure_loaded()

        betweenness = {nid: 0.0 for nid in self._nodes}
        node_ids = list(self._nodes.keys())

        # Sample nodes for efficiency
        import random
        sample = random.sample(node_ids, min(sample_size, len(node_ids)))

        for source in sample:
            # BFS from source
            dist = {source: 0}
            num_paths = {source: 1}
            predecessors = defaultdict(list)
            queue = deque([source])
            order = []

            while queue:
                v = queue.popleft()
                order.append(v)

                for w, _ in self._adjacency[v]:
                    if w not in dist:
                        dist[w] = dist[v] + 1
                        queue.append(w)

                    if dist[w] == dist[v] + 1:
                        num_paths[w] = num_paths.get(w, 0) + num_paths[v]
                        predecessors[w].append(v)

            # Accumulate betweenness
            delta = {v: 0.0 for v in order}
            for w in reversed(order):
                for v in predecessors[w]:
                    if num_paths[w] > 0:
                        delta[v] += (num_paths[v] / num_paths[w]) * (1 + delta[w])
                if w != source:
                    betweenness[w] += delta[w]

        # Normalize
        n = len(self._nodes)
        scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0

        for node_id in betweenness:
            betweenness[node_id] *= scale
            self._nodes[node_id].betweenness = betweenness[node_id]

        return betweenness

    def compute_clustering_coefficients(self) -> Dict[int, float]:
        """
        Compute local clustering coefficient for each node.

        Measures how clustered a claim's neighbors are.
        """
        self._ensure_loaded()

        clustering = {}

        for node_id in self._nodes:
            neighbors = set(n for n, _ in self._adjacency[node_id])
            neighbors.update(n for n, _ in self._reverse_adjacency[node_id])
            k = len(neighbors)

            if k < 2:
                clustering[node_id] = 0.0
                continue

            # Count edges between neighbors
            neighbor_edges = 0
            for n1 in neighbors:
                for n2, _ in self._adjacency[n1]:
                    if n2 in neighbors and n2 != n1:
                        neighbor_edges += 1

            # Clustering coefficient
            max_edges = k * (k - 1)
            clustering[node_id] = neighbor_edges / max_edges if max_edges > 0 else 0.0
            self._nodes[node_id].clustering_coefficient = clustering[node_id]

        return clustering

    # =========================================================================
    # COMMUNITY DETECTION
    # =========================================================================

    def detect_communities(self, max_iterations: int = 10) -> List[Community]:
        """
        Detect communities using a Louvain-like algorithm.

        Groups claims into coherent clusters.

        Args:
            max_iterations: Maximum iterations for convergence (default 10)
        """
        self._ensure_loaded()

        # Skip community detection for very large graphs
        edge_count = sum(len(adj) for adj in self._adjacency.values())
        if edge_count > 20000:
            logger.warning(f"Graph too large ({edge_count} edges) for community detection. Returning empty.")
            return []

        # Initialize: each node is its own community
        community = {nid: nid for nid in self._nodes}
        total_weight = sum(
            sum(e.strength for _, e in adj)
            for adj in self._adjacency.values()
        )

        if total_weight == 0:
            # No edges, each node is its own community
            communities = []
            for nid, node in self._nodes.items():
                communities.append(Community(
                    id=nid,
                    node_ids=[nid],
                    size=1,
                    density=0.0,
                    dominant_domains=node.domains[:2] if node.domains else [],
                    bridge_nodes=[],
                    coherence=1.0
                ))
            return communities

        improved = True
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for node_id in self._nodes:
                current_comm = community[node_id]

                # Calculate modularity gain for each neighbor's community
                best_comm = current_comm
                best_gain = 0.0

                neighbor_comms = set()
                for neighbor, edge in self._adjacency[node_id]:
                    neighbor_comms.add(community[neighbor])
                for neighbor, edge in self._reverse_adjacency[node_id]:
                    neighbor_comms.add(community[neighbor])

                for new_comm in neighbor_comms:
                    if new_comm == current_comm:
                        continue

                    # Calculate modularity gain (simplified)
                    gain = self._modularity_gain(
                        node_id, new_comm, community, total_weight
                    )

                    if gain > best_gain:
                        best_gain = gain
                        best_comm = new_comm

                if best_comm != current_comm:
                    community[node_id] = best_comm
                    improved = True

        # Build community objects
        comm_nodes = defaultdict(list)
        for node_id, comm_id in community.items():
            comm_nodes[comm_id].append(node_id)
            self._nodes[node_id].community_id = comm_id

        communities = []
        for comm_id, node_ids in comm_nodes.items():
            if not node_ids:
                continue

            # Calculate community properties
            density = self._compute_community_density(node_ids)
            dominant_domains = self._get_dominant_domains(node_ids)
            bridge_nodes = self._find_bridge_nodes(node_ids, community)
            coherence = self._compute_community_coherence(node_ids)

            communities.append(Community(
                id=comm_id,
                node_ids=node_ids,
                size=len(node_ids),
                density=density,
                dominant_domains=dominant_domains,
                bridge_nodes=bridge_nodes,
                coherence=coherence
            ))

        communities.sort(key=lambda c: c.size, reverse=True)
        return communities

    def _modularity_gain(
        self,
        node_id: int,
        new_comm: int,
        community: Dict[int, int],
        total_weight: float
    ) -> float:
        """Calculate modularity gain for moving a node to a new community."""
        if total_weight == 0:
            return 0.0

        # Sum of edge weights to new community
        k_in = 0.0
        for neighbor, edge in self._adjacency[node_id]:
            if community[neighbor] == new_comm:
                k_in += edge.strength
        for neighbor, edge in self._reverse_adjacency[node_id]:
            if community[neighbor] == new_comm:
                k_in += edge.strength

        # Node degree
        k_i = sum(e.strength for _, e in self._adjacency[node_id])
        k_i += sum(e.strength for _, e in self._reverse_adjacency[node_id])

        # Community total degree
        sigma_tot = sum(
            sum(e.strength for _, e in self._adjacency[n]) +
            sum(e.strength for _, e in self._reverse_adjacency[n])
            for n, c in community.items() if c == new_comm
        )

        return k_in / total_weight - (sigma_tot * k_i) / (2 * total_weight ** 2)

    def _compute_community_density(self, node_ids: List[int]) -> float:
        """Compute edge density within a community."""
        if len(node_ids) < 2:
            return 0.0

        node_set = set(node_ids)
        internal_edges = 0

        for node_id in node_ids:
            for neighbor, _ in self._adjacency[node_id]:
                if neighbor in node_set:
                    internal_edges += 1

        max_edges = len(node_ids) * (len(node_ids) - 1)
        return internal_edges / max_edges if max_edges > 0 else 0.0

    def _get_dominant_domains(self, node_ids: List[int]) -> List[int]:
        """Get the most common domains in a community."""
        domain_counts = defaultdict(int)
        for node_id in node_ids:
            for domain in self._nodes[node_id].domains:
                domain_counts[domain] += 1

        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        return [d for d, _ in sorted_domains[:3]]

    def _find_bridge_nodes(
        self,
        node_ids: List[int],
        community: Dict[int, int]
    ) -> List[int]:
        """Find nodes that connect to other communities."""
        node_set = set(node_ids)
        bridges = []

        for node_id in node_ids:
            for neighbor, _ in self._adjacency[node_id]:
                if neighbor not in node_set:
                    bridges.append(node_id)
                    break

        return bridges

    def _compute_community_coherence(self, node_ids: List[int]) -> float:
        """Compute semantic coherence of a community based on claim similarity."""
        if len(node_ids) < 2:
            return 1.0

        # Average confidence as proxy for coherence
        total_conf = sum(self._nodes[nid].confidence for nid in node_ids)
        return total_conf / len(node_ids)

    # =========================================================================
    # CROSS-DOMAIN ANALYSIS
    # =========================================================================

    async def find_domain_bridges(self, domain_a: int, domain_b: int) -> List[GraphPath]:
        """
        Find all paths that bridge two domains.

        Uses recursive CTE for efficiency.
        """
        rows = await self._conn.fetch("""
            WITH RECURSIVE bridge_search AS (
                -- Start from claims in domain A
                SELECT
                    c.source_claim_id,
                    c.target_claim_id,
                    ARRAY[c.source_claim_id] as path,
                    1 as depth,
                    c.strength as total_strength,
                    cl.domains as current_domains
                FROM synthesis.connections c
                JOIN synthesis.claims cl ON c.source_claim_id = cl.id
                WHERE $1 = ANY(cl.domains)

                UNION ALL

                SELECT
                    c.source_claim_id,
                    c.target_claim_id,
                    bs.path || c.source_claim_id,
                    bs.depth + 1,
                    bs.total_strength + c.strength,
                    cl.domains
                FROM synthesis.connections c
                JOIN synthesis.claims cl ON c.target_claim_id = cl.id
                INNER JOIN bridge_search bs ON c.source_claim_id = bs.target_claim_id
                WHERE NOT c.source_claim_id = ANY(bs.path)
                AND bs.depth < 5
            )
            SELECT DISTINCT ON (path)
                path || target_claim_id as full_path,
                depth,
                total_strength
            FROM bridge_search bs
            JOIN synthesis.claims cl ON bs.target_claim_id = cl.id
            WHERE $2 = ANY(cl.domains)
            ORDER BY path, total_strength DESC
            LIMIT 20
        """, domain_a, domain_b)

        paths = []
        for row in rows:
            paths.append(GraphPath(
                nodes=row['full_path'],
                edges=[],
                total_weight=row['total_strength'],
                path_type='cross_domain',
                domains_traversed={domain_a, domain_b}
            ))

        return paths

    async def get_cross_domain_hubs(self, min_domains: int = 2) -> List[Tuple[int, int, List[int]]]:
        """
        Find claims that connect multiple domains.

        Returns: List of (claim_id, domain_count, domains)
        """
        rows = await self._conn.fetch("""
            SELECT
                c.id,
                array_length(c.domains, 1) as domain_count,
                c.domains,
                (
                    SELECT COUNT(DISTINCT
                        CASE WHEN conn.cross_domain THEN
                            CASE WHEN conn.source_claim_id = c.id
                                THEN conn.target_claim_id
                                ELSE conn.source_claim_id
                            END
                        END
                    )
                    FROM synthesis.connections conn
                    WHERE conn.source_claim_id = c.id OR conn.target_claim_id = c.id
                ) as cross_domain_connections
            FROM synthesis.claims c
            WHERE array_length(c.domains, 1) >= $1
            ORDER BY cross_domain_connections DESC, domain_count DESC
            LIMIT 50
        """, min_domains)

        return [(row['id'], row['domain_count'], row['domains']) for row in rows]

    # =========================================================================
    # GRAPH STATISTICS
    # =========================================================================

    def compute_graph_stats(self, fast: bool = False) -> GraphStats:
        """
        Compute overall graph statistics.

        Args:
            fast: If True, skip expensive clustering and community detection
        """
        self._ensure_loaded()

        node_count = len(self._nodes)
        edge_count = sum(len(adj) for adj in self._adjacency.values())

        if node_count == 0:
            return GraphStats(
                node_count=0, edge_count=0, density=0.0, avg_degree=0.0,
                avg_clustering=0.0, num_communities=0, largest_community_size=0,
                cross_domain_edge_ratio=0.0
            )

        # Density
        max_edges = node_count * (node_count - 1)
        density = edge_count / max_edges if max_edges > 0 else 0.0

        # Average degree
        avg_degree = sum(n.degree for n in self._nodes.values()) / node_count

        # Cross-domain edge ratio (always compute - it's fast)
        cross_domain_edges = sum(
            1 for adj in self._adjacency.values()
            for _, edge in adj if edge.cross_domain
        )
        cross_domain_ratio = cross_domain_edges / edge_count if edge_count > 0 else 0.0

        # Skip expensive operations for large graphs or fast mode
        if fast or edge_count > 10000:
            logger.info(f"Skipping clustering/community detection for large graph ({edge_count} edges)")
            return GraphStats(
                node_count=node_count,
                edge_count=edge_count,
                density=density,
                avg_degree=avg_degree,
                avg_clustering=0.0,
                num_communities=0,
                largest_community_size=0,
                cross_domain_edge_ratio=cross_domain_ratio
            )

        # Compute clustering if not done
        if all(n.clustering_coefficient == 0 for n in self._nodes.values()):
            self.compute_clustering_coefficients()
        avg_clustering = sum(n.clustering_coefficient for n in self._nodes.values()) / node_count

        # Community stats
        communities = self.detect_communities()
        num_communities = len(communities)
        largest_community_size = max((c.size for c in communities), default=0)

        return GraphStats(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            avg_degree=avg_degree,
            avg_clustering=avg_clustering,
            num_communities=num_communities,
            largest_community_size=largest_community_size,
            cross_domain_edge_ratio=cross_domain_ratio
        )

    def get_top_nodes_by_centrality(
        self,
        metric: str = 'pagerank',
        limit: int = 20
    ) -> List[Tuple[int, float, str]]:
        """
        Get top nodes by centrality metric.

        Args:
            metric: 'pagerank', 'betweenness', 'degree', or 'clustering'
            limit: Number of results

        Returns:
            List of (node_id, score, claim_text)
        """
        self._ensure_loaded()

        if metric == 'pagerank':
            if all(n.pagerank == 0 for n in self._nodes.values()):
                self.compute_pagerank()
            key = lambda n: n.pagerank
        elif metric == 'betweenness':
            if all(n.betweenness == 0 for n in self._nodes.values()):
                self.compute_betweenness_centrality()
            key = lambda n: n.betweenness
        elif metric == 'degree':
            key = lambda n: n.degree
        elif metric == 'clustering':
            if all(n.clustering_coefficient == 0 for n in self._nodes.values()):
                self.compute_clustering_coefficients()
            key = lambda n: n.clustering_coefficient
        else:
            raise ValueError(f"Unknown metric: {metric}")

        sorted_nodes = sorted(self._nodes.values(), key=key, reverse=True)

        return [
            (n.id, key(n), n.claim_text[:100])
            for n in sorted_nodes[:limit]
        ]


# Convenience functions
async def get_graph_engine(db_connection_string: str) -> GraphEngine:
    """Get a connected and loaded GraphEngine instance."""
    engine = GraphEngine(db_connection_string)
    await engine.connect()
    await engine.load_graph()
    return engine
