from abc import ABC, abstractmethod
from typing import Any, Dict, List

class DatabaseInterface(ABC):
    @abstractmethod
    async def create_entry(self, entry_data: Dict[str, Any]) -> None:
        """Create a new entry in the database."""
        pass
    
    @abstractmethod
    async def get_entries(self) -> List[Dict[str, Any]]:
        """Retrieve all entries from the database."""
        pass

    @abstractmethod
    async def get_entry(self, entry_id: str) -> Dict[str, Any]:
        """Retrieve a specific entry by entry_id from the database."""
        pass

    @abstractmethod
    async def update_entry(self, entry_id: str, updated_data: Dict[str, Any]) -> None:
        """Update an existing entry in the database."""
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> None:
        """Delete a specific entry by entry_id from the database."""
        pass

    @abstractmethod 
    async def delete_all_entries(self) -> None:
        """Delete all entries from the database."""
        pass