#!/usr/bin/env python3
"""
Simple test to check if the editing system is working
"""

import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_basic_editing():
    """Test basic editing functionality"""
    base_url = "https://webgen-ai-11.preview.emergentagent.com/api"
    
    # Create session
    async with aiohttp.ClientSession() as session:
        # Create session
        logger.info("Creating session...")
        async with session.post(
            f"{base_url}/session/create",
            json={"project_name": "Simple Edit Test"},
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                logger.error(f"Session creation failed: {response.status}")
                return False
            
            data = await response.json()
            session_id = data.get('session_id')
            logger.info(f"✅ Created session: {session_id}")
        
        # Generate initial website
        logger.info("Generating initial website...")
        start_time = time.time()
        
        async with session.post(
            f"{base_url}/generate/website",
            json={
                "session_id": session_id,
                "prompt": "Create a simple landing page with a hero section and contact form",
                "model": "gpt-5",
                "framework": "html"
            },
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=180)
        ) as response:
            generation_time = time.time() - start_time
            
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Website generation failed: {response.status} - {error_text}")
                return False
            
            data = await response.json()
            html_content = data.get('html_content', '')
            logger.info(f"✅ Generated website in {generation_time:.2f}s")
            logger.info(f"   HTML length: {len(html_content)} chars")
            
            # Check for blank screen issues
            if len(html_content) < 500:
                logger.error(f"❌ HTML too short: {len(html_content)} chars")
                return False
            
            if '<body>' not in html_content.lower():
                logger.error("❌ No body tag found")
                return False
            
            if 'hero' not in html_content.lower():
                logger.error("❌ Hero section not found")
                return False
            
            if 'contact' not in html_content.lower():
                logger.error("❌ Contact form not found")
                return False
            
            logger.info("✅ Initial website validation passed")
        
        # Test editing - add a button
        logger.info("Testing edit: Add a button...")
        start_time = time.time()
        
        async with session.post(
            f"{base_url}/generate/website",
            json={
                "session_id": session_id,
                "prompt": "Add a 'Get Started' button to the hero section",
                "model": "gpt-5",
                "framework": "html"
            },
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=180)
        ) as response:
            edit_time = time.time() - start_time
            
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Edit failed: {response.status} - {error_text}")
                return False
            
            data = await response.json()
            edited_html = data.get('html_content', '')
            logger.info(f"✅ Edit completed in {edit_time:.2f}s")
            logger.info(f"   Edited HTML length: {len(edited_html)} chars")
            
            # Check if button was added
            if 'get started' not in edited_html.lower():
                logger.error("❌ 'Get Started' button not found in edited HTML")
                return False
            
            # Check if original content is preserved
            if 'hero' not in edited_html.lower():
                logger.error("❌ Hero section missing after edit")
                return False
            
            if 'contact' not in edited_html.lower():
                logger.error("❌ Contact form missing after edit")
                return False
            
            logger.info("✅ Edit validation passed")
            logger.info("✅ Original content preserved")
            logger.info("✅ New button added successfully")
            
            return True

async def main():
    """Main test runner"""
    logger.info("🚀 Starting Simple Editing Test")
    
    success = await test_basic_editing()
    
    if success:
        logger.info("🎉 Simple editing test PASSED!")
        return 0
    else:
        logger.error("💥 Simple editing test FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)