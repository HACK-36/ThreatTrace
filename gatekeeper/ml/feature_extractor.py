"""
Gatekeeper Feature Extraction Module
Extracts 102 features from HTTP requests for ML anomaly detection
"""
import re
import math
from typing import Dict, List
from collections import Counter
from urllib.parse import urlparse, parse_qs
import base64


class FeatureExtractor:
    """Extract features from HTTP requests for ML classification"""
    
    # Suspicious pattern lists
    SQL_KEYWORDS = [
        'SELECT', 'UNION', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'EXEC', 'EXECUTE', 'DECLARE', 'CAST', 'CONVERT', 'FROM',
        'WHERE', ' OR ', ' AND ', ' LIKE ', ' HAVING ', ' INFORMATION_SCHEMA',
        'SLEEP', 'LOAD_FILE', 'BENCHMARK'
    ]
    
    XSS_PATTERNS = [
        '<script', 'javascript:', 'onerror=', 'onload=', 'onclick=',
        '<iframe', '<object', '<embed', 'alert(', 'eval('
    ]
    
    COMMAND_PATTERNS = [
        'bash', 'sh', 'cmd', 'powershell', 'wget', 'curl',
        'nc', 'netcat', '/bin/', '&&', '||', ';', '|'
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        '../', '..\\', '%2e%2e', '%252e%252e'
    ]
    
    def __init__(self):
        pass
    
    def extract(self, request: Dict) -> Dict[str, float]:
        """
        Extract all 102 features from a request
        
        Args:
            request: Dict with keys: method, url, headers, body, query_params
            
        Returns:
            Dict of feature_name -> float value
        """
        features = {}
        
        # Basic request characteristics (10 features)
        features.update(self._extract_basic_features(request))
        
        # Content analysis (20 features)
        features.update(self._extract_content_features(request))
        
        # Pattern matching (25 features)
        features.update(self._extract_pattern_features(request))
        
        # Entropy and encoding (15 features)
        features.update(self._extract_entropy_features(request))
        
        # Behavioral features (20 features) - requires session history
        features.update(self._extract_behavioral_features(request))
        
        # Header analysis (12 features)
        features.update(self._extract_header_features(request))
        
        # Total: 102 features
        return features
    
    def _extract_basic_features(self, request: Dict) -> Dict[str, float]:
        """Basic request characteristics"""
        url = request.get('url', '')
        body = request.get('body', '')
        headers = request.get('headers', {})
        query_params = request.get('query_params', {})
        
        return {
            'request_length': len(body),
            'url_length': len(url),
            'header_count': len(headers),
            'param_count': len(query_params),
            'method_is_post': 1.0 if request.get('method') == 'POST' else 0.0,
            'method_is_get': 1.0 if request.get('method') == 'GET' else 0.0,
            'method_is_put': 1.0 if request.get('method') == 'PUT' else 0.0,
            'method_is_delete': 1.0 if request.get('method') == 'DELETE' else 0.0,
            'has_body': 1.0 if len(body) > 0 else 0.0,
            'has_query_params': 1.0 if len(query_params) > 0 else 0.0,
        }
    
    def _extract_content_features(self, request: Dict) -> Dict[str, float]:
        """Content-based features"""
        url = request.get('url', '')
        body = request.get('body', '')
        combined = url + ' ' + body
        
        return {
            'digit_ratio': self._char_ratio(combined, str.isdigit),
            'alpha_ratio': self._char_ratio(combined, str.isalpha),
            'special_char_ratio': self._special_char_ratio(combined),
            'uppercase_ratio': self._char_ratio(combined, str.isupper),
            'lowercase_ratio': self._char_ratio(combined, str.islower),
            'space_ratio': self._char_ratio(combined, str.isspace),
            'null_byte_count': float(combined.count('\x00')),
            'newline_count': float(combined.count('\n')),
            'url_depth': float(url.count('/')),
            'url_params_length': len(request.get('query_params', {})),
            'body_lines': float(body.count('\n') + 1 if body else 0),
            'avg_word_length': self._avg_word_length(combined),
            'max_word_length': self._max_word_length(combined),
            'unique_char_count': float(len(set(combined))),
            'repeated_char_ratio': self._repeated_char_ratio(combined),
            'hex_ratio': self._hex_ratio(combined),
            'base64_ratio': self._base64_ratio(combined),
            'url_encoded_ratio': self._url_encoded_ratio(combined),
            'json_like': 1.0 if '{' in body and '}' in body else 0.0,
            'xml_like': 1.0 if '<' in body and '>' in body else 0.0,
        }
    
    def _extract_pattern_features(self, request: Dict) -> Dict[str, float]:
        """Attack pattern detection"""
        url = request.get('url', '')
        body = request.get('body', '')
        combined = url + ' ' + body
        combined_upper = combined.upper()
        
        return {
            'sql_keyword_count': self._count_keywords(combined_upper, self.SQL_KEYWORDS),
            'xss_pattern_count': self._count_patterns(combined.lower(), self.XSS_PATTERNS),
            'command_pattern_count': self._count_patterns(combined.lower(), self.COMMAND_PATTERNS),
            'path_traversal_count': self._count_patterns(combined.lower(), self.PATH_TRAVERSAL_PATTERNS),
            'has_union': 1.0 if 'UNION' in combined_upper else 0.0,
            'has_select': 1.0 if 'SELECT' in combined_upper else 0.0,
            'has_script_tag': 1.0 if '<script' in combined.lower() else 0.0,
            'has_iframe': 1.0 if '<iframe' in combined.lower() else 0.0,
            'has_javascript': 1.0 if 'javascript:' in combined.lower() else 0.0,
            'has_eval': 1.0 if 'eval(' in combined.lower() else 0.0,
            'has_exec': 1.0 if 'exec' in combined.lower() else 0.0,
            'sql_comment_count': float(combined.count('--') + combined.count('/*')),
            'quote_count': float(combined.count("'") + combined.count('"')),
            'semicolon_count': float(combined.count(';')),
            'equals_count': float(combined.count('=')),
            'angle_bracket_count': float(combined.count('<') + combined.count('>')),
            'parenthesis_count': float(combined.count('(') + combined.count(')')),
            'pipe_count': float(combined.count('|')),
            'ampersand_count': float(combined.count('&')),
            'percent_count': float(combined.count('%')),
            'dollar_count': float(combined.count('$')),
            'backslash_count': float(combined.count('\\')),
            'dot_dot_slash': float(combined.count('../')),
            'double_encoding': 1.0 if '%25' in combined else 0.0,
            'ldap_injection': 1.0 if any(p in combined for p in ['*(', '*)', '(|']) else 0.0,
        }
    
    def _extract_entropy_features(self, request: Dict) -> Dict[str, float]:
        """Entropy and randomness features"""
        url = request.get('url', '')
        body = request.get('body', '')
        
        return {
            'entropy_url': self._calculate_entropy(url),
            'entropy_body': self._calculate_entropy(body),
            'entropy_combined': self._calculate_entropy(url + body),
            'url_entropy_per_char': self._calculate_entropy(url) / max(len(url), 1),
            'body_entropy_per_char': self._calculate_entropy(body) / max(len(body), 1),
            'url_randomness': self._randomness_score(url),
            'body_randomness': self._randomness_score(body),
            'longest_alphanum_sequence': float(self._longest_alphanum_sequence(url + body)),
            'longest_repeated_char': float(self._longest_repeated_char(url + body)),
            'consonant_ratio': self._consonant_ratio(url + body),
            'vowel_ratio': self._vowel_ratio(url + body),
            'digit_sequence_max': float(self._max_digit_sequence(url + body)),
            'has_long_hex_string': 1.0 if self._has_long_hex_string(url + body) else 0.0,
            'has_long_base64_string': 1.0 if self._has_long_base64_string(url + body) else 0.0,
            'compression_ratio': self._compression_ratio(url + body),
        }
    
    def _extract_behavioral_features(self, request: Dict) -> Dict[str, float]:
        """Behavioral features (requires session context)"""
        # In production, these would come from session history
        # For now, return default values
        metadata = request.get('metadata', {})
        
        return {
            'requests_per_second': metadata.get('req_per_sec', 0.0),
            'requests_in_session': metadata.get('req_count', 1.0),
            'unique_paths_visited': metadata.get('unique_paths', 1.0),
            'failed_auth_attempts': metadata.get('failed_auth', 0.0),
            'method_switches': metadata.get('method_switches', 0.0),
            'user_agent_changes': metadata.get('ua_changes', 0.0),
            'time_since_last_request': metadata.get('time_since_last', 0.0),
            'avg_request_size': metadata.get('avg_req_size', len(request.get('body', ''))),
            'error_responses': metadata.get('error_count', 0.0),
            'redirect_count': metadata.get('redirect_count', 0.0),
            'session_duration': metadata.get('session_duration', 0.0),
            'path_depth_variance': metadata.get('path_depth_var', 0.0),
            'suspicious_path_ratio': metadata.get('suspicious_path_ratio', 0.0),
            'repeated_param_names': metadata.get('repeated_params', 0.0),
            'http_version_anomaly': metadata.get('http_version_anomaly', 0.0),
            'referer_anomaly': 1.0 if not request.get('headers', {}).get('Referer') else 0.0,
            'accept_header_missing': 1.0 if not request.get('headers', {}).get('Accept') else 0.0,
            'cookie_count': float(len(request.get('headers', {}).get('Cookie', '').split(';'))),
            'unusual_port': metadata.get('unusual_port', 0.0),
            'protocol_violation': metadata.get('protocol_violation', 0.0),
        }
    
    def _extract_header_features(self, request: Dict) -> Dict[str, float]:
        """HTTP header analysis"""
        headers = request.get('headers', {})
        user_agent = headers.get('User-Agent', '')
        
        return {
            'user_agent_length': float(len(user_agent)),
            'user_agent_entropy': self._calculate_entropy(user_agent),
            'has_user_agent': 1.0 if user_agent else 0.0,
            'user_agent_is_curl': 1.0 if 'curl' in user_agent.lower() else 0.0,
            'user_agent_is_python': 1.0 if 'python' in user_agent.lower() else 0.0,
            'user_agent_is_scanner': 1.0 if any(s in user_agent.lower() for s in ['nikto', 'sqlmap', 'nmap', 'masscan']) else 0.0,
            'has_x_forwarded_for': 1.0 if 'X-Forwarded-For' in headers else 0.0,
            'has_authorization': 1.0 if 'Authorization' in headers else 0.0,
            'has_cookie': 1.0 if 'Cookie' in headers else 0.0,
            'content_type_json': 1.0 if 'application/json' in headers.get('Content-Type', '') else 0.0,
            'content_type_xml': 1.0 if 'xml' in headers.get('Content-Type', '').lower() else 0.0,
            'suspicious_content_type': 1.0 if any(ct in headers.get('Content-Type', '').lower() for ct in ['multipart', 'octet-stream']) else 0.0,
        }
    
    # Helper methods
    
    def _char_ratio(self, text: str, char_test) -> float:
        """Calculate ratio of characters matching a test function"""
        if not text:
            return 0.0
        count = sum(1 for c in text if char_test(c))
        return count / len(text)
    
    def _special_char_ratio(self, text: str) -> float:
        """Calculate ratio of special characters"""
        if not text:
            return 0.0
        special = sum(1 for c in text if not c.isalnum() and not c.isspace())
        return special / len(text)
    
    def _avg_word_length(self, text: str) -> float:
        """Average word length"""
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
        return sum(len(w) for w in words) / len(words)
    
    def _max_word_length(self, text: str) -> float:
        """Maximum word length"""
        words = re.findall(r'\b\w+\b', text)
        return float(max((len(w) for w in words), default=0))
    
    def _repeated_char_ratio(self, text: str) -> float:
        """Ratio of repeated characters"""
        if len(text) < 2:
            return 0.0
        repeated = sum(1 for i in range(len(text)-1) if text[i] == text[i+1])
        return repeated / len(text)
    
    def _hex_ratio(self, text: str) -> float:
        """Ratio of hexadecimal characters"""
        hex_chars = set('0123456789abcdefABCDEF')
        if not text:
            return 0.0
        hex_count = sum(1 for c in text if c in hex_chars)
        return hex_count / len(text)
    
    def _base64_ratio(self, text: str) -> float:
        """Estimate ratio of base64-encoded content"""
        base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if not text:
            return 0.0
        b64_count = sum(1 for c in text if c in base64_chars)
        return b64_count / len(text)
    
    def _url_encoded_ratio(self, text: str) -> float:
        """Ratio of URL-encoded characters"""
        if not text:
            return 0.0
        encoded_count = text.count('%')
        return encoded_count / len(text)
    
    def _count_keywords(self, text: str, keywords: List[str]) -> float:
        """Count occurrences of keywords"""
        return float(sum(text.count(kw) for kw in keywords))
    
    def _count_patterns(self, text: str, patterns: List[str]) -> float:
        """Count occurrences of patterns"""
        return float(sum(text.count(pat) for pat in patterns))
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy"""
        if not text:
            return 0.0
        
        counter = Counter(text)
        length = len(text)
        entropy = 0.0
        
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _randomness_score(self, text: str) -> float:
        """Score indicating randomness (0-1)"""
        if not text or len(text) < 4:
            return 0.0
        
        # Check for common English patterns
        vowels = set('aeiouAEIOU')
        consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
        
        vowel_count = sum(1 for c in text if c in vowels)
        consonant_count = sum(1 for c in text if c in consonants)
        
        if vowel_count + consonant_count == 0:
            return 1.0  # All special chars = very random
        
        # English text typically has vowel ratio of 0.3-0.4
        vowel_ratio = vowel_count / (vowel_count + consonant_count)
        expected_ratio = 0.35
        deviation = abs(vowel_ratio - expected_ratio)
        
        return min(deviation * 3, 1.0)
    
    def _longest_alphanum_sequence(self, text: str) -> int:
        """Find longest alphanumeric sequence"""
        sequences = re.findall(r'[a-zA-Z0-9]+', text)
        return max((len(s) for s in sequences), default=0)
    
    def _longest_repeated_char(self, text: str) -> int:
        """Find longest sequence of repeated character"""
        if not text:
            return 0
        max_len = 1
        current_len = 1
        for i in range(1, len(text)):
            if text[i] == text[i-1]:
                current_len += 1
                max_len = max(max_len, current_len)
            else:
                current_len = 1
        return max_len
    
    def _consonant_ratio(self, text: str) -> float:
        """Ratio of consonants"""
        consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
        if not text:
            return 0.0
        consonant_count = sum(1 for c in text if c in consonants)
        return consonant_count / len(text)
    
    def _vowel_ratio(self, text: str) -> float:
        """Ratio of vowels"""
        vowels = set('aeiouAEIOU')
        if not text:
            return 0.0
        vowel_count = sum(1 for c in text if c in vowels)
        return vowel_count / len(text)
    
    def _max_digit_sequence(self, text: str) -> int:
        """Longest sequence of digits"""
        sequences = re.findall(r'\d+', text)
        return max((len(s) for s in sequences), default=0)
    
    def _has_long_hex_string(self, text: str, min_length: int = 16) -> bool:
        """Check for long hexadecimal strings"""
        hex_pattern = r'[0-9a-fA-F]{%d,}' % min_length
        return bool(re.search(hex_pattern, text))
    
    def _has_long_base64_string(self, text: str, min_length: int = 20) -> bool:
        """Check for long base64 strings"""
        b64_pattern = r'[A-Za-z0-9+/]{%d,}={0,2}' % min_length
        return bool(re.search(b64_pattern, text))
    
    def _compression_ratio(self, text: str) -> float:
        """Estimate compressibility (proxy for randomness)"""
        if not text:
            return 0.0
        try:
            import zlib
            compressed = zlib.compress(text.encode())
            return len(compressed) / len(text)
        except:
            return 1.0
