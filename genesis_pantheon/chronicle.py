"""Memory management for GenesisPantheon personas."""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field

from genesis_pantheon.schema import Signal


class Chronicle(BaseModel):
    """Message history storage indexed by directive type.

    Provides efficient retrieval by role, directive/action type,
    or keyword search across all stored signals.
    """

    storage: list[Signal] = Field(default_factory=list)
    index: dict = Field(
        default_factory=lambda: defaultdict(list)
    )

    model_config = {"arbitrary_types_allowed": True}

    def add(self, signal: Signal) -> None:
        """Append a single signal to the chronicle.

        Args:
            signal: Signal to store.
        """
        self.storage.append(signal)
        self.index[signal.cause_by].append(signal)

    def add_batch(self, signals: list[Signal]) -> None:
        """Append multiple signals at once.

        Args:
            signals: Iterable of Signal objects to add.
        """
        for signal in signals:
            self.add(signal)

    def get(self, k: int = 0) -> list[Signal]:
        """Return stored signals.

        Args:
            k: If positive, return the most recent *k* signals.
               If 0 (default), return all signals.

        Returns:
            List of Signal objects.
        """
        if k > 0:
            return self.storage[-k:]
        return list(self.storage)

    def get_by_role(self, role: str) -> list[Signal]:
        """Return signals whose role matches the given string.

        Args:
            role: Role string to filter by (e.g. ``"user"``).

        Returns:
            Filtered list of Signal objects.
        """
        return [s for s in self.storage if s.role == role]

    def get_by_actions(self, actions: set) -> list[Signal]:
        """Return signals caused by any of the given action types.

        Args:
            actions: Set of action/directive name strings.

        Returns:
            Matching Signal objects in insertion order.
        """
        results: list[Signal] = []
        for action in actions:
            results.extend(self.index.get(action, []))
        # Preserve insertion order, deduplicate by id
        seen: set = set()
        ordered: list[Signal] = []
        for s in self.storage:
            if s.id not in seen and s in results:
                seen.add(s.id)
                ordered.append(s)
        return ordered

    def try_recall(self, keyword: str) -> list[Signal]:
        """Full-text search for signals containing a keyword.

        Args:
            keyword: Case-insensitive search term.

        Returns:
            Signals whose content contains the keyword.
        """
        kw = keyword.lower()
        return [
            s for s in self.storage if kw in s.content.lower()
        ]

    def clear(self) -> None:
        """Remove all signals from the chronicle."""
        self.storage.clear()
        self.index.clear()

    def count(self) -> int:
        """Return the total number of stored signals.

        Returns:
            Integer count.
        """
        return len(self.storage)

    def latest(self) -> Signal | None:
        """Return the most recently added signal, or None.

        Returns:
            Most recent Signal or None if empty.
        """
        return self.storage[-1] if self.storage else None


__all__ = ["Chronicle"]
