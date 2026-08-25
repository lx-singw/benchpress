/**
 * Firestore Database Client with Pluggable Adapter Pattern & In-Memory Fallback.
 */

import { TrajectoryStatus } from "@benchpress/telemetry";

export interface TrajectoryDoc {
  trajectoryId: string;
  taskSuite: string;
  taskId: string;
  modelId: string;
  status: TrajectoryStatus;
  budgetLimitUsd: number;
  maxTurns: number;
  currentTurn: number;
  totalCostUsd: number;
  createdAt: string;
  updatedAt: string;
  result?: Record<string, unknown>;
}

export interface IDatabase {
  createTrajectory(doc: TrajectoryDoc): Promise<void>;
  getTrajectory(trajectoryId: string): Promise<TrajectoryDoc | null>;
  updateTrajectory(trajectoryId: string, updates: Partial<TrajectoryDoc>): Promise<void>;
}

class GcpFirestoreAdapter implements IDatabase {
  private db: any;
  private collectionName = "trajectories";

  constructor() {
    const { Firestore } = require("@google-cloud/firestore");
    this.db = new Firestore();
  }

  async createTrajectory(doc: TrajectoryDoc): Promise<void> {
    await this.db.collection(this.collectionName).doc(doc.trajectoryId).set(doc);
  }

  async getTrajectory(trajectoryId: string): Promise<TrajectoryDoc | null> {
    const snap = await this.db.collection(this.collectionName).doc(trajectoryId).get();
    return snap.exists ? (snap.data() as TrajectoryDoc) : null;
  }

  async updateTrajectory(trajectoryId: string, updates: Partial<TrajectoryDoc>): Promise<void> {
    await this.db.collection(this.collectionName).doc(trajectoryId).update({
      ...updates,
      updatedAt: new Date().toISOString(),
    });
  }
}

class InMemoryDatabaseAdapter implements IDatabase {
  private store = new Map<string, TrajectoryDoc>();

  async createTrajectory(doc: TrajectoryDoc): Promise<void> {
    this.store.set(doc.trajectoryId, { ...doc });
  }

  async getTrajectory(trajectoryId: string): Promise<TrajectoryDoc | null> {
    return this.store.get(trajectoryId) || null;
  }

  async updateTrajectory(trajectoryId: string, updates: Partial<TrajectoryDoc>): Promise<void> {
    const current = this.store.get(trajectoryId);
    if (current) {
      this.store.set(trajectoryId, {
        ...current,
        ...updates,
        updatedAt: new Date().toISOString(),
      });
    }
  }
}

let dbInstance: IDatabase | null = null;

export function getDatabase(): IDatabase {
  if (dbInstance) return dbInstance;

  const useMock = process.env.USE_LOCAL_MOCK === "true" || !process.env.GOOGLE_CLOUD_PROJECT;
  if (useMock) {
    dbInstance = new InMemoryDatabaseAdapter();
  } else {
    try {
      dbInstance = new GcpFirestoreAdapter();
    } catch {
      console.warn("[Database] Falling back to InMemoryDatabaseAdapter due to Firestore initialization error");
      dbInstance = new InMemoryDatabaseAdapter();
    }
  }

  return dbInstance;
}
