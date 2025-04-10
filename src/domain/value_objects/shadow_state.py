"""
Shadow State value object representing a device's state properties.

This immutable object encapsulates device state data for shadow synchronization.
"""
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ShadowState:
    """Value object representing a device's state properties.

    This immutable object holds device state properties and provides
    methods to update state safely without mutation.

    Attributes:
        state: Dictionary of state properties and values
    """

    state: Dict[str, Any]

    def __post_init__(self):
        """Validate the shadow state after initialization."""
        # Ensure state is a dictionary
        if not isinstance(self.state, dict):
            raise ValueError(f"State must be a dictionary, got {type(self.state)}")

    def update(self, updates: Dict[str, Any]) -> "ShadowState":
        """Create a new shadow state with updated properties.

        This method creates a new ShadowState instance with the updated properties
        to maintain immutability.

        Args:
            updates: Dictionary of properties to update

        Returns:
            A new ShadowState instance with updated properties
        """
        # Create a copy of the current state and apply updates
        new_state = {**self.state, **updates}

        # Create and return a new instance
        return ShadowState(state=new_state)

    def get(self, key: str, default=None) -> Any:
        """Get a property value from the state.

        Args:
            key: Property name to retrieve
            default: Default value if property doesn't exist

        Returns:
            The property value or default if not found
        """
        return self.state.get(key, default)

    def contains(self, key: str) -> bool:
        """Check if a property exists in the state.

        Args:
            key: Property name to check

        Returns:
            True if property exists, False otherwise
        """
        return key in self.state
