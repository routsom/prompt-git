/**
 * prompt-git TypeScript SDK — read-only access to prompt-git repositories.
 *
 * This SDK can read .promptgit/store.db and provide typed access to
 * commits, blobs, trees, and tags. It does NOT support write operations.
 */

export { PromptRepo } from "./repo";
export { Blob, Commit, Tag, Tree } from "./objects";
