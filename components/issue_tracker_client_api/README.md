# issue_tracker_client_api

A Python package that defines an **abstract contract** for interacting with an issue tracker (e.g., Trello, etc.).

This package does **not** implement a concrete integration. Instead, it provides:

- Immutable data models (`Issue`, `Comment`)
- An abstract interface (`IssueTrackerClient`)
- A simple global factory registration system (`register`, `get_client`)

It allows your application to depend only on a stable interface, while concrete implementations can be swapped in at runtime.

---

## Why This Exists

Applications often need to integrate with an issue tracker but shouldn't depend directly on a specific provider.

This package enables:

- Clean separation of concerns  
- Testable architecture  

---
