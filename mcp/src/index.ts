#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import axios from "axios";
import { z } from "zod";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

const server = new McpServer({
  name: "incident-analyzer-server",
  version: "1.0.0",
});

const axiosInstance = axios.create({ baseURL: API_BASE_URL });

type TextContent = {
  content: [
    {
      type: "text";
      text: string;
    }
  ];
  isError?: boolean;
};

function handleAxiosError(error: unknown): TextContent {
  if (axios.isAxiosError(error)) {
    return {
      content: [
        {
          type: "text",
          text: `API error: ${error.response?.data.message ?? error.message}`,
        },
      ],
      isError: true,
    };
  }
  throw error;
}

// Tool: Get Incidents
server.registerTool(
  "get_incidents",
  {
    title: "Get Incidents",
    description: "Get all incidents",
    inputSchema: {}, // no inputs
  },
  async (): Promise<TextContent> => {
    try {
      const response = await axiosInstance.get("/api/incidents");
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Tool: Add Incident
server.registerTool(
  "add_incident",
  {
    title: "Add Incident",
    description: "Add a new incident",
    inputSchema: {
      incident: z.object({
        incident_id: z.string(),
        timestamp: z.string(),
        category: z.string(),
        severity: z.string(),
        description: z.string(),
        root_cause: z.string().nullable().optional(),
        resolution: z.string().nullable().optional(),
        affected_components: z.array(z.string()).nullable().optional(),
        impact: z.string().nullable().optional(),
        resolution_time_mins: z.number(),
      }),
    },
  },
  async ({ incident }): Promise<TextContent> => {
    try {
      const response = await axiosInstance.post("/api/incidents", incident);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Tool: Analyze Root Cause
server.registerTool(
  "analyze_root_cause",
  {
    title: "Analyze Root Cause",
    description: "Analyze root cause of an incident",
    inputSchema: {
      query: z.string(),
      k: z.number().default(5),
    },
  },
  async ({ query, k }): Promise<TextContent> => {
    try {
      const response = await axiosInstance.post("/api/analyze/root-cause", { query, k });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Tool: Analyze Patterns
server.registerTool(
  "analyze_patterns",
  {
    title: "Analyze Patterns",
    description: "Analyze patterns across incidents",
    inputSchema: {
      query: z.string(),
      k: z.number().default(5),
    },
  },
  async ({ query, k }): Promise<TextContent> => {
    try {
      const response = await axiosInstance.post("/api/analyze/patterns", { query, k });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Tool: Search Incidents
server.registerTool(
  "search_incidents",
  {
    title: "Search Incidents",
    description: "Search for similar incidents",
    inputSchema: {
      query: z.string(),
      k: z.number().default(5),
    },
  },
  async ({ query, k }): Promise<TextContent> => {
    try {
      const response = await axiosInstance.get("/api/search", { params: { query, k } });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Tool: Get Stats
server.registerTool(
  "get_stats",
  {
    title: "Get Stats",
    description: "Get incident statistics",
    inputSchema: {}, // no inputs
  },
  async (): Promise<TextContent> => {
    try {
      const response = await axiosInstance.get("/api/incidents/stats");
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error) {
      return handleAxiosError(error);
    }
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log("Incident Analyzer MCP server running on stdio");
}

main().catch(console.error);
