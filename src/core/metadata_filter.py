from typing import List, Dict, Any, Optional
from datetime import datetime

class MetadataFilter:
    """
    Advanced metadata filtering and transformation utility
    """

    @staticmethod
    def filter_by_date(
        documents: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by date range

        Args:
            documents: List of document dictionaries
            start_date: Minimum date for filtering
            end_date: Maximum date for filtering
            date_field: Metadata field containing date information

        Returns:
            Filtered list of documents
        """
        filtered_docs = []
        for doc in documents:
            doc_date = doc.get('metadata', {}).get(date_field)

            if doc_date is None:
                continue

            if isinstance(doc_date, str):
                try:
                    doc_date = datetime.fromisoformat(doc_date)
                except ValueError:
                    continue

            if (start_date is None or doc_date >= start_date) and \
               (end_date is None or doc_date <= end_date):
                filtered_docs.append(doc)

        return filtered_docs

    @staticmethod
    def filter_by_tags(
        documents: List[Dict[str, Any]],
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        tags_field: str = 'tags'
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by inclusion or exclusion of tags

        Args:
            documents: List of document dictionaries
            include_tags: Tags that must be present
            exclude_tags: Tags that must not be present
            tags_field: Metadata field containing tags

        Returns:
            Filtered list of documents
        """
        filtered_docs = []
        for doc in documents:
            doc_tags = doc.get('metadata', {}).get(tags_field, [])

            # Ensure doc_tags is a list
            if not isinstance(doc_tags, list):
                doc_tags = [doc_tags]

            include_condition = (
                not include_tags or
                any(tag in doc_tags for tag in include_tags)
            )

            exclude_condition = (
                not exclude_tags or
                not any(tag in doc_tags for tag in exclude_tags)
            )

            if include_condition and exclude_condition:
                filtered_docs.append(doc)

        return filtered_docs

    @staticmethod
    def transform_metadata(
        documents: List[Dict[str, Any]],
        field_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform metadata fields

        Args:
            documents: List of document dictionaries
            field_mapping: Dictionary mapping old field names to new names

        Returns:
            List of documents with transformed metadata
        """
        if not field_mapping:
            return documents

        transformed_docs = []
        for doc in documents:
            new_doc = doc.copy()
            new_metadata = new_doc.get('metadata', {}).copy()

            for old_field, new_field in field_mapping.items():
                if old_field in new_metadata:
                    new_metadata[new_field] = new_metadata.pop(old_field)

            new_doc['metadata'] = new_metadata
            transformed_docs.append(new_doc)

        return transformed_docs