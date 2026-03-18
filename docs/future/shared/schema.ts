import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, timestamp, pgEnum } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const returnStatusEnum = pgEnum("return_status", [
  "initiated",
  "pickup_scheduled",
  "picked_up",
  "in_transit",
  "received",
  "inspecting",
  "refund_initiated",
  "refund_completed",
  "rejected",
]);

export const platformEnum = pgEnum("platform", [
  "amazon",
  "flipkart",
  "myntra",
  "meesho",
  "ajio",
  "nykaa",
  "other",
]);

export const returnReasonEnum = pgEnum("return_reason", [
  "wrong_item",
  "damaged",
  "defective",
  "size_issue",
  "quality_issue",
  "not_as_described",
  "changed_mind",
  "other",
]);

export const orderStatusEnum = pgEnum("order_status", [
  "active",
  "expiring_soon",
  "expired",
  "return_initiated",
  "returned",
]);

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const returnRequests = pgTable("return_requests", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  orderId: text("order_id").notNull(),
  productName: text("product_name").notNull(),
  platform: platformEnum("platform").notNull(),
  reason: returnReasonEnum("reason").notNull(),
  status: returnStatusEnum("status").notNull().default("initiated"),
  amount: integer("amount").notNull(),
  imageUrl: text("image_url"),
  description: text("description"),
  trackingId: text("tracking_id"),
  pickupDate: timestamp("pickup_date"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

export const statusHistory = pgTable("status_history", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  returnRequestId: varchar("return_request_id").notNull(),
  status: returnStatusEnum("status").notNull(),
  note: text("note"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const orders = pgTable("orders", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  orderId: text("order_id").notNull(),
  productName: text("product_name").notNull(),
  platform: text("platform").notNull(),
  status: orderStatusEnum("status").notNull().default("active"),
  amount: integer("amount"),
  orderDate: timestamp("order_date"),
  returnDeadline: timestamp("return_deadline"),
  emailSubject: text("email_subject"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertReturnRequestSchema = createInsertSchema(returnRequests).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  trackingId: true,
  pickupDate: true,
  status: true,
});

export const insertStatusHistorySchema = createInsertSchema(statusHistory).omit({
  id: true,
  createdAt: true,
});

export const insertOrderSchema = createInsertSchema(orders).omit({
  id: true,
  createdAt: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type ReturnRequest = typeof returnRequests.$inferSelect;
export type InsertReturnRequest = z.infer<typeof insertReturnRequestSchema>;
export type StatusHistory = typeof statusHistory.$inferSelect;
export type InsertStatusHistory = z.infer<typeof insertStatusHistorySchema>;
export type Order = typeof orders.$inferSelect;
export type InsertOrder = z.infer<typeof insertOrderSchema>;
