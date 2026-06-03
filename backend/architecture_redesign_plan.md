# Information Cognition System — Backend Architecture Redesign

This document outlines the complete architectural redesign of the backend, transitioning from a traditional search engine to an **Information Cognition System**. The API contract with the frontend remains strictly identical, while the internal philosophy, algorithms, and data flows are entirely reinvented.

## 1. MICRO-MODULAR FILE STRUCTURE

The backend is decomposed into atomic, single-responsibility files. Monoliths and "utils" dumping grounds have been strictly prohibited.

```text
backend/
├── core/
│   ├── brain/
│   │   ├── intent_distiller.py       # Distills raw string into intent vectors
│   │   ├── semantic_pressure.py      # Calculates semantic pressure fields
│   │   └── context_drift.py          # Maps contextual drift over query states
│   ├── signal/
│   │   ├── signal_expander.py        # Expands intent into retrieval fields
│   │   └── field_generator.py        # Generates semantic retrieval boundaries
│   └── state/
│       └── cognitive_state.py        # Maintains state for recursive evaluation
│
├── engine/
│   ├── executor/
│   │   ├── async_swarm.py            # Orchestrates parallel agent execution
│   │   └── branch_evaluator.py       # Determines adaptive branching execution
│   ├── scheduler/
│   │   └── feedback_injector.py      # Manages feedback re-injection loops
│   └── pipeline/
│       └── cognition_flow.py         # Main execution coordinator (Step 1-6)
│
├── ranking/
│   ├── semantic_weight/
│   │   └── resonance_calc.py         # Computes semantic resonance score
│   ├── conflict/
│   │   └── contradiction_layer.py    # Calculates contradiction penalty index
│   ├── temporal/
│   │   └── freshness_decay.py        # Computes non-linear freshness decay curve
│   ├── trust/
│   │   └── gravity_field.py          # Computes authority gravity field
│   ├── alignment/
│   │   └── contextual_delta.py       # Computes contextual alignment delta
│   └── cognitive_ranker.py           # Aggregates scores using custom formulas
│
├── retrieval/
│   ├── crawler_nodes/
│   │   └── node_allocator.py         # Allocates target spaces for agents
│   ├── fetch_agents/
│   │   ├── web_signal_agent.py       # Extracts raw signals from open web
│   │   ├── knowledge_drift_agent.py  # Extracts signals from knowledge graphs
│   │   ├── context_harvester.py      # Extracts deep contextual signals
│   │   └── live_stream_agent.py      # Extracts real-time temporal signals
│   └── response_harvesters/
│       └── signal_parser.py          # Parses raw signals into fragment objects
│
├── transform/
│   ├── conflict_mapper/
│   │   └── truth_layer.py            # Maps contradictions across signal fragments
│   ├── deduplicator/
│   │   └── semantic_fusion.py        # Reduces redundancy via semantic fusion
│   └── result_weaver/
│       ├── uncertainty_preserver.py  # Maintains uncertainty as first-class data
│       └── response_weaver.py        # Merges signals into Weaved Cognitive Response
│
├── api/
│   ├── search_handler.py             # Receives query, invokes Cognition Flow
│   └── response_builder.py           # Translates Cognitive Response to API Contract
│
├── config/
│   └── system_constants.py           # Atomic configuration variables
│
└── main.py                           # Application entry point
```

## 2. CORE SYSTEM DESIGN & PHILOSOPHY

The system Abandons traditional IR paradigms.
- **The Query is not a String**: It is treated as an *Intent Vector* accompanied by a *Semantic Pressure Field* and a *Context Drift Map*.
- **Execution is not Linear**: It utilizes *recursive evaluation loops*, *adaptive branching execution*, and *feedback re-injection cycles*.
- **Relevance is not a Score**: It is defined by *intent alignment strength*, *contradiction suppression*, *semantic resonance*, *temporal coherence*, and *trust-field gravity*.

## 3. SEARCH FLOW (THE ALGORITHM)

1. **Intent Distillation Layer**: Converts the user's raw string into a multi-dimensional intent object.
2. **Signal Expansion Layer**: Projects the intent into semantic fields (bypassing keyword matching).
3. **Retrieval Swarm Layer**: Dispatches independent agents asynchronously to gather raw signal fragments.
4. **Conflict Mapping Layer**: Cross-references fragments to detect contradictions and establish truth layers.
5. **Cognitive Ranking Engine**: Computes absolute relevance using a multi-factor logic system.
6. **Result Weaving Layer**: Compresses fragments into a *Weaved Cognitive Response Object*, merging data while preserving uncertainty.

## 4. EXECUTION FLOW DIAGRAM

```text
[API: search_handler] -> Raw String
       ↓
[Intent Distillation] -> (Intent Vector, Context Drift Map)
       ↓
[Signal Expansion]    -> Semantic Pressure Fields
       ↓
       +----------------------- [Retrieval Swarm] -----------------------+
       |                                                                 |
 [WebSignalAgent]  [KnowledgeDriftAgent]  [ContextHarvester]  [LiveStreamAgent]
       |                                                                 |
       +---------------------- (Raw Signal Fragments) -------------------+
       ↓
[Conflict Mapping]    -> Truth Layers & Contradiction Detection
       ↓
[Cognitive Ranking]   -> (Resonance, Gravity, Decay, Alignment, Stability)
       ↓
[Result Weaving]      -> Semantic Fusion & Uncertainty Preservation
       ↓
[API: response_builder] -> Formats to Legacy JSON API Contract
```

## 5. KEY FUNCTION DESIGN SNIPPETS

### A. Intent Distillation (`core/brain/intent_distiller.py`)
```python
from dataclasses import dataclass
from typing import List

@dataclass
class IntentVector:
    primary_axis: str
    semantic_pressure: float
    drift_tolerance: float

async def distill_intent(raw_query: str) -> IntentVector:
    """
    Converts raw query string into a multi-dimensional intent object.
    Does NOT execute search; only maps the cognitive boundary.
    """
    primary_axis = _extract_primary_axis(raw_query)
    pressure = _calculate_semantic_pressure(raw_query)
    tolerance = _calculate_drift_tolerance(raw_query)
    
    return IntentVector(
        primary_axis=primary_axis,
        semantic_pressure=pressure,
        drift_tolerance=tolerance
    )
```

### B. Cognitive Ranking (`ranking/cognitive_ranker.py`)
```python
from dataclasses import dataclass
from ..ranking.semantic_weight.resonance_calc import compute_resonance
from ..ranking.conflict.contradiction_layer import compute_contradiction_penalty
from ..ranking.trust.gravity_field import compute_gravity

@dataclass
class CognitiveScore:
    final_relevance: float
    uncertainty_index: float

async def compute_cognitive_relevance(signal_fragment: dict, intent: 'IntentVector') -> CognitiveScore:
    """
    Computes custom multi-factor logic for a signal fragment.
    Never uses BM25/TF-IDF. Operates purely on resonance and gravity.
    """
    resonance = await compute_resonance(signal_fragment, intent)
    penalty = await compute_contradiction_penalty(signal_fragment)
    gravity = await compute_gravity(signal_fragment)
    
    relevance = (resonance * gravity) - penalty
    uncertainty = 1.0 - (gravity / (penalty + 1.0))
    
    return CognitiveScore(final_relevance=relevance, uncertainty_index=uncertainty)
```

### C. Retrieval Swarm Layer (`retrieval/fetch_agents/web_signal_agent.py`)
```python
import asyncio
from typing import List

async def harvest_web_signals(semantic_field: dict) -> List[dict]:
    """
    Operates independently to fetch raw signals from open web nodes.
    Returns signal fragments, NOT finalized results.
    """
    target_nodes = _allocate_nodes(semantic_field)
    
    tasks = [_extract_signal_fragment(node) for node in target_nodes]
    fragments = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [f for f in fragments if isinstance(f, dict)]
```

### D. Result Weaving (`transform/result_weaver/response_weaver.py`)
```python
from typing import List, Dict, Any

async def weave_cognitive_response(ranked_fragments: List[dict], truth_layers: dict) -> Dict[str, Any]:
    """
    Merges conflicting results and reduces redundancy using semantic fusion.
    Output is the Weaved Cognitive Response Object.
    """
    weaved_response = {
        "primary_synthesis": [],
        "truth_divergence": [],
        "uncertainty_matrix": truth_layers
    }
    
    for fragment in ranked_fragments:
        if _is_redundant(fragment, weaved_response["primary_synthesis"]):
            weaved_response["primary_synthesis"] = _fuse_semantics(weaved_response["primary_synthesis"], fragment)
        elif _is_contradiction(fragment, truth_layers):
            weaved_response["truth_divergence"].append(fragment)
        else:
            weaved_response["primary_synthesis"].append(fragment)
            
    return weaved_response
```

### E. API Response Builder (`api/response_builder.py`)
```python
from typing import Dict, Any

def build_legacy_api_contract(weaved_response: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Translates the advanced Weaved Cognitive Response Object back into the
    strict JSON structure required by the untouched frontend.
    """
    results = []
    
    # Flatten the synthesis back into standard result blocks
    for synthetic_node in weaved_response["primary_synthesis"]:
        results.append({
            "title": synthetic_node.get("resolved_title", ""),
            "url": synthetic_node.get("origin_gravity_node", ""),
            "content": synthetic_node.get("fused_content", ""),
            "parsed_url": ["https", synthetic_node.get("origin_domain", ""), "", "", "", ""]
        })
        
    return {
        "query": query,
        "number_of_results": len(results),
        "results": results,
        "answers": [],
        "suggestions": []
    }
```
