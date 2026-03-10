import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertReturnRequestSchema } from "@shared/schema";
import { z } from "zod";

const updateStatusSchema = z.object({
  status: z.enum([
    "initiated",
    "pickup_scheduled",
    "picked_up",
    "in_transit",
    "received",
    "inspecting",
    "refund_initiated",
    "refund_completed",
    "rejected",
  ]),
  note: z.string().optional(),
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.get("/api/returns", async (_req, res) => {
    try {
      const returns = await storage.getAllReturns();
      res.json(returns);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch returns" });
    }
  });

  app.get("/api/returns/track/:orderId", async (req, res) => {
    try {
      const returns = await storage.getReturnsByOrderId(req.params.orderId);
      res.json(returns);
    } catch (error) {
      res.status(500).json({ message: "Failed to search returns" });
    }
  });

  app.get("/api/returns/:id", async (req, res) => {
    try {
      const ret = await storage.getReturnById(req.params.id);
      if (!ret) {
        return res.status(404).json({ message: "Return not found" });
      }
      res.json(ret);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch return" });
    }
  });

  app.get("/api/returns/:id/history", async (req, res) => {
    try {
      const history = await storage.getStatusHistory(req.params.id);
      res.json(history);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch history" });
    }
  });

  app.post("/api/returns", async (req, res) => {
    try {
      const parsed = insertReturnRequestSchema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ message: "Invalid data", errors: parsed.error.issues });
      }
      const ret = await storage.createReturn(parsed.data);
      res.status(201).json(ret);
    } catch (error) {
      res.status(500).json({ message: "Failed to create return" });
    }
  });

  app.patch("/api/returns/:id/status", async (req, res) => {
    try {
      const parsed = updateStatusSchema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ message: "Invalid status", errors: parsed.error.issues });
      }
      const { status, note } = parsed.data;
      const ret = await storage.updateReturnStatus(req.params.id, status);
      if (!ret) {
        return res.status(404).json({ message: "Return not found" });
      }
      await storage.addStatusHistory({
        returnRequestId: req.params.id,
        status,
        note: note || null,
      });
      res.json(ret);
    } catch (error) {
      res.status(500).json({ message: "Failed to update status" });
    }
  });

  return httpServer;
}
