from bs4 import BeautifulSoup
import os
from typing import Dict, List, Optional
import re
from dataclasses import dataclass
import json
from pathlib import Path
import hashlib
from datetime import datetime

@dataclass
class DocChunk:
    """Represents a logical chunk of documentation content"""
    chunk_id: str
    page_id: str
    chunk_type: str  # e.g., 'main_content', 'section', 'subsection'
    content: str
    metadata: Dict

class DocumentationProcessor:
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text

    def extract_doc_info(self, html_content: str) -> Dict:
        """Extract key documentation information from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Initialize doc info dictionary
        doc_info = {
            'title': '',
            'main_content': '',
            'sections': [],
            'breadcrumbs': [],
            'metadata': {}
        }

        # Extract title
        title_elem = soup.find('h1', class_='doc-page-title')
        if title_elem:
            doc_info['title'] = self.clean_text(title_elem.text)

        # Extract last modified date
        last_modified = soup.find('div', class_='last-modified')
        if last_modified:
            date_span = last_modified.find('span', class_='date')
            if date_span:
                doc_info['metadata']['last_modified'] = date_span.text

        # Extract breadcrumbs
        breadcrumb_items = soup.find_all('li', class_='breadcrumb-item')
        if breadcrumb_items:
            doc_info['breadcrumbs'] = [self.clean_text(item.text) for item in breadcrumb_items]

        # Extract main content
        main_content = soup.find('div', class_='doc-section')
        if main_content:
            # Get all paragraphs and lists
            content_elements = main_content.find_all(['p', 'ul', 'ol'])
            doc_info['main_content'] = ' '.join([self.clean_text(elem.text) for elem in content_elements])

            # Extract sections (assuming sections are divided by headers)
            sections = []
            current_section = {'title': '', 'content': []}

            for elem in main_content.children:
                if elem.name in ['h2', 'h3', 'h4']:
                    if current_section['content']:
                        sections.append(current_section)
                        current_section = {'title': '', 'content': []}
                    current_section['title'] = self.clean_text(elem.text)
                elif elem.name in ['p', 'ul', 'ol']:
                    current_section['content'].append(self.clean_text(elem.text))

            if current_section['content']:
                sections.append(current_section)

            doc_info['sections'] = sections

        return doc_info

    def create_chunks(self, doc_info: Dict) -> List[DocChunk]:
        """Create logical chunks from documentation information"""
        chunks = []
        page_id = hashlib.md5(doc_info['title'].encode()).hexdigest()

        # Create title + overview chunk
        overview_chunk = DocChunk(
            chunk_id=f"{page_id}_overview",
            page_id=page_id,
            chunk_type='overview',
            content=f"{' > '.join(doc_info['breadcrumbs'])}. {doc_info['title']}. {doc_info['main_content'][:500]}",
            metadata={
                'type': 'overview',
                'breadcrumbs': doc_info['breadcrumbs'],
                **doc_info['metadata']
            }
        )
        chunks.append(overview_chunk)

        # Create main content chunks
        if doc_info['main_content']:
            content_chunk = DocChunk(
                chunk_id=f"{page_id}_content",
                page_id=page_id,
                chunk_type='main_content',
                content=doc_info['main_content'],
                metadata={
                    'type': 'main_content',
                    'title': doc_info['title'],
                    **doc_info['metadata']
                }
            )
            chunks.append(content_chunk)

        # Create section chunks
        for idx, section in enumerate(doc_info['sections']):
            if section['content']:
                section_chunk = DocChunk(
                    chunk_id=f"{page_id}_section_{idx}",
                    page_id=page_id,
                    chunk_type='section',
                    content=f"{section['title']}. {' '.join(section['content'])}",
                    metadata={
                        'type': 'section',
                        'section_title': section['title'],
                        **doc_info['metadata']
                    }
                )
                chunks.append(section_chunk)

        return chunks

    def process_html_file(self, file_path: str) -> List[DocChunk]:
        """Process a single HTML file and return chunks"""
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        doc_info = self.extract_doc_info(html_content)
        chunks = self.create_chunks(doc_info)
        return chunks

    def process_directory(self, directory_path: str, output_path: str):
        """Process all HTML files in a directory and save chunks to JSON"""
        all_chunks = []
        directory = Path(directory_path)

        for html_file in directory.glob('**/*.html'):
            chunks = self.process_html_file(str(html_file))
            all_chunks.extend(chunks)

        # Convert chunks to dictionary format for JSON serialization
        chunks_data = [
            {
                'chunk_id': chunk.chunk_id,
                'page_id': chunk.page_id,
                'chunk_type': chunk.chunk_type,
                'content': chunk.content,
                'metadata': chunk.metadata
            }
            for chunk in all_chunks
        ]

        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2)


def main():
    # Example usage
    processor = DocumentationProcessor()
    processor.process_directory(
        directory_path='Feedback',
        output_path='Feedback/processed_chunks.json'
    )


if __name__ == "__main__":
    main()
