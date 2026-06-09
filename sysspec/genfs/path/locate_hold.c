#include "path.h"

/**
 * locate_hold - Traverse a path starting from a locked directory, retaining the lock on the starting directory.
 * @cur:   The starting directory inode (must be locked by caller).
 * @path:  NULL-terminated array of path components.
 *
 * Return: The target inode (locked) on success, NULL on failure.
 *         On success, the lock on @cur is retained. On failure, @cur remains locked.
 */
struct inode* locate_hold(struct inode *cur, char *path[])
{
    // If path is empty, return the current inode itself (already locked).
    if (path == NULL || path[0] == NULL) {
        return cur;
    }

    char *first = path[0];
    char **remaining = &path[1];

    // Look up the first component using inode_find.
    // Note: inode_find will release the lock on cur and acquire the lock on the found inode.
    struct inode *next = inode_find(cur, first);

    if (next == NULL) {
        // Component not found; must re-acquire lock on cur before returning.
        lock(cur);
        return NULL;
    }

    // At this point, next is locked and cur is unlocked.
    // Delegate the rest of the traversal to locate.
    // locate will release next and lock the final target.
    struct inode *target = locate(next, remaining);

    // Re-acquire the lock on cur to satisfy the post-condition.
    lock(cur);

    return target;
}