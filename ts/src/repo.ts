/**
 * PromptRepo — read-only TypeScript interface to a prompt-git repository.
 *
 * Opens the SQLite database and provides typed access to objects.
 * Requires a SQLite library like better-sqlite3.
 */

import type { Blob, Commit, Tag, Tree } from "./objects";

export class PromptRepo {
  private dbPath: string;

  constructor(rootPath: string) {
    this.dbPath = `${rootPath}/.promptgit/store.db`;
  }

  /**
   * Get HEAD commit hash.
   * Implementation note: requires better-sqlite3 or similar.
   */
  async getHead(): Promise<string | null> {
    // Placeholder — needs SQLite driver
    throw new Error("Not implemented: requires better-sqlite3");
  }

  /**
   * Get a commit by hash.
   */
  async getCommit(hash: string): Promise<Commit | null> {
    throw new Error("Not implemented: requires better-sqlite3");
  }

  /**
   * Get a blob by hash.
   */
  async getBlob(hash: string): Promise<Blob | null> {
    throw new Error("Not implemented: requires better-sqlite3");
  }

  /**
   * Get a tree by hash.
   */
  async getTree(hash: string): Promise<Tree | null> {
    throw new Error("Not implemented: requires better-sqlite3");
  }

  /**
   * Get commit log.
   */
  async log(limit: number = 20): Promise<Commit[]> {
    throw new Error("Not implemented: requires better-sqlite3");
  }
}
