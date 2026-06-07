"""
@Input:  Book IDs, Prompts
@Output: Summaries Result Map
@Pos:    modules / worker.py. Domain Logic Engine.

!!! Maintenance Protocol: If logic, dependencies, or output change, 
!!! update this header AND the parent directory's _DIR_META.md.
"""
from calibre_plugins.smart_summary_pro.infrastructure.api_manager import APIManager
import concurrent.futures

class GenerationWorker:
    """
    Background worker for generating book summaries.
    Compatible with Calibre 8.x job_manager.run_threaded_job() API.
    """
    def __init__(self, book_ids, metadata_map, system_prompt, user_prompt):
        self.book_ids = book_ids
        self.metadata_map = metadata_map
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.api_manager = APIManager()
        
        self.results = {}
        self.failed = False
        self.was_aborted = False
        self.completed_count = 0
        self.total_count = len(book_ids)
        
    def __call__(self):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(self.process_book, book_id): book_id for book_id in self.book_ids}
                for future in concurrent.futures.as_completed(futures):
                    if self.was_aborted:
                        continue
                    self.completed_count += 1
        except Exception as e:
            self.failed = True
            self.results['fatal_error'] = str(e)

    def process_book(self, book_id):
        if getattr(self, 'was_aborted', False):
            return
            
        mi_dict = self.metadata_map.get(book_id, {})
        title = mi_dict.get('title', 'Unknown')
        
        try:
            formatted_system = self.system_prompt
            formatted_user = self.user_prompt.format(**mi_dict)
            prompt = (formatted_system, formatted_user)
            
            summary = self.api_manager.generate_summary(prompt)
            self.results[book_id] = {
                'success': True, 
                'content': summary, 
                'title': title
            }
        except KeyError as e:
            self.results[book_id] = {
                'success': False, 
                'error': f"Template variable {e} not found.", 
                'title': title
            }
        except Exception as e:
            self.results[book_id] = {
                'success': False, 
                'error': str(e), 
                'title': title
            }
