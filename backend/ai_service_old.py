import os
import logging
import json
import re
from typing import Dict, Any, List, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get_model_config(self, model: str) -> tuple:
        """Map model ID to provider and model name"""
        model_map = {
            "claude-sonnet-4": ("anthropic", "claude-4-sonnet-20250514"),
            "gpt-5": ("openai", "gpt-5"),
            "gpt-5-mini": ("openai", "gpt-5-mini"),
            "gemini-2.5-pro": ("gemini", "gemini-2.5-pro")
        }
        return model_map.get(model, ("openai", "gpt-5"))

    async def generate_response(self, prompt: str, model: str, session_id: str) -> Dict[str, Any]:
        """
        Generate AI response for user prompt
        """
        provider, model_name = self._get_model_config(model)
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="You are Code Weaver, an expert AI assistant that helps users create professional websites. You understand web design, modern frameworks, and can generate clean, production-ready code. Always be helpful, creative, and provide clear explanations."
            )
            chat.with_model(provider, model_name)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {
                "content": response,
                "website_data": None,
                "image_urls": None
            }
        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            return {
                "content": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                "website_data": None,
                "image_urls": None
            }

    async def generate_website(self, prompt: str, model: str, framework: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Generate complete website with proper HTML/CSS/JS
        """
        provider, model_name = self._get_model_config(model)
        session_id = f"gen_{os.urandom(8).hex()}"
        
        logger.info(f"Starting website generation with {provider}/{model_name}")
        logger.info(f"User prompt: {prompt}")
        
        try:
            # Direct generation with very explicit instructions
            result = await self._generate_complete_website(prompt, provider, model_name, session_id)
            
            # Log what was generated
            html_len = len(result.get('html_content', ''))
            css_len = len(result.get('css_content', ''))
            js_len = len(result.get('js_content', ''))
            
            logger.info(f"Generated HTML: {html_len} chars, CSS: {css_len} chars, JS: {js_len} chars")
            
            # Validate we have substantial content
            if html_len < 500:
                logger.error(f"HTML too short ({html_len} chars), retrying...")
                result = await self._generate_complete_website(prompt, provider, model_name, session_id + "_retry")
                html_len = len(result.get('html_content', ''))
                logger.info(f"Retry generated HTML: {html_len} chars")
            
            return result
            
        except Exception as e:
            logger.error(f"Website generation failed: {str(e)}", exc_info=True)
            return self._create_fallback_website(prompt)

    async def _generate_complete_website(self, prompt: str, provider: str, model: str, session_id: str) -> Dict[str, Any]:
        """
        Generate a complete website with explicit, forceful prompting
        """
        chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message="""You are an expert full-stack web developer. You MUST generate complete, working HTML websites.

CRITICAL RULES - FOLLOW EXACTLY:
1. Generate COMPLETE HTML documents (minimum 1000 characters)
2. Include ALL HTML structure: <!DOCTYPE html>, <html>, <head>, <body>
3. Embed ALL CSS inside <style> tags in the <head>
4. Embed ALL JavaScript inside <script> tags before </body>
5. Use modern, beautiful design with proper colors and spacing
6. Make it fully responsive with media queries
7. Include realistic content (not "Lorem ipsum" placeholders)
8. Add interactivity with JavaScript where appropriate
9. Use semantic HTML5 tags
10. Output ONLY the HTML code, nothing else

You will be penalized for:
- Empty or minimal responses
- Missing CSS or JavaScript
- Placeholder text instead of real content
- Incomplete HTML structure
- Black screens or blank pages"""
        )
        chat.with_model(provider, model)
        
        # Create very explicit prompt
        full_prompt = f"""CREATE A COMPLETE, WORKING WEBSITE:

{prompt}

REQUIREMENTS:
1. Full HTML5 document structure
2. Embedded CSS with modern styling (colors, fonts, spacing, animations)
3. Embedded JavaScript for any interactive features
4. Responsive design (mobile, tablet, desktop)
5. Professional appearance
6. Real, meaningful content (not placeholders)

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Title</title>
    <style>
        /* PUT ALL CSS HERE */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            /* MORE STYLES */
        }}
        
        /* ADD ALL YOUR CSS RULES HERE */
    </style>
</head>
<body>
    <!-- PUT ALL HTML CONTENT HERE -->
    
    <script>
        // PUT ALL JAVASCRIPT HERE
    </script>
</body>
</html>
```

START GENERATING NOW. Output ONLY the HTML code block above with your complete website."""
        
        user_message = UserMessage(text=full_prompt)
        response = await chat.send_message(user_message)
        
        logger.info(f"AI Response length: {len(response)} characters")
        logger.info(f"Response preview: {response[:500]}...")
        
        # Extract HTML with multiple strategies
        html_content = self._extract_html_aggressively(response)
        
        if not html_content or len(html_content) < 500:
            logger.warning("HTML extraction failed or too short, using full response")
            html_content = response
        
        # Ensure proper HTML structure
        html_content = self._ensure_proper_html(html_content)
        
        # Extract embedded CSS and JS for reference
        css_content = self._extract_embedded_css(html_content)
        js_content = self._extract_embedded_js(html_content)
        
        logger.info(f"Final HTML length: {len(html_content)}")
        logger.info(f"Extracted CSS length: {len(css_content)}")
        logger.info(f"Extracted JS length: {len(js_content)}")
        
        return {
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "structure": {}
        }

    def _extract_html_aggressively(self, text: str) -> str:
        """Extract HTML using multiple strategies"""
        # Strategy 1: Look for ```html code block
        if "```html" in text:
            try:
                parts = text.split("```html")
                if len(parts) > 1:
                    html = parts[1].split("```")[0].strip()
                    if len(html) > 100:
                        logger.info("Extracted HTML from ```html block")
                        return html
            except:
                pass
        
        # Strategy 2: Look for any ``` code block with HTML content
        if "```" in text:
            try:
                parts = text.split("```")
                for i in range(1, len(parts), 2):
                    potential_html = parts[i].strip()
                    # Remove language identifier if present
                    if potential_html.startswith(("html\n", "HTML\n")):
                        potential_html = potential_html.split("\n", 1)[1]
                    
                    if "<!DOCTYPE" in potential_html or "<html" in potential_html:
                        logger.info("Extracted HTML from generic code block")
                        return potential_html
            except:
                pass
        
        # Strategy 3: Look for DOCTYPE or <html> directly in response
        if "<!DOCTYPE" in text or "<html" in text:
            try:
                # Find start of HTML
                start_idx = text.find("<!DOCTYPE")
                if start_idx == -1:
                    start_idx = text.find("<html")
                
                if start_idx != -1:
                    # Find end of HTML
                    end_idx = text.rfind("</html>")
                    if end_idx != -1:
                        html = text[start_idx:end_idx + 7].strip()
                        logger.info("Extracted HTML by finding DOCTYPE/html tags")
                        return html
            except:
                pass
        
        # Strategy 4: Use regex to find HTML structure
        try:
            pattern = r'<!DOCTYPE html>.*?</html>'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                logger.info("Extracted HTML using regex")
                return match.group(0)
        except:
            pass
        
        logger.warning("All HTML extraction strategies failed")
        return ""

    def _ensure_proper_html(self, html: str) -> str:
        """Ensure HTML has proper structure"""
        html = html.strip()
        
        # Add DOCTYPE if missing
        if not html.startswith("<!DOCTYPE"):
            html = "<!DOCTYPE html>\n" + html
        
        # Ensure it has <html> tags
        if "<html" not in html.lower():
            html = f"<!DOCTYPE html>\n<html lang='en'>\n<head>\n<meta charset='UTF-8'>\n<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n<title>Generated Website</title>\n</head>\n<body>\n{html}\n</body>\n</html>"
        
        # Ensure it has closing tags
        if "</html>" not in html.lower():
            html += "\n</html>"
        
        return html

    def _extract_embedded_css(self, html: str) -> str:
        """Extract CSS from <style> tags"""
        try:
            pattern = r'<style[^>]*>(.*?)</style>'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            return "\n\n".join(matches)
        except:
            return ""

    def _extract_embedded_js(self, html: str) -> str:
        """Extract JavaScript from <script> tags"""
        try:
            pattern = r'<script[^>]*>(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            # Filter out external scripts (those with src attribute)
            return "\n\n".join([m for m in matches if m.strip()])
        except:
            return ""

    def _create_fallback_website(self, prompt: str) -> Dict[str, Any]:
        """Create a fallback website if generation fails"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .container {{
            background: white;
            padding: 60px 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            text-align: center;
        }}
        
        h1 {{
            color: #333;
            font-size: 3em;
            margin-bottom: 20px;
        }}
        
        p {{
            color: #666;
            font-size: 1.2em;
            line-height: 1.6;
            margin-bottom: 30px;
        }}
        
        .button {{
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            transition: transform 0.3s ease;
        }}
        
        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Welcome</h1>
        <p>This is your generated website based on: <strong>{prompt[:200]}</strong></p>
        <p>The website generation system is working. This is a fallback template.</p>
        <a href="#" class="button">Get Started</a>
    </div>
    
    <script>
        console.log('Website loaded successfully!');
        document.querySelector('.button').addEventListener('click', (e) => {{
            e.preventDefault();
            alert('Button clicked! This website is working.');
        }});
    </script>
</body>
</html>"""
        
        return {
            "html_content": html,
            "css_content": self._extract_embedded_css(html),
            "js_content": self._extract_embedded_js(html),
            "structure": {}
        }

    async def generate_image(self, prompt: str) -> str:
        """Generate image using Gemini Imagen"""
        session_id = f"img_{os.urandom(8).hex()}"
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="You are a helpful AI assistant that generates images."
            )
            chat.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(modalities=["image", "text"])
            
            msg = UserMessage(text=f"Create an image: {prompt}")
            text, images = await chat.send_message_multimodal_response(msg)
            
            if images and len(images) > 0:
                return f"data:{images[0]['mime_type']};base64,{images[0]['data']}"
            else:
                raise Exception("No image generated")
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            return "https://via.placeholder.com/800x600?text=Image+Generation+Placeholder"