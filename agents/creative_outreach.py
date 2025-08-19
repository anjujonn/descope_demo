import os
import json
import logging
import re
import time
import random
from pathlib import Path
from typing import Dict, Optional
import subprocess
import requests
from torch.serialization import safe_globals
import numpy as np

from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from config import D_ID_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreativeOutreachAgent:

    def __init__(self, storage, db_path: str):
        self.storage = storage
        self.output_dir = Path(os.path.dirname(os.path.abspath(db_path))) / "creative_outreach"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self._bark_initialized = False
        
        self.d_id_api_key = D_ID_KEY
        if self.d_id_api_key:
            logger.info("D-ID API key loaded from environment")
        else:
            logger.warning("D-ID API key not found. Add D_ID_API_KEY to your .env file")
        
        self.ffmpeg_available = self.check_ffmpeg()
        logger.info(f"FFmpeg available: {self.ffmpeg_available}")

    def _initialize_bark(self):
        if not self._bark_initialized:
            logger.info("Initializing Bark TTS models...")
            with safe_globals([
                np.core.multiarray.scalar,
                np.dtype,
                np.dtypes.Float64DType
            ]):
                preload_models()
                logger.info("Bark TTS models loaded successfully")
                self._bark_initialized = True

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)#, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def extract_company_name(self, lead: Dict):
        company = lead.get('detected_company')
        if company and company != 'Unknown Company' and len(company) > 2:
            return company
        
        domain = lead.get('detected_domain', '')
        if domain:
            domain_clean = domain.replace('www.', '').replace('https://', '').replace('http://', '')
            domain_parts = domain_clean.split('.')[0]
            return domain_parts.capitalize()
        
        title = lead.get('title', '')
        if title != 'Unknown' or title != None:
            return title.capitalize()
        
        return 'Your Company'

    def generate_script(self, lead: Dict):
        company = self.extract_company_name(lead)
        domain = lead.get('detected_domain', '').replace('https://', '').replace('http://', '')
        title = lead.get('title', '')
        context_excerpt = lead.get('content_excerpt', '')
        
        context_type = self._analyze_lead_context(lead)
        
        prompt = f"""Generate a 300 characters or less spoken sales pitch script that promotes Descope, customized for {company} to use for {context_type}.

                     Context Excerpt: {context_excerpt}
                     Title: {title[:100]}
                     Domain: {domain}
 
                     Requirements:
                     - Professional but conversational tone
                     - Mention specific auth/security pain point
                     - Clear value proposition
                     - End with soft call-to-action
                     - Maximum 70 words
                     - No fluff or filler words

                     Script: """

        try:
            models_to_try = ['llama3.2:3b', 'llama2:7b-chat', 'llama2']
            
            for model in models_to_try:
                try:
                    result = subprocess.run(
                        ["ollama", "run", model, prompt],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        # timeout=65,
                        check=True
                    )
                    script = result.stdout.strip()
                    if len(script) > 20 and len(script.split()) > 10:
                        logger.info(f"Generated script for {company} using {model}")
                        return self._clean_script(script)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
                    
            logger.warning(f"All Ollama models failed for {company}...using contextual fallback ;-;")
            return self.get_contextual_fallback_script(lead, context_type)
            
        except Exception as e:
            logger.error(f"Script generation error for {company}: {e}")
            return self.get_contextual_fallback_script(lead, context_type)

    def _analyze_lead_context(self, lead: Dict):
        title = lead.get('title', '').lower()
        domain = lead.get('detected_domain', '').lower()
        content = lead.get('content_excerpt', '').lower()
        
        if 'migration' in title or 'migrate' in title:
            return 'migration'
        elif 'outage' in title or 'status' in domain:
            return 'reliability'
        elif 'alternative' in title or 'open-source' in title:
            return 'alternative'
        elif 'auth0' in content or 'okta' in content:
            return 'competitor'
        else:
            return 'general'

    def _clean_script(self, script: str):
        script_list = script.split('.')
        script_final = ''.join(script_list)
        script_final = script_final.strip()
        
        if not script_final.endswith(('?', '.', '!')):
            script_final += '.'
            
        return script_final

    def get_contextual_fallback_script(self, lead: Dict, context_type: str):
        """Context-aware fallback scripts"""
        company = self.extract_company_name(lead)
        
        scripts = {
            'migration': f"Hi! I noticed {company} is migrating away from your current CIAM. Descope has helped 50+ teams cut migration time dramatically, and our platform maintains 100% uptime for Console and API—recently verified across both US and EU in mid‑2025. Can we chat about how we make migrations seamless?",

            'reliability': f"Hi! I saw {company} experienced some auth service issues. Descope delivers reliable auth with consistently 100% operational uptime. Would you be open to discuss strategies to strengthen your authentication resilience?",

            'alternative': f"Hi! I love what {company} is building a CIAM alternative. Descope supports scalable, low‑code, passwordless auth—empowered by strong industry recognition, including being a 2025 Rising Star in Passwordless CIAM by KuppingerCole. Interested in exchanging notes on passwordless tooling?",

            'competitor': f"Hi! I understand {company} is evaluating auth providers. Descope reduces auth complexity while improving security and UX. 75% of global consumers now know about passkeys—with 53% seeing them as more secure and 54% more convenient. Can we schedule a brief chat along with some real‑world cases?",

            'general': f"Hi! I see {company} is working on authentication. Descope’s CIAM platform enables secure, passwordless auth with low/no‑code workflows and proven reliability. We’ve also been named a 2025 Rising Star in CIAM and Passwordless by KuppingerCole. Would you like to explore whether it aligns with your current setup?"
        }
        return scripts.get(context_type, scripts['general'])

    def create_d_id_video(self, script: str, video_path: Path):
        if not self.d_id_api_key:
            logger.warning("D-ID API key not configured - skipping AI avatar")
            return None
        
        clean_script = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', script[:350])

        try:
            url = "https://api.d-id.com/talks"

            default_avatars = [
                "amy-jBaWBj6FYr",
                "mark-vwX6VXB4Kk",
                "sarah-Lm8XnQ3jKp",
            ]
            source_url = f"https://create-images-results.d-id.com/DefaultPresenters/{random.choice(default_avatars)}/image.jpeg"

            payload = {
                "script": {
                    "type": "text",
                    "input": clean_script,
                    "provider": {
                        "type": "microsoft",
                        "voice_id": "en-US-GuyNeural"
                    }
                },
                "source_url": source_url,
                "config": {
                    "result_format": "mp4",
                    "fluent": True,
                    "pad_audio": 0.2,
                    "stitch": True
                }
            }

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Basic {self.d_id_api_key}"
            }

            def make_json_safe(obj):
                if isinstance(obj, dict):
                    return {k: make_json_safe(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_json_safe(x) for x in obj]
                elif isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                else:
                    return str(obj)

            logger.debug(f"D-ID payload: {json.dumps(payload)}")
            logger.info("Creating D-ID video...")
            response = requests.post(url, json=payload, headers=headers)


            if response.status_code != 201:
                logger.error(f"D-ID request failed: {response.status_code} - {response.text}")
                return None

            talk_id = response.json()['id']
            logger.info(f"D-ID video creation started: {talk_id}")

            max_wait_time = 300
            poll_interval = 3
            start_time = time.time()

            while (time.time() - start_time) < max_wait_time:
                time.sleep(poll_interval)
                try:
                    status_response = requests.get(f"{url}/{talk_id}", headers=headers, timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        if status == 'done':
                            video_url = status_data['result_url']
                            logger.info(f"Downloading D-ID video to {video_path}")
                            video_resp = requests.get(video_url, stream=True, timeout=60)
                            video_resp.raise_for_status()
                            with open(video_path, 'wb') as f:
                                for chunk in video_resp.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            logger.info(f"D-ID video completed: {video_path}")
                            return video_path
                        elif status == 'error':
                            error_msg = status_data.get('error', {}).get('message', 'Unknown error')
                            logger.error(f"D-ID video failed: {error_msg}")
                            return None
                        poll_interval = min(poll_interval * 1.2, 10)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"D-ID status check failed: {e}")
                    continue

            logger.warning("D-ID video timed out")
            return None

        except Exception as e:
            logger.error(f"D-ID video creation error: {e}")
            return None

    def generate_linkedin_email(self, script: str, lead: Dict):
        company = self.extract_company_name(lead)
        
        prompt = f"""Convert this outreach script into 2 formats:
                    Script: {script}

                    Output as JSON:
                    {{
                    "linkedin": "Short LinkedIn message (max 150 chars)",
                    "email_subject": "Compelling email subject",
                    "email_body": "Professional email body"
                    }}

                    JSON only:"""
        
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3.2:3b", prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                # timeout=12,
                check=True
            )
            
            response = result.stdout.strip()
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)
                    logger.debug(f"LinkedIn message generated: {parsed}")
                    if all(key in parsed for key in ['linkedin', 'email_subject', 'email_body']):
                        return parsed
                    logger.debug(f"LinkedIn message generated but Failed: {parsed}")
                        
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"LinkedIn message generation failed (1): {e}" )
                
            return self.get_fallback_copies(script, company)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.warning(f"LinkedIn/email generation failed: {e}")
            return self.get_fallback_copies(script, company)

    def get_fallback_copies(self, script: str, company: str):
        return {
            "linkedin": f"Hello {company}, I’d love to share a quick insight on optimizing your auth setup that could save time and improve security. Would you be open to a short conversation?",
            "email_subject": f"Auth optimization opportunity for {company}",
            "email_body": script
        }

    def create_assets_for_lead(self, lead: Dict):
        company = self.extract_company_name(lead)
        safe_domain = lead.get("detected_domain", "unknown").replace(".", "_").replace("/", "_")[:50]
        
        logger.info(f"Creating assets for {company}")
        
        # generate script
        script = self.generate_script(lead)
        logger.info(f"Generated script ({len(script)} chars)")
        
        # File paths
        timestamp = int(time.time())
        video_file = self.output_dir / f"{safe_domain}_{timestamp}_video.mp4"
        
        # Generate video
        video_path = self.create_d_id_video(script, video_file)
        
        # Generate LinkedIn/email copies
        copies = self.generate_linkedin_email(script, lead)

        result = {
            "company": company,
            "script": script,
            "video": str(video_path) if video_path and video_path.exists() else None,
            "linkedin": copies.get("linkedin"),
            "email_subject": copies.get("email_subject"),
            "email_body": copies.get("email_body")
        }
        
        # Log asset creation summary
        assets_created = sum(1 for v in [result['video']] if v)
        logger.info(f"-----  Created {assets_created}/2 media assets for {company}  -----")
        
        return result

    def run_for_top_leads(self, top_n=5):
        try:
            leads = self.storage.fetch_joined()[:top_n]
            if not leads:
                logger.warning("No leads found")
                return []
            
            results = []
            total_leads = len(leads)
            
            logger.info(f"Processing {total_leads} top leads...")
            start_time = time.time()
            
            for i, lead in enumerate(leads, 1):
                company = self.extract_company_name(lead)
                logger.info(f"Processing lead {i}/{total_leads}: {company}")
                
                try:
                    lead_start = time.time()
                    assets = self.create_assets_for_lead(lead)
                    lead_time = time.time() - lead_start
                    
                    results.append({**lead, **assets})
                    logger.info(f"Completed lead {i}: {company} ({lead_time:.1f}s)")
                    
                except Exception as e:
                    logger.error(f"Failed to process lead {i} ({company}): {e}")
                    results.append({
                        **lead,
                        "company": company,
                        "script": f"Failed to generate assets for {company}",
                        "video": None,
                        "linkedin": f"Hi! Would love to discuss auth solutions with {company}. Quick chat?",
                        "email_subject": f"Auth optimization for {company}",
                        "email_body": f"Hi there! I'd love to discuss how we can help {company} optimize your authentication systems."
                    })
                    continue
                    
            total_time = time.time() - start_time
            successful_leads = len([r for r in results if r.get('script') and 'Failed to generate' not in r.get('script', '')])
            successful_videos = len([r for r in results if r.get('video')])

            logger.info(f"""
                            Creative Outreach Process Complete:
                            Total Time: {total_time:.1f}s
                            Successful Leads: {successful_leads}/{total_leads}
                            Video Files: {successful_videos}
                            Average Time/Lead: {total_time/total_leads:.1f}s""")
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error in run_for_top_leads: {e}")
            return []