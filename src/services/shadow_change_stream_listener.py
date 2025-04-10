"""
MongoDB Change Stream Listener for Device Shadows.

This module implements a change stream listener that monitors changes to device shadows
in MongoDB and notifies registered handlers when changes occur.
"""
import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from bson.timestamp import Timestamp
from motor.motor_asyncio import AsyncIOMotorClient


class ShadowChangeEvent:
    """
    Represents a change event for a device shadow in MongoDB.

    This class encapsulates the data from a MongoDB change event and provides
    a consistent interface for handlers to process shadow changes.
    """

    def __init__(
        self,
        device_id: str,
        operation_type: str,
        full_document: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ):
        """
        Initialize a ShadowChangeEvent.

        Args:
            device_id: The ID of the device associated with the shadow.
            operation_type: The type of operation (insert, update, delete).
            full_document: The complete shadow document after the change.
            changed_fields: Fields that were changed in an update operation.
            timestamp: The timestamp of the change event.
        """
        self.device_id = device_id
        self.operation_type = operation_type
        self.full_document = full_document
        self.changed_fields = changed_fields

        if timestamp is None:
            timestamp = datetime.now().isoformat()
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary representation.

        Returns:
            A dictionary containing the event data.
        """
        return {
            "device_id": self.device_id,
            "operation_type": self.operation_type,
            "full_document": self.full_document,
            "changed_fields": self.changed_fields,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShadowChangeEvent":
        """
        Create a ShadowChangeEvent from a dictionary.

        Args:
            data: A dictionary containing the event data.

        Returns:
            A new ShadowChangeEvent instance.
        """
        return cls(
            device_id=data.get("device_id"),
            operation_type=data.get("operation_type"),
            full_document=data.get("full_document"),
            changed_fields=data.get("changed_fields"),
            timestamp=data.get("timestamp"),
        )


class ShadowChangeStreamListener:
    """
    Listens for changes to device shadows in MongoDB using change streams.

    This class connects to a MongoDB collection and sets up a change stream
    to monitor changes to device shadows. When changes occur, registered
    handlers are notified with ShadowChangeEvent objects.
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "iotsphere",
        collection_name: str = "device_shadows",
    ):
        """
        Initialize the ShadowChangeStreamListener.

        Args:
            mongo_uri: URI for connecting to MongoDB.
            db_name: Name of the database containing shadow data.
            collection_name: Name of the collection containing shadow data.
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.mongo_client = None
        self.change_stream = None
        self.initialized = False
        self.is_listening = False
        self.event_handlers = []

    async def _connect(self) -> None:
        """
        Connect to MongoDB.

        Establishes a connection to MongoDB using the configured URI.
        """
        self.mongo_client = AsyncIOMotorClient(self.mongo_uri)

    async def initialize(self) -> None:
        """
        Initialize the change stream listener.

        Connects to MongoDB and sets up a change stream for the shadows collection.
        Must be called before start_listening.
        """
        if self.mongo_client is None:
            await self._connect()

        # Get the database and collection
        db = self.mongo_client[self.db_name]
        collection = db[self.collection_name]

        # Create a change stream on the collection
        self.change_stream = collection.watch()
        self.initialized = True

    async def start_listening(self) -> None:
        """
        Start listening for changes on the change stream.

        Begins processing events from the change stream and notifying handlers.
        The initialize method must be called before this method.

        Raises:
            RuntimeError: If the listener has not been initialized.
        """
        if not self.initialized:
            raise RuntimeError(
                "ShadowChangeStreamListener must be initialized before starting"
            )

        self.is_listening = True
        await self._process_change_events()

    async def stop_listening(self) -> None:
        """
        Stop listening for changes on the change stream.

        Stops processing events and closes the change stream.
        """
        if self.change_stream:
            await self.change_stream.close()
        self.is_listening = False

    async def _process_change_events(self) -> None:
        """
        Process events from the change stream.

        Listens for events from the change stream and forwards them to handlers.
        This method runs in a loop until stop_listening is called.
        """
        while self.is_listening:
            try:
                async for change_event in self.change_stream:
                    await self._handle_change_event(change_event)
            except Exception as e:
                # Log error and attempt to reconnect
                print(f"Error processing change stream: {e}")
                if self.is_listening:
                    # Sleep briefly before reconnecting
                    await asyncio.sleep(1)
                    # Attempt to reinitialize the change stream
                    try:
                        await self.initialize()
                    except Exception as reconnect_error:
                        print(f"Error reconnecting to change stream: {reconnect_error}")
                        self.is_listening = False

    async def _handle_change_event(self, change_event: Dict[str, Any]) -> None:
        """
        Handle a change event from the change stream.

        Extracts data from the change event, creates a ShadowChangeEvent,
        and notifies registered handlers.

        Args:
            change_event: A MongoDB change event dictionary.
        """
        # Extract device ID
        device_id = self._extract_device_id(change_event)

        # Create a ShadowChangeEvent
        event = self._create_shadow_change_event(change_event)

        # Notify handlers
        await self._notify_handlers(event)

    def _extract_device_id(self, change_event: Dict[str, Any]) -> str:
        """
        Extract the device ID from a change event.

        For insert/replace operations, the device ID is in the _id field of the full document.
        For update/delete operations, the device ID is in the documentKey.

        Args:
            change_event: A MongoDB change event dictionary.

        Returns:
            The extracted device ID as a string.
        """
        operation_type = change_event.get("operationType")

        if operation_type in ["insert", "replace"]:
            return change_event.get("fullDocument", {}).get("_id")
        else:  # update, delete
            return change_event.get("documentKey", {}).get("_id")

    def _extract_timestamp(self, change_event: Dict[str, Any]) -> str:
        """
        Extract the timestamp from a change event.

        Attempts to get the timestamp from the full document or generates a new one.

        Args:
            change_event: A MongoDB change event dictionary.

        Returns:
            A timestamp string in ISO format.
        """
        # Try to get timestamp from the full document
        if (
            "fullDocument" in change_event
            and "timestamp" in change_event["fullDocument"]
        ):
            return change_event["fullDocument"]["timestamp"]

        # Generate a new timestamp
        return datetime.now().isoformat()

    def _create_shadow_change_event(
        self, change_event: Dict[str, Any]
    ) -> ShadowChangeEvent:
        """
        Create a ShadowChangeEvent from a MongoDB change event.

        Args:
            change_event: A MongoDB change event dictionary.

        Returns:
            A ShadowChangeEvent object.
        """
        operation_type = change_event.get("operationType")
        device_id = self._extract_device_id(change_event)
        timestamp = self._extract_timestamp(change_event)

        full_document = None
        changed_fields = None

        if operation_type in ["insert", "replace", "update"]:
            full_document = change_event.get("fullDocument")

        if operation_type == "update":
            changed_fields = change_event.get("updateDescription", {}).get(
                "updatedFields"
            )

        return ShadowChangeEvent(
            device_id=device_id,
            operation_type=operation_type,
            full_document=full_document,
            changed_fields=changed_fields,
            timestamp=timestamp,
        )

    async def _notify_handlers(self, event: ShadowChangeEvent) -> None:
        """
        Notify all registered event handlers of a shadow change event.

        Args:
            event: A ShadowChangeEvent object to send to handlers.
        """
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log error but continue notifying other handlers
                print(f"Error in event handler: {e}")

    def register_event_handler(
        self, handler: Callable[[ShadowChangeEvent], None]
    ) -> None:
        """
        Register a handler to be notified of shadow change events.

        Args:
            handler: A callable that takes a ShadowChangeEvent parameter.
        """
        if handler not in self.event_handlers:
            self.event_handlers.append(handler)

    def unregister_event_handler(
        self, handler: Callable[[ShadowChangeEvent], None]
    ) -> None:
        """
        Unregister a previously registered handler.

        Args:
            handler: The handler to unregister.
        """
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
