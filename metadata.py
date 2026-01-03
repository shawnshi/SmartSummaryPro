from datetime import datetime

class MetadataProcessor:
    def __init__(self, db):
        """
        :param db: The Calibre database object (gui.current_db or gui.current_db.new_api)
        """
        self.db = db

    def get_book_info(self, book_id):
        """
        Extracts metadata for a single book_id.
        Returns a dictionary suitable for LLM Context.
        """
        # mi is a Metadata object
        # In Calibre's GUI db interface, get_metadata returns a Metadata object
        mi = self.db.get_metadata(book_id, index_is_id=True)
        
        # Handle languages (could be list or string depending on version/context, usually list)
        langs = mi.languages
        if langs and isinstance(langs, list):
            langs = ", ".join(langs)
        
        info = {
            'id': book_id,
            'title': mi.title,
            'authors': mi.authors if mi.authors else ["Unknown"],
            'publisher': mi.publisher,
            'pubdate': mi.pubdate,
            'languages': langs,
            'series': mi.series,
            'series_index': mi.series_index,
            'tags': mi.tags if mi.tags else [],
            'comments': mi.comments
        }
        
        return info

    def format_for_prompt(self, info):
        """
        Converts the info dict into a readable string block for the AI prompt.
        """
        # Helper to join lists
        authors = ", ".join(info['authors']) if isinstance(info['authors'], list) else info['authors']
        
        lines = []
        lines.append(f"Title: {info['title']}")
        lines.append(f"Author: {authors}")
        if info['publisher']:
            lines.append(f"Publisher: {info['publisher']}")
        if info['pubdate']:
            # Format date safely
            try:
                d = info['pubdate']
                # Check if it's a datetime object or string
                val = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)
                lines.append(f"Publication Date: {val}")
            except:
                lines.append(f"Publication Date: {str(info['pubdate'])}")
                
        if info['series']:
            idx = info['series_index']
            lines.append(f"Series: {info['series']} (Book {idx})")
        
        return "\n".join(lines)

