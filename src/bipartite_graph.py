"""
Bipartite Causal Knowledge Graph (CKG) Constructor.
Constructs G = (V_transcript U V_XBRL, E_cross U E_calc) coupling spoken conference
claims with audited regulatory XBRL balance sheets and footnote disclosures.
"""

from typing import Dict, Any, List, Tuple
import networkx as nx
import logging

logger = logging.getLogger("BipartiteGraph")

class BipartiteCausalGraphBuilder:
    """
    Constructs and traverses the Bipartite Causal Knowledge Graph.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def build_graph(self,
                    transcript_turns: List[Dict[str, Any]],
                    xbrl_nodes: List[Dict[str, Any]]
                    ) -> nx.DiGraph:
        """
        Builds the unified graph coupling spoken claims with XBRL nodes.
        """
        self.graph.clear()
        
        # 1. Add XBRL Nodes
        for x_node in xbrl_nodes:
            nid = x_node["node_id"]
            self.graph.add_node(
                nid,
                bipartite=0, # Partition 0: Audited Regulatory Domain
                node_type=x_node["node_type"],
                concept=x_node.get("concept", ""),
                value=x_node.get("value", None),
                statement=x_node.get("statement", ""),
                source=x_node.get("source", ""),
                raw_data=x_node
            )
            
        # 2. Add Transcript Nodes (Partition 1: Spoken Discourse Domain)
        for t_turn in transcript_turns:
            turn_id = t_turn["turn_id"]
            speaker = t_turn.get("speaker", "Executive")
            section = t_turn.get("section", "Presentation")
            text = t_turn.get("text", "")
            prosody = t_turn.get("acoustic_diagnostics", {})
            claimed_concept = t_turn.get("claimed_concept", "")
            claimed_value = t_turn.get("claimed_value", None)
            
            nid = f"TRANSCRIPT_{turn_id}"
            self.graph.add_node(
                nid,
                bipartite=1, # Partition 1: Spoken Assertions Domain
                node_type="TranscriptClaim",
                turn_id=turn_id,
                speaker=speaker,
                section=section,
                text=text,
                claimed_concept=claimed_concept,
                claimed_value=claimed_value,
                prosody_score=prosody.get("composite_prosody_score", 0.0),
                is_dissonant=prosody.get("is_acoustically_dissonant", False),
                diagnostic_flags=prosody.get("diagnostic_flags", [])
            )
            
        # 3. Add Cross-Modal Edges E_cross linking spoken claims to audited concepts
        self._add_cross_modal_alignment_edges(transcript_turns)
        
        # 4. Add Calculation and Dependency Arcs E_calc
        self._add_xbrl_calculation_arcs()
        
        logger.info(f"Constructed Bipartite CKG with {self.graph.number_of_nodes()} nodes "
                    f"and {self.graph.number_of_edges()} edges.")
        return self.graph

    def _add_cross_modal_alignment_edges(self, transcript_turns: List[Dict[str, Any]]):
        """
        Connects transcript claim nodes to matching XBRL concept nodes.
        """
        concept_to_node = {}
        for nid, data in self.graph.nodes(data=True):
            if data.get("bipartite") == 0 and "concept" in data:
                concept_to_node[data["concept"]] = nid
                
        for t_turn in transcript_turns:
            t_nid = f"TRANSCRIPT_{t_turn['turn_id']}"
            claimed_concept = t_turn.get("claimed_concept", "")
            
            # Direct mapping
            target_xbrl = f"XBRL_{claimed_concept}"
            if target_xbrl in self.graph:
                self.graph.add_edge(
                    t_nid, target_xbrl,
                    edge_type="AssertsAlignment",
                    weight=1.0,
                    relation="claims_match_to_balance_sheet"
                )
                
            # Semantic / Accounting mappings for key claims
            if claimed_concept == "ShortTermDebtMaturity":
                # Links to Note 7 (Debt Obligation & Accelerated Maturities)
                if "FN_Note_7" in self.graph:
                    self.graph.add_edge(t_nid, "FN_Note_7", edge_type="AuditedAgainstFootnote", weight=1.0)
                if "XBRL_CurrentPortionOfLongTermDebt" in self.graph:
                    self.graph.add_edge(t_nid, "XBRL_CurrentPortionOfLongTermDebt", edge_type="CrossVerifies", weight=1.0)
                    
            elif claimed_concept == "ContractAssetsExtendedTerms":
                # Links to Note 3 (Revenue Recognition & Contract Assets)
                if "FN_Note_3" in self.graph:
                    self.graph.add_edge(t_nid, "FN_Note_3", edge_type="AuditedAgainstFootnote", weight=1.0)
                if "XBRL_ContractAssetsUnbilled" in self.graph:
                    self.graph.add_edge(t_nid, "XBRL_ContractAssetsUnbilled", edge_type="CrossVerifies", weight=1.0)
                    
            elif claimed_concept == "OffBalanceSheetGuarantees":
                # Links to Note 14 (Commitments & Unconsolidated Guarantees)
                if "FN_Note_14" in self.graph:
                    self.graph.add_edge(t_nid, "FN_Note_14", edge_type="AuditedAgainstFootnote", weight=1.0)
                if "FACT_Note_14_OffBalanceSheetGuarantees" in self.graph:
                    self.graph.add_edge(t_nid, "FACT_Note_14_OffBalanceSheetGuarantees", edge_type="CrossVerifies", weight=1.0)

    def _add_xbrl_calculation_arcs(self):
        """
        Enforces internal GAAP calculation trees (E_calc).
        """
        # Balance sheet calculation arcs
        if "XBRL_CashAndCashEquivalents" in self.graph and "XBRL_TotalCurrentAssets" in self.graph:
            self.graph.add_edge("XBRL_CashAndCashEquivalents", "XBRL_TotalCurrentAssets", edge_type="ComponentOf", weight=1.0)
        if "XBRL_AccountsReceivableNet" in self.graph and "XBRL_TotalCurrentAssets" in self.graph:
            self.graph.add_edge("XBRL_AccountsReceivableNet", "XBRL_TotalCurrentAssets", edge_type="ComponentOf", weight=1.0)
        if "XBRL_ContractAssetsUnbilled" in self.graph and "XBRL_TotalCurrentAssets" in self.graph:
            self.graph.add_edge("XBRL_ContractAssetsUnbilled", "XBRL_TotalCurrentAssets", edge_type="ComponentOf", weight=1.0)
        if "XBRL_TotalCurrentAssets" in self.graph and "XBRL_TotalAssets" in self.graph:
            self.graph.add_edge("XBRL_TotalCurrentAssets", "XBRL_TotalAssets", edge_type="ComponentOf", weight=1.0)
            
        # Footnote linkage to balance sheet
        if "FN_Note_3" in self.graph and "XBRL_ContractAssetsUnbilled" in self.graph:
            self.graph.add_edge("FN_Note_3", "XBRL_ContractAssetsUnbilled", edge_type="ExplainsLineItem", weight=1.0)
        if "FN_Note_7" in self.graph and "XBRL_CurrentPortionOfLongTermDebt" in self.graph:
            self.graph.add_edge("FN_Note_7", "XBRL_CurrentPortionOfLongTermDebt", edge_type="ExplainsLineItem", weight=1.0)

    def get_contradiction_subgraph(self, turn_id: str) -> nx.DiGraph:
        """Extracts the immediate ego-graph surrounding a given claim turn."""
        t_nid = f"TRANSCRIPT_{turn_id}"
        if t_nid not in self.graph:
            return nx.DiGraph()
        neighbors = list(self.graph.neighbors(t_nid)) + [t_nid]
        return self.graph.subgraph(neighbors).copy()
