import {
  type User,
  type InsertUser,
  type ReturnRequest,
  type InsertReturnRequest,
  type StatusHistory,
  type InsertStatusHistory,
  users,
  returnRequests,
  statusHistory,
} from "@shared/schema";
import { eq, desc, ilike } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import pg from "pg";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  getAllReturns(): Promise<ReturnRequest[]>;
  getReturnById(id: string): Promise<ReturnRequest | undefined>;
  getReturnsByOrderId(orderId: string): Promise<ReturnRequest[]>;
  createReturn(data: InsertReturnRequest): Promise<ReturnRequest>;
  updateReturnStatus(id: string, status: string): Promise<ReturnRequest | undefined>;

  getStatusHistory(returnRequestId: string): Promise<StatusHistory[]>;
  addStatusHistory(data: InsertStatusHistory): Promise<StatusHistory>;
}

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
});
const db = drizzle(pool);

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }

  async getAllReturns(): Promise<ReturnRequest[]> {
    return db.select().from(returnRequests).orderBy(desc(returnRequests.createdAt));
  }

  async getReturnById(id: string): Promise<ReturnRequest | undefined> {
    const [ret] = await db.select().from(returnRequests).where(eq(returnRequests.id, id));
    return ret;
  }

  async getReturnsByOrderId(orderId: string): Promise<ReturnRequest[]> {
    return db
      .select()
      .from(returnRequests)
      .where(ilike(returnRequests.orderId, `%${orderId}%`))
      .orderBy(desc(returnRequests.createdAt));
  }

  async createReturn(data: InsertReturnRequest): Promise<ReturnRequest> {
    const [ret] = await db.insert(returnRequests).values(data).returning();
    await db.insert(statusHistory).values({
      returnRequestId: ret.id,
      status: "initiated",
      note: "Return request created",
    });
    return ret;
  }

  async updateReturnStatus(id: string, status: string): Promise<ReturnRequest | undefined> {
    const [ret] = await db
      .update(returnRequests)
      .set({ status: status as any, updatedAt: new Date() })
      .where(eq(returnRequests.id, id))
      .returning();
    return ret;
  }

  async getStatusHistory(returnRequestId: string): Promise<StatusHistory[]> {
    return db
      .select()
      .from(statusHistory)
      .where(eq(statusHistory.returnRequestId, returnRequestId))
      .orderBy(statusHistory.createdAt);
  }

  async addStatusHistory(data: InsertStatusHistory): Promise<StatusHistory> {
    const [entry] = await db.insert(statusHistory).values(data).returning();
    return entry;
  }
}

export const storage = new DatabaseStorage();
