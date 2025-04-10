"""
MongoDB Change Data Capture (CDC) Event Handler.

This module implements a handler for MongoDB Change Data Capture events,
converting database change events into domain events and publishing them
through the message broker.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from pymongo.errors import PyMongoError

from src.domain.events.device_shadow_events import (
    DeviceShadowCreatedEvent,
    DeviceShadowDeletedEvent,
    DeviceShadowDesiredStateUpdatedEvent,
    DeviceShadowReportedStateUpdatedEvent,
)
from src.domain.events.water_heater_events import (
    WaterHeaterCreatedEvent,
    WaterHeaterDeletedEvent,
    WaterHeaterUpdatedEvent,
)
from src.gateways.message_broker import MessageBroker

logger = logging.getLogger(__name__)


class MongoDBCDCHandler:
    """Handler for MongoDB Change Data Capture (CDC) events.

    This class monitors the MongoDB change streams and converts database change events
    into domain events that are published to the message broker. It follows the
    Clean Architecture principle of keeping external interfaces in the adapter layer.
    """

    def __init__(
        self,
        connection_string: str,
        database_name: str,
        message_broker: MessageBroker,
        collections_to_watch: Optional[List[str]] = None,
    ):
        """Initialize the MongoDB CDC Handler.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to watch
            message_broker: Message broker to publish events to
            collections_to_watch: List of collections to watch for changes (if None, watch all)
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.message_broker = message_broker
        self.collections_to_watch = collections_to_watch or [
            "water_heaters",
            "device_shadows",
        ]

        self.client = None
        self.watches = {}
        self.is_watching = False

    async def start(self) -> None:
        """Start watching for MongoDB change events.

        This method initializes the MongoDB client and starts watching for change events
        on the specified collections.
        """
        if self.is_watching:
            return

        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            db = self.client[self.database_name]

            # Start a watch for each collection
            tasks = []
            for collection_name in self.collections_to_watch:
                collection = db[collection_name]
                pipeline = []  # Empty pipeline to capture all changes

                # Create a change stream for the collection
                change_stream = collection.watch(pipeline, full_document="updateLookup")

                # Start a task to process events from this stream
                task = asyncio.create_task(
                    self._process_change_stream(collection_name, change_stream)
                )
                tasks.append(task)
                self.watches[collection_name] = (change_stream, task)

            self.is_watching = True
            logger.info(f"Started watching collections: {self.collections_to_watch}")

        except PyMongoError as e:
            logger.error(f"Failed to start MongoDB CDC handler: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop watching for MongoDB change events.

        This method stops all change stream watchers and cleans up resources.
        """
        if not self.is_watching:
            return

        # Cancel all watch tasks
        for collection_name, (change_stream, task) in self.watches.items():
            try:
                change_stream.close()
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                logger.error(f"Error closing change stream for {collection_name}: {e}")

        self.watches.clear()

        # Close the client connection
        if self.client:
            self.client.close()
            self.client = None

        self.is_watching = False
        logger.info("Stopped MongoDB CDC handler")

    async def _process_change_stream(self, collection_name: str, change_stream) -> None:
        """Process changes from a MongoDB change stream.

        This method continually reads from a change stream and processes the events.

        Args:
            collection_name: Name of the collection being watched
            change_stream: MongoDB change stream to process
        """
        try:
            async for change in change_stream:
                try:
                    await self._handle_change_event(collection_name, change)
                except Exception as e:
                    logger.error(
                        f"Error handling change event for {collection_name}: {e}"
                    )
        except PyMongoError as e:
            if not self.is_watching:
                # If we're shutting down, this is expected
                return

            logger.error(f"Error in change stream for {collection_name}: {e}")
            # Restart the watch if it was unexpected
            await self._restart_watch(collection_name)
        except asyncio.CancelledError:
            # Task was cancelled, just exit
            pass
        except Exception as e:
            logger.error(
                f"Unexpected error in change stream for {collection_name}: {e}"
            )
            if self.is_watching:
                await self._restart_watch(collection_name)

    async def _restart_watch(self, collection_name: str) -> None:
        """Restart a watch for a specific collection.

        Args:
            collection_name: Name of the collection to restart watching
        """
        try:
            # Remove the old watch
            if collection_name in self.watches:
                old_stream, old_task = self.watches.pop(collection_name)
                try:
                    old_stream.close()
                    old_task.cancel()
                except:
                    pass

            # Start a new watch
            if self.is_watching and self.client:
                db = self.client[self.database_name]
                collection = db[collection_name]
                pipeline = []

                # Create a new change stream
                change_stream = collection.watch(pipeline, full_document="updateLookup")

                # Start a new task
                task = asyncio.create_task(
                    self._process_change_stream(collection_name, change_stream)
                )
                self.watches[collection_name] = (change_stream, task)
                logger.info(f"Restarted watch for collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to restart watch for {collection_name}: {e}")

    async def _handle_change_event(
        self, collection_name: str, change_event: Dict[str, Any]
    ) -> None:
        """Handle a single change event from MongoDB.

        This method converts MongoDB change events into domain events and publishes them
        to the message broker.

        Args:
            collection_name: Name of the collection that changed
            change_event: MongoDB change event
        """
        operation_type = change_event.get("operationType")
        document_key = change_event.get("documentKey", {})
        document_id = document_key.get("_id")

        # Full document is available for inserts and updates
        full_document = change_event.get("fullDocument")

        # For updates, we also have information about what changed
        update_description = change_event.get("updateDescription", {})
        updated_fields = update_description.get("updatedFields", {})

        if collection_name == "water_heaters":
            await self._handle_water_heater_change(
                operation_type, document_id, full_document, updated_fields
            )
        elif collection_name == "device_shadows":
            await self._handle_device_shadow_change(
                operation_type, document_id, full_document, updated_fields
            )
        else:
            logger.debug(
                f"Ignoring change event for unhandled collection: {collection_name}"
            )

    async def _handle_water_heater_change(
        self,
        operation_type: str,
        document_id: str,
        full_document: Optional[Dict[str, Any]],
        updated_fields: Dict[str, Any],
    ) -> None:
        """Handle a change event for the water_heaters collection.

        Args:
            operation_type: Type of operation (insert, update, delete)
            document_id: ID of the document that changed
            full_document: Full document (for inserts and updates)
            updated_fields: Fields that were updated (for updates)
        """
        topic = "water-heater-events"

        if operation_type == "insert" and full_document:
            # Water heater created
            event = WaterHeaterCreatedEvent(
                heater_id=document_id,
                timestamp=datetime.now().isoformat(),
                heater_data=full_document,
            )
            self.message_broker.publish_event(topic, event, key=document_id)
            logger.debug(
                f"Published WaterHeaterCreatedEvent for heater_id: {document_id}"
            )

        elif operation_type == "update" and full_document:
            # Water heater updated
            event = WaterHeaterUpdatedEvent(
                heater_id=document_id,
                timestamp=datetime.now().isoformat(),
                heater_data=full_document,
                changed_fields=list(updated_fields.keys()),
            )
            self.message_broker.publish_event(topic, event, key=document_id)
            logger.debug(
                f"Published WaterHeaterUpdatedEvent for heater_id: {document_id}"
            )

        elif operation_type == "delete":
            # Water heater deleted
            event = WaterHeaterDeletedEvent(
                heater_id=document_id, timestamp=datetime.now().isoformat()
            )
            self.message_broker.publish_event(topic, event, key=document_id)
            logger.debug(
                f"Published WaterHeaterDeletedEvent for heater_id: {document_id}"
            )

    async def _handle_device_shadow_change(
        self,
        operation_type: str,
        document_id: str,
        full_document: Optional[Dict[str, Any]],
        updated_fields: Dict[str, Any],
    ) -> None:
        """Handle a change event for the device_shadows collection.

        Args:
            operation_type: Type of operation (insert, update, delete)
            document_id: ID of the document that changed
            full_document: Full document (for inserts and updates)
            updated_fields: Fields that were updated (for updates)
        """
        topic = "device-shadow-events"

        if operation_type == "insert" and full_document:
            # Device shadow created
            event = DeviceShadowCreatedEvent(
                device_id=document_id,
                timestamp=datetime.now().isoformat(),
                shadow_data=full_document,
            )
            self.message_broker.publish_event(topic, event, key=document_id)
            logger.debug(
                f"Published DeviceShadowCreatedEvent for device_id: {document_id}"
            )

        elif operation_type == "update" and full_document:
            # Check what was updated
            desired_updated = any(
                field.startswith("desired.") for field in updated_fields.keys()
            )
            reported_updated = any(
                field.startswith("reported.") for field in updated_fields.keys()
            )

            if desired_updated:
                # Desired state updated
                event = DeviceShadowDesiredStateUpdatedEvent(
                    device_id=document_id,
                    timestamp=datetime.now().isoformat(),
                    shadow_data=full_document,
                    changed_fields=[
                        field.replace("desired.", "")
                        for field in updated_fields.keys()
                        if field.startswith("desired.")
                    ],
                )
                self.message_broker.publish_event(topic, event, key=document_id)
                logger.debug(
                    f"Published DeviceShadowDesiredStateUpdatedEvent for device_id: {document_id}"
                )

            if reported_updated:
                # Reported state updated
                event = DeviceShadowReportedStateUpdatedEvent(
                    device_id=document_id,
                    timestamp=datetime.now().isoformat(),
                    shadow_data=full_document,
                    changed_fields=[
                        field.replace("reported.", "")
                        for field in updated_fields.keys()
                        if field.startswith("reported.")
                    ],
                )
                self.message_broker.publish_event(topic, event, key=document_id)
                logger.debug(
                    f"Published DeviceShadowReportedStateUpdatedEvent for device_id: {document_id}"
                )

        elif operation_type == "delete":
            # Device shadow deleted
            event = DeviceShadowDeletedEvent(
                device_id=document_id, timestamp=datetime.now().isoformat()
            )
            self.message_broker.publish_event(topic, event, key=document_id)
            logger.debug(
                f"Published DeviceShadowDeletedEvent for device_id: {document_id}"
            )

    async def manually_trigger_event(
        self,
        collection_name: str,
        operation_type: str,
        document_id: str,
        full_document: Optional[Dict[str, Any]] = None,
        updated_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Manually trigger a CDC event.

        This method allows for manually triggering a CDC event, which can be useful
        for testing or handling events that were missed.

        Args:
            collection_name: Name of the collection
            operation_type: Type of operation (insert, update, delete)
            document_id: ID of the document
            full_document: Full document data (for inserts and updates)
            updated_fields: Fields that were updated (for updates)
        """
        if not updated_fields:
            updated_fields = {}

        # Create a synthetic change event
        change_event = {
            "operationType": operation_type,
            "documentKey": {"_id": document_id},
            "fullDocument": full_document,
            "updateDescription": {"updatedFields": updated_fields},
        }

        # Process the event
        await self._handle_change_event(collection_name, change_event)
