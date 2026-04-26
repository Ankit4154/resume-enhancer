import json
import re
import requests
from bs4 import BeautifulSoup, Tag
from typing import Dict


class JobDetailsFetcherService:
    """Service to fetch and parse job details from URLs"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def fetch_job_details(self, url: str) -> Dict[str, str]:
        """
        Fetch job details from a URL and extract key sections

        Args:
            url: The job posting URL

        Returns:
            Dictionary containing extracted job details
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            json_data = self._extract_jsonld_job_posting(soup)

            job_description = (
                self._extract_meta_description(soup)
                or self._extract_jsonld_field(json_data, 'description')
                or self._extract_section(soup, ['description', 'job-description', 'job_description'])
                or self._extract_text_section(soup, ['overview', 'description', 'role'])
            )
            roles_responsibilities = (
                self._extract_jsonld_field(json_data, 'responsibilities')
                or self._extract_section(soup, ['responsibilities', 'roles', 'role-responsibility', 'about-the-role'])
                or self._extract_text_section(soup, ['responsibilities', 'role', 'duties'])
            )
            minimum_qualifications = (
                self._extract_jsonld_field(json_data, 'experienceRequirements')
                or self._extract_jsonld_field(json_data, 'qualifications')
                or self._extract_section(soup, ['minimum', 'qualifications', 'required', 'requirements'])
                or self._extract_text_section(soup, ['minimum qualifications', 'required qualifications', 'required', 'qualifications'])
            )
            preferred_qualifications = (
                self._extract_jsonld_field(json_data, 'skills')
                or self._extract_jsonld_field(json_data, 'preferredQualifications')
                or self._extract_section(soup, ['preferred', 'nice-to-have', 'additional-qualifications'])
                or self._extract_text_section(soup, ['preferred qualifications', 'nice to have', 'additional qualifications'])
            )

            if not job_description:
                job_description = self._extract_main_content(soup)

            combined_details = self._combine_details(
                job_description,
                roles_responsibilities,
                minimum_qualifications,
                preferred_qualifications,
            )

            return {
                'status': 'success',
                'combined': combined_details,
                'job_description': job_description,
                'roles_and_responsibilities': roles_responsibilities,
                'minimum_qualifications': minimum_qualifications,
                'preferred_qualifications': preferred_qualifications,
            }

        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'Failed to fetch URL: {str(e)}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Error processing job details: {str(e)}'}

    def _extract_jsonld_job_posting(self, soup: BeautifulSoup) -> dict:
        scripts = soup.find_all('script', type=re.compile(r'application/ld\\+json', re.I))
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue

            if isinstance(data, list):
                for item in data:
                    if self._is_job_posting(item):
                        return item
            elif self._is_job_posting(data):
                return data

        return {}

    def _is_job_posting(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        job_type = data.get('@type') or data.get('type')
        return isinstance(job_type, str) and job_type.strip().lower() == 'jobposting'

    def _extract_jsonld_field(self, data: dict, field: str) -> str:
        if not data or field not in data:
            return ''

        value = data[field]
        if isinstance(value, list):
            value = ' '.join(str(v) for v in value)
        if isinstance(value, dict):
            value = value.get('description') or value.get('name') or ''

        extracted = self._clean_text(self._strip_html(str(value))) if value else ''
        return '' if self._is_noise_text(extracted) else extracted

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
        if meta and meta.get('content'):
            extracted = self._clean_text(str(meta.get('content')))
            return '' if self._is_noise_text(extracted) else extracted
        og = soup.find('meta', attrs={'property': re.compile(r'og:description', re.I)})
        if og and og.get('content'):
            extracted = self._clean_text(str(og.get('content')))
            return '' if self._is_noise_text(extracted) else extracted
        return ''

    def _is_noise_text(self, text: str) -> bool:
        if not text:
            return True
        noise_tokens = [
            'roletype',
            'employment_type',
            'locationRadiusDistanceDefault',
            'locationSearch',
            'includeRemoteDefault',
            'mapConfig',
            'hiring_title',
            'positionLocationDisplay',
        ]
        lower_text = text.lower()
        if any(token.lower() in lower_text for token in noise_tokens):
            return True

        punctuation_hits = len(re.findall(r'[{}\[\]"<>]', text))
        if punctuation_hits > 10 and len(text) < 1000:
            return True

        if re.search(r'\b(api|json|http|https|cdn|callback|function|var|script|window|document)\b', lower_text):
            return True

        return False

    def _extract_section(self, soup: BeautifulSoup, keywords: list) -> str:
        # Try data attributes first (modern web apps)
        for keyword in keywords:
            # Look for data-testid, data-cy, etc.
            data_selectors = [
                f'[data-testid*="{keyword}"]',
                f'[data-cy*="{keyword}"]',
                f'[data-test*="{keyword}"]'
            ]
            for selector in data_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self._clean_text(element.get_text())
                    if text and len(text) > 20 and not self._is_noise_text(text):
                        return text

        # Try class and ID patterns
        for keyword in keywords:
            # Class-based search
            elements = soup.find_all(class_=re.compile(keyword.replace('-', '[-_]?'), re.I))
            for element in elements:
                text = self._clean_text(element.get_text())
                if text and len(text) > 20 and not self._is_noise_text(text):
                    return text

            # ID-based search
            elements = soup.find_all(id=re.compile(keyword.replace('-', '[-_]?'), re.I))
            for element in elements:
                text = self._clean_text(element.get_text())
                if text and len(text) > 20 and not self._is_noise_text(text):
                    return text

        # Try heading-based search with improved sibling detection
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text().lower()
            if any(keyword.lower() in heading_text for keyword in keywords):
                # Look for content in the next sibling or parent container
                next_sibling = heading.find_next_sibling()
                if next_sibling and next_sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content = self._clean_text(next_sibling.get_text())
                    if content and len(content) > 20 and not self._is_noise_text(content):
                        return content

                # Try parent container
                parent = heading.parent
                if parent:
                    # Get all text after the heading in the parent
                    heading_index = None
                    for i, child in enumerate(parent.children):
                        if child == heading:
                            heading_index = i
                            break

                    if heading_index is not None:
                        content_parts = []
                        for child in list(parent.children)[heading_index + 1:]:
                            # Check if child is a Tag and is a heading
                            if isinstance(child, Tag) and child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                break
                            if hasattr(child, 'get_text'):
                                content_parts.append(child.get_text())

                        content = self._clean_text(' '.join(content_parts))
                        if content and len(content) > 20 and not self._is_noise_text(content):
                            return content

        return ''

    def _extract_text_section(self, soup: BeautifulSoup, keywords: list) -> str:
        # Clean the soup by removing scripts, styles, and navigation
        clean_soup = BeautifulSoup(str(soup), 'html.parser')
        for tag in clean_soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', '.sidebar', '.navigation']):
            tag.decompose()

        text = clean_soup.get_text(separator='\n')
        normalized = self._clean_text_preserve_breaks(text)
        lower_text = normalized.lower()

        # Expanded section headers for better detection
        section_headers = [
            r'overview', r'description', r'responsibilities', r'role[s]?', r'duties',
            r'qualifications', r'requirements', r'preferred', r'nice to have',
            r'what you will do', r'about the role', r'basic qualifications',
            r'minimum requirements', r'additional qualifications', r'skills required',
            r'job summary', r'position summary', r'key responsibilities'
        ]
        stop_pattern = re.compile(r'\n\s*(?:' + '|'.join(section_headers) + r')\s*\n', re.I)

        for keyword in keywords:
            # Look for exact section headers
            section_patterns = [
                rf'\n\s*{re.escape(keyword)}\s*\n',
                rf'\n\s*{re.escape(keyword)}:\s*',
                rf'\n\s*{re.escape(keyword)}\s*-\s*',
                rf'###\s*{re.escape(keyword)}',
                rf'##\s*{re.escape(keyword)}'
            ]

            for pattern in section_patterns:
                matches = list(re.finditer(pattern, lower_text, re.I))
                for match in matches:
                    start = match.end()
                    end_match = stop_pattern.search(normalized, pos=start)
                    if end_match:
                        section_text = normalized[start:end_match.start()]
                    else:
                        # Take next 1000 characters or until end
                        section_text = normalized[start:start+1000]
                        # Try to find a reasonable stopping point
                        sentences = re.split(r'[.!?]+', section_text)
                        section_text = '.'.join(sentences[:3]) if len(sentences) > 3 else section_text

                    section_text = self._clean_text(section_text)
                    if section_text and len(section_text) > 30 and not self._is_noise_text(section_text):
                        return section_text

            # Fallback: simple text search
            start = lower_text.find(keyword.lower())
            if start == -1:
                continue

            end_match = stop_pattern.search(normalized, pos=start + len(keyword))
            if end_match:
                section_text = normalized[start:end_match.start()]
            else:
                section_text = normalized[start:start+800]

            section_text = self._clean_text(section_text)
            if section_text and len(section_text) > 30 and not self._is_noise_text(section_text):
                return section_text

        return ''

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        main_content = soup.find(['main', 'article'])
        if main_content:
            return self._clean_text(main_content.get_text())

        body = soup.find('body')
        if body:
            for tag in body.find_all(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            return self._clean_text(body.get_text())

        return self._clean_text(soup.get_text())

    def _strip_html(self, text: str) -> str:
        return BeautifulSoup(text, 'html.parser').get_text(separator=' ')

    def _clean_text_preserve_breaks(self, text: str) -> str:
        text = re.sub(r'[ \t\r]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n\n', text)
        return text.strip()

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if len(text) > 5000:
            text = text[:5000] + '...'
        return text

    def _combine_details(self, description: str, roles: str, minimum: str, preferred: str) -> str:
        sections = []

        if description:
            sections.append(description)
        if roles:
            sections.append(roles)
        if minimum:
            sections.append(minimum)
        if preferred:
            sections.append(preferred)

        return '\n\n'.join(sections)
