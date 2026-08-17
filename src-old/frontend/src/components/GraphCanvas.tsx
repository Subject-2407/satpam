import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import type { Core, ElementDefinition } from "cytoscape";
import { riskColor } from "../lib/risk";
import { safeLabel } from "../lib/format";
import type { GraphNode, GraphRelationship, NodeRef, RiskLevel } from "../types/api";

interface GraphCanvasProps {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  rootId?: string;
  // Tipe node yang disembunyikan (filter sisi klien).
  hiddenTypes?: Set<string>;
  onSelectNode?: (node: NodeRef & { label?: string }) => void;
}

export function GraphCanvas({
  nodes,
  relationships,
  rootId,
  hiddenTypes,
  onSelectNode,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const onSelectRef = useRef(onSelectNode);
  onSelectRef.current = onSelectNode;

  useEffect(() => {
    if (!containerRef.current) return;

    const visibleNodes = nodes.filter((n) => !hiddenTypes?.has(n.type));
    const visibleIds = new Set(visibleNodes.map((n) => n.id));

    const elements: ElementDefinition[] = [
      ...visibleNodes.map((n) => ({
        data: {
          id: n.id,
          label: safeLabel(n.label ?? n.id),
          type: n.type,
          color: riskColor(n.riskLevel as RiskLevel | undefined),
          isRoot: n.id === rootId ? 1 : 0,
        },
      })),
      ...relationships
        .filter((r) => visibleIds.has(r.from.id) && visibleIds.has(r.to.id))
        .map((r) => ({
          data: { id: r.id, source: r.from.id, target: r.to.id, label: r.type },
        })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "data(color)",
            label: "data(label)",
            "font-size": "9px",
            color: "#1e293b",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 4,
            width: 22,
            height: 22,
            "border-width": 1,
            "border-color": "#ffffff",
          },
        },
        {
          selector: "node[isRoot = 1]",
          style: { width: 34, height: 34, "border-width": 3, "border-color": "#2563eb" },
        },
        {
          selector: "edge",
          style: {
            width: 1.4,
            "line-color": "#cbd5e1",
            "target-arrow-color": "#cbd5e1",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": "7px",
            color: "#94a3b8",
            "text-rotation": "autorotate",
          },
        },
        {
          selector: "node:selected",
          style: { "border-width": 3, "border-color": "#2563eb" },
        },
      ],
      layout: { name: "cose", animate: false, padding: 30, nodeRepulsion: 6000 } as cytoscape.LayoutOptions,
      minZoom: 0.2,
      maxZoom: 2.5,
      wheelSensitivity: 0.2,
    });

    cy.on("tap", "node", (evt) => {
      const data = evt.target.data();
      onSelectRef.current?.({ id: data.id, type: data.type, label: data.label });
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [nodes, relationships, rootId, hiddenTypes]);

  return <div ref={containerRef} className="h-[540px] w-full rounded-lg bg-slate-50" />;
}
